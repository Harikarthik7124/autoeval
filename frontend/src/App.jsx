import { useState } from 'react'
import axios from 'axios'
import {
  RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  Radar, ResponsiveContainer, Tooltip
} from 'recharts'
import './App.css'

const API_URL = 'http://127.0.0.1:8000'

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
  commit_hygiene: '#5FE596',
  documentation: '#4DC9FF',
  stack_breadth: '#FFB84D',
  project_complexity: '#FF7A5C',
  recency: '#5FE5C4',
  oss_contributions: '#FF8FCB',
  ai_ml_presence: '#C9A8FF'
}

function formatRadarData(finalScores) {
  return Object.entries(finalScores).map(([key, score]) => ({
    key: key,
    rubric: RUBRIC_LABELS[key] || key,
    score: score
  }))
}

function gradeLabel(composite) {
  if (composite >= 75) return { text: 'Strong hire signal', tone: 'strong' }
  if (composite >= 50) return { text: 'Promising, needs review', tone: 'moderate' }
  return { text: 'Early-stage profile', tone: 'weak' }
}

function CustomTooltip({ active, payload }) {
  if (!active || !payload?.length) return null
  const point = payload[0].payload
  return (
    <div className="chart-tooltip">
      <span className="tooltip-dot" style={{ background: RUBRIC_COLORS[point.key] }} />
      <span className="tooltip-label">{point.rubric}</span>
      <span className="tooltip-value">{payload[0].value.toFixed(1)}/10</span>
    </div>
  )
}

function RadarDot(props) {
  const { cx, cy, payload } = props
  return (
    <circle
      cx={cx}
      cy={cy}
      r={5}
      fill={RUBRIC_COLORS[payload.key]}
      stroke="#161821"
      strokeWidth={2}
    />
  )
}

