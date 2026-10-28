import asyncio
import collections
import re
from datetime import UTC, date, datetime
from typing import Any, Literal

import httpx2
import structlog
from pydantic import BaseModel

from backend.configs.constants import MAX_COMPANY_BOARDS

log = structlog.get_logger(__name__)

Level = Literal["internship", "entry_level", "mid_level", "senior"]

INTERNSHIPS_URL = (
    "https://raw.githubusercontent.com/SimplifyJobs/Summer2027-Internships/dev"
    "/.github/scripts/listings.json"
)
NEW_GRAD_URL = (
    "https://raw.githubusercontent.com/SimplifyJobs/New-Grad-Positions/dev"
    "/.github/scripts/listings.json"
)
GREENHOUSE_BOARD_URL = "https://boards-api.greenhouse.io/v1/boards/{slug}/jobs"
GREENHOUSE_SLUG = re.compile(r"(?:boards|job-boards)\.greenhouse\.io/([A-Za-z0-9_-]+)")

# Title words that decide a Greenhouse job's level.
SENIOR_TITLE = re.compile(r"\b(senior|sr\.?|staff|principal|lead)\b", re.I)
ENTRY_TITLE = re.compile(
    r"\b(new grad|new graduate|entry[- ]level|junior|jr\.?|associate|university grad|"
    r"early career|graduate)\b|\b(I|1)$",
    re.I,
)
EXCLUDED_TITLE = re.compile(
    r"\b(intern|internship|co-?op|director|head of|vp|vice president|chief|manager)\b", re.I
)


class Job(BaseModel):
    company: str
    title: str
    location: str
    url: str
    posted: date | None
    source: str


class Posting(Job):
    """A job as stored in Postgres."""

    id: str  # "<source>:<id in that source>"
    level: Level


async def _fetch_json(client: httpx2.AsyncClient, url: str) -> Any:
    response = await client.get(url)
    response.raise_for_status()
    return response.json()


# -----------------------------
# SimplifyJobs
# -----------------------------


async def fetch_simplify(client: httpx2.AsyncClient, url: str) -> list[dict[str, Any]]:
    """Active rows from a SimplifyJobs listings.json file."""
    rows = await _fetch_json(client, url)
    active = [r for r in rows if r.get("active") and r.get("is_visible", True)]
    log.info("job_source_loaded", url=url, rows=len(rows), active=len(active))
    return active


def simplify_posting(row: dict[str, Any], level: Level) -> Posting:
    posted = row.get("date_posted")
    return Posting(
        id=f"simplify:{row['id']}",
        level=level,
        company=row["company_name"],
        title=row["title"],
        location="; ".join(row.get("locations") or []) or "Not listed",
        url=row["url"],
        posted=datetime.fromtimestamp(posted, UTC).date() if posted else None,
        source="SimplifyJobs",
    )


# -----------------------------
# Greenhouse
# -----------------------------


def greenhouse_slugs(rows: list[dict[str, Any]]) -> list[str]:
    """Greenhouse boards of the companies that appear most often in the Simplify lists."""
    counts: collections.Counter[str] = collections.Counter()
    for row in rows:
        match = GREENHOUSE_SLUG.search(row.get("url") or "")
        if match and match.group(1) != "embed":
            counts[match.group(1)] += 1
    return [slug for slug, _ in counts.most_common(MAX_COMPANY_BOARDS)]


async def fetch_greenhouse(client: httpx2.AsyncClient, slugs: list[str]) -> list[dict[str, Any]]:
    """Every opening on the given Greenhouse boards. Boards that fail are skipped."""
    semaphore = asyncio.Semaphore(20)

    async def board(slug: str) -> list[dict[str, Any]]:
        async with semaphore:
            try:
                data = await _fetch_json(client, GREENHOUSE_BOARD_URL.format(slug=slug))
            except (httpx2.HTTPError, ValueError) as e:
                log.warning("greenhouse_board_failed", slug=slug, error=str(e))
                return []
        jobs: list[dict[str, Any]] = data.get("jobs", [])
        return jobs

    boards = await asyncio.gather(*(board(s) for s in slugs))
    jobs = [job for b in boards for job in b]
    log.info("greenhouse_loaded", boards=len(slugs), jobs=len(jobs))
    return jobs


def greenhouse_level(title: str) -> Level | None:
    """Level from the title; None for internships and management roles."""
    if EXCLUDED_TITLE.search(title):
        return None
    if SENIOR_TITLE.search(title):
        return "senior"
    if ENTRY_TITLE.search(title):
        return "entry_level"
    return "mid_level"


def greenhouse_posting(job: dict[str, Any], level: Level) -> Posting:
    published = job.get("first_published") or job.get("updated_at")
    return Posting(
        id=f"greenhouse:{job['id']}",
        level=level,
        company=job.get("company_name") or "Unknown company",
        title=job["title"],
        location=(job.get("location") or {}).get("name") or "Not listed",
        url=job["absolute_url"],
        posted=date.fromisoformat(published[:10]) if published else None,
        source="Greenhouse",
    )
