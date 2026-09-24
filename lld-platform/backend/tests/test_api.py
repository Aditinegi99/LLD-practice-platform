import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# make sure no real GROQ key is picked up during API tests - we want the
# LLM evaluator's documented no-key fallback path to be exercised
os.environ["GROQ_API_KEY"] = ""

from app.main import app
from app.database import Base, get_db
from app.seed import seed

TEST_ENGINE = create_engine(
    "sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool
)
TestSession = sessionmaker(bind=TEST_ENGINE)


def override_get_db():
    db = TestSession()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True, scope="module")
def setup_db():
    Base.metadata.create_all(bind=TEST_ENGINE)
    session = TestSession()
    seed(session)
    session.close()


client = TestClient(app)


def test_health():
    resp = client.get("/api/health")
    assert resp.status_code == 200


def test_list_problems_returns_seeded_problems():
    resp = client.get("/api/problems")
    assert resp.status_code == 200
    slugs = {p["slug"] for p in resp.json()}
    assert {"parking-lot", "elevator-system", "vending-machine"}.issubset(slugs)


def test_get_problem_detail_includes_criteria():
    resp = client.get("/api/problems/parking-lot")
    assert resp.status_code == 200
    body = resp.json()
    assert body["title"] == "Parking Lot System"
    assert len(body["criteria"]) >= 4


def test_get_unknown_problem_404s():
    resp = client.get("/api/problems/does-not-exist")
    assert resp.status_code == 404


def test_full_practice_loop_end_to_end():
    problem = client.get("/api/problems/vending-machine").json()

    attempt_resp = client.post("/api/attempts", json={"problem_id": problem["id"], "learner_name": "test-learner"})
    assert attempt_resp.status_code == 200
    attempt = attempt_resp.json()
    assert attempt["status"] == "in_progress"

    submission_resp = client.post("/api/submissions", json={
        "attempt_id": attempt["id"],
        "rationale": "I separated Inventory from Payment handling.",
        "code_payload": "class VendingMachine:\n    def dispense(self): pass\nclass Inventory:\n    def check_stock(self): pass\n",
    })
    assert submission_resp.status_code == 200
    submission = submission_resp.json()
    # no GROQ key configured in this test run -> LLM evaluator degrades gracefully
    assert submission["job_status"] == "completed"
    assert submission["llm_degraded"] is True
    assert submission["feedback"] is not None
    assert submission["feedback"]["overall_score"] >= 0

    history_resp = client.get("/api/history", params={"learner_name": "test-learner"})
    assert history_resp.status_code == 200
    history = history_resp.json()
    assert any(h["attempt_id"] == attempt["id"] for h in history)


def test_submission_requires_some_content():
    problem = client.get("/api/problems/vending-machine").json()
    attempt = client.post("/api/attempts", json={"problem_id": problem["id"], "learner_name": "test-learner"}).json()
    resp = client.post("/api/submissions", json={"attempt_id": attempt["id"]})
    assert resp.status_code == 422


def test_retry_endpoint_recomputes_feedback():
    problem = client.get("/api/problems/parking-lot").json()
    attempt = client.post("/api/attempts", json={"problem_id": problem["id"], "learner_name": "test-learner"}).json()
    submission = client.post("/api/submissions", json={
        "attempt_id": attempt["id"], "code_payload": "class ParkingLot:\n    def park(self): pass\n",
    }).json()

    retry_resp = client.post(f"/api/submissions/{submission['id']}/retry")
    assert retry_resp.status_code == 200
    assert retry_resp.json()["job_status"] == "completed"
