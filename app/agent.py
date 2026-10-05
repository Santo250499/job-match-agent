import re
from collections import Counter

from openai import APIConnectionError, APIError, AuthenticationError, OpenAI
from pydantic import ValidationError

from app.config import Settings
from app.schemas import JobMatchAnalysis, JobMatchRequest, SkillAssessment


COMMON_SKILLS = {
    "python",
    "javascript",
    "typescript",
    "react",
    "next.js",
    "node.js",
    "fastapi",
    "flask",
    "django",
    "sql",
    "excel",
    "power bi",
    "tableau",
    "azure",
    "aws",
    "google cloud",
    "git",
    "github",
    "docker",
    "automation",
    "artificial intelligence",
    "machine learning",
    "data analysis",
    "data entry",
    "customer service",
    "communication",
    "stakeholder management",
    "project management",
    "leadership",
    "teamwork",
    "problem solving",
    "attention to detail",
    "microsoft office",
    "microsoft teams",
    "crm",
    "salesforce",
    "xero",
    "myob",
    "accounts payable",
    "accounts receivable",
    "administration",
    "reporting",
}


class AgentError(Exception):
    """A safe application-level error that can be shown to an API user."""


def normalise_text(text: str) -> str:
    """
    Convert text into a consistent form for keyword comparison.
    """
    lowered = text.lower()
    lowered = re.sub(r"[^a-z0-9+#.\-\s]", " ", lowered)
    return " ".join(lowered.split())


def contains_skill(text: str, skill: str) -> bool:
    """
    Check whether a skill appears as a recognisable phrase.
    """
    escaped_skill = re.escape(skill)
    pattern = rf"(?<![a-z0-9]){escaped_skill}(?![a-z0-9])"

    return re.search(
        pattern,
        text,
        flags=re.IGNORECASE,
    ) is not None


def detect_job_seniority(job_description: str) -> str:
    """
    Detect an approximate job seniority level from the advertisement.

    The function is deliberately conservative. If the advertisement does not
    contain enough evidence, it returns 'unknown'.
    """
    job = normalise_text(job_description)

    senior_patterns = [
        r"\bsenior\b",
        r"\bteam lead\b",
        r"\blead developer\b",
        r"\blead analyst\b",
        r"\blead engineer\b",
        r"\bmanager\b",
        r"\bmanagement role\b",
        r"\bprincipal\b",
        r"\b5\+?\s*years?\b",
        r"\bfive\s+years?\b",
        r"\b6\+?\s*years?\b",
        r"\bsix\s+years?\b",
        r"\b7\+?\s*years?\b",
        r"\bseven\s+years?\b",
    ]

    mid_patterns = [
        r"\bmid[- ]level\b",
        r"\bintermediate\b",
        r"\b3\+?\s*years?\b",
        r"\bthree\s+years?\b",
        r"\b4\+?\s*years?\b",
        r"\bfour\s+years?\b",
    ]

    entry_patterns = [
        r"\bjunior\b",
        r"\bgraduate\b",
        r"\bentry[- ]level\b",
        r"\bentry level\b",
        r"\btrainee\b",
        r"\bintern\b",
        r"\b0[- ]?2\s+years?\b",
        r"\b1[- ]?2\s+years?\b",
    ]

    if any(re.search(pattern, job) for pattern in senior_patterns):
        return "senior"

    if any(re.search(pattern, job) for pattern in mid_patterns):
        return "mid"

    if any(re.search(pattern, job) for pattern in entry_patterns):
        return "entry"

    return "unknown"


def extract_job_skills(job_description: str) -> list[str]:
    """
    Extract known skills mentioned in the job description.
    """
    normalised_job = normalise_text(job_description)

    found_skills = [
        skill
        for skill in sorted(COMMON_SKILLS)
        if contains_skill(normalised_job, skill)
    ]

    return found_skills


def find_repeated_job_terms(job_description: str) -> list[str]:
    """
    Find frequently repeated meaningful words.
    """
    ignored_words = {
        "and",
        "the",
        "with",
        "for",
        "you",
        "your",
        "our",
        "are",
        "will",
        "this",
        "that",
        "from",
        "have",
        "has",
        "job",
        "role",
        "work",
        "team",
        "skills",
        "experience",
        "required",
        "preferred",
        "candidate",
        "position",
        "ability",
        "including",
        "responsibilities",
    }

    words = re.findall(
        r"\b[a-z][a-z+#.-]{2,}\b",
        job_description.lower(),
    )

    useful_words = [
        word
        for word in words
        if word not in ignored_words
    ]

    counts = Counter(useful_words)

    return [
        word
        for word, count in counts.most_common(8)
        if count >= 2
    ]


