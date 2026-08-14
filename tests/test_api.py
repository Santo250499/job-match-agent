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

    assert result["job_seniority"] in [
        "entry",
        "mid",
        "senior",
        "unknown",
    ]

    assert isinstance(
        result["matched_skills"],
        list,
    )

    assert isinstance(
        result["partial_skills"],
        list,
    )

    assert isinstance(
        result["missing_skills"],
        list,
    )

    assert isinstance(
        result["recommended_actions"],
        list,
    )

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
        "Python FastAPI Excel reporting communication stakeholder "
        "management and automation experience with detailed "
        "responsibilities and outcomes."
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

    assert (
        "identical"
        in response.json()["detail"].lower()
    )


def test_missing_required_field_is_rejected() -> None:
    response = client.post(
        "/analyse",
        json={
            "resume_text": SAMPLE_RESUME,
        },
    )

    assert response.status_code == 422


def test_entry_level_job_is_detected() -> None:
    entry_job = """
    Junior Automation Assistant

    This entry-level position is suitable for a graduate who wants
    to develop professional automation experience. The candidate
    should understand Python, Excel, communication and reporting.
    """

    response = client.post(
        "/analyse",
        json={
            "resume_text": SAMPLE_RESUME,
            "job_description": entry_job,
            "australian_context": True,
        },
    )

    assert response.status_code == 200

    assert (
        response.json()["job_seniority"]
        == "entry"
    )


def test_senior_job_is_detected() -> None:
    senior_job = """
    Senior Automation Engineer

    We are seeking a senior automation engineer with at least
    five years of professional experience. The successful
    candidate will lead automation projects and mentor team
    members. Python, FastAPI, Git and stakeholder management
    skills are required.
    """

    response = client.post(
        "/analyse",
        json={
            "resume_text": SAMPLE_RESUME,
            "job_description": senior_job,
            "australian_context": True,
        },
    )

    assert response.status_code == 200

    assert (
        response.json()["job_seniority"]
        == "senior"
    )


def test_australian_notes_can_be_disabled() -> None:
    response = client.post(
        "/analyse",
        json={
            "resume_text": SAMPLE_RESUME,
            "job_description": SAMPLE_JOB,
            "australian_context": False,
        },
    )

    assert response.status_code == 200

    assert (
        response.json()["australian_market_notes"]
        == []
    )