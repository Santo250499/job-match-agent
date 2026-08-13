from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from app.agent import AgentError, analyse_job_match
from app.config import get_settings
from app.schemas import (
    ErrorResponse,
    HealthResponse,
    JobMatchAnalysis,
    JobMatchRequest,
)

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    description=(
        "A Day 8 bootcamp API that compares résumé text with a job description "
        "and returns validated structured output."
    ),
    version="1.0.0",
)

# These development origins allow a local frontend to call the API.
# Production deployment should list only the real deployed frontend URL.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.get(
    "/",
    summary="API information",
)
def root() -> dict[str, str]:
    return {
        "message": "Day 8 Job Match Agent API is running.",
        "documentation": "/docs",
        "health_check": "/health",
        "analysis_endpoint": "/analyse",
        "mode": settings.app_mode,
    }


@app.get(
    "/health",
    response_model=HealthResponse,
    summary="Check whether the API is healthy",
)
def health_check() -> HealthResponse:
    return HealthResponse(
        status="healthy",
        mode=settings.app_mode,
        application=settings.app_name,
    )


@app.post(
    "/analyse",
    response_model=JobMatchAnalysis,
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": ErrorResponse},
        status.HTTP_413_REQUEST_ENTITY_TOO_LARGE: {"model": ErrorResponse},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": ErrorResponse},
        status.HTTP_503_SERVICE_UNAVAILABLE: {"model": ErrorResponse},
    },
    summary="Analyse a résumé against a job description",
)
def analyse(request: JobMatchRequest) -> JobMatchAnalysis:
    total_characters = len(request.resume_text) + len(request.job_description)

    if total_characters > settings.max_input_characters:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=(
                "The combined résumé and job description are too long. "
                f"The maximum is {settings.max_input_characters:,} characters."
            ),
        )

    if request.resume_text.lower() == request.job_description.lower():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "The résumé and job description appear to be identical. "
                "Please submit two different documents."
            ),
        )

    try:
        return analyse_job_match(request, settings)

    except AgentError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(error),
        ) from error

    except Exception as error:
        # A real production system should send the full technical error
        # to secure server logs, not expose it to the user.
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "An unexpected server error occurred. Check the terminal logs "
                "and try again."
            ),
        ) from error