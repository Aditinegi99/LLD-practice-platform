const BASE = '/api'

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error(body.detail || `Request failed: ${res.status}`)
  }
  return res.json()
}

export const api = {
  listProblems: () => request('/problems'),
  getProblem: (slug) => request(`/problems/${slug}`),
  createAttempt: (problemId, learnerName = 'learner') =>
    request('/attempts', { method: 'POST', body: JSON.stringify({ problem_id: problemId, learner_name: learnerName }) }),
  createSubmission: (attemptId, rationale, codePayload) =>
    request('/submissions', {
      method: 'POST',
      body: JSON.stringify({ attempt_id: attemptId, rationale, code_payload: codePayload }),
    }),
  retrySubmission: (submissionId) => request(`/submissions/${submissionId}/retry`, { method: 'POST' }),
  getHistory: (learnerName = 'learner') => request(`/history?learner_name=${encodeURIComponent(learnerName)}`),
  getAttemptSubmissions: (attemptId) => request(`/history/${attemptId}/submissions`),
}
