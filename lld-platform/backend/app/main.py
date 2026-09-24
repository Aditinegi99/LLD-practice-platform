from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import models
from .database import engine, SessionLocal
from .seed import seed
from .routers import problems, attempts, submissions, history

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="LLD Practice Platform API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # fine for a local take-home prototype; would be locked down for real deployment
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    db = SessionLocal()
    try:
        seed(db)
    finally:
        db.close()


@app.get("/api/health")
def health():
    return {"status": "ok"}


app.include_router(problems.router)
app.include_router(attempts.router)
app.include_router(submissions.router)
app.include_router(history.router)
