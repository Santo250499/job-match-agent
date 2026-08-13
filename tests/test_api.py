from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


SAMPLE_RESUME = """
Nawshin E Tasnim

Profile:
Entry-level AI automation developer with project experience using Python,
FastAPI, Excel, Git and GitHub.

Projects:
Created an AI job application assistant that compares CV content with job
descriptions. Developed validation logic and structured project documentation.
Used Excel for data checking and reporting.

Experience:
Supported customers, prepared reports and worked with team members to solve
administrative problems. Improved a repeated reporting process and completed
three automation projects.
"""

SAMPLE_JOB = """
Junior Automation Assistant

We are seeking a candidate with Python, FastAPI, Git, GitHub and Excel skills.
The successful candidate will support automation projects, communicate with
stakeholders, prepare reports and demonstrate attention to detail.

Experience with Azure and Power BI is preferred. Strong communication and
problem solving are required.
"""


def test_root_endpoint() -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert response.json()["documentation"] == "/docs"


def test_health_endpoint() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    assert response.json()["mode"] in ["demo", "openai"]


def test_analysis_returns_valid_structure() -> None:
    response = client.post(
        "/analyse",
        json={
            "resume_text": SAMPLE_RESUME,
            "job_description": SAMPLE_JOB,
            "australian_context": True,
        },
    )

    assert response.status_code == 200

    result = response.json()

    assert 0 <= result["overall_score"] <= 100
    assert isinstance(result["matched_skills"], list)
    assert isinstance(result["partial_skills"], list)
    assert isinstance(result["missing_skills"], list)
    assert isinstance(result["recommended_actions"], list)
    assert result["honesty_statement"]


def test_short_resume_is_rejected() -> None:
    response = client.post(
        "/analyse",
        json={
            "resume_text": "Too short",
            "job_description": SAMPLE_JOB,
            "australian_context": True,
        },
    )

    assert response.status_code == 422


def test_identical_documents_are_rejected() -> None:
    repeated_text = (
        "Python FastAPI Excel reporting communication stakeholder management "
        "and automation experience with detailed responsibilities and outcomes."
    )

    response = client.post(
        "/analyse",
        json={
            "resume_text": repeated_text,
            "job_description": repeated_text,
            "australian_context": True,
        },
    )

    assert response.status_code == 400
    assert "identical" in response.json()["detail"].lower()


def test_missing_required_field_is_rejected() -> None:
    response = client.post(
        "/analyse",
        json={
            "resume_text": SAMPLE_RESUME,
        },
    )

    assert response.status_code == 422