from typing import Any, Literal

import structlog
from openai import APIError
from pydantic import BaseModel, Field

from backend.clients import get_openai
from backend.configs.constants import PROFILE_ANALYSIS_MAX_TOKENS
from backend.configs.exceptions import UpstreamError
from backend.configs.settings import get_settings

log = structlog.get_logger(__name__)


# -----------------------------
# Output schema (also the API response body)
# -----------------------------


class Experience(BaseModel):
    title: str
    organization: str
    start: str | None = Field(description="e.g. 'Jul 2026'; null if not stated")
    end: str | None = Field(description="e.g. 'Present' or 'May 2025'; null if not stated")
    location: str | None
    highlights: list[str] = Field(description="Accomplishments, kept factual and specific")


class Education(BaseModel):
    school: str
    degree: str | None
    field_of_study: str | None
    start: str | None
    end: str | None
    details: list[str] = Field(description="GPA, honors, activities, relevant coursework")


class CandidateProfile(BaseModel):
    name: str | None
    headline: str | None
    location: str | None
    career_stage: Literal["student", "entry_level", "mid_level", "senior", "executive"]
    summary: str = Field(description="Two or three sentences on who this person is professionally")
    experiences: list[Experience]
    education: list[Education]
    skills: list[str]
    certifications: list[str]
    other_accomplishments: list[str] = Field(
        description="Awards, publications, projects, licenses, volunteering, etc."
    )


class JobTarget(BaseModel):
    name: str = Field(
        description="Short label for this kind of job, e.g. 'Backend Software Engineer'"
    )
    industry: str
    seniority: str = Field(description="e.g. 'internship', 'new grad', 'attending physician'")
    employment_type: str = Field(description="e.g. 'internship', 'full-time', 'contract', 'locum'")
    example_titles: list[str] = Field(description="Job-posting titles to look for")
    search_keywords: list[str] = Field(description="Keywords to search job boards with")
    why_it_fits: str = Field(description="One or two sentences grounded in the profile")


class SearchPreferences(BaseModel):
    locations: list[str] = Field(description="Places the person wants to work; empty if unknown")
    open_to_remote: bool | None
    notes: list[str] = Field(description="Other stated preferences (company size, hours, ...)")


class ProfileAnalysis(BaseModel):
    profile: CandidateProfile
    job_targets: list[JobTarget] = Field(description="Ordered from best fit to weakest fit")
    preferences: SearchPreferences
    open_questions: list[str] = Field(
        description="Things worth asking the person that would sharpen the job search"
    )


# -----------------------------
# Prompt
# -----------------------------

SYSTEM_PROMPT = """\
You help people find jobs. You will receive someone's professional profile, usually their \
LinkedIn profile as a PDF, sometimes with notes they wrote themselves.

Do two things:

1. Extract their profile into the structured format. Copy facts faithfully: titles, \
organizations, dates, numbers. Never invent or embellish anything. If something is not in the \
input, leave it null or empty.

2. Decide which kinds of jobs they should search for. Return 3 to 8 job targets, best fit \
first. These people can be in any field (software, medicine, law, trades, education, finance, \
and so on), so reason from their actual background rather than assuming a field. Use their \
career stage to set seniority: a student wants internships or new-grad roles, an experienced \
physician wants attending or locum roles. Include adjacent roles they are clearly qualified \
for, not only their current title. If their notes state preferences (location, remote, roles \
to avoid), follow them and record them under preferences.

Use open_questions for things that would meaningfully change the search and that the profile \
does not answer, such as work authorization, relocation, or preferred locations."""


async def analyze_profile(content: list[dict[str, Any]], notes: str | None) -> ProfileAnalysis:
    """Extract a structured profile and a ranked list of job targets with an OpenAI model."""
    user_content = [*content]
    if notes:
        user_content.append({"type": "input_text", "text": f"Notes from the person:\n{notes}"})
    user_content.append(
        {
            "type": "input_text",
            "text": "Extract my profile and decide which jobs I should look for.",
        }
    )

    try:
        response = await get_openai().responses.parse(
            model=get_settings().openai_model,
            max_output_tokens=PROFILE_ANALYSIS_MAX_TOKENS,
            reasoning={"effort": "medium"},
            instructions=SYSTEM_PROMPT,
            input=[{"role": "user", "content": user_content}],  # type: ignore[list-item,misc]
            text_format=ProfileAnalysis,
            store=False,
        )
    except APIError as e:
        log.error("profile_analysis_api_error", error_type=type(e).__name__, error=str(e))
        raise UpstreamError("The profile could not be analyzed right now. Try again.") from e

    usage = response.usage
    log.info(
        "profile_analysis_complete",
        model=response.model,
        status=response.status,
        input_tokens=usage.input_tokens if usage else None,
        output_tokens=usage.output_tokens if usage else None,
    )
    if response.status == "incomplete":
        reason = response.incomplete_details.reason if response.incomplete_details else None
        log.warning("profile_analysis_incomplete", reason=reason)
        raise UpstreamError("The analysis came back incomplete. Try again.")
    if response.output_parsed is None:
        # The model refused, or returned no structured output.
        raise UpstreamError("The profile could not be analyzed.")
    return response.output_parsed
