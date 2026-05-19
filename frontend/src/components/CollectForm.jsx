import { useState, useEffect, useRef } from 'react'
import { api } from '../api'
import { BUSINESS_TYPES } from '../constants'

const CITIES = [
  { label: 'Bangalore, India',  lat: 12.9716, lng: 77.5946 },
  { label: 'Mumbai, India',     lat: 19.0760, lng: 72.8777 },
  { label: 'Delhi, India',      lat: 28.6139, lng: 77.2090 },
  { label: 'Chennai, India',    lat: 13.0827, lng: 80.2707 },
  { label: 'Hyderabad, India',  lat: 17.3850, lng: 78.4867 },
  { label: 'Pune, India',       lat: 18.5204, lng: 73.8567 },
  { label: 'Kolkata, India',    lat: 22.5726, lng: 88.3639 },
  { label: 'Ahmedabad, India',  lat: 23.0225, lng: 72.5714 },
  { label: 'New York, USA',     lat: 40.7128, lng: -74.0060 },
  { label: 'London, UK',        lat: 51.5074, lng: -0.1278  },
  { label: 'Dubai, UAE',        lat: 25.2048, lng: 55.2708  },
  { label: 'Singapore',         lat: 1.3521,  lng: 103.8198 },
]

const RESULTS_OPTIONS = [10, 20, 30, 50]

const LOADING_STEPS = [
  'Connecting to Google Maps…',
  'Searching businesses…',
  'Extracting contact details…',
  'Saving leads to database…',
  'Almost done…',
]

export default function CollectForm({ onCollected, toast }) {
  const [keyword, setKeyword]       = useState('')
  const [city, setCity]             = useState(CITIES[0])
  const [maxResults, setMaxResults] = useState(20)
  const [loading, setLoading]       = useState(false)
  const [progress, setProgress]     = useState(0)
  const [stepLabel, setStepLabel]   = useState('')
  const [showList, setShowList]     = useState(false)
  const progressRef                 = useRef(null)

  const filtered = keyword.trim()
    ? BUSINESS_TYPES.filter((t) => t.toLowerCase().includes(keyword.toLowerCase()))
    : BUSINESS_TYPES

  useEffect(() => {
    if (!loading) { setProgress(0); setStepLabel(''); return }

    setProgress(5)
    setStepLabel(LOADING_STEPS[0])

    const steps = [
      { pct: 20, delay: 800,  label: LOADING_STEPS[1] },
      { pct: 45, delay: 2500, label: LOADING_STEPS[2] },
      { pct: 68, delay: 5000, label: LOADING_STEPS[3] },
      { pct: 85, delay: 9000, label: LOADING_STEPS[4] },
    ]

    const timers = steps.map(({ pct, delay, label }) =>
      setTimeout(() => {
        setProgress(pct)
        setStepLabel(label)
      }, delay)
    )

    return () => timers.forEach(clearTimeout)
  }, [loading])

  async function handleSubmit(e) {
    e.preventDefault()
    if (!keyword.trim()) return toast('Enter a business type', 'error')
    setShowList(false)
    setLoading(true)
    try {
      const res = await api.collectLeads({
        keyword:     keyword.trim(),
        latitude:    city.lat,
        longitude:   city.lng,
        radius:      5000,
        max_results: maxResults,
      })
      setProgress(100)
      setStepLabel('Done!')
      setTimeout(() => {
        toast(`Saved ${res.new_leads} new leads (found ${res.total_found})`, 'success')
        onCollected()
        setLoading(false)
      }, 500)
    } catch (err) {
      toast(err.message, 'error')
      setLoading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} style={{ position: 'relative' }}>
      <div className="card-title">Collect Leads</div>

      <div className="form-group" style={{ position: 'relative' }}>
        <label>Business Type</label>
        <input
          placeholder="e.g. Restaurants, Salons, Gyms…"
          value={keyword}
          autoComplete="off"
          disabled={loading}
          onChange={(e) => { setKeyword(e.target.value); setShowList(true) }}
          onFocus={() => setShowList(true)}
          onBlur={() => setTimeout(() => setShowList(false), 150)}
        />
        {showList && filtered.length > 0 && (
          <ul className="keyword-dropdown">
            {filtered.map((t) => (
              <li
                key={t}
                className="keyword-option"
                onMouseDown={() => { setKeyword(t); setShowList(false) }}
              >
                {t}
              </li>
            ))}
          </ul>
        )}
      </div>

      <div className="form-group">
        <label>City</label>
        <select
          value={city.label}
          disabled={loading}
          onChange={(e) => setCity(CITIES.find((c) => c.label === e.target.value))}
        >
          {CITIES.map((c) => (
            <option key={c.label} value={c.label}>{c.label}</option>
          ))}
        </select>
      </div>

      <div className="form-group">
        <label>Max Results</label>
        <select value={maxResults} disabled={loading} onChange={(e) => setMaxResults(Number(e.target.value))}>
          {RESULTS_OPTIONS.map((n) => (
            <option key={n} value={n}>{n} businesses</option>
          ))}
        </select>
      </div>

      {/* Progress bar — visible only while loading */}
      {loading && (
        <div className="collect-progress">
          <div className="collect-progress-track">
            <div
              className="collect-progress-fill"
              style={{ width: `${progress}%` }}
            />
          </div>
          <div className="collect-progress-label">{stepLabel}</div>
        </div>
      )}

      <button className="btn collect-btn" type="submit" disabled={loading}>
        {loading ? (
          <span className="collect-btn-loading">
            <span className="collect-dot" /><span className="collect-dot" /><span className="collect-dot" />
          </span>
        ) : (
          <>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/>
            </svg>
            Collect Leads
          </>
        )}
      </button>
    </form>
  )
}
