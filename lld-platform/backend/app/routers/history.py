from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload

from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/api/history", tags=["history"])


@router.get("", response_model=list[schemas.AttemptHistoryItem])
def get_history(learner_name: str = "learner", db: Session = Depends(get_db)):
    attempts = (
        db.query(models.Attempt)
        .options(joinedload(models.Attempt.problem), joinedload(models.Attempt.submissions))
        .filter(models.Attempt.learner_name == learner_name)
        .order_by(models.Attempt.created_at.desc())
        .all()
    )
    items = []
    for a in attempts:
        latest_score = None
        for s in reversed(a.submissions):
            if s.job and s.job.feedback:
                latest_score = s.job.feedback.overall_score
                break
        items.append(schemas.AttemptHistoryItem(
            attempt_id=a.id,
            problem_title=a.problem.title,
            problem_slug=a.problem.slug,
            status=a.status.value,
            created_at=a.created_at,
            latest_score=latest_score,
            submission_count=len(a.submissions),
        ))
    return items


@router.get("/{attempt_id}/submissions")
def get_attempt_submissions(attempt_id: str, db: Session = Depends(get_db)):
    from ..routers.submissions import _to_out
    attempt = db.query(models.Attempt).options(joinedload(models.Attempt.submissions)).filter(
        models.Attempt.id == attempt_id
    ).first()
    if not attempt:
        return []
    return [_to_out(s) for s in attempt.submissions]
