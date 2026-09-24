"""
CompositeEvaluator

Runs every registered Evaluator against the same EvaluationInput and merges
their CriterionResults into one list, keyed by criterion name. Because each
Criterion has exactly one evaluation_mode, there's no overlap to resolve in
practice - but the merge is written to tolerate it (last-write-wins with a
warning) so a future 'BOTH' mode that runs two evaluators on one criterion
and blends their scores is a small change here, not a redesign.
"""
from .base import Evaluator, EvaluationInput, EvaluatorOutput


class CompositeEvaluator(Evaluator):
    handles_mode = "both"

    def __init__(self, evaluators: list[Evaluator]):
        self.evaluators = evaluators

    def evaluate(self, data: EvaluationInput) -> EvaluatorOutput:
        merged_results = {}
        follow_ups = []
        degraded = False
        errors = []

        for evaluator in self.evaluators:
            output = evaluator.evaluate(data)
            for result in output.results:
                merged_results[result.criterion_name] = result
            follow_ups.extend(output.follow_up_questions)
            if output.degraded:
                degraded = True
                if output.error_message:
                    errors.append(output.error_message)

        return EvaluatorOutput(
            results=list(merged_results.values()),
            follow_up_questions=follow_ups[:3],
            degraded=degraded,
            error_message="; ".join(errors) if errors else None,
        )
