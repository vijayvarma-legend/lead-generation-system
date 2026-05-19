import { useEffect, useState } from 'react'
import { api } from '../api'

export default function StatsBar({ refreshKey }) {
  const [stats, setStats] = useState(null)

  useEffect(() => {
    api.getStats().then(setStats).catch(() => {})
  }, [refreshKey])

  const total       = stats?.total       ?? '—'
  const noWebsite   = stats?.no_website  ?? '—'
  const personalized = stats?.personalized ?? '—'

  return (
    <div className="stats-bar">
      <div className="stat-card">
        <div className="stat-value">{total}</div>
        <div className="stat-label">Total Leads</div>
      </div>
      <div className="stat-card">
        <div className="stat-value" style={{ color: 'var(--danger)' }}>{noWebsite}</div>
        <div className="stat-label">No Website</div>
      </div>
      <div className="stat-card success">
        <div className="stat-value">{personalized}</div>
        <div className="stat-label">Outreach Sent</div>
      </div>
      <div className="stat-card accent">
        <div className="stat-value">{stats?.avg_score ?? '—'}</div>
        <div className="stat-label">Avg Score</div>
      </div>
    </div>
  )
}
