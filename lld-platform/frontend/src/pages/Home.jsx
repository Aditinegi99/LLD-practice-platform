import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api/client'

const difficultyColor = {
  easy: '#5FAE7B',
  medium: '#E8A33D',
  hard: '#C0564F',
}

export default function Home() {
  const [problems, setProblems] = useState([])
  const [error, setError] = useState(null)

  useEffect(() => {
    api.listProblems().then(setProblems).catch((e) => setError(e.message))
  }, [])

  return (
    <div className="max-w-3xl mx-auto px-6 py-14">
      <p className="mono-tag text-xs text-blue-glow mb-3">practice loop: choose → design → submit → feedback → retry</p>
      <h1 className="font-display text-3xl font-semibold text-paper-100 mb-3">Pick a problem to design.</h1>
      <p className="text-paper-300 mb-10 max-w-xl leading-relaxed">
        Each one comes with a rubric that mixes mechanical checks against your structure and
        AI judgment on your reasoning. You'll see exactly which is which in the feedback.
      </p>

      {error && <p className="text-bad text-sm mb-6">Could not load problems: {error}. Is the backend running on :8000?</p>}

      <div className="border-t border-ink-600">
        {problems.map((p) => (
          <Link
            key={p.id}
            to={`/problem/${p.slug}`}
            className="block py-6 border-b border-ink-600 group no-underline"
          >
            <div className="flex items-baseline justify-between gap-4">
              <h2 className="font-display text-xl text-paper-100 group-hover:text-amber transition-colors">
                {p.title}
              </h2>
              <span
                className="mono-tag text-[11px] shrink-0"
                style={{ color: difficultyColor[p.difficulty] || '#8B9AA6' }}
              >
                {p.difficulty}
              </span>
            </div>
            <p className="text-sm text-paper-300 mt-2 max-w-lg leading-relaxed">{p.summary}</p>
          </Link>
        ))}
        {problems.length === 0 && !error && (
          <p className="text-paper-300 text-sm py-6">Loading problems…</p>
        )}
      </div>
    </div>
  )
}
