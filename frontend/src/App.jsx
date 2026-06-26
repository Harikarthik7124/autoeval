import { useState } from 'react'
import axios from 'axios'
import {
  RadarChart, PolarGrid, PolarAngleAxis,
  Radar, ResponsiveContainer, Tooltip
} from 'recharts'
import './App.css'

const API_URL = import.meta.env.VITE_API_URL || 'https://autoeval-production.up.railway.app'

const RUBRIC_LABELS = {
  code_quality: 'Code quality',
  commit_hygiene: 'Commit hygiene',
  documentation: 'Documentation',
  stack_breadth: 'Stack breadth',
  project_complexity: 'Project complexity',
  recency: 'Recency',
  oss_contributions: 'OSS contributions',
  ai_ml_presence: 'AI/ML presence'
}

const RUBRIC_COLORS = {
  code_quality: '#9B93F5',
  commit_hygiene: '#4ADE80',
  documentation: '#38BDF8',
  stack_breadth: '#FB923C',
  project_complexity: '#F87171',
  recency: '#34D399',
  oss_contributions: '#F472B6',
  ai_ml_presence: '#C084FC'
}

const SHORT_LABELS = {
  code_quality: 'Code',
  commit_hygiene: 'Commits',
  documentation: 'Docs',
  stack_breadth: 'Stack',
  project_complexity: 'Complexity',
  recency: 'Recency',
  oss_contributions: 'OSS',
  ai_ml_presence: 'AI/ML'
}

function formatRadarData(finalScores) {
  return Object.entries(finalScores).map(([key, score]) => ({
    key,
    rubric: SHORT_LABELS[key] || key,
    fullName: RUBRIC_LABELS[key] || key,
    score
  }))
}

function gradeLabel(composite) {
  if (composite >= 75) return { text: 'Strong hire signal', tone: 'strong' }
  if (composite >= 50) return { text: 'Promising — needs review', tone: 'moderate' }
  return { text: 'Early-stage profile', tone: 'weak' }
}

function CustomTooltip({ active, payload }) {
  if (!active || !payload?.length) return null
  const point = payload[0].payload
  return (
    <div className="chart-tooltip">
      <div className="tooltip-dot" style={{ background: RUBRIC_COLORS[point.key] }} />
      <div>
        <div className="tooltip-label">{point.fullName}</div>
        <div className="tooltip-value">{payload[0].value.toFixed(1)} / 10</div>
      </div>
    </div>
  )
}

function CustomDot(props) {
  const { cx, cy, payload } = props
  if (!cx || !cy) return null
  return (
    <circle
      cx={cx} cy={cy} r={5}
      fill={RUBRIC_COLORS[payload.key]}
      stroke="#0B0D12"
      strokeWidth={2}
    />
  )
}

function ScoreBar({ label, score, color }) {
  return (
    <div className="score-row">
      <div className="score-dot" style={{ background: color }} />
      <span className="score-label">{label}</span>
      <div className="score-track">
        <div
          className="score-fill"
          style={{ width: `${score * 10}%`, background: color }}
        />
      </div>
      <span className="score-num">{score.toFixed(1)}</span>
    </div>
  )
}