function App() {
  const [username, setUsername] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')
  const [hoveredRubric, setHoveredRubric] = useState(null)

  const handleEvaluate = async () => {
    if (!username.trim()) {
      setError('Enter a GitHub username to get started')
      return
    }
    setLoading(true)
    setError('')
    setResult(null)
    try {
      const response = await axios.post(`${API_URL}/evaluate`, {
        username: username.trim()
      })
      setResult(response.data)
    } catch (err) {
      setError(err.response?.data?.detail || "Couldn't complete that scan — check the username and try again")
    } finally {
      setLoading(false)
    }
  }

  const grade = result ? gradeLabel(result.composite) : null

  return (
    <div className="shell">
      <header className="topbar">
        <div className="brand">
          <div className="brand-icon">A</div>
          <span className="brand-name">AutoEval</span>
        </div>
        <span className="brand-meta">Powered by dual-model consensus scoring</span>
      </header>

      <main className="stage">
        <section className={`hero ${result ? 'hero-compact' : ''}`}>
          {!result && (
            <>
              <h1 className="hero-title">Evaluate any developer profile</h1>
              <p className="hero-subtitle">Enter a GitHub username and get an instant, rubric-based assessment</p>
            </>
          )}

          <div className="search-bar">
            <i className="ti ti-brand-github search-icon" aria-hidden="true"></i>
            <input
              className="search-input"
              type="text"
              placeholder="Enter a GitHub username, e.g. octocat"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleEvaluate()}
              spellCheck="false"
            />
            <button className="search-btn" onClick={handleEvaluate} disabled={loading}>
              {loading ? (
                <span className="btn-spinner" />
              ) : (
                <>Evaluate <i className="ti ti-arrow-right" aria-hidden="true"></i></>
              )}
            </button>
          </div>
          {error && (
            <p className="search-error"><i className="ti ti-alert-circle" aria-hidden="true"></i>{error}</p>
          )}
        </section>

        {loading && (
          <section className="loading-panel">
            <div className="loading-steps">
              <span className="loading-step active">Fetching GitHub profile</span>
              <span className="loading-step active">Scoring with two models</span>
              <span className="loading-step active">Resolving consensus</span>
            </div>
          </section>
        )}

        {result && !loading && (
          <section className="results">
            <div className="result-summary">
              <div className="summary-left">
                <div className="avatar-circle">
                  {result.username.slice(0, 2).toUpperCase()}
                </div>
                <div>
                  <h2 className="summary-name">{result.username}</h2>
                  <span className={`grade-pill grade-${grade.tone}`}>{grade.text}</span>
                </div>
              </div>
              <div className="summary-score">
                <span className="score-num">{Math.round(result.composite)}</span>
                <span className="score-denom">/ 100</span>
              </div>
            </div>

            <div className="grid">
              <div className="card chart-card">
                <div className="card-header">
                  <h3 className="card-title">Rubric profile</h3>
                  <span className="card-hint">Hover the chart for exact scores</span>
                </div>
                <ResponsiveContainer width="100%" height={360}>
                  <RadarChart
                    data={formatRadarData(result.final_scores)}
                    margin={{ top: 24, right: 60, bottom: 10, left: 60 }}
                  >
                    <PolarGrid stroke="var(--border)" />
                    <PolarAngleAxis
                      dataKey="rubric"
                      tick={{ fill: '#C7C9D1', fontSize: 11 }}
                    />
                    <PolarRadiusAxis angle={30} domain={[0, 10]} tick={{ fontSize: 10, fill: '#8B8D98' }} />
                    <Tooltip content={<CustomTooltip />} />
                    <Radar
                      dataKey="score"
                      stroke="#9B93F5"
                      fill="#9B93F5"
                      fillOpacity={0.22}
                      strokeWidth={2}
                      animationDuration={600}
                      dot={<RadarDot />}
                    />
                  </RadarChart>
                </ResponsiveContainer>
              </div>

              <div className="card list-card">
                <div className="card-header">
                  <h3 className="card-title">Score breakdown</h3>
                </div>
                <ul className="rubric-list">
                  {Object.entries(result.final_scores).map(([key, score]) => (
                    <li
                      key={key}
                      className={`rubric-row ${hoveredRubric === key ? 'rubric-hover' : ''}`}
                      onMouseEnter={() => setHoveredRubric(key)}
                      onMouseLeave={() => setHoveredRubric(null)}
                    >
                      <span className="rubric-dot" style={{ background: RUBRIC_COLORS[key] }} />
                      <span className="rubric-name">{RUBRIC_LABELS[key] || key}</span>
                      <div className="rubric-bar-track">
                        <div
                          className="rubric-bar-fill"
                          style={{ width: `${score * 10}%`, background: RUBRIC_COLORS[key] }}
                        />
                      </div>
                      <span className="rubric-score">{score.toFixed(1)}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>

            {result.conflicts.length > 0 && (
              <details className="conflicts-card">
                <summary className="conflicts-summary">
                  <i className="ti ti-git-compare" aria-hidden="true"></i>
                  {result.conflicts.length} model disagreement{result.conflicts.length > 1 ? 's' : ''} detected
                  <i className="ti ti-chevron-down chevron" aria-hidden="true"></i>
                </summary>
                <p className="conflicts-sub">These rubrics had a score gap greater than 1.5 between the two models — worth a manual look.</p>
                <div className="conflict-grid">
                  {result.conflicts.map((c, i) => (
                    <div className="conflict-item" key={i}>
                      <span className="conflict-name">
                        <span className="rubric-dot" style={{ background: RUBRIC_COLORS[c.rubric] }} />
                        {RUBRIC_LABELS[c.rubric] || c.rubric}
                      </span>
                      <div className="conflict-vals">
                        <span>70B · {c.llama70.toFixed(1)}</span>
                        <span className="conflict-delta">Δ {c.delta.toFixed(1)}</span>
                        <span>8B · {c.llama8.toFixed(1)}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </details>
            )}

            <button className="reset-btn" onClick={() => { setResult(null); setUsername('') }}>
              <i className="ti ti-refresh" aria-hidden="true"></i> Run another scan
            </button>
          </section>
        )}
      </main>
    </div>
  )
}

export default App