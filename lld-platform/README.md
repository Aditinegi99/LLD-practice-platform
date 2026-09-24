# DesignLoop — LLD Practice Platform

A small practice platform for Low-Level Design: pick a problem, write a design (rationale +
code/pseudocode), submit it, and get feedback that's explicit about what was checked
mechanically versus judged by an AI reviewer. Attempts are tracked over time so you can see
whether your next submission actually improved.

See `docs/RESEARCH_NOTE.md` for the problem/landscape research and `docs/DESIGN_NOTE.md` for
the full design writeup (domain model, evaluation approach, trade-offs). This README is just
run instructions + a summary.

## Stack

- **Backend**: Python, FastAPI, SQLAlchemy, SQLite
- **LLM**: Groq's free API (Llama 3.3 70B) for the judgment-based rubric criteria
- **Frontend**: React + Vite + Tailwind CSS

## Running it

### 1. Backend

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate   # optional but recommended
pip install -r requirements.txt

cp .env.example .env
# edit .env and set GROQ_API_KEY to your own free key from https://console.groq.com

python -m uvicorn app.main:app --reload --port 8000
```

The API is now at `http://localhost:8000`. On first startup it seeds three problems into a
local `lld_platform.db` SQLite file automatically. Interactive API docs at
`http://localhost:8000/docs`.

### 2. Frontend

In a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`. The dev server proxies `/api` to the backend on port 8000
(see `vite.config.js`), so both need to be running.

### 3. Tests

```bash
cd backend
python -m pytest tests/ -v
```

17 tests covering the deterministic evaluator's individual checks, the full evaluation
pipeline (including simulated LLM failure/degradation), and end-to-end API flows. Tests run
against an in-memory SQLite DB and do **not** call the real Groq API (a `GROQ_API_KEY=""`
override in `tests/test_api.py` deliberately exercises the no-key fallback path), so they pass
with zero network access and zero cost.

## What's implemented vs. deliberately left out

**Implemented:** the full practice loop end-to-end, 3 problems with real rubrics, a
deterministic + LLM evaluation pipeline with explicit source-labeling per criterion, graceful
degradation when the LLM call fails/times out with a retry affordance, attempt history across
problems, and a from-scratch UI (not a component-library default look).

**Left out on purpose** (see Design Note's "Key trade-offs" and "Extensibility" sections for
why each is a narrow, deliberate seam rather than a missing feature):
- No accounts/login — single demo learner (`learner_name` defaults to `"learner"`).
- No diagram-based submissions — designed for via `content_type`, not built.
- No background job queue — evaluation runs synchronously; documented one-line swap point if
  volume required it.
- Deterministic checks are regex-based heuristics, not a real AST parser — can be fooled by
  unusual formatting; this is a known, accepted limitation for the take-home's scope.

## Known limitations

- The god-class heuristic counts methods per class via regex, not a real parser, so heavily
  nested or multi-line method signatures can under/over-count. It's a signal, not a verdict —
  which is exactly why it's labeled "checked" (not "ai judgment") in the UI, so the learner
  knows to sanity-check it themselves.
- Groq's free tier has rate limits; hitting them will trigger the same degraded-feedback path
  as a timeout (by design — see Design Note).
- SQLite means this is single-writer; fine for a local demo, would move to Postgres for
  multiple concurrent learners (one env var change, see Design Note).

See `AI_USAGE.md` for how AI tools were used while building this.