export default function App() {
  const [username, setUsername] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')

  async function handleEvaluate() {
    if (!username.trim()) { setError('Enter a GitHub username'); return }
    setLoading(true); setError(''); setResult(null)
    try {
      const res = await axios.post(`${API_URL}/evaluate`, { username: username.trim() })
      setResult(res.data)
    } catch (e) {
      setError(e.response?.data?.detail || 'Could not complete scan — try again')
    } finally {
      setLoading(false)
    }
  }

  const grade = result ? gradeLabel(result.composite) : null

  return (
    <div className="shell">
      <header className="topbar">
        <div className="brand">
          <div className="brand-icon">AE</div>
          <span className="brand-name">AutoEval</span>
        </div>
        <span className="topbar-tag">Dual-model consensus scoring</span>
      </header>

      <main className="stage">
        {!result && (
          <div className="hero">
            <div className="hero-badge">AI-powered · GitHub analysis · 8 rubrics</div>
            <h1 className="hero-title">Evaluate any developer<br />GitHub profile instantly</h1>
            <p className="hero-sub">Enter a username and get a detailed rubric-based assessment powered by two LLMs in consensus</p>
          </div>
        )}

        <div className={`search-wrap ${result ? 'search-compact' : ''}`}>
          <div className="search-bar">
            <i className="ti ti-brand-github search-icon" aria-hidden="true" />
            <input
              className="search-input"
              placeholder="Enter GitHub username, e.g. torvalds"
              value={username}
              onChange={e => setUsername(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleEvaluate()}
              spellCheck="false"
            />
            <button className="search-btn" onClick={handleEvaluate} disabled={loading}>
              {loading ? <span className="spinner" /> : 'Evaluate'}
            </button>
          </div>
          {error && <p className="search-error"><i className="ti ti-alert-circle" /> {error}</p>}
        </div>

        {loading && (
          <div className="loading-wrap">
            <div className="loading-bar" />
            <div className="loading-steps">
              <div className="loading-step"><span className="step-spin" />Fetching GitHub profile</div>
              <div className="loading-step"><span className="step-spin" />Running dual-model scoring</div>
              <div className="loading-step"><span className="step-spin" />Calculating consensus</div>
            </div>
          </div>
        )}

        {result && !loading && (
          <div className="results">
            <div className="summary-card">
              <div className="summary-left">
                <div className="avatar">{result.username.slice(0, 2).toUpperCase()}</div>
                <div>
                  <h2 className="summary-name">{result.username}</h2>
                  <span className={`grade grade-${grade.tone}`}>{grade.text}</span>
                </div>
              </div>
              <div className="summary-score">
                <span className="score-big">{Math.round(result.composite)}</span>
                <span className="score-denom">/ 100</span>
              </div>
            </div>

            <div className="results-grid">
              <div className="card">
                <div className="card-head">
                  <span className="card-title">Rubric profile</span>
                  <span className="card-hint">Hover for exact scores</span>
                </div>
                <ResponsiveContainer width="100%" height={420}>
                  <RadarChart
                    data={formatRadarData(result.final_scores)}
                    margin={{ top: 30, right: 50, bottom: 30, left: 50 }}
                  >
                    <PolarGrid stroke="rgba(255,255,255,0.08)" />
                    <PolarAngleAxis
                      dataKey="rubric"
                      tick={{ fill: '#C4C5CC', fontSize: 12, fontFamily: 'Inter, sans-serif' }}
                      tickLine={false}
                    />
                    <Tooltip content={<CustomTooltip />} />
                    <Radar
                      dataKey="score"
                      stroke="#9B93F5"
                      fill="#9B93F5"
                      fillOpacity={0.2}
                      strokeWidth={2}
                      dot={<CustomDot />}
                    />
                  </RadarChart>
                </ResponsiveContainer>
              </div>

              <div className="card">
                <div className="card-head">
                  <span className="card-title">Score breakdown</span>
                </div>
                <div className="score-list">
                  {Object.entries(result.final_scores).map(([key, score]) => (
                    <ScoreBar
                      key={key}
                      label={RUBRIC_LABELS[key]}
                      score={score}
                      color={RUBRIC_COLORS[key]}
                    />
                  ))}
                </div>
              </div>
            </div>

            {result.conflicts?.length > 0 && (
              <details className="conflicts-card">
                <summary className="conflicts-summary">
                  <i className="ti ti-alert-triangle" aria-hidden="true" />
                  {result.conflicts.length} model disagreement{result.conflicts.length > 1 ? 's' : ''} detected
                  <i className="ti ti-chevron-down conflicts-chevron" aria-hidden="true" />
                </summary>
                <p className="conflicts-desc">Score gap &gt;1.5 points between models — manual review suggested</p>
                <div className="conflicts-grid">
                  {result.conflicts.map((c, i) => (
                    <div className="conflict-item" key={i}>
                      <div className="conflict-dot" style={{ background: RUBRIC_COLORS[c.rubric] }} />
                      <div>
                        <div className="conflict-name">{RUBRIC_LABELS[c.rubric] || c.rubric}</div>
                        <div className="conflict-vals">
                          <span>70B · {c.llama70.toFixed(1)}</span>
                          <span className="conflict-delta">Δ {c.delta.toFixed(1)}</span>
                          <span>8B · {c.llama8.toFixed(1)}</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </details>
            )}

            <button className="reset-btn" onClick={() => { setResult(null); setUsername('') }}>
              <i className="ti ti-refresh" aria-hidden="true" /> Evaluate another profile
            </button>
          </div>
        )}

        {!result && !loading && (
          <div className="feature-grid">
            <div className="feature-card">
              <i className="ti ti-brand-github feature-icon" aria-hidden="true" />
              <div className="feature-title">GitHub analysis</div>
              <div className="feature-desc">Fetches repos, commits, READMEs, languages and contribution patterns</div>
            </div>
            <div className="feature-card">
              <i className="ti ti-robot feature-icon" aria-hidden="true" />
              <div className="feature-title">Dual LLM scoring</div>
              <div className="feature-desc">Two models score independently — consensus layer resolves disagreements</div>
            </div>
            <div className="feature-card">
              <i className="ti ti-chart-radar feature-icon" aria-hidden="true" />
              <div className="feature-title">8 rubric axes</div>
              <div className="feature-desc">Code quality, commits, docs, stack breadth, complexity, recency and more</div>
            </div>
          </div>
        )}
      </main>
    </div>
  )
}