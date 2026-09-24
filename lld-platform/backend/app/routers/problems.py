from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/api/problems", tags=["problems"])


@router.get("", response_model=list[schemas.ProblemSummary])
def list_problems(db: Session = Depends(get_db)):
    return db.query(models.Problem).all()


@router.get("/{slug}", response_model=schemas.ProblemDetail)
def get_problem(slug: str, db: Session = Depends(get_db)):
    problem = (
        db.query(models.Problem)
        .options(joinedload(models.Problem.criteria))
        .filter(models.Problem.slug == slug)
        .first()
    )
    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found")
    return problem
