from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..evaluators.pipeline import EvaluationPipeline

router = APIRouter(prefix="/api/submissions", tags=["submissions"])


def _to_out(submission: models.Submission) -> schemas.SubmissionOut:
    job = submission.job
    feedback = None
    if job and job.feedback:
        feedback = schemas.FeedbackOut(
            overall_score=job.feedback.overall_score,
            summary=job.feedback.summary,
            follow_up_questions=job.feedback.follow_up_questions,
            criterion_scores=job.feedback.criterion_scores,
        )
    return schemas.SubmissionOut(
        id=submission.id,
        attempt_id=submission.attempt_id,
        content_type=submission.content_type.value,
        rationale=submission.rationale,
        code_payload=submission.code_payload,
        created_at=submission.created_at,
        job_status=job.status.value if job else "pending",
        job_error=job.error_message if job else None,
        llm_degraded=bool(job.llm_degraded) if job else False,
        feedback=feedback,
    )


def _run_evaluation(db: Session, submission: models.Submission):
    """Runs the pipeline inline. Kept as its own function so it's the one
    place to swap for a background task queue later without touching the
    route handlers (see docs/DESIGN_NOTE.md, 'scaling evaluation')."""
    pipeline = EvaluationPipeline(db)
    try:
        pipeline.run(submission.job)
    except Exception:
        # job.status is already set to FAILED inside the pipeline;
        # we swallow here so the HTTP response still returns the submission
        # with its failed status rather than a 500.
        pass


@router.post("", response_model=schemas.SubmissionOut)
def create_submission(payload: schemas.SubmissionCreate, db: Session = Depends(get_db)):
    attempt = db.query(models.Attempt).filter(models.Attempt.id == payload.attempt_id).first()
    if not attempt:
        raise HTTPException(status_code=404, detail="Attempt not found")
    if not (payload.rationale or "").strip() and not (payload.code_payload or "").strip():
        raise HTTPException(status_code=422, detail="Submission needs a rationale, code, or both.")

    content_type = models.ContentType.CODE if (payload.code_payload or "").strip() else models.ContentType.TEXT
    submission = models.Submission(
        attempt_id=attempt.id, content_type=content_type,
        rationale=payload.rationale, code_payload=payload.code_payload,
    )
    db.add(submission)
    db.flush()

    job = models.EvaluationJob(submission_id=submission.id)
    db.add(job)
    attempt.status = models.AttemptStatus.SUBMITTED
    db.commit()
    db.refresh(submission)

    _run_evaluation(db, submission)
    db.refresh(submission)
    if submission.job and submission.job.status == models.JobStatus.COMPLETED:
        attempt.status = models.AttemptStatus.EVALUATED
        db.commit()

    return _to_out(submission)


@router.get("/{submission_id}", response_model=schemas.SubmissionOut)
def get_submission(submission_id: str, db: Session = Depends(get_db)):
    submission = db.query(models.Submission).filter(models.Submission.id == submission_id).first()
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    return _to_out(submission)


@router.post("/{submission_id}/retry", response_model=schemas.SubmissionOut)
def retry_evaluation(submission_id: str, db: Session = Depends(get_db)):
    """Re-runs evaluation for a submission whose job FAILED or degraded
    (e.g. the LLM call timed out). Deterministic results are recomputed too,
    since they're cheap and idempotent - only the job/feedback rows are replaced."""
    submission = db.query(models.Submission).filter(models.Submission.id == submission_id).first()
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")

    if submission.job and submission.job.feedback:
        db.delete(submission.job.feedback)
    if submission.job:
        submission.job.status = models.JobStatus.PENDING
        submission.job.error_message = None
        submission.job.llm_degraded = 0
    else:
        submission.job = models.EvaluationJob(submission_id=submission.id)
        db.add(submission.job)
    db.commit()
    db.refresh(submission)

    _run_evaluation(db, submission)
    db.refresh(submission)
    return _to_out(submission)
