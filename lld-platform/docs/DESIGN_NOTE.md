# Design Note

## MVP scope

Practice loop: **choose problem → write rationale + code/pseudocode → submit → get feedback
(deterministic + AI, clearly labeled) → review → resubmit.** Three seeded problems (Parking Lot,
Elevator System, Vending Machine), each with a weighted rubric of six criteria. Deliberately out
of scope: accounts/auth (single demo learner), diagram-based submissions (designed for, not
built — see Extensibility below), background job queues (see "evaluation timing/failures"
below), and any multi-region/HLD concerns.

## User flow

```
Home (problem list)
   └─ Workspace (/problem/:slug)
         - shows requirements + constraints
         - creates an Attempt on load
         - learner writes rationale + code, submits
         - Submission -> EvaluationJob runs synchronously -> Feedback rendered inline
         - learner can revise and resubmit under the same Attempt (shown as a growing list)
   └─ History
         - every Attempt across every problem, with latest score
         - expand an Attempt to see all its Submissions and their Feedback
```

## Core domain model

```
Problem 1---* Criterion            (rubric line item: name, weight, evaluation_mode)
Problem 1---* Attempt              (one learner session on one problem)
Attempt 1---* Submission           (a learner can submit, get feedback, revise, resubmit)
Submission 1---1 EvaluationJob     (PENDING -> RUNNING -> COMPLETED / FAILED)
EvaluationJob 1---1 Feedback       (overall_score, summary, follow_up_questions, criterion_scores[])
```

**Why Attempt and Submission are separate.** A learner improving across iterations is the whole
point of a practice tool (see Research Note). Modeling "one submission = one attempt" would make
history meaningless — you'd only ever see the last try. Separating them means an Attempt's
status (`in_progress` / `submitted` / `evaluated`) tracks the session, while each Submission is
an immutable snapshot with its own Feedback, so a learner can literally watch a criterion score
go from 50 to 90 across three submissions in the same Attempt.

**Why EvaluationJob is its own entity rather than a status column on Submission.** It isolates
the "did evaluation succeed" state machine from the submission content itself, which matters
once evaluation can fail or degrade independently of what was submitted (see below), and makes
retry a first-class operation: `POST /submissions/{id}/retry` replaces the Job and Feedback
without touching the original Submission.

## Evaluation approach

### Evaluator (Strategy pattern)

```python
class Evaluator(ABC):
    def evaluate(self, data: EvaluationInput) -> EvaluatorOutput: ...
```

`DeterministicEvaluator` and `LLMEvaluator` both implement this. Neither knows about the other,
and neither knows about persistence — they take a plain `EvaluationInput` dataclass and return
an `EvaluatorOutput` of `CriterionResult`s. This is what makes "which parts of evaluation should
be deterministic vs. LLM-driven" a *data* decision rather than a code decision: each `Criterion`
row carries its own `evaluation_mode` (`deterministic` / `llm` / `both`), and each evaluator
simply filters to the criteria it's responsible for. Adding a third evaluator (a static-analysis
tool, a second LLM as a sanity check) means writing one new class and adding it to the list
below — nothing else in the pipeline changes.

### CompositeEvaluator

```python
CompositeEvaluator([DeterministicEvaluator(), LLMEvaluator()])
```

Runs every evaluator against the same input and merges results by criterion name. This is the
seam for the "what if evaluation takes time or fails" question: each evaluator's `evaluate()`
call is wrapped so a failure produces a *degraded* `EvaluatorOutput` (neutral placeholder scores,
`confidence=0`, an error message) instead of throwing. The composite just merges whatever came
back — deterministic results are never lost because the LLM had a bad day.

### EvaluationPipeline (Template Method)

Fixed skeleton: `_parse → evaluate → _aggregate → _persist`, with the job's state machine
(`PENDING → RUNNING → COMPLETED / FAILED`) advanced around it. `_aggregate` computes a
weight-normalized overall score and writes a short summary that names the weakest and strongest
criterion by name — not a generic "good job," a rationale-specific pointer to what to fix next.
If any evaluator degraded, the summary says so explicitly and the API response carries
`llm_degraded: true` so the frontend can offer a one-click retry (`FeedbackPanel.jsx`) instead of
quietly showing a score the learner should distrust.

