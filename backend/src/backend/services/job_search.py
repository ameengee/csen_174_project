"""Find listed jobs that match the user's chosen roles and level."""

import asyncio
import re

import structlog
from openai import APIError
from pydantic import BaseModel, Field

from backend.clients import get_openai
from backend.configs.constants import (
    CLASSIFY_BATCH_SIZE,
    CLASSIFY_CONCURRENCY,
    MAX_JOBS_PER_ROLE,
    MAX_SEARCH_CANDIDATES,
)
from backend.configs.exceptions import UpstreamError
from backend.configs.settings import get_settings
from backend.database.job_postings import list_postings
from backend.services.job_sources import Job, Level

log = structlog.get_logger(__name__)


# -----------------------------
# Request / response
# -----------------------------


class RoleQuery(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    example_titles: list[str] = Field(default_factory=list, max_length=20)


class JobSearchRequest(BaseModel):
    roles: list[RoleQuery] = Field(min_length=1, max_length=12)
    level: Level
    # Free-text preferences (answers to the onboarding questions, locations, ...)
    context: str = Field(default="", max_length=4000)


class JobResult(Job):
    location_match: bool


class RoleResults(BaseModel):
    role: str
    jobs: list[JobResult]


class JobSearchResponse(BaseModel):
    level: Level
    jobs_considered: int
    results: list[RoleResults]


# -----------------------------
# Keyword pre-filter
# -----------------------------

# Words that say nothing about the kind of work, so they can't narrow the search.
GENERIC_WORDS = {
    "intern", "internship", "interns", "co-op", "coop", "new", "grad", "graduate", "entry",
    "level", "junior", "senior", "staff", "principal", "lead", "associate", "i", "ii", "iii",
    "and", "or", "of", "for", "the", "a", "an", "in", "to", "with", "role", "roles", "position",
    "summer", "fall", "winter", "spring", "2026", "2027", "2028", "engineer", "engineering",
    "specialist", "team", "early", "career",
}  # fmt: skip


ADVANCED_DEGREE = re.compile(r"\b(phd|ph\.d|doctoral|ms/phd|masters?)\b", re.I)


def _keywords(role: RoleQuery) -> set[str]:
    text = " ".join([role.name, *role.example_titles]).lower()
    return {w for w in re.findall(r"[a-z0-9+#.]+", text) if w not in GENERIC_WORDS and len(w) > 1}


def _matches_any(title: str, keywords: set[str]) -> bool:
    words = set(re.findall(r"[a-z0-9+#.]+", title.lower()))
    return bool(words & keywords)


# -----------------------------
# Model classification
# -----------------------------


class JobMatch(BaseModel):
    id: int
    role: int | None = Field(description="Number of the best-fitting role, or null if none fit")
    location_match: bool


class JobMatches(BaseModel):
    matches: list[JobMatch]


CLASSIFY_PROMPT = """\
You sort job postings for one job seeker. You get the roles they want (numbered), what they \
told us about their preferences, and a list of postings as "id | title | company | location".

For every posting, return its id and:
- role: the number of the role whose kind of work the posting clearly is, or null if it fits \
none of them. Judge the type of work from the title and be strict: the posting must be the same \
discipline as the role, not merely share a word with it. For example, a "Manufacturing Quality \
Engineer" or "RF Test Engineer" is not a software QA role, and a "Thermal Simulation Software \
Engineer" is not a backend role. A generic title such as "Software Engineer" fits a general \
software role but not a specialized one. When unsure, use null.
- location_match: true if the location fits their stated location preferences (a remote \
posting counts when they are open to remote), or if they stated none; otherwise false.

Return every id exactly once."""


async def _classify(
    batch: list[tuple[int, Job]], roles: list[RoleQuery], context: str
) -> list[JobMatch]:
    role_lines = "\n".join(f"{i}. {r.name}" for i, r in enumerate(roles, 1))
    job_lines = "\n".join(f"{i} | {j.title} | {j.company} | {j.location}" for i, j in batch)
    text = (
        f"Roles:\n{role_lines}\n\n"
        f"Preferences:\n{context or 'None stated.'}\n\n"
        f"Postings:\n{job_lines}"
    )
    response = await get_openai().responses.parse(
        model=get_settings().openai_model,
        reasoning={"effort": "low"},
        instructions=CLASSIFY_PROMPT,
        input=text,
        text_format=JobMatches,
        store=False,
    )
    if response.output_parsed is None:
        raise UpstreamError("The job matching came back empty.")
    return response.output_parsed.matches


async def search_jobs(request: JobSearchRequest) -> JobSearchResponse:
    """Return listed jobs at the requested level, grouped by the role they fit."""
    jobs = await list_postings(request.level)
    if not jobs:
        raise UpstreamError(
            "No job listings are loaded yet. Run: python scripts/sync_jobs.py"
        )

    if request.level in ("internship", "entry_level"):
        # Research roles that require a PhD or Master's aren't open to these candidates.
        jobs = [j for j in jobs if not ADVANCED_DEGREE.search(j.title)]

    keywords = set().union(*(_keywords(r) for r in request.roles))
    candidates = [j for j in jobs if _matches_any(j.title, keywords)][:MAX_SEARCH_CANDIDATES]
    log.info(
        "job_search_candidates",
        level=request.level,
        listed=len(jobs),
        candidates=len(candidates),
        keywords=sorted(keywords),
    )

    numbered = list(enumerate(candidates))
    batches = [
        numbered[i : i + CLASSIFY_BATCH_SIZE] for i in range(0, len(numbered), CLASSIFY_BATCH_SIZE)
    ]
    semaphore = asyncio.Semaphore(CLASSIFY_CONCURRENCY)

    async def run(batch: list[tuple[int, Job]]) -> list[JobMatch]:
        async with semaphore:
            try:
                return await _classify(batch, request.roles, request.context)
            except (APIError, UpstreamError) as e:
                log.error("job_classify_batch_failed", size=len(batch), error=str(e))
                return []

    matches = [m for ms in await asyncio.gather(*(run(b) for b in batches)) for m in ms]
    if batches and not matches:
        raise UpstreamError("Couldn't match jobs right now. Try again.")

    grouped: dict[int, list[JobResult]] = {i: [] for i in range(len(request.roles))}
    for m in matches:
        if m.role is None or not 1 <= m.role <= len(request.roles):
            continue
        if not 0 <= m.id < len(candidates):
            continue
        job = candidates[m.id]
        grouped[m.role - 1].append(JobResult(**job.model_dump(), location_match=m.location_match))

    results = []
    for i, role in enumerate(request.roles):
        # Jobs in the right place first; within that, newest first (sort is stable).
        role_jobs = sorted(grouped[i], key=lambda j: j.posted or "", reverse=True)
        role_jobs.sort(key=lambda j: not j.location_match)
        results.append(RoleResults(role=role.name, jobs=role_jobs[:MAX_JOBS_PER_ROLE]))

    return JobSearchResponse(level=request.level, jobs_considered=len(jobs), results=results)
