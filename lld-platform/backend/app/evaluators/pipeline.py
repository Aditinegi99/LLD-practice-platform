"""
EvaluationPipeline - Template Method.

Fixed skeleton: parse -> evaluate -> aggregate -> persist. Each step is a
separate method so a future problem type or submission format can override
just the step it needs (e.g. a DiagramSubmission might need a different
`_parse` that runs OCR/graph-extraction before handing off to the same
evaluate/aggregate/persist steps).

This is also where failure handling lives: if the LLM evaluator degrades,
we still persist whatever deterministic results we have, mark the job as
COMPLETED but flagged `llm_degraded`, and let the API surface that so the
frontend can show "AI feedback unavailable, retry" instead of silently
dropping half the rubric.
"""
from datetime import datetime

from sqlalchemy.orm import Session

from .. import models
from .base import EvaluationInput
from .composite import CompositeEvaluator
from .deterministic import DeterministicEvaluator
from .llm import LLMEvaluator


class EvaluationPipeline:
    def __init__(self, db: Session, evaluator: CompositeEvaluator | None = None):
        self.db = db
        self.evaluator = evaluator or CompositeEvaluator([DeterministicEvaluator(), LLMEvaluator()])

    def run(self, job: models.EvaluationJob) -> models.Feedback:
        job.status = models.JobStatus.RUNNING
        self.db.commit()

        try:
            data = self._parse(job)
            output = self.evaluator.evaluate(data)
            feedback = self._aggregate(job, data, output)
            self._persist(job, feedback, degraded=output.degraded, error=output.error_message)
            return feedback
        except Exception as exc:
            job.status = models.JobStatus.FAILED
            job.error_message = f"{type(exc).__name__}: {exc}"
            job.completed_at = datetime.utcnow()
            self.db.commit()
            raise

    # -- template steps --------------------------------------------------

    def _parse(self, job: models.EvaluationJob) -> EvaluationInput:
        submission = job.submission
        attempt = submission.attempt
        problem = attempt.problem
        criteria = [
            {
                "name": c.name,
                "description": c.description,
                "weight": c.weight,
                "evaluation_mode": c.evaluation_mode.value,
            }
            for c in problem.criteria
        ]
        return EvaluationInput(
            problem_title=problem.title,
            requirements=problem.requirements,
            constraints=problem.constraints or [],
            expected_entities=problem.expected_entities or [],
            criteria=criteria,
            rationale=submission.rationale,
            code_payload=submission.code_payload,
        )

    def _aggregate(self, job, data: EvaluationInput, output) -> models.Feedback:
        weight_by_name = {c["name"]: c["weight"] for c in data.criteria}
        total_weight = sum(weight_by_name.values()) or 1.0

        criterion_scores = []
        weighted_sum = 0.0
        for result in output.results:
            w = weight_by_name.get(result.criterion_name, 1.0)
            weighted_sum += result.score * w
            criterion_scores.append({
                "name": result.criterion_name,
                "score": round(result.score, 1),
                "source": result.source,
                "evidence": result.evidence,
                "confidence": result.confidence,
            })

        overall = round(weighted_sum / total_weight, 1) if output.results else 0.0
        summary = self._summarize(overall, criterion_scores, output.degraded)

        return models.Feedback(
            job_id=job.id,
            overall_score=overall,
            summary=summary,
            follow_up_questions=output.follow_up_questions,
            criterion_scores=criterion_scores,
        )

    def _summarize(self, overall: float, criterion_scores: list, degraded: bool) -> str:
        if not criterion_scores:
            return "No criteria could be evaluated for this submission."
        weakest = min(criterion_scores, key=lambda c: c["score"])
        strongest = max(criterion_scores, key=lambda c: c["score"])
        tier = "strong" if overall >= 80 else "solid" if overall >= 60 else "needs work"
        msg = (
            f"Overall this is a {tier} attempt ({overall}/100). "
            f"Strongest area: {strongest['name']} ({strongest['score']}/100). "
            f"Focus next on: {weakest['name']} ({weakest['score']}/100) - {weakest['evidence']}"
        )
        if degraded:
            msg += " Note: AI-based feedback was unavailable for part of this evaluation; scores from the AI reviewer are neutral placeholders and should be treated with caution."
        return msg

    def _persist(self, job: models.EvaluationJob, feedback: models.Feedback, degraded: bool, error: str | None):
        job.status = models.JobStatus.COMPLETED
        job.llm_degraded = 1 if degraded else 0
        job.error_message = error
        job.completed_at = datetime.utcnow()
        self.db.add(feedback)
        self.db.commit()
        self.db.refresh(feedback)
