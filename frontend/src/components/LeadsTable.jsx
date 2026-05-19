import { useState } from 'react'
import { api } from '../api'
import LeadModal from './LeadModal'
import { BUSINESS_TYPES } from '../constants'

// Converts a display label like "Schools & Colleges" → "School"
// so the backend ILIKE "%School%" matches real Google Maps categories.
function labelToKeyword(label) {
  const first = label.split(/\s*&\s*/)[0].trim()
  // Naive singular: strip trailing 's' (avoids "Schools"→ no match for "School")
  if (first.length > 4 && first.endsWith('s') && !first.endsWith('ss')) {
    return first.slice(0, -1)
  }
  return first
}

const EMAIL_SVG = (
  <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
    <rect x="2" y="4" width="20" height="16" rx="2"/>
    <path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/>
  </svg>
)

function mailtoLink(email, businessName, body) {
  const subject = `Free Website Demo for ${businessName} – MadTech Solutions`
  const params = new URLSearchParams({ subject, body: body || '' }).toString().replace(/\+/g, '%20')
  return email ? `mailto:${email}?${params}` : `mailto:?${params}`
}

const STATUS_BADGE = {
  new: 'badge-new', analyzing: 'badge-default', analyzed: 'badge-analyzed',
  scored: 'badge-scored', personalized: 'badge-personalized',
  contacted: 'badge-contacted', converted: 'badge-converted', rejected: 'badge-default',
}

const STATUS_LABEL = {
  personalized: '✉ Ready to Send',
}

function StatusBadge({ status }) {
  return (
    <span className={`badge ${STATUS_BADGE[status] || 'badge-default'}`}>
      {STATUS_LABEL[status] || status}
    </span>
  )
}


const WA_SVG = (
  <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor" aria-hidden>
    <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z" />
  </svg>
)

function toWaPhone(phone) {
  if (!phone) return null
  const d = phone.replace(/\D/g, '')
  if (!d) return null
  if (d.length === 10) return '91' + d
  if (d.length === 11 && d.startsWith('0')) return '91' + d.slice(1)
  return d
}

