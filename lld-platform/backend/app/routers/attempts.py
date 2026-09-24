from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/api/attempts", tags=["attempts"])


@router.post("", response_model=schemas.AttemptOut)
def create_attempt(payload: schemas.AttemptCreate, db: Session = Depends(get_db)):
    problem = db.query(models.Problem).filter(models.Problem.id == payload.problem_id).first()
    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found")
    attempt = models.Attempt(problem_id=problem.id, learner_name=payload.learner_name)
    db.add(attempt)
    db.commit()
    db.refresh(attempt)
    return attempt


@router.get("/{attempt_id}", response_model=schemas.AttemptOut)
def get_attempt(attempt_id: str, db: Session = Depends(get_db)):
    attempt = db.query(models.Attempt).filter(models.Attempt.id == attempt_id).first()
    if not attempt:
        raise HTTPException(status_code=404, detail="Attempt not found")
    return attempt
