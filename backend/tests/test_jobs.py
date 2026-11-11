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
from backend.services.job_sources import Job, greenhouse_level


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
