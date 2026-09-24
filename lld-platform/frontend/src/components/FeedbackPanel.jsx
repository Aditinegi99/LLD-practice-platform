import CriterionRow from './CriterionRow'

function scoreColor(score) {
  if (score >= 75) return '#5FAE7B'
  if (score >= 50) return '#E8A33D'
  return '#C0564F'
}

export default function FeedbackPanel({ submission, onRetry, retrying }) {
  const { feedback, job_status: jobStatus, llm_degraded: llmDegraded } = submission

  if (jobStatus === 'failed') {
    return (
      <div className="border border-bad/50 bg-bad/5 p-6">
        <p className="mono-tag text-xs text-bad mb-2">evaluation failed</p>
        <p className="text-sm text-paper-300 mb-4">{submission.job_error || 'Something went wrong while evaluating this submission.'}</p>
        <button
          onClick={onRetry}
          disabled={retrying}
          className="mono-tag text-xs px-3 py-2 border border-amber text-amber hover:bg-amber/10 disabled:opacity-50"
        >
          {retrying ? 'retrying…' : 'retry evaluation'}
        </button>
      </div>
    )
  }

  if (!feedback) return null

  return (
    <div>
      <div className="flex items-start gap-6 pb-6 border-b border-ink-600">
        <div className="shrink-0 text-center border border-ink-600 px-6 py-4">
          <div className="font-display text-4xl font-semibold" style={{ color: scoreColor(feedback.overall_score) }}>
            {Math.round(feedback.overall_score)}
          </div>
          <div className="mono-tag text-[10px] text-paper-300 mt-1">overall / 100</div>
        </div>
        <div className="flex-1">
          <p className="text-paper-100 leading-relaxed">{feedback.summary}</p>
          {llmDegraded && (
            <p className="mono-tag text-xs text-warn mt-3 flex items-center gap-2">
              ai feedback was unavailable for part of this evaluation
              <button onClick={onRetry} disabled={retrying} className="underline hover:text-amber disabled:opacity-50">
                {retrying ? 'retrying…' : 'retry'}
              </button>
            </p>
          )}
        </div>
      </div>

      {feedback.follow_up_questions?.length > 0 && (
        <div className="py-5 border-b border-ink-600">
          <p className="mono-tag text-xs text-blue-glow mb-3">worth thinking about</p>
          <ul className="space-y-2">
            {feedback.follow_up_questions.map((q, i) => (
              <li key={i} className="text-sm text-paper-300 flex gap-2">
                <span className="text-blue-glow">—</span>
                <span>{q}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="pt-2">
        {feedback.criterion_scores.map((c) => (
          <CriterionRow key={c.name} criterion={c} />
        ))}
      </div>
    </div>
  )
}
