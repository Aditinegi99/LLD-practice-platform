"""
Strategy interface for evaluators.

Any evaluator — deterministic, LLM-based, or a future one (static-analysis
tool, a second LLM, a rule engine) — implements `evaluate` and returns a
list of CriterionResult. The pipeline doesn't care how a result was
produced, only that it declares its own `source` so the learner-facing
feedback can distinguish "checked mechanically" from "AI judgment."
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class CriterionResult:
    criterion_name: str
    score: float              # 0-100
    source: str                # "deterministic" | "llm"
    evidence: str              # short, specific justification
    confidence: float = 1.0    # 0-1, mainly meaningful for LLM results


@dataclass
class EvaluationInput:
    problem_title: str
    requirements: list
    constraints: list
    expected_entities: list
    criteria: list             # list of dicts: {name, description, weight, evaluation_mode}
    rationale: Optional[str]
    code_payload: Optional[str]


@dataclass
class EvaluatorOutput:
    results: list = field(default_factory=list)   # list[CriterionResult]
    follow_up_questions: list = field(default_factory=list)
    degraded: bool = False       # True if this evaluator could not run fully
    error_message: Optional[str] = None


class Evaluator(ABC):
    @abstractmethod
    def evaluate(self, data: EvaluationInput) -> EvaluatorOutput:
        raise NotImplementedError

    @property
    @abstractmethod
    def handles_mode(self):
        """Which EvaluationMode value(s) this evaluator is responsible for."""
        raise NotImplementedError
