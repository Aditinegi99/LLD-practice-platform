"""
Domain models for the LLD Practice Platform.

Design notes (see docs/DESIGN_NOTE.md for the full writeup):
- Problem owns a Rubric made of Criteria. Each Criterion declares its own
  evaluation_mode (deterministic / llm / both) so the pipeline knows which
  evaluator(s) are responsible for it.
- Attempt is the "session" for one learner working a problem; it can hold
  many Submissions (a learner can submit, get feedback, revise, resubmit).
- Submission stores content polymorphically via `content_type` +
  `content_payload` (JSON). This is the persistence side of the
  SubmissionContent strategy described in the design note — adding a new
  submission format (e.g. a diagram) means adding a new content_type and a
  parser, not changing this table.
- EvaluationJob is a small state machine (PENDING -> RUNNING -> COMPLETED /
  FAILED) so submission and evaluation are decoupled. Feedback belongs to
  the job, not the submission directly, because a resubmission triggers a
  brand new evaluation job.
"""
import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Column, String, Text, DateTime, ForeignKey, Float, Integer, JSON, Enum as SAEnum
)
from sqlalchemy.orm import relationship

from .database import Base


def gen_id() -> str:
    return uuid.uuid4().hex[:12]


class EvaluationMode(str, enum.Enum):
    DETERMINISTIC = "deterministic"
    LLM = "llm"
    BOTH = "both"


class ContentType(str, enum.Enum):
    TEXT = "text"          # free-form design rationale
    CODE = "code"           # class/interface stubs, pseudocode or real code


class AttemptStatus(str, enum.Enum):
    IN_PROGRESS = "in_progress"
    SUBMITTED = "submitted"
    EVALUATED = "evaluated"


class JobStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class Problem(Base):
    __tablename__ = "problems"

    id = Column(String, primary_key=True, default=gen_id)
    slug = Column(String, unique=True, nullable=False)
    title = Column(String, nullable=False)
    difficulty = Column(String, nullable=False, default="medium")
    summary = Column(Text, nullable=False)
    requirements = Column(JSON, nullable=False)          # list[str]
    constraints = Column(JSON, nullable=False, default=list)  # list[str]
    expected_entities = Column(JSON, nullable=False, default=list)  # hints for deterministic checks
    created_at = Column(DateTime, default=datetime.utcnow)

    criteria = relationship("Criterion", back_populates="problem", cascade="all, delete-orphan")
    attempts = relationship("Attempt", back_populates="problem", cascade="all, delete-orphan")


class Criterion(Base):
    """One rubric line item for a Problem, e.g. 'Responsibility Assignment'."""
    __tablename__ = "criteria"

    id = Column(String, primary_key=True, default=gen_id)
    problem_id = Column(String, ForeignKey("problems.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    weight = Column(Float, nullable=False, default=1.0)   # relative weight, normalized at scoring time
    evaluation_mode = Column(SAEnum(EvaluationMode), nullable=False, default=EvaluationMode.LLM)

    problem = relationship("Problem", back_populates="criteria")


class Attempt(Base):
    """A learner's ongoing session working one Problem. Can span multiple submissions."""
    __tablename__ = "attempts"

    id = Column(String, primary_key=True, default=gen_id)
    problem_id = Column(String, ForeignKey("problems.id"), nullable=False)
    learner_name = Column(String, nullable=False, default="learner")
    status = Column(SAEnum(AttemptStatus), nullable=False, default=AttemptStatus.IN_PROGRESS)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    problem = relationship("Problem", back_populates="attempts")
    submissions = relationship("Submission", back_populates="attempt", cascade="all, delete-orphan",
                                order_by="Submission.created_at")


class Submission(Base):
    __tablename__ = "submissions"

    id = Column(String, primary_key=True, default=gen_id)
    attempt_id = Column(String, ForeignKey("attempts.id"), nullable=False)
    content_type = Column(SAEnum(ContentType), nullable=False)
    rationale = Column(Text, nullable=True)      # learner's written design reasoning
    code_payload = Column(Text, nullable=True)   # class/interface stubs or pseudocode
    created_at = Column(DateTime, default=datetime.utcnow)

    attempt = relationship("Attempt", back_populates="submissions")
    job = relationship("EvaluationJob", back_populates="submission", uselist=False,
                        cascade="all, delete-orphan")


class EvaluationJob(Base):
    __tablename__ = "evaluation_jobs"

    id = Column(String, primary_key=True, default=gen_id)
    submission_id = Column(String, ForeignKey("submissions.id"), nullable=False, unique=True)
    status = Column(SAEnum(JobStatus), nullable=False, default=JobStatus.PENDING)
    error_message = Column(Text, nullable=True)
    llm_degraded = Column(Integer, default=0)  # 1 if LLM step failed and we fell back to deterministic-only
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    submission = relationship("Submission", back_populates="job")
    feedback = relationship("Feedback", back_populates="job", uselist=False, cascade="all, delete-orphan")


class Feedback(Base):
    __tablename__ = "feedback"

    id = Column(String, primary_key=True, default=gen_id)
    job_id = Column(String, ForeignKey("evaluation_jobs.id"), nullable=False, unique=True)
    overall_score = Column(Float, nullable=False)          # 0-100, weighted aggregate
    summary = Column(Text, nullable=False)                 # short narrative
    follow_up_questions = Column(JSON, nullable=False, default=list)  # Socratic prompts, list[str]
    criterion_scores = Column(JSON, nullable=False)        # list[dict]: name, score, source, evidence
    created_at = Column(DateTime, default=datetime.utcnow)

    job = relationship("EvaluationJob", back_populates="feedback")
