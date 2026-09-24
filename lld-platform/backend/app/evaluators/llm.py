"""
LLMEvaluator

Handles the criteria that need judgment rather than pattern matching:
trade-off reasoning, quality of separation of concerns, comparison against
sane reference approaches, and generating Socratic follow-up questions.

Uses Groq's OpenAI-compatible chat completions endpoint (free tier,
Llama 3.3 70B by default). If the call fails or times out, `evaluate`
returns a degraded EvaluatorOutput instead of raising - the pipeline
decides what to do with that (see pipeline.py / EvaluationJob states).
"""
import json
import os
import re

import requests

from .base import Evaluator, EvaluationInput, EvaluatorOutput, CriterionResult

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
DEFAULT_MODEL = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")
TIMEOUT_SECONDS = 20


class LLMEvaluator(Evaluator):
    handles_mode = "llm"

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.environ.get("GROQ_API_KEY")

    def evaluate(self, data: EvaluationInput) -> EvaluatorOutput:
        llm_criteria = [c for c in data.criteria if c["evaluation_mode"] in ("llm", "both")]
        if not llm_criteria:
            return EvaluatorOutput(results=[])

        if not self.api_key:
            return EvaluatorOutput(
                results=[self._fallback_result(c["name"]) for c in llm_criteria],
                degraded=True,
                error_message="No GROQ_API_KEY configured.",
            )

        prompt = self._build_prompt(data, llm_criteria)
        try:
            response = requests.post(
                GROQ_URL,
                headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                json={
                    "model": DEFAULT_MODEL,
                    "messages": [
                        {"role": "system", "content": self._system_prompt()},
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": 0.3,
                    "response_format": {"type": "json_object"},
                },
                timeout=TIMEOUT_SECONDS,
            )
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
            parsed = self._parse_json(content)
        except Exception as exc:  # network error, timeout, bad JSON, rate limit, etc.
            return EvaluatorOutput(
                results=[self._fallback_result(c["name"]) for c in llm_criteria],
                degraded=True,
                error_message=f"{type(exc).__name__}: {exc}",
            )

        results = []
        for c in llm_criteria:
            item = next((x for x in parsed.get("criteria", []) if x.get("name") == c["name"]), None)
            if item:
                results.append(CriterionResult(
                    criterion_name=c["name"],
                    score=float(item.get("score", 50)),
                    source="llm",
                    evidence=item.get("evidence", "").strip() or "No evidence returned.",
                    confidence=float(item.get("confidence", 0.7)),
                ))
            else:
                results.append(self._fallback_result(c["name"]))

        return EvaluatorOutput(
            results=results,
            follow_up_questions=parsed.get("follow_up_questions", [])[:3],
        )

    # -- helpers -------------------------------------------------------

    def _system_prompt(self) -> str:
        return (
            "You are a strict but constructive Low-Level Design (LLD) reviewer. "
            "You evaluate a learner's design rationale and code/pseudocode against a rubric. "
            "There is often more than one valid design - judge whether the *given* design is "
            "internally consistent, meets the stated requirements, and follows good "
            "object-oriented principles, not whether it matches one 'correct' answer. "
            "Always respond with a single JSON object, no prose outside the JSON, matching this shape: "
            '{"criteria": [{"name": str, "score": 0-100, "evidence": str (1-3 sentences, specific, '
            'reference actual class/method names from the submission when possible), "confidence": 0-1}], '
            '"follow_up_questions": [str, str, str] (Socratic questions that probe an edge case or '
            "trade-off the learner's design may not have considered)}"
        )

    def _build_prompt(self, data: EvaluationInput, llm_criteria) -> str:
        criteria_desc = "\n".join(f"- {c['name']}: {c['description']}" for c in llm_criteria)
        return (
            f"Problem: {data.problem_title}\n"
            f"Requirements:\n" + "\n".join(f"- {r}" for r in data.requirements) + "\n"
            f"Constraints:\n" + "\n".join(f"- {c}" for c in data.constraints) + "\n\n"
            f"Criteria to evaluate:\n{criteria_desc}\n\n"
            f"Learner's design rationale:\n{data.rationale or '(none provided)'}\n\n"
            f"Learner's code/pseudocode:\n{data.code_payload or '(none provided)'}\n"
        )

    def _parse_json(self, content: str) -> dict:
        content = content.strip()
        # some models wrap JSON in markdown fences despite instructions
        match = re.search(r"\{.*\}", content, re.DOTALL)
        return json.loads(match.group(0) if match else content)

    def _fallback_result(self, criterion_name: str) -> CriterionResult:
        return CriterionResult(
            criterion_name=criterion_name,
            score=50.0,
            source="llm",
            evidence="AI evaluation unavailable for this criterion; showing a neutral placeholder score.",
            confidence=0.0,
        )
