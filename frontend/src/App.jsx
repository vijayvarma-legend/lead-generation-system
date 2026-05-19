import { useState, useEffect, useCallback, useRef } from 'react'
import { api } from './api'
import CollectForm from './components/CollectForm'
import ManualForm from './components/ManualForm'
import LeadsTable from './components/LeadsTable'
import StatsBar from './components/StatsBar'
import Toast from './components/Toast'

let toastId = 0

export default function App() {
  const [leads, setLeads] = useState([])
  const [pagination, setPagination] = useState(null)
  const [page, setPage] = useState(1)
  const [loading, setLoading] = useState(false)
  const [statsKey, setStatsKey] = useState(0)
  const [online, setOnline] = useState(null)
  const [toasts, setToasts] = useState([])
  const [filters, setFilters] = useState({ search: '', status: '', category: '', no_website: false })
  const [debouncedSearch, setDebouncedSearch] = useState('')

  function toast(message, type = 'info') {
    const id = ++toastId
    setToasts((t) => [...t, { id, message, type }])
  }

  function removeToast(id) {
    setToasts((t) => t.filter((x) => x.id !== id))
  }

  // Debounce search input (350ms)
  useEffect(() => {
    const timer = setTimeout(() => setDebouncedSearch(filters.search), 350)
    return () => clearTimeout(timer)
  }, [filters.search])

  const fetchLeads = useCallback(async () => {
    setLoading(true)
    try {
      const params = { page, page_size: 20 }
      if (debouncedSearch) params.search = debouncedSearch
      if (filters.status) params.status = filters.status
      if (filters.category) params.category = filters.category
      if (filters.no_website) params.has_website = false
      const res = await api.getLeads(params)
      setLeads(res.items)
      setPagination({ page: res.page, pages: res.pages, total: res.total })
    } catch (err) {
      toast(err.message, 'error')
    } finally {
      setLoading(false)
      setStatsKey((k) => k + 1)
    }
  }, [page, debouncedSearch, filters.status, filters.category, filters.no_website])

  // Health check
  useEffect(() => {
    api.health()
      .then(() => setOnline(true))
      .catch(() => setOnline(false))
  }, [])

  useEffect(() => { fetchLeads() }, [fetchLeads])

  function handlePageChange(p) {
    setPage(p)
  }

  function handleFilterChange(key, value) {
    setPage(1)
    setFilters((prev) => ({ ...prev, [key]: value }))
  }

  return (
    <div className="app">
      <nav className="navbar">
        <div className="navbar-brand">
          🎯 <span>LeadGen</span> AI
        </div>
        <div className="navbar-status">
          <span className={`status-dot ${online === true ? 'online' : ''}`} />
          {online === true ? 'API connected' : online === false ? 'API offline' : 'Checking…'}
        </div>
      </nav>

      <div className="main">
        {/* Sidebar */}
        <aside className="sidebar">
          <div className="card">
            <CollectForm onCollected={() => { setPage(1); fetchLeads() }} toast={toast} />
          </div>
          <div className="card">
            <ManualForm onCreated={() => { setPage(1); fetchLeads() }} toast={toast} />
          </div>


          <div className="card">
            <div className="card-title">Send Messages</div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              <div style={{ display: 'flex', alignItems: 'flex-start', gap: 10, fontSize: 13 }}>
                <span style={{ fontSize: 18 }}>💬</span>
                <div>
                  <div style={{ fontWeight: 600, color: 'var(--text)', marginBottom: 2 }}>WhatsApp</div>
                  <div style={{ color: 'var(--muted)', fontSize: 12, lineHeight: 1.5 }}>Click <strong>Outreach</strong> on any lead to generate a message, then hit <strong>WhatsApp</strong> to send it directly.</div>
                </div>
              </div>
              <div style={{ display: 'flex', alignItems: 'flex-start', gap: 10, fontSize: 13 }}>
                <span style={{ fontSize: 18 }}>✉️</span>
                <div>
                  <div style={{ fontWeight: 600, color: 'var(--text)', marginBottom: 2 }}>Email</div>
                  <div style={{ color: 'var(--muted)', fontSize: 12, lineHeight: 1.5 }}>After generating outreach, click <strong>Email</strong> to open your email client with the message pre-filled and ready to send.</div>
                </div>
              </div>
            </div>
          </div>
        </aside>

        {/* Main content */}
        <main className="content">
          <StatsBar refreshKey={statsKey} />
          <LeadsTable
            leads={leads}
            loading={loading}
            pagination={pagination}
            onPageChange={handlePageChange}
            onRefresh={fetchLeads}
            toast={toast}
            filters={filters}
            onFilterChange={handleFilterChange}
          />
        </main>
      </div>

      <Toast toasts={toasts} remove={removeToast} />
    </div>
  )
}
