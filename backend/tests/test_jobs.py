from datetime import date

import pytest
from fastapi.testclient import TestClient

from backend.services import job_search
from backend.services.job_search import (
    JobMatch,
    JobSearchRequest,
    RoleQuery,
    _keywords,
    search_jobs,
)
from backend.services.job_sources import Job, adzuna_posting, greenhouse_level, title_level


def _job(title: str, location: str = "San Jose, CA", posted: date = date(2026, 10, 1)) -> Job:
    return Job(
        company="Acme", title=title, location=location, url="https://x", posted=posted, source="t"
    )


@pytest.mark.parametrize(
    ("title", "level"),
    [
        ("Senior Backend Engineer", "senior"),
        ("Staff Software Engineer", "senior"),
        ("Software Engineer, New Grad", "entry_level"),
        ("Software Engineer I", "entry_level"),
        ("QA Engineer", "mid_level"),
        ("Software Engineering Intern", None),
        ("Engineering Manager", None),
    ],
)
def test_greenhouse_level(title: str, level: str | None) -> None:
    assert greenhouse_level(title) == level


@pytest.mark.parametrize(
    ("title", "level"),
    [
        ("Registered Nurse - ICU", "mid_level"),
        ("Charge Nurse, Med/Surg", "mid_level"),
        ("Graduate Nurse Residency Program", "entry_level"),
        ("Internal Medicine Resident", "entry_level"),
        ("Nurse Manager, Emergency Department", "senior"),
        ("Senior Accountant", "senior"),
        ("Staff Accountant", "mid_level"),
        ("Pharmacy Intern", "internship"),
    ],
)
def test_title_level_covers_non_tech_titles(title: str, level: str) -> None:
    assert title_level(title) == level


def test_adzuna_posting() -> None:
    posting = adzuna_posting(
        {
            "id": "5874770803",
            "title": "Dialysis Registered Nurse",
            "company": {"display_name": "Satellite Healthcare"},
            "location": {"display_name": "San Jose, Santa Clara County"},
            "redirect_url": "https://www.adzuna.com/land/ad/5874770803",
            "created": "2026-09-07T17:35:48Z",
        }
    )
    assert posting.id == "adzuna:5874770803"
    assert posting.level == "mid_level"
    assert posting.company == "Satellite Healthcare"
    assert posting.posted == date(2026, 9, 7)


def test_keywords_drop_generic_words() -> None:
    role = RoleQuery(name="Backend Software Engineering Internship", example_titles=["QA Intern"])
    assert _keywords(role) == {"backend", "software", "qa"}


async def test_search_groups_by_role_and_puts_location_matches_first(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    jobs = [
        _job("Backend Engineer", "New York, NY", posted=date(2026, 10, 5)),
        _job("Backend Engineer", "San Jose, CA", posted=date(2026, 9, 1)),
        _job("QA Analyst"),
        _job("Account Executive"),  # dropped by the keyword filter
    ]

    async def _list_postings(level: str) -> list[Job]:
        return jobs

    async def _classify(batch: list[tuple[int, Job]], roles: object, context: str) -> list:
        assert [j.title for _, j in batch] == ["Backend Engineer", "Backend Engineer", "QA Analyst"]
        return [
            JobMatch(id=0, role=1, location_match=False),
            JobMatch(id=1, role=1, location_match=True),
            JobMatch(id=2, role=None, location_match=True),
        ]

    async def _no_adzuna(request: JobSearchRequest) -> None:
        return None

    monkeypatch.setattr(job_search, "_add_adzuna_postings", _no_adzuna)
    monkeypatch.setattr(job_search, "list_postings", _list_postings)
    monkeypatch.setattr(job_search, "_classify", _classify)

    response = await search_jobs(
        JobSearchRequest(
            roles=[RoleQuery(name="Backend Engineer"), RoleQuery(name="QA Tester")],
            level="mid_level",
            context="California",
        )
    )
    backend, qa = response.results
    assert [j.location for j in backend.jobs] == ["San Jose, CA", "New York, NY"]
    assert qa.jobs == []  # the model said "QA Analyst" fits neither role
    assert response.jobs_considered == 4


def test_search_route_validates_level(client: TestClient) -> None:
    response = client.post("/jobs/search", json={"roles": [{"name": "QA"}], "level": "wizard"})
    assert response.status_code == 422
