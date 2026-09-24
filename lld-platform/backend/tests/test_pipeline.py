from app import models
from app.evaluators.base import Evaluator, EvaluatorOutput, CriterionResult
from app.evaluators.composite import CompositeEvaluator
from app.evaluators.deterministic import DeterministicEvaluator
from app.evaluators.pipeline import EvaluationPipeline


class FakeLLMEvaluator(Evaluator):
    """Stand-in for the real Groq-backed evaluator so pipeline tests don't
    depend on network access or an API key."""
    handles_mode = "llm"

    def __init__(self, should_fail=False):
        self.should_fail = should_fail

    def evaluate(self, data):
        if self.should_fail:
            return EvaluatorOutput(
                results=[CriterionResult(c["name"], 50.0, "llm", "AI evaluation unavailable.", confidence=0.0)
                         for c in data.criteria if c["evaluation_mode"] in ("llm", "both")],
                degraded=True,
                error_message="Simulated network failure",
            )
        results = [
            CriterionResult(c["name"], 85.0, "llm", "Looks reasonable.", confidence=0.8)
            for c in data.criteria if c["evaluation_mode"] in ("llm", "both")
        ]
        return EvaluatorOutput(results=results, follow_up_questions=["What if a bus arrives with no double spot free?"])


def make_attempt_and_submission(db_session, problem, code="class ParkingLot:\n    def find_spot(self): pass\n"):
    attempt = models.Attempt(problem_id=problem.id, learner_name="learner")
    db_session.add(attempt)
    db_session.flush()
    submission = models.Submission(
        attempt_id=attempt.id, content_type=models.ContentType.CODE,
        rationale="I split responsibilities across ParkingLot and ParkingSpot.",
        code_payload=code,
    )
    db_session.add(submission)
    db_session.flush()
    job = models.EvaluationJob(submission_id=submission.id)
    db_session.add(job)
    db_session.commit()
    return attempt, submission, job


def test_pipeline_completes_and_persists_feedback(db_session, parking_problem):
    _, _, job = make_attempt_and_submission(db_session, parking_problem)
    evaluator = CompositeEvaluator([DeterministicEvaluator(), FakeLLMEvaluator(should_fail=False)])
    pipeline = EvaluationPipeline(db_session, evaluator=evaluator)

    feedback = pipeline.run(job)

    assert job.status == models.JobStatus.COMPLETED
    assert job.llm_degraded == 0
    assert feedback.overall_score > 0
    assert len(feedback.criterion_scores) == len(parking_problem.criteria)
    assert len(feedback.follow_up_questions) >= 1


def test_pipeline_marks_degraded_when_llm_fails_but_still_completes(db_session, parking_problem):
    _, _, job = make_attempt_and_submission(db_session, parking_problem)
    evaluator = CompositeEvaluator([DeterministicEvaluator(), FakeLLMEvaluator(should_fail=True)])
    pipeline = EvaluationPipeline(db_session, evaluator=evaluator)

    feedback = pipeline.run(job)

    # Key failure-handling behaviour: a failed LLM call degrades the job,
    # it does NOT fail the whole evaluation - deterministic results still land.
    assert job.status == models.JobStatus.COMPLETED
    assert job.llm_degraded == 1
    assert "unavailable" in feedback.summary.lower()
    deterministic_results = [c for c in feedback.criterion_scores if c["source"] == "deterministic"]
    assert len(deterministic_results) > 0


def test_weighted_aggregation_favors_higher_weight_criteria(db_session, parking_problem):
    _, _, job = make_attempt_and_submission(db_session, parking_problem, code="")
    evaluator = CompositeEvaluator([DeterministicEvaluator(), FakeLLMEvaluator(should_fail=False)])
    pipeline = EvaluationPipeline(db_session, evaluator=evaluator)

    feedback = pipeline.run(job)

    # Empty code tanks deterministic criteria (weight ~2.5 total) while the
    # fake LLM still returns 85s for llm criteria (weight 4.0 total) - overall
    # should sit noticeably above the deterministic-only average.
    deterministic_scores = [c["score"] for c in feedback.criterion_scores if c["source"] == "deterministic"]
    assert feedback.overall_score > sum(deterministic_scores) / len(deterministic_scores)


def test_pipeline_raises_and_marks_failed_on_unexpected_error(db_session, parking_problem):
    _, submission, job = make_attempt_and_submission(db_session, parking_problem)

    class ExplodingEvaluator(Evaluator):
        handles_mode = "both"
        def evaluate(self, data):
            raise RuntimeError("boom")

    pipeline = EvaluationPipeline(db_session, evaluator=ExplodingEvaluator())
    try:
        pipeline.run(job)
        assert False, "expected RuntimeError to propagate"
    except RuntimeError:
        pass

    assert job.status == models.JobStatus.FAILED
    assert "boom" in job.error_message
