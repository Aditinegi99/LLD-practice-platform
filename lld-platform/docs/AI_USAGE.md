# AI Usage

Built with Claude (Anthropic) as a pair-programming assistant throughout. Below are the
meaningful decisions where AI suggestions were accepted, rejected, or modified — not just "AI
wrote code."

## 1. God-class heuristic threshold — rejected the first version, tuned against real tests

**Suggested:** flag a class as a god-class if its method count exceeded `mean + 2*stdev` across
all classes in the file.

**What happened:** written this way, it failed on a deliberately unbalanced test case (one class
with 8 methods, another with 1) — the statistical threshold was too lenient for small class
counts, which is the common case in a short LLD submission. Rejected the stdev-based version and
replaced it with a simpler relative check: flag if the largest class has ≥4 methods *and* is at
least 3x the average of the *other* classes. Kept the original attempt's underlying idea (relative
imbalance, not an absolute cap) but fixed it for small-N inputs, which is what real submissions
actually look like. Verified against both the balanced and imbalanced test fixtures before
accepting.

## 2. Synchronous evaluation vs. a job queue — accepted, with a documented reversal point

**Suggested:** run the evaluation pipeline synchronously inside the submission request, rather
than building a background task queue, given the assignment's explicit scope boundary against
distributed-systems complexity.

**Accepted as-is**, but pushed to make the reversal point concrete rather than a vague "could add
a queue later" — the design note calls out the exact line (`_run_evaluation` in
`submissions.py`) that would change to `BackgroundTasks`/Celery, and why nothing else in the
pipeline would need to move. Wanted the trade-off to be a stated, inspectable decision, not just
an omission.

## 3. Source-labeling every criterion score — my addition, not the initial suggestion

**Initial AI draft** of the Feedback model only stored a per-criterion score and evidence
string. Added the `source` (deterministic/llm) and `confidence` fields myself after realizing
that without them, a learner has no way to tell "this is a fact" from "this is the AI's
opinion" — which was one of the assignment's own explicit questions ("what makes feedback
useful when there's more than one valid solution"). This ended up shaping the whole evaluator
interface (`CriterionResult` carries `source` from the start) and the UI (the `ai judgment` /
`checked` tags in `CriterionRow.jsx`).

## 4. LLM failure handling — accepted the degrade-not-fail pattern, added the test coverage

**Suggested:** if the LLM call fails, return neutral placeholder scores with `confidence=0`
instead of failing the whole submission.

**Accepted**, because losing a learner's deterministic feedback just because a third-party API
had a bad moment seemed clearly worse than a partial result. Where I pushed further: asked for
this to be a first-class tested behavior, not just a try/except — `test_pipeline.py` has an
explicit `FakeLLMEvaluator(should_fail=True)` test asserting the job still completes and
deterministic results still land, and `test_api.py`'s end-to-end test runs with no Groq key
configured at all specifically to exercise this path on every test run, at zero cost.

## 5. Visual design direction — rejected the default aesthetic, asked for something grounded in the subject

**Initial suggestion** leaned toward a standard dark-mode SaaS look (rounded cards, drop
shadows, a generic accent color). Rejected it as generic and asked for something that actually
reflects what the product is for — a blueprint/schematic theme (grid background, rule-line
dividers instead of shadow-cards, an amber "annotation pen" accent against structural blue)
made sense for a tool about class diagrams and structure. Small thing, but it's the difference
between a template and a product with a point of view.