def build_demo_analysis(
    request: JobMatchRequest,
) -> JobMatchAnalysis:
    """
    Produce a deterministic analysis without calling an AI API.
    """
    resume = normalise_text(request.resume_text)
    job = normalise_text(request.job_description)

    job_seniority = detect_job_seniority(
        request.job_description
    )

    requested_skills = extract_job_skills(job)
    repeated_terms = find_repeated_job_terms(job)

    if not requested_skills:
        requested_skills = repeated_terms[:6]

    if not requested_skills:
        requested_skills = [
            "communication",
            "problem solving",
            "attention to detail",
        ]

    matched: list[SkillAssessment] = []
    partial: list[SkillAssessment] = []
    missing: list[SkillAssessment] = []

    for skill in requested_skills:
        resume_has_skill = contains_skill(
            resume,
            skill,
        )

        job_occurrences = len(
            re.findall(
                rf"(?<![a-z0-9])"
                rf"{re.escape(skill)}"
                rf"(?![a-z0-9])",
                job,
            )
        )

        if resume_has_skill:
            matched.append(
                SkillAssessment(
                    skill=skill.title(),
                    status="matched",
                    evidence=(
                        f"The résumé contains a direct reference to "
                        f"'{skill}'. The candidate should ensure that "
                        "the statement includes a real example or result."
                    ),
                    recommendation=(
                        "Keep the skill and connect it to a truthful "
                        "achievement, responsibility or project result."
                    ),
                )
            )

        elif job_occurrences >= 2:
            missing.append(
                SkillAssessment(
                    skill=skill.title(),
                    status="missing",
                    evidence=(
                        f"The job description emphasises '{skill}', "
                        "but no direct evidence was found in the résumé."
                    ),
                    recommendation=(
                        "Add this skill only when it is genuinely "
                        "supported by your experience. Otherwise, "
                        "identify it as a development area."
                    ),
                )
            )

        else:
            partial.append(
                SkillAssessment(
                    skill=skill.title(),
                    status="partial",
                    evidence=(
                        f"The job description mentions '{skill}', "
                        "but the résumé does not state it clearly "
                        "enough for automatic matching."
                    ),
                    recommendation=(
                        "Review your real experience for related "
                        "evidence and use clear wording without "
                        "exaggerating your capability."
                    ),
                )
            )

    total_requirements = max(
        len(requested_skills),
        1,
    )

    matched_points = len(matched) * 1.0
    partial_points = len(partial) * 0.4

    skill_score = (
        (matched_points + partial_points)
        / total_requirements
    ) * 70

    completeness_score = 0

    if len(request.resume_text) >= 400:
        completeness_score += 10

    if any(
        indicator in resume
        for indicator in [
            "achieved",
            "improved",
            "reduced",
            "increased",
            "managed",
            "created",
            "developed",
            "delivered",
        ]
    ):
        completeness_score += 10

    if re.search(
        r"\b\d+([.%+]|\s?(years?|months?|clients?|projects?))\b",
        resume,
    ):
        completeness_score += 10

    overall_score = round(
        min(
            skill_score + completeness_score,
            100,
        )
    )

    actions: list[str] = []

    if missing:
        actions.append(
            "Review the missing requirements and add only those "
            "supported by your real work, study, volunteering "
            "or project experience."
        )

    if partial:
        actions.append(
            "Replace vague skill claims with short "
            "evidence-based bullet points."
        )

    if completeness_score < 20:
        actions.append(
            "Add measurable and truthful outcomes, such as time "
            "saved, volume processed, customers supported or "
            "errors reduced."
        )

    actions.extend(
        [
            (
                "Use wording from the job advertisement only where "
                "it accurately describes your experience."
            ),
            (
                "Proofread the final résumé and confirm that every "
                "claim can be explained in an interview."
            ),
        ]
    )

    information_to_confirm: list[str] = []

    if not re.search(
        r"\b\d+([.%+]|\s?(years?|months?|clients?|projects?))\b",
        resume,
    ):
        information_to_confirm.append(
            "Provide truthful numbers or outcomes for "
            "relevant achievements."
        )

    if (
        "australia" not in resume
        and request.australian_context
    ):
        information_to_confirm.append(
            "Confirm your Australian work rights, location and "
            "availability before adding them to the application."
        )

    australian_notes: list[str] = []

    if request.australian_context:
        australian_notes = [
            "Use Australian English spelling consistently.",
            (
                "Include work-rights information only when it is "
                "accurate and useful."
            ),
            (
                "Focus the résumé on evidence relevant to the "
                "advertised selection criteria."
            ),
            (
                "Do not include sensitive personal details that "
                "the employer did not request."
            ),
        ]

    if overall_score >= 80:
        summary = (
            "The résumé has strong visible alignment with the "
            "analysed job requirements, subject to manual "
            "verification of every claim."
        )

    elif overall_score >= 60:
        summary = (
            "The résumé has moderate alignment but needs clearer "
            "evidence and more direct coverage of important "
            "requirements."
        )

    else:
        summary = (
            "The résumé currently shows limited visible alignment "
            "with the job description and needs targeted, "
            "truthful improvement."
        )

    score_explanation = (
        f"The demonstration score is {overall_score}/100. "
        "Up to 70 points come from direct and partial skill "
        "alignment. Up to 30 points come from résumé "
        "completeness, action-focused evidence and measurable "
        "outcomes. The score is an application-strength "
        "indicator, not a promise of employment."
    )

    return JobMatchAnalysis(
        overall_score=overall_score,
        job_seniority=job_seniority,
        score_explanation=score_explanation,
        summary=summary,
        matched_skills=matched,
        partial_skills=partial,
        missing_skills=missing,
        recommended_actions=actions,
        information_to_confirm=information_to_confirm,
        australian_market_notes=australian_notes,
    )


