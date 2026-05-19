import { useState } from 'react'
import { api } from '../api'
import { BUSINESS_TYPES } from '../constants'

export default function ManualForm({ onCreated, toast }) {
  const [open, setOpen]       = useState(false)
  const [loading, setLoading] = useState(false)
  const [showCatList, setShowCatList] = useState(false)
  const [form, setForm]       = useState({
    business_name: '', category: '', phone: '', website: '', address: '',
  })

  function set(k, v) { setForm((f) => ({ ...f, [k]: v })) }

  const filteredCats = form.category.trim()
    ? BUSINESS_TYPES.filter((t) => t.toLowerCase().includes(form.category.toLowerCase()))
    : BUSINESS_TYPES

  async function handleSubmit(e) {
    e.preventDefault()
    if (!form.business_name.trim()) return toast('Business name required', 'error')
    setLoading(true)
    try {
      await api.createLead(form)
      toast('Lead created', 'success')
      setForm({ business_name: '', category: '', phone: '', website: '', address: '' })
      setOpen(false)
      onCreated()
    } catch (err) {
      toast(err.message, 'error')
    } finally {
      setLoading(false)
    }
  }

  if (!open) {
    return (
      <button className="btn btn-ghost" style={{ width: '100%' }} onClick={() => setOpen(true)}>
        + Add Lead Manually
      </button>
    )
  }

  return (
    <form onSubmit={handleSubmit}>
      <div className="card-title">Add Manually</div>

      <div className="form-group">
        <label>Business Name *</label>
        <input
          placeholder="Pizza Palace"
          value={form.business_name}
          onChange={(e) => set('business_name', e.target.value)}
        />
      </div>

      <div className="form-group" style={{ position: 'relative' }}>
        <label>Category</label>
        <input
          placeholder="Restaurant, Salon, Gym…"
          value={form.category}
          autoComplete="off"
          onChange={(e) => { set('category', e.target.value); setShowCatList(true) }}
          onFocus={() => setShowCatList(true)}
          onBlur={() => setTimeout(() => setShowCatList(false), 150)}
        />
        {showCatList && filteredCats.length > 0 && (
          <ul className="keyword-dropdown">
            {filteredCats.map((t) => (
              <li
                key={t}
                className="keyword-option"
                onMouseDown={() => { set('category', t); setShowCatList(false) }}
              >
                {t}
              </li>
            ))}
          </ul>
        )}
      </div>

      {[
        ['phone',   'Phone',   '+91 98765 43210'],
        ['website', 'Website', 'https://example.com'],
        ['address', 'Address', '123 Main St, City'],
      ].map(([key, label, ph]) => (
        <div className="form-group" key={key}>
          <label>{label}</label>
          <input placeholder={ph} value={form[key]} onChange={(e) => set(key, e.target.value)} />
        </div>
      ))}

      <div style={{ display: 'flex', gap: 8, marginTop: 4 }}>
        <button className="btn btn-primary" type="submit" disabled={loading} style={{ flex: 1 }}>
          {loading ? <span className="spinner" /> : 'Save'}
        </button>
        <button className="btn btn-ghost" type="button" onClick={() => setOpen(false)}>Cancel</button>
      </div>
    </form>
  )
}
