import { useState, useEffect } from 'react'
import { api } from '../api'

const STATUS_OPTIONS = ['new', 'analyzing', 'analyzed', 'scored', 'personalized', 'contacted', 'converted', 'rejected']

const WA_SVG = (
  <svg width="13" height="13" viewBox="0 0 24 24" fill="currentColor" aria-hidden>
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

function waLink(phone, message) {
  const num = toWaPhone(phone)
  if (!num) return null
  return message
    ? `https://wa.me/${num}?text=${encodeURIComponent(message)}`
    : `https://wa.me/${num}`
}

function mailtoLink(email, businessName, body) {
  const subject = `Free Website Demo for ${businessName} – MadTech Solutions`
  const params = new URLSearchParams({ subject, body: body || '' }).toString().replace(/\+/g, '%20')
  return email ? `mailto:${email}?${params}` : `mailto:?${params}`
}

const EMAIL_SVG = (
  <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
    <rect x="2" y="4" width="20" height="16" rx="2"/>
    <path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/>
  </svg>
)

function CopyButton({ text }) {
  const [copied, setCopied] = useState(false)
  async function handleCopy() {
    try {
      await navigator.clipboard.writeText(text)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch {
      // fallback for non-secure contexts
      const ta = document.createElement('textarea')
      ta.value = text
      document.body.appendChild(ta)
      ta.select()
      document.execCommand('copy')
      document.body.removeChild(ta)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }
  }
  return (
    <button className={`copy-btn ${copied ? 'copied' : ''}`} onClick={handleCopy} type="button">
      {copied ? '✓ Copied' : 'Copy'}
    </button>
  )
}

function OutreachSection({ title, message, phone, isWhatsApp }) {
  const link = isWhatsApp ? waLink(phone, message) : null
  return (
    <div className="modal-section">
      <div className="outreach-header">
        <div className="modal-section-title">{title}</div>
        <div className="outreach-actions">
          <CopyButton text={message} />
          {link && (
            <a href={link} target="_blank" rel="noreferrer" className="btn btn-sm btn-whatsapp">
              {WA_SVG} Send
            </a>
          )}
        </div>
      </div>
      <div className="outreach-box">{message}</div>
    </div>
  )
}

export default function LeadModal({ lead, onClose, onRefresh, toast }) {
  const [busy, setBusy] = useState(null)
  const [data, setData] = useState(lead)

  useEffect(() => {
    api.getLead(lead.id).then(setData).catch(() => {})
  }, [lead.id])

  const scoreClass = data.ai_score != null
    ? (data.ai_score >= 70 ? 'high' : data.ai_score >= 40 ? 'med' : 'low')
    : null
  const waNum = toWaPhone(data.phone)

  return (
    <div className="modal-overlay" onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className="modal">
        {/* Header */}
        <div className="modal-header">
          <div>
            <div className="modal-title">{data.business_name}</div>
            <div className="modal-subtitle">
              {[data.category, data.address].filter(Boolean).join(' · ') || 'No details'}
            </div>
          </div>
          <button className="modal-close" onClick={onClose} aria-label="Close">✕</button>
        </div>

        <div className="modal-body">
          {/* Business Info */}
          <div className="modal-section">
            <div className="modal-section-title">Business Info</div>
            <div className="info-grid">
              <InfoItem label="Phone" value={
                data.phone ? (
                  <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
                    <a href={`tel:${data.phone}`} className="phone-link">{data.phone}</a>
                    {waNum && (
                      <a href={`https://wa.me/${waNum}`} target="_blank" rel="noreferrer" className="wa-chip">
                        {WA_SVG} Chat
                      </a>
                    )}
                  </div>
                ) : '—'
              } />
              <InfoItem label="Email" value={
                data.email
                  ? <a href={`mailto:${data.email}`} className="phone-link">{data.email}</a>
                  : <span className="no-site">—</span>
              } />
              <InfoItem label="Website" value={
                data.website
                  ? <a href={data.website} target="_blank" rel="noreferrer" className="phone-link">{data.website}</a>
                  : <span className="no-site">No website</span>
              } />
              <InfoItem label="Rating" value={
                data.rating
                  ? `⭐ ${data.rating}${data.reviews_count ? ` (${data.reviews_count} reviews)` : ''}`
                  : '—'
              } />
              <InfoItem label="Status" value={<StatusBadge status={data.status} />} />
              <InfoItem label="AI Score" value={
                data.ai_score != null
                  ? <span className={`score-pill ${scoreClass}`}>{data.ai_score}/100</span>
                  : '—'
              } />
              <InfoItem label="Website Quality" value={data.website_quality || '—'} />
            </div>
          </div>

          {/* Website Analysis */}
          {data.website_analysis_summary && (
            <div className="modal-section">
              <div className="modal-section-title">Website Analysis</div>
              <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 10 }}>
                <Chip ok={data.is_mobile_responsive} label="Mobile" />
                <Chip ok={data.has_modern_ui} label="Modern UI" />
                <Chip ok={data.has_contact_form} label="Contact Form" />
                <Chip ok={data.has_gallery} label="Gallery" />
              </div>
              <p style={{ fontSize: 12, color: 'var(--muted)', lineHeight: 1.6 }}>
                {data.website_analysis_summary}
              </p>
            </div>
          )}

          {/* Outreach — WhatsApp first (primary action) */}
          {data.outreach_whatsapp && (
            <OutreachSection
              title="WhatsApp Message"
              message={data.outreach_whatsapp}
              phone={data.phone}
              isWhatsApp
            />
          )}
          {data.outreach_email && (
            <OutreachSection title="Email Outreach" message={data.outreach_email} />
          )}
          {data.outreach_dm && (
            <OutreachSection title="Cold DM" message={data.outreach_dm} />
          )}

          {/* Status updater */}
          <div className="modal-section">
            <div className="modal-section-title">Update Status</div>
            <select
              value={data.status}
              disabled={busy === 'status'}
              onChange={async (e) => {
                const newStatus = e.target.value
                setBusy('status')
                try {
                  const updated = await api.updateStatus(data.id, newStatus)
                  setData(updated)
                  onRefresh()
                  toast('Status updated', 'success')
                } catch (err) {
                  toast(err.message, 'error')
                } finally {
                  setBusy(null)
                }
              }}
              style={{ width: '100%' }}
            >
              {STATUS_OPTIONS.map((s) => <option key={s} value={s}>{s}</option>)}
            </select>
          </div>
        </div>

        {/* Action bar */}
        <div className="modal-actions">
          <button
            className="action-btn action-outreach"
            disabled={!!busy}
            onClick={async () => {
              setBusy('Personalization')
              try {
                await api.personalizeLead(data.id)
                const fresh = await api.getLead(data.id)
                setData(fresh)
                onRefresh()
                toast('Outreach generated', 'success')
              } catch (err) {
                toast(err.message, 'error')
              } finally {
                setBusy(null)
              }
            }}
          >
            {busy === 'Personalization' ? <span className="spinner-xs" /> : '✉'} Outreach
          </button>
          {waNum && (
            <a
              href={data.outreach_whatsapp ? waLink(data.phone, data.outreach_whatsapp) : `https://wa.me/${waNum}`}
              target="_blank"
              rel="noreferrer"
              className="btn btn-sm btn-whatsapp"
              title={data.outreach_whatsapp ? 'Send pre-filled WhatsApp message' : 'Open WhatsApp chat'}
            >
              {WA_SVG} {data.outreach_whatsapp ? 'Send WhatsApp' : 'WhatsApp'}
            </a>
          )}
          {data.outreach_email && (
            <a
              href={mailtoLink(data.email, data.business_name, data.outreach_email)}
              className="btn btn-sm btn-email"
              title={data.email ? `Send email to ${data.email}` : 'Open email client (fill in recipient)'}
            >
              {EMAIL_SVG} {data.email ? 'Send Email' : 'Draft Email'}
            </a>
          )}
          <div className="modal-actions-spacer" />
          <button
            className="btn btn-sm btn-danger"
            disabled={!!busy}
            onClick={async () => {
              if (!confirm('Delete this lead?')) return
              await api.deleteLead(data.id)
              toast('Lead deleted', 'info')
              onRefresh()
              onClose()
            }}
          >
            🗑 Delete
          </button>
        </div>
      </div>
    </div>
  )
}

function InfoItem({ label, value }) {
  return (
    <div className="info-item">
      <label>{label}</label>
      <span>{value}</span>
    </div>
  )
}

function Chip({ ok, label }) {
  const styles = ok === true
    ? { background: '#d1fae5', border: '1px solid #86efac', color: '#065f46' }
    : ok === false
    ? { background: '#fee2e2', border: '1px solid #fca5a5', color: '#991b1b' }
    : { background: 'var(--surface2)', border: '1px solid var(--border)', color: 'var(--muted)' }
  const icon = ok === true ? '✓' : ok === false ? '✕' : '?'
  return (
    <span style={{ fontSize: 11, fontWeight: 600, padding: '2px 9px', borderRadius: 20, ...styles }}>
      {icon} {label}
    </span>
  )
}

function StatusBadge({ status }) {
  const cls = {
    new: 'badge-new', analyzed: 'badge-analyzed', scored: 'badge-scored',
    personalized: 'badge-personalized', contacted: 'badge-contacted', converted: 'badge-converted',
  }[status] || 'badge-default'
  return <span className={`badge ${cls}`}>{status}</span>
}
