function scoreColor(score) {
  if (score >= 75) return '#5FAE7B'
  if (score >= 50) return '#E8A33D'
  return '#C0564F'
}

export default function CriterionRow({ criterion }) {
  const color = scoreColor(criterion.score)
  return (
    <div className="py-4 border-b border-ink-600 last:border-b-0">
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <h4 className="font-display text-[15px] font-medium text-paper-100">{criterion.name}</h4>
            <span
              className="mono-tag text-[10px] px-1.5 py-0.5 border rounded-sm"
              style={{
                color: criterion.source === 'llm' ? '#6FA9C9' : '#B9812F',
                borderColor: criterion.source === 'llm' ? '#3D6E8C' : '#B9812F',
              }}
              title={criterion.source === 'llm' ? 'Judged by the AI reviewer' : 'Checked mechanically'}
            >
              {criterion.source === 'llm' ? 'ai judgment' : 'checked'}
            </span>
            {criterion.confidence === 0 && (
              <span className="mono-tag text-[10px] px-1.5 py-0.5 border border-bad text-bad rounded-sm">
                unavailable
              </span>
            )}
          </div>
          <p className="text-sm text-paper-300 mt-1 leading-relaxed max-w-xl">{criterion.evidence}</p>
        </div>
        <div className="w-20 shrink-0 text-right">
          <span className="font-display text-lg font-semibold" style={{ color }}>
            {Math.round(criterion.score)}
          </span>
          <span className="text-paper-300 text-sm">/100</span>
          <div className="h-1 mt-2 bg-ink-700 rounded-sm overflow-hidden">
            <div className="h-full" style={{ width: `${criterion.score}%`, background: color }} />
          </div>
        </div>
      </div>
    </div>
  )
}
