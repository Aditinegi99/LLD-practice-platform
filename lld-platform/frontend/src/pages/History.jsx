import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api/client'
import FeedbackPanel from '../components/FeedbackPanel'

function scoreColor(score) {
  if (score == null) return '#8B9AA6'
  if (score >= 75) return '#5FAE7B'
  if (score >= 50) return '#E8A33D'
  return '#C0564F'
}

export default function History() {
  const [attempts, setAttempts] = useState([])
  const [expanded, setExpanded] = useState(null)
  const [submissionsByAttempt, setSubmissionsByAttempt] = useState({})
  const [error, setError] = useState(null)

  useEffect(() => {
    api.getHistory().then(setAttempts).catch((e) => setError(e.message))
  }, [])

  async function toggle(attemptId) {
    if (expanded === attemptId) {
      setExpanded(null)
      return
    }
    setExpanded(attemptId)
    if (!submissionsByAttempt[attemptId]) {
      const subs = await api.getAttemptSubmissions(attemptId)
      setSubmissionsByAttempt((prev) => ({ ...prev, [attemptId]: subs }))
    }
  }

  return (
    <div className="max-w-3xl mx-auto px-6 py-14">
      <h1 className="font-display text-3xl font-semibold text-paper-100 mb-3">Your attempts.</h1>
      <p className="text-paper-300 mb-10 max-w-xl leading-relaxed">
        Every attempt you've made, across every problem, with your most recent score. Open one to
        see how your feedback changed across submissions.
      </p>

      {error && <p className="text-bad text-sm mb-6">{error}</p>}

      <div className="border-t border-ink-600">
        {attempts.map((a) => (
          <div key={a.attempt_id} className="border-b border-ink-600">
            <button
              onClick={() => toggle(a.attempt_id)}
              className="w-full text-left py-5 flex items-center justify-between gap-4 group"
            >
              <div>
                <h2 className="font-display text-lg text-paper-100 group-hover:text-amber transition-colors">
                  {a.problem_title}
                </h2>
                <p className="mono-tag text-[11px] text-paper-300 mt-1">
                  {a.status} · {a.submission_count} submission{a.submission_count !== 1 ? 's' : ''} ·{' '}
                  {new Date(a.created_at).toLocaleDateString()}
                </p>
              </div>
              <div className="text-right shrink-0">
                <span className="font-display text-2xl font-semibold" style={{ color: scoreColor(a.latest_score) }}>
                  {a.latest_score != null ? Math.round(a.latest_score) : '—'}
                </span>
                <span className="text-paper-300 text-sm">/100</span>
              </div>
            </button>

            {expanded === a.attempt_id && (
              <div className="pb-6 space-y-8">
                <Link to={`/problem/${a.problem_slug}`} className="mono-tag text-xs text-blue-glow hover:text-blue-line">
                  → attempt this problem again
                </Link>
                {(submissionsByAttempt[a.attempt_id] || []).map((s, idx) => (
                  <div key={s.id} className="border border-ink-600 p-6">
                    <p className="mono-tag text-[11px] text-paper-300 mb-4">
                      submission #{(submissionsByAttempt[a.attempt_id] || []).length - idx} ·{' '}
                      {new Date(s.created_at).toLocaleString()}
                    </p>
                    <FeedbackPanel submission={s} onRetry={() => {}} retrying={false} />
                  </div>
                ))}
                {!submissionsByAttempt[a.attempt_id] && (
                  <p className="text-paper-300 text-sm">Loading submissions…</p>
                )}
              </div>
            )}
          </div>
        ))}
        {attempts.length === 0 && !error && (
          <p className="text-paper-300 text-sm py-6">No attempts yet — go pick a problem.</p>
        )}
      </div>
    </div>
  )
}
