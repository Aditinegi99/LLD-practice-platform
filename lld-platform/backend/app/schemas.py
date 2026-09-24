from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class CriterionOut(BaseModel):
    name: str
    description: str
    weight: float
    evaluation_mode: str

    class Config:
        from_attributes = True


class ProblemSummary(BaseModel):
    id: str
    slug: str
    title: str
    difficulty: str
    summary: str

    class Config:
        from_attributes = True


class ProblemDetail(ProblemSummary):
    requirements: list[str]
    constraints: list[str]
    criteria: list[CriterionOut]

    class Config:
        from_attributes = True


class AttemptCreate(BaseModel):
    problem_id: str
    learner_name: str = "learner"


class AttemptOut(BaseModel):
    id: str
    problem_id: str
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SubmissionCreate(BaseModel):
    attempt_id: str
    rationale: Optional[str] = None
    code_payload: Optional[str] = None


class CriterionScoreOut(BaseModel):
    name: str
    score: float
    source: str
    evidence: str
    confidence: float


class FeedbackOut(BaseModel):
    overall_score: float
    summary: str
    follow_up_questions: list[str]
    criterion_scores: list[CriterionScoreOut]

    class Config:
        from_attributes = True


class SubmissionOut(BaseModel):
    id: str
    attempt_id: str
    content_type: str
    rationale: Optional[str]
    code_payload: Optional[str]
    created_at: datetime
    job_status: str
    job_error: Optional[str] = None
    llm_degraded: bool = False
    feedback: Optional[FeedbackOut] = None

    class Config:
        from_attributes = True


class AttemptHistoryItem(BaseModel):
    attempt_id: str
    problem_title: str
    problem_slug: str
    status: str
    created_at: datetime
    latest_score: Optional[float] = None
    submission_count: int
