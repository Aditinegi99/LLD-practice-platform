# Deliverable Checklist

This maps directly to the assignment's "What to Submit" table, with links to where each
piece lives in this repo.

| Deliverable | What we expect | Where it is |
|---|---|---|
| Research note | 1–2 pages: learner problem, existing approaches researched, key gaps, product direction | `docs/RESEARCH_NOTE.md` |
| Design note | MVP explanation, user flow, important classes/interfaces, evaluation approach, key trade-offs | `docs/DESIGN_NOTE.md` |
| Working prototype | End-to-end flow: problem selection → feedback → attempt history | `backend/` (FastAPI API) + `frontend/` (React UI) — run both per README |
| Tests | Important behaviour + failure/edge cases | `backend/tests/` — 17 tests, `python -m pytest tests/ -v` |
| README + AI_USAGE.md | How to run, key decisions, limitations, AI usage | `README.md` (root) + `AI_USAGE.md` (root, full version in `docs/`) |

## What a reviewer will see, in order

1. **Problem selection** — `/` lists 3 seeded LLD problems (Parking Lot, Elevator System, Vending Machine), each with real requirements/constraints.
2. **Design + submit** — `/problem/:slug` lets the learner write a rationale and code/pseudocode, then submit.
3. **Feedback** — each criterion is labeled `checked` (deterministic) or `ai judgment` (LLM), with an overall weighted score, a specific summary naming the strongest/weakest area, and 2-3 follow-up questions.
4. **Retry on failure** — if the LLM call fails/times out, the submission still completes with deterministic scores intact, flagged `llm_degraded`, with a retry button. Covered by `test_pipeline.py`.
5. **History** — `/history` shows every attempt across every problem with its latest score; expanding one shows every submission's full feedback, so improvement across resubmissions is visible.

## Before you submit — a short verification pass

Don't submit sight-unseen. Confirm these three things take under 5 minutes total:

1. `cd backend && pip install -r requirements.txt && python -m pytest tests/ -v` → should show `17 passed`.
2. Copy `.env.example` to `.env`, add your own free Groq key, then `python -m uvicorn app.main:app --reload --port 8000` → visit `http://localhost:8000/docs` and confirm it loads.
3. `cd frontend && npm install && npm run dev` → visit `http://localhost:5173`, pick a problem, submit something, confirm real feedback comes back (not just the deterministic fallback — that means your Groq key is wired correctly).

If step 3 shows `llm_degraded: true` in the UI even with a key set, double check the key was pasted into `backend/.env` (not `.env.example`) with no extra quotes or spaces.

## If the form asks for a link, not a zip

- **GitHub repo**: push this folder as-is (the `.gitignore` already excludes `.env`, `node_modules`, and the SQLite db file — do not remove those exclusions, since your `.env` has your real API key).
- **Live demo link**: not required by the assignment (explicitly scoped against HLD/deployment concerns), but if you want one anyway, the backend deploys as-is to Render/Railway (set `GROQ_API_KEY` as an environment variable there, not in a committed file) and the frontend to Vercel/Netlify with the API's public URL swapped into `vite.config.js`'s proxy target.