export default function LeadsTable({ leads, loading, pagination, onPageChange, onRefresh, toast, filters, onFilterChange }) {
  const [selected, setSelected] = useState(null)
  const [busyId, setBusyId] = useState(null)
  const [localLeads, setLocalLeads] = useState({})
  const [checkedIds, setCheckedIds] = useState(new Set())
  const [bulkBusy, setBulkBusy] = useState(false)
  const [showCatFilter, setShowCatFilter] = useState(false)

  const filteredCatOptions = filters.category
    ? BUSINESS_TYPES.filter((t) =>
        t.toLowerCase().includes(filters.category.toLowerCase()) ||
        labelToKeyword(t).toLowerCase().includes(filters.category.toLowerCase())
      )
    : BUSINESS_TYPES

  const allPageIds = leads.map((l) => l.id)
  const allChecked = allPageIds.length > 0 && allPageIds.every((id) => checkedIds.has(id))
  const someChecked = checkedIds.size > 0

  function toggleRow(id) {
    setCheckedIds((prev) => {
      const next = new Set(prev)
      next.has(id) ? next.delete(id) : next.add(id)
      return next
    })
  }

  function toggleAll() {
    if (allChecked) {
      setCheckedIds((prev) => {
        const next = new Set(prev)
        allPageIds.forEach((id) => next.delete(id))
        return next
      })
    } else {
      setCheckedIds((prev) => new Set([...prev, ...allPageIds]))
    }
  }

  async function handleBulkDelete() {
    if (!checkedIds.size) return
    if (!confirm(`Delete ${checkedIds.size} selected lead(s)?`)) return
    setBulkBusy(true)
    try {
      await api.bulkDeleteLeads([...checkedIds])
      toast(`Deleted ${checkedIds.size} leads`, 'success')
      setCheckedIds(new Set())
      onRefresh()
    } catch (err) {
      toast(err.message, 'error')
    } finally {
      setBulkBusy(false)
    }
  }

  async function handleDeleteAll() {
    if (!confirm('Delete ALL leads? This cannot be undone.')) return
    setBulkBusy(true)
    try {
      const res = await api.deleteAllLeads()
      toast(`Deleted all ${res.deleted} leads`, 'success')
      setCheckedIds(new Set())
      onRefresh()
    } catch (err) {
      toast(err.message, 'error')
    } finally {
      setBulkBusy(false)
    }
  }

  function getLead(lead) {
    return localLeads[lead.id] ? { ...lead, ...localLeads[lead.id] } : lead
  }

  async function runOutreach(e, lead) {
    e.stopPropagation()
    setBusyId(lead.id + 'Personalize')
    try {
      await api.personalizeLead(lead.id)
      const fresh = await api.getLead(lead.id)
      setLocalLeads((prev) => ({ ...prev, [lead.id]: fresh }))
      toast('Outreach generated', 'success')
      onRefresh()
    } catch (err) {
      toast(err.message, 'error')
    } finally {
      setBusyId(null)
    }
  }

  return (
    <>
      <div className="table-header">
        <span className="table-title">
          Leads
          {pagination && <span style={{ fontSize: 13, fontWeight: 400, color: 'var(--muted)', marginLeft: 8 }}>({pagination.total})</span>}
        </span>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8, alignItems: 'flex-end' }}>
          {/* Business type filter */}
          <div style={{ position: 'relative' }}>
            <input
              className="search-input"
              placeholder="Filter by business type…"
              value={filters.category}
              autoComplete="off"
              style={{ width: 220 }}
              onChange={(e) => { onFilterChange('category', e.target.value); setShowCatFilter(true) }}
              onFocus={() => setShowCatFilter(true)}
              onBlur={() => setTimeout(() => setShowCatFilter(false), 150)}
            />
            {filters.category && (
              <button
                onClick={() => onFilterChange('category', '')}
                style={{ position: 'absolute', right: 8, top: '50%', transform: 'translateY(-50%)', background: 'none', border: 'none', cursor: 'pointer', color: 'var(--muted)', fontSize: 14, lineHeight: 1 }}
                tabIndex={-1}
              >✕</button>
            )}
            {showCatFilter && filteredCatOptions.length > 0 && (
              <ul className="keyword-dropdown" style={{ minWidth: 220 }}>
                {filteredCatOptions.map((t) => (
                  <li
                    key={t}
                    className={`keyword-option ${filters.category === labelToKeyword(t) ? 'keyword-option-active' : ''}`}
                    onMouseDown={() => { onFilterChange('category', labelToKeyword(t)); setShowCatFilter(false) }}
                  >
                    <span>{t}</span>
                    <small style={{ color: 'var(--muted)', marginLeft: 6 }}>→ {labelToKeyword(t)}</small>
                  </li>
                ))}
              </ul>
            )}
          </div>

        <div className="filter-bar">
          <input
            className="search-input"
            placeholder="Search name or category…"
            value={filters.search}
            onChange={(e) => onFilterChange('search', e.target.value)}
          />
          <label className="filter-toggle">
            <input
              type="checkbox"
              checked={filters.no_website}
              onChange={(e) => onFilterChange('no_website', e.target.checked)}
            />
            No website
          </label>
          <button className="btn btn-ghost btn-sm" onClick={onRefresh}>↻</button>
          <button className="btn btn-sm btn-danger" disabled={bulkBusy} onClick={handleDeleteAll} title="Delete all leads">
            🗑 All
          </button>
        </div>
        </div>
      </div>

      {someChecked && (
        <div className="bulk-bar">
          <span className="bulk-count">{checkedIds.size} selected</span>
          <button className="btn btn-sm btn-danger" disabled={bulkBusy} onClick={handleBulkDelete}>
            {bulkBusy ? <span className="spinner-xs" /> : '🗑'} Delete Selected
          </button>
          <button className="btn btn-sm btn-ghost" onClick={() => setCheckedIds(new Set())}>
            Clear
          </button>
        </div>
      )}

      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th style={{ width: 36 }}>
                <input type="checkbox" checked={allChecked} onChange={toggleAll} style={{ cursor: 'pointer', accentColor: 'var(--accent)' }} />
              </th>
              <th>Business</th>
              <th>Phone</th>
              <th>Website</th>
              <th>Rating</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={7} style={{ textAlign: 'center', padding: 40 }}>
                <span className="spinner" />
              </td></tr>
            ) : leads.length === 0 ? (
              <tr><td colSpan={7}>
                <div className="empty">
                  <div className="empty-icon">📭</div>
                  <p>No leads found. Try adjusting filters or collect some!</p>
                </div>
              </td></tr>
            ) : (
              leads.map((rawLead) => {
                const lead = getLead(rawLead)
                const waNum = toWaPhone(lead.phone)
                return (
                  <tr key={lead.id} style={{ cursor: 'pointer' }} onClick={() => setSelected(lead)}>
                    <td onClick={(e) => e.stopPropagation()}>
                      <input
                        type="checkbox"
                        checked={checkedIds.has(lead.id)}
                        onChange={() => toggleRow(lead.id)}
                        style={{ cursor: 'pointer', accentColor: 'var(--accent)' }}
                      />
                    </td>
                    <td>
                      <div className="td-name">
                        {lead.business_name}
                        <small>{lead.category || '—'}</small>
                      </div>
                    </td>
                    <td>
                      {lead.phone
                        ? <a href={`tel:${lead.phone}`} className="phone-link" onClick={(e) => e.stopPropagation()}>{lead.phone}</a>
                        : <span className="no-site">—</span>}
                    </td>
                    <td>
                      {lead.has_website
                        ? <span className="has-site">✓ Yes</span>
                        : <span className="no-site">✕ No</span>}
                    </td>
                    <td>{lead.rating ? `⭐ ${lead.rating}` : '—'}</td>
                    <td>
                      <StatusBadge status={lead.status} />
                    </td>
                    <td>
                      <div className="td-actions" onClick={(e) => e.stopPropagation()}>
                        {lead.outreach_whatsapp ? (
                          <>
                            {lead.outreach_email && (
                              <a
                                href={mailtoLink(lead.email, lead.business_name, lead.outreach_email)}
                                className="action-btn action-email"
                                title={lead.email ? `Send email to ${lead.email}` : 'Open email client'}
                                onClick={(e) => e.stopPropagation()}
                              >
                                {EMAIL_SVG} Email
                              </a>
                            )}
                            {waNum && (
                              <a
                                href={`https://wa.me/${waNum}?text=${encodeURIComponent(lead.outreach_whatsapp)}`}
                                target="_blank"
                                rel="noreferrer"
                                className="action-btn action-wa"
                                title="Send WhatsApp with outreach message"
                              >
                                {WA_SVG} WhatsApp
                              </a>
                            )}
                          </>
                        ) : (
                          <>
                            <button
                              className="action-btn action-outreach"
                              title="Generate outreach messages"
                              disabled={!!busyId}
                              onClick={(e) => runOutreach(e, lead)}
                            >
                              {busyId === lead.id + 'Personalize' ? <span className="spinner-xs" /> : '✉'}
                              Outreach
                            </button>
                            {waNum && (
                              <a
                                href={`https://wa.me/${waNum}`}
                                target="_blank"
                                rel="noreferrer"
                                className="action-btn action-wa"
                                title="Open WhatsApp chat"
                              >
                                {WA_SVG}
                              </a>
                            )}
                          </>
                        )}
                      </div>
                    </td>
                  </tr>
                )
              })
            )}
          </tbody>
        </table>

        {pagination && pagination.pages > 1 && (
          <div className="pagination">
            <span>Page {pagination.page} of {pagination.pages} · {pagination.total} leads</span>
            <div className="pagination-btns">
              <button
                className="btn btn-sm btn-ghost"
                disabled={pagination.page <= 1}
                onClick={() => onPageChange(pagination.page - 1)}
              >← Prev</button>
              <button
                className="btn btn-sm btn-ghost"
                disabled={pagination.page >= pagination.pages}
                onClick={() => onPageChange(pagination.page + 1)}
              >Next →</button>
            </div>
          </div>
        )}
      </div>

      {selected && (
        <LeadModal
          lead={selected}
          onClose={() => setSelected(null)}
          onRefresh={onRefresh}
          toast={toast}
        />
      )}
    </>
  )
}
