const BASE = '/api/v1'

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || 'Request failed')
  }
  if (res.status === 204) return null
  return res.json()
}

export const api = {
  health: () => request('/health'),

  collectLeads: (body) =>
    request('/leads/collect', { method: 'POST', body: JSON.stringify(body) }),

  getLeads: (params = {}) => {
    const qs = new URLSearchParams(
      Object.fromEntries(Object.entries(params).filter(([, v]) => v != null && v !== ''))
    ).toString()
    return request(`/leads${qs ? '?' + qs : ''}`)
  },

  getLead: (id) => request(`/leads/${id}`),

  createLead: (body) =>
    request('/leads', { method: 'POST', body: JSON.stringify(body) }),

  deleteLead: (id) => request(`/leads/${id}`, { method: 'DELETE' }),

  bulkDeleteLeads: (ids) => request('/leads/bulk', {
    method: 'DELETE',
    body: JSON.stringify({ ids }),
  }),

  deleteAllLeads: () => request('/leads/all', { method: 'DELETE' }),

  getStats: () => request('/leads/stats/summary'),

  updateStatus: (id, status) =>
    request(`/leads/${id}/status`, {
      method: 'PATCH',
      body: JSON.stringify({ status }),
    }),

  analyseLead: (id) => request(`/analysis/${id}`, { method: 'POST' }),

  scoreLead: (id) => request(`/score/${id}`, { method: 'POST' }),

  personalizeLead: (id) => request(`/personalize/${id}`, { method: 'POST' }),

  seedLeads: () => request('/leads/seed', { method: 'POST' }),
}