### What's deterministic vs. LLM, concretely

| Criterion type | Evaluator | Why |
|---|---|---|
| Entity/requirement coverage | Deterministic | Objectively checkable: is `ParkingSpot` in the code or not. |
| God-class / coupling heuristic | Deterministic | A method-count imbalance across classes is a cheap, reproducible signal — not proof of a bad design, but a fair flag. |
| Naming consistency | Deterministic | Pattern matching, no judgment needed. |
| Responsibility assignment | LLM | Requires reading the learner's *stated intent* and judging whether the split makes sense for this domain — genuinely open-ended. |
| Extensibility | LLM | "Could a new vehicle type be added without touching existing classes" requires reasoning about hypothetical future change, not just present structure. |
| Trade-off reasoning | LLM | Directly evaluates the learner's own written rationale, which by definition has no fixed answer key. |

The deterministic checks are heuristic, not a real parser (documented limitation, see README) —
they're intentionally cheap regex-based signals so they stay instant and fully reproducible;
the LLM is reserved for genuinely open-ended judgment.

### Handling evaluation failure/timeout (kept practical, not a distributed-systems project)

Submission today runs the pipeline **synchronously** in the request (fine at this scale — a
Groq call is a couple seconds). Failure handling is real, not hypothetical, and is covered by
tests (`test_pipeline_marks_degraded_when_llm_fails_but_still_completes`,
`test_pipeline_raises_and_marks_failed_on_unexpected_error`):

- LLM call times out / errors / returns malformed JSON → `LLMEvaluator` catches it, returns
  neutral placeholder scores with `confidence=0`, job still completes with `llm_degraded=1`.
- A genuinely unexpected error (e.g. a bug, not a network blip) → job marked `FAILED`, error
  message stored, surfaced to the frontend, retry button offered.
- `POST /submissions/{id}/retry` re-runs the whole pipeline (deterministic checks are cheap
  enough to just redo) and replaces the Job/Feedback rows.

**If this needed to scale**: the one-line change is swapping `_run_evaluation`'s inline call
(`backend/app/routers/submissions.py`) for a background task (FastAPI `BackgroundTasks`, then a
real queue like Celery/RQ if volume grew further) and returning the Submission with
`job_status: "pending"` immediately; the frontend already polls-on-demand via
`GET /submissions/{id}`, so almost nothing else moves. This was deliberately not built now —
it's a swap-in-place decision, not a rewrite, which is the extensibility point.

## Extensibility: accommodating another submission format or evaluator later

`Submission` currently stores `rationale` (text) and `code_payload` (code/pseudocode) directly.
Adding a diagram format cleanly extends this: a new `content_type` value, a new field or a JSON
payload column, and a `_parse` step in the pipeline that turns the diagram into the same
`EvaluationInput` shape (e.g. via an OCR/graph-extraction step) that every evaluator already
consumes. No evaluator, no aggregation logic, and no API contract changes — the pipeline's
`_parse` step is exactly the seam designed for this.

## Key trade-offs

- **Regex-based deterministic checks over a real AST parser.** Faster to build, works across
  pseudocode/Python/Java-ish input without a real compiler front-end, but is a heuristic and can
  be fooled (documented as a known limitation).
- **Synchronous evaluation over a job queue.** Right-sized for the current scale (single learner,
  seconds-long LLM call); the swap point is deliberately narrow (see above) rather than building
  unused queue infrastructure now.
- **SQLite over Postgres.** Zero setup for a take-home reviewer; `DATABASE_URL` is already an
  env var, so switching is a one-line change, not a migration project.
- **One LLM provider (Groq/Llama) with a hard fallback rather than a multi-provider abstraction.**
  Keeps the surface area small; the `Evaluator` interface is already the seam if a second
  provider is desired.