def build_agent_instructions(
    australian_context: bool,
) -> str:
    australian_instruction = (
        """
Include practical Australian employment-market guidance.
Use Australian English spelling.
Do not assume the candidate has Australian work rights.
Tell the candidate to confirm location, availability and work rights when missing.
"""
        if australian_context
        else ""
    )

    return f"""
You are a careful job-application analysis agent.

Your task is to compare a candidate's real résumé with a job description.

Critical honesty rules:
1. Never invent employment, education, skills, achievements, qualifications,
   certificates, projects, dates or numerical results.
2. Treat absent evidence as absent.
3. Clearly identify information the candidate needs to confirm.
4. Do not promise interviews or employment.
5. Do not inflate the score to satisfy the user.
6. Recommendations must be practical and supported by the supplied text.
7. An overall score of 80 or above is allowed only when the supplied résumé
   genuinely supports strong alignment.
8. Every matched skill must include résumé evidence.
9. Every missing skill must clearly say that no supporting evidence was found.
10. The score explanation must describe the scoring logic.

Classify job_seniority as exactly one of:
- entry
- mid
- senior
- unknown

Use the job advertisement itself as evidence.
Do not assume a seniority level when it is unclear.

Scoring guidance:
- Relevant skills and requirements: 70 points.
- Evidence quality and specific achievements: 20 points.
- Clarity and application readiness: 10 points.

{australian_instruction}
""".strip()


def build_openai_analysis(
    request: JobMatchRequest,
    settings: Settings,
) -> JobMatchAnalysis:
    """
    Ask the external model for a structured response.
    """
    if not settings.openai_api_key:
        raise AgentError(
            "APP_MODE is set to 'openai', but OPENAI_API_KEY "
            "is missing. Add the key to your private .env file "
            "or change APP_MODE to 'demo'."
        )

    client = OpenAI(
        api_key=settings.openai_api_key
    )

    user_input = f"""
RÉSUMÉ:
{request.resume_text}

JOB DESCRIPTION:
{request.job_description}
""".strip()

    try:
        response = client.responses.parse(
            model=settings.openai_model,
            instructions=build_agent_instructions(
                australian_context=request.australian_context
            ),
            input=user_input,
            text_format=JobMatchAnalysis,
        )

        parsed_result = response.output_parsed

        if parsed_result is None:
            raise AgentError(
                "The AI service returned no validated analysis. "
                "Try again or switch to demonstration mode."
            )

        return parsed_result

    except AuthenticationError as error:
        raise AgentError(
            "The AI API rejected the key. Check "
            "OPENAI_API_KEY in your private .env file."
        ) from error

    except APIConnectionError as error:
        raise AgentError(
            "The application could not connect to the AI "
            "service. Check your internet connection and try again."
        ) from error

    except ValidationError as error:
        raise AgentError(
            "The AI response did not match the required "
            "data structure."
        ) from error

    except APIError as error:
        raise AgentError(
            "The AI service returned an error. Try again later "
            "or use demo mode."
        ) from error


def analyse_job_match(
    request: JobMatchRequest,
    settings: Settings,
) -> JobMatchAnalysis:
    """
    Route the request to the configured analysis method.
    """
    if settings.app_mode == "demo":
        return build_demo_analysis(request)

    if settings.app_mode == "openai":
        return build_openai_analysis(
            request,
            settings,
        )

    raise AgentError(
        "The configured APP_MODE is not supported."
    )