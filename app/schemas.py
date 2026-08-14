from typing import Literal

from pydantic import BaseModel, Field, field_validator


class JobMatchRequest(BaseModel):
    """
    Information submitted by the user for analysis.
    """

    resume_text: str = Field(
        ...,
        min_length=50,
        description="The candidate's real résumé or CV text.",
    )
    job_description: str = Field(
        ...,
        min_length=50,
        description="The complete job advertisement or position description.",
    )
    australian_context: bool = Field(
        default=True,
        description="Whether to include Australian employment-market guidance.",
    )

    @field_validator("resume_text", "job_description")
    @classmethod
    def clean_text(cls, value: str) -> str:
        cleaned_value = " ".join(value.split())

        if not cleaned_value:
            raise ValueError("This field cannot be empty.")

        return cleaned_value


class SkillAssessment(BaseModel):
    """
    Assessment of one job-related skill or requirement.
    """

    skill: str = Field(min_length=1, max_length=100)
    status: Literal["matched", "partial", "missing"]
    evidence: str = Field(
        min_length=1,
        description=(
            "Evidence found in the résumé, or a clear statement that "
            "no evidence was found."
        ),
    )
    recommendation: str = Field(
        min_length=1,
        description="An honest action the candidate can take.",
    )


class JobMatchAnalysis(BaseModel):
    """
    Validated structure returned by the agent.
    """

    overall_score: int = Field(ge=0, le=100)

    job_seniority: Literal[
        "entry",
        "mid",
        "senior",
        "unknown",
    ] = "unknown"

    score_explanation: str = Field(min_length=20)
    summary: str = Field(min_length=20)

    matched_skills: list[SkillAssessment] = Field(default_factory=list)
    partial_skills: list[SkillAssessment] = Field(default_factory=list)
    missing_skills: list[SkillAssessment] = Field(default_factory=list)

    recommended_actions: list[str] = Field(default_factory=list)
    information_to_confirm: list[str] = Field(default_factory=list)
    australian_market_notes: list[str] = Field(default_factory=list)

    honesty_statement: str = Field(
        default=(
            "This analysis must not invent employment, qualifications, skills, "
            "achievements or experience."
        )
    )

    @field_validator(
        "recommended_actions",
        "information_to_confirm",
        "australian_market_notes",
    )
    @classmethod
    def remove_empty_list_items(cls, values: list[str]) -> list[str]:
        return [value.strip() for value in values if value.strip()]


class HealthResponse(BaseModel):
    status: Literal["healthy"]
    mode: Literal["demo", "openai"]
    application: str


class ErrorResponse(BaseModel):
    detail: str