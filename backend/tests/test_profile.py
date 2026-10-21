from typing import Any

import pytest
from fastapi.testclient import TestClient

from backend.configs.exceptions import InvalidRequestError
from backend.services.profile_analysis import (
    CandidateProfile,
    JobTarget,
    ProfileAnalysis,
    SearchPreferences,
)
from backend.services.profile_input import build_profile_content


def _analysis() -> ProfileAnalysis:
    return ProfileAnalysis(
        profile=CandidateProfile(
            name="Ada Lovelace",
            headline=None,
            location="London",
            career_stage="mid_level",
            summary="Mathematician.",
            experiences=[],
            education=[],
            skills=["Mathematics"],
            certifications=[],
            other_accomplishments=[],
        ),
        job_targets=[
            JobTarget(
                name="Research Mathematician",
                industry="Research",
                seniority="mid-level",
                employment_type="full-time",
                example_titles=["Mathematician"],
                search_keywords=["mathematics"],
                why_it_fits="Published analysis of the Analytical Engine.",
            )
        ],
        preferences=SearchPreferences(locations=["London"], open_to_remote=None, notes=[]),
        open_questions=[],
    )


def test_pdf_becomes_input_file() -> None:
    blocks = build_profile_content(b"%PDF-1.7 fake")
    assert blocks[0]["type"] == "input_file"
    assert blocks[0]["file_data"].startswith("data:application/pdf;base64,")


def test_unknown_file_type_is_rejected() -> None:
    with pytest.raises(InvalidRequestError):
        build_profile_content(b"just some text")


def test_analyze_route(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    seen: dict[str, Any] = {}

    async def _fake_analyze(content: list[dict[str, Any]], notes: str | None) -> ProfileAnalysis:
        seen["content"], seen["notes"] = content, notes
        return _analysis()

    monkeypatch.setattr("backend.server.routes.profile.analyze_profile", _fake_analyze)

    response = client.post(
        "/profile/analyze",
        files={"file": ("profile.pdf", b"%PDF-1.7 fake", "application/pdf")},
        data={"notes": "  Prefer London  "},
    )
    assert response.status_code == 200
    assert response.json()["job_targets"][0]["name"] == "Research Mathematician"
    assert seen["notes"] == "Prefer London"
    assert seen["content"][0]["type"] == "input_file"


def test_analyze_route_rejects_bad_upload(client: TestClient) -> None:
    response = client.post(
        "/profile/analyze", files={"file": ("notes.txt", b"hello", "text/plain")}
    )
    assert response.status_code == 400
