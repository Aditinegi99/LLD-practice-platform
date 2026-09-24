# Research Note

## The learner problem

Practicing Low-Level Design is easy to start and hard to evaluate. A learner can design a
Parking Lot or Elevator system and produce *something* — classes, a diagram, some pseudocode —
but has no reliable way to tell whether their responsibilities, abstractions, and trade-offs
are actually good. Unlike DSA practice (where a test suite gives a binary pass/fail), LLD has
no single correct answer, so "is this good?" is a judgment call most learners can't make about
their own work, and most existing tools don't help them make it.

## Existing approaches and their gaps

- **LeetCode-style "OOD" question banks** (e.g. Educative's Grokking OOD, various YouTube
  walkthroughs): give a reference solution to compare against. Useful for exposure, but a
  learner can only check *if they matched the reference*, not whether their own different
  approach is also valid. This actively discourages the trade-off thinking LLD is supposed to
  teach.
- **Generic AI chat (asking ChatGPT/Claude to "review my design")**: flexible and can reason
  about trade-offs, but feedback is inconsistent between runs, isn't tied to a rubric, has no
  memory of past attempts, and gives no way to tell which parts of the verdict are "solid fact"
  versus "the model's opinion." A learner can't calibrate trust in the feedback.
- **Mock-interview platforms** (Pramp-style peer practice): feedback quality depends entirely on
  the peer's own LLD skill, and there's no structured history to track improvement over time.
- **University/bootcamp code review**: high quality when available, but not repeatable or
  scalable — a learner can't get five reviews of five iterations on their own schedule.

The common gap: **nothing combines a stable rubric, judgment where judgment is needed, and a
visible record of improvement across attempts.**

## Product direction

Build a small, repeatable **practice loop** — choose a problem, design, submit, get feedback
that is explicit about what's mechanically checked versus AI-judged, review, and try again —
rather than a one-shot grader or an open-ended chat. Two decisions follow directly from the
gaps above:

1. **Split evaluation into deterministic and LLM layers, and label every score with its
   source.** This directly answers "what makes feedback useful when there's more than one valid
   solution": the mechanical layer checks things that are objectively true (are the required
   entities present, is one class doing everything), while the LLM layer is scoped to genuine
   judgment calls (is this separation of concerns actually good, given the learner's own
   stated rationale) and is never allowed to silently stand in for a fact-check.
2. **Track attempts as a history, not a single submission.** A learner who resubmits after
   reading feedback is the entire point of practice; the product needs to make that visible
   improvement legible, not just grade in isolation.

## Key open questions this MVP tries to answer in the code, not just in prose

- What must a learner provide for an attempt to be meaningful? (Answer implemented: a written
  rationale *and* code/pseudocode — the rationale is what lets the LLM evaluator judge intent
  and trade-offs rather than just static structure.)
- Which parts of evaluation should be deterministic vs. LLM-driven, and how does the system
  behave when the LLM step is slow, degraded, or unavailable? (Answered in the evaluation
  pipeline and covered by tests — see Design Note.)
