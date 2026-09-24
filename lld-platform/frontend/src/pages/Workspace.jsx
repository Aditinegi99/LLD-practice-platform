import { useEffect, useRef, useState } from 'react'
import { useParams } from 'react-router-dom'
import { api } from '../api/client'
import FeedbackPanel from '../components/FeedbackPanel'

export default function Workspace() {
  const { slug } = useParams()
  const [problem, setProblem] = useState(null)
  const [attemptId, setAttemptId] = useState(null)
  const [rationale, setRationale] = useState('')
  const [code, setCode] = useState('')
  const [submissions, setSubmissions] = useState([])
  const [submitting, setSubmitting] = useState(false)
  const [retryingId, setRetryingId] = useState(null)
  const [error, setError] = useState(null)
  const attemptCreated = useRef(false)

  useEffect(() => {
    api.getProblem(slug).then(setProblem).catch((e) => setError(e.message))
  }, [slug])

  useEffect(() => {
    if (!problem || attemptCreated.current) return
    attemptCreated.current = true
    api.createAttempt(problem.id).then((a) => setAttemptId(a.id)).catch((e) => setError(e.message))
  }, [problem])

  async function handleSubmit(e) {
    e.preventDefault()
    if (!rationale.trim() && !code.trim()) {
      setError('Write a rationale, some code, or both before submitting.')
      return
    }
    setError(null)
    setSubmitting(true)
    try {
      const result = await api.createSubmission(attemptId, rationale, code)
      setSubmissions((prev) => [result, ...prev])
    } catch (err) {
      setError(err.message)
    } finally {
      setSubmitting(false)
    }
  }

  async function handleRetry(submissionId) {
    setRetryingId(submissionId)
    try {
      const updated = await api.retrySubmission(submissionId)
      setSubmissions((prev) => prev.map((s) => (s.id === submissionId ? updated : s)))
    } catch (err) {
      setError(err.message)
    } finally {
      setRetryingId(null)
    }
  }

  if (error && !problem) {
    return <div className="max-w-3xl mx-auto px-6 py-14 text-bad text-sm">{error}</div>
  }
  if (!problem) {
    return <div className="max-w-3xl mx-auto px-6 py-14 text-paper-300 text-sm">Loading…</div>
  }

  return (
    <div className="max-w-3xl mx-auto px-6 py-12">
      <p className="mono-tag text-xs text-blue-glow mb-2">{problem.difficulty}</p>
      <h1 className="font-display text-3xl font-semibold text-paper-100 mb-6">{problem.title}</h1>
      <p className="text-paper-300 leading-relaxed mb-8">{problem.summary}</p>

      <div className="grid grid-cols-2 gap-8 mb-10">
        <div>
          <h3 className="mono-tag text-xs text-amber mb-3">requirements</h3>
          <ul className="space-y-2">
            {problem.requirements.map((r, i) => (
              <li key={i} className="text-sm text-paper-100 flex gap-2 leading-relaxed">
                <span className="text-paper-300">{i + 1}.</span>{r}
              </li>
            ))}
          </ul>
        </div>
        <div>
          <h3 className="mono-tag text-xs text-amber mb-3">constraints</h3>
          <ul className="space-y-2">
            {problem.constraints.map((c, i) => (
              <li key={i} className="text-sm text-paper-300 flex gap-2 leading-relaxed">
                <span className="text-blue-glow">·</span>{c}
              </li>
            ))}
          </ul>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="border-t border-ink-600 pt-8">
        <h3 className="mono-tag text-xs text-amber mb-3">your design rationale</h3>
        <textarea
          value={rationale}
          onChange={(e) => setRationale(e.target.value)}
          placeholder="What entities did you choose, and why? What trade-offs did you consider?"
          rows={4}
          className="w-full border border-ink-600 p-3 text-sm text-paper-100 placeholder:text-paper-300/50 mb-6 resize-y"
        />
        <h3 className="mono-tag text-xs text-amber mb-3">class / interface stubs (pseudocode is fine)</h3>
        <textarea
          value={code}
          onChange={(e) => setCode(e.target.value)}
          placeholder={'class ParkingLot:\n    def find_spot(self, vehicle): ...\n'}
          rows={10}
          spellCheck={false}
          className="w-full border border-ink-600 p-3 text-sm font-mono text-paper-100 placeholder:text-paper-300/50 mb-4 resize-y"
        />
        {error && <p className="text-bad text-sm mb-4">{error}</p>}
        <button
          type="submit"
          disabled={submitting || !attemptId}
          className="mono-tag text-xs px-4 py-2.5 bg-amber text-ink-950 font-medium hover:bg-amber-dim disabled:opacity-50 transition-colors"
        >
          {submitting ? 'evaluating…' : 'submit for feedback'}
        </button>
      </form>

      {submissions.length > 0 && (
        <div className="mt-14">
          <h3 className="mono-tag text-xs text-paper-300 mb-4">
            attempt history · {submissions.length} submission{submissions.length > 1 ? 's' : ''}
          </h3>
          <div className="space-y-10">
            {submissions.map((s, idx) => (
              <div key={s.id} className="border border-ink-600 p-6">
                <p className="mono-tag text-[11px] text-paper-300 mb-4">
                  submission #{submissions.length - idx} · {new Date(s.created_at).toLocaleString()}
                </p>
                <FeedbackPanel
                  submission={s}
                  onRetry={() => handleRetry(s.id)}
                  retrying={retryingId === s.id}
                />
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
