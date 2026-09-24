"""
DeterministicEvaluator

Runs cheap, reproducible, explainable checks against the code payload.
Deliberately narrow: it should never need an LLM call and the same input
should always produce the same output. This is what should be trusted for
"is the required structure present" style criteria, while nuanced
judgment ("is this a *good* separation of concerns") is left to the LLM.

Checks implemented:
1. Entity coverage - do the expected class/interface names (or close
   variants) appear in the submitted code?
2. God-class heuristic - flag any class block with an unusually high
   method count relative to the others (simple line-based heuristic, not
   a real parser - documented limitation in README).
3. Naming convention - classes should be CapWords, methods snake_case or
   camelCase consistently (either is accepted, mixing within one file is
   flagged).
"""
import re
from statistics import mean

from .base import Evaluator, EvaluationInput, EvaluatorOutput, CriterionResult

CLASS_DECL_RE = re.compile(r"\b(?:class|interface)\s+([A-Za-z_][A-Za-z0-9_]*)")
METHOD_DECL_RE = re.compile(r"\b(?:def|public|private|protected)?\s*[A-Za-z_<>\[\],\s]*\b([a-zA-Z_][A-Za-z0-9_]*)\s*\(")


class DeterministicEvaluator(Evaluator):
    handles_mode = "deterministic"

    def evaluate(self, data: EvaluationInput) -> EvaluatorOutput:
        code = data.code_payload or ""
        results = []

        for criterion in [c for c in data.criteria if c["evaluation_mode"] in ("deterministic", "both")]:
            name = criterion["name"].lower()
            if "entit" in name or "structur" in name or "requirement" in name:
                results.append(self._check_entity_coverage(criterion["name"], code, data.expected_entities))
            elif "god" in name or "coupling" in name or "cohesion" in name:
                results.append(self._check_god_class(criterion["name"], code))
            elif "naming" in name:
                results.append(self._check_naming(criterion["name"], code))
            else:
                # generic fallback: presence of *any* class/interface at all
                results.append(self._check_has_structure(criterion["name"], code))

        return EvaluatorOutput(results=results)

    # -- individual checks -------------------------------------------------

    def _check_entity_coverage(self, criterion_name, code, expected_entities):
        if not expected_entities:
            return CriterionResult(criterion_name, 100.0, "deterministic",
                                    "No specific entities required by this problem.")
        found = set(m.group(1).lower() for m in CLASS_DECL_RE.finditer(code))
        expected = [e.lower() for e in expected_entities]
        hits = [e for e in expected if any(e in f or f in e for f in found)]
        coverage = len(hits) / len(expected)
        missing = [e for e in expected_entities if e.lower() not in hits]
        evidence = (
            f"Found {len(hits)}/{len(expected)} expected entities."
            + (f" Missing: {', '.join(missing)}." if missing else " All expected entities present.")
        )
        return CriterionResult(criterion_name, round(coverage * 100, 1), "deterministic", evidence)

    def _check_god_class(self, criterion_name, code):
        classes = list(CLASS_DECL_RE.finditer(code))
        if len(classes) < 2:
            return CriterionResult(criterion_name, 70.0, "deterministic",
                                    "Fewer than 2 classes detected; god-class heuristic is not meaningful yet.",
                                    confidence=0.4)
        # split code roughly by class boundaries and count method decls per block
        bounds = [m.start() for m in classes] + [len(code)]
        method_counts = []
        for i in range(len(classes)):
            block = code[bounds[i]:bounds[i + 1]]
            method_counts.append(len(METHOD_DECL_RE.findall(block)))
        avg = mean(method_counts) if method_counts else 0
        worst = max(method_counts) if method_counts else 0
        if avg == 0:
            return CriterionResult(criterion_name, 60.0, "deterministic",
                                    "Could not reliably count methods per class.", confidence=0.3)
        rest = method_counts.copy()
        rest.remove(worst)
        rest_avg = mean(rest) if rest else 0
        # flagged if the largest class dwarfs the rest of the classes, in both
        # relative (>=3x the rest' average) and absolute (>=4 methods) terms
        flagged = worst >= 4 and worst >= 3 * max(rest_avg, 1)
        score = 55.0 if flagged else 90.0
        evidence = (
            f"Method counts per class: {method_counts}. "
            + ("One class has disproportionately many methods relative to the rest — "
               "possible god-class." if flagged else "Method counts are reasonably balanced across classes.")
        )
        return CriterionResult(criterion_name, score, "deterministic", evidence)

    def _check_naming(self, criterion_name, code):
        classes = [m.group(1) for m in CLASS_DECL_RE.finditer(code)]
        methods = [m.group(1) for m in METHOD_DECL_RE.finditer(code)]
        bad_classes = [c for c in classes if not re.match(r"^[A-Z][A-Za-z0-9]*$", c)]
        snake = sum(1 for m in methods if re.match(r"^[a-z][a-z0-9_]*$", m))
        camel = sum(1 for m in methods if re.match(r"^[a-z][A-Za-z0-9]*$", m) and "_" not in m)
        mixed = snake > 0 and camel > 0 and min(snake, camel) / max(snake, camel, 1) > 0.25
        issues = []
        if bad_classes:
            issues.append(f"non-CapWords class names: {', '.join(bad_classes)}")
        if mixed:
            issues.append("inconsistent method naming (mix of snake_case and camelCase)")
        score = 100.0 - 25 * len(issues)
        evidence = "No naming issues detected." if not issues else "Issues: " + "; ".join(issues) + "."
        return CriterionResult(criterion_name, max(score, 30.0), "deterministic", evidence)

    def _check_has_structure(self, criterion_name, code):
        n_classes = len(CLASS_DECL_RE.findall(code))
        score = min(100.0, n_classes * 25.0)
        return CriterionResult(criterion_name, score, "deterministic",
                                f"Detected {n_classes} class/interface declaration(s).",
                                confidence=0.5)
