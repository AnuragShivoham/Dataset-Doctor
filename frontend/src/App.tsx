import { useEffect, useMemo, useState } from 'react'
import { Link, NavLink, Route, Routes, useMatch, useNavigate } from 'react-router-dom'
import './App.css'
import { getAnalysis, uploadDataset } from './api'
import type { AnalysisSummary, ColumnDiagnostic, Recommendation, Severity } from './types'

const severityTone: Record<Severity, string> = {
  Critical: 'critical',
  Warning: 'warning',
  Moderate: 'moderate',
  Healthy: 'healthy',
}

function App() {
  const [analysis, setAnalysis] = useState<AnalysisSummary | null>(null)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [isUploading, setIsUploading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const navigate = useNavigate()
  const match = useMatch('/analysis/:analysisId/*')
  const analysisIdFromUrl = match?.params.analysisId

  useEffect(() => {
    const storedAnalysis = window.sessionStorage.getItem('dataset-doctor-analysis')
    if (!storedAnalysis) {
      return
    }

    try {
      const parsed = JSON.parse(storedAnalysis) as AnalysisSummary
      setAnalysis(parsed)
    } catch {
      window.sessionStorage.removeItem('dataset-doctor-analysis')
    }
  }, [])

  useEffect(() => {
    if (!analysisIdFromUrl) {
      return
    }

    if (analysis && analysis.analysisId === analysisIdFromUrl) {
      return
    }

    const loadAnalysis = async () => {
      try {
        const backendAnalysis = await getAnalysis(analysisIdFromUrl)
        setAnalysis(backendAnalysis)
        window.sessionStorage.setItem('dataset-doctor-analysis', JSON.stringify(backendAnalysis))
      } catch (fetchError) {
        setError(fetchError instanceof Error ? fetchError.message : 'Unable to load the requested analysis.')
      }
    }

    void loadAnalysis()
  }, [analysis, analysisIdFromUrl])

  const readinessLabel = useMemo(() => {
    if (!analysis) return 'Upload a dataset to begin'
    if (analysis.healthScore >= 80) return 'Ready for training'
    if (analysis.healthScore >= 65) return 'Needs review'
    return 'High-risk dataset'
  }, [analysis])

  const handleUpload = async () => {
    if (!selectedFile) {
      setError('Choose a CSV or Excel file first.')
      return
    }

    const supportedPattern = /\.(csv|xlsx|xls)$/i
    if (!supportedPattern.test(selectedFile.name)) {
      setError('Unsupported file type. Please upload CSV or Excel.')
      return
    }

    setIsUploading(true)
    setError(null)

    try {
      const payload = await uploadDataset(selectedFile)
      setAnalysis(payload)
      window.sessionStorage.setItem('dataset-doctor-analysis', JSON.stringify(payload))
      navigate(`/analysis/${payload.analysisId}`)
      setSelectedFile(null)
    } catch (uploadError) {
      setError(uploadError instanceof Error ? uploadError.message : 'Upload failed.')
    } finally {
      setIsUploading(false)
    }
  }

  return (
    <div className="app-shell">
        <header className="topbar">
        <div>
          <p className="eyebrow">AI-powered dataset quality analyzer</p>
          <h1>Dataset Doctor</h1>
        </div>
        <nav aria-label="Primary" className="topnav">
          <NavLink to="/" end>
            Upload
          </NavLink>
          <NavLink to={analysis ? `/analysis/${analysis.analysisId}` : '/'}>Overview</NavLink>
          <NavLink to={analysis ? `/analysis/${analysis.analysisId}/columns` : '/'}>Columns</NavLink>
          <NavLink to={analysis ? `/analysis/${analysis.analysisId}/recommendations` : '/'}>Recommendations</NavLink>
          <NavLink to={analysis ? `/analysis/${analysis.analysisId}/report` : '/'}>Report</NavLink>
          <NavLink to="/about">About</NavLink>
        </nav>
      </header>

        <main className="content">
          <Routes>
            <Route
              path="/"
              element={
                <LandingPage
                  analysis={analysis}
                  readinessLabel={readinessLabel}
                  selectedFile={selectedFile}
                  isUploading={isUploading}
                  error={error}
                  onFileChange={setSelectedFile}
                  onUpload={handleUpload}
                  onClear={() => {
                    setSelectedFile(null)
                    setError(null)
                  }}
                />
              }
            />
            <Route
              path="/analysis/:analysisId"
              element={<OverviewPage analysis={analysis} readinessLabel={readinessLabel} />}
            />
            <Route path="/analysis/:analysisId/columns" element={<ColumnsPage analysis={analysis} />} />
            <Route path="/analysis/:analysisId/recommendations" element={<RecommendationsPage analysis={analysis} />} />
            <Route path="/analysis/:analysisId/report" element={<ReportPage analysis={analysis} />} />
            <Route path="/about" element={<AboutPage />} />
            <Route path="*" element={<NotFoundPage />} />
          </Routes>
        </main>
      </div>
  )
}

function LandingPage({
  analysis,
  readinessLabel,
  selectedFile,
  isUploading,
  error,
  onFileChange,
  onUpload,
  onClear,
}: {
  analysis: AnalysisSummary | null
  readinessLabel: string
  selectedFile: File | null
  isUploading: boolean
  error: string | null
  onFileChange: (file: File | null) => void
  onUpload: () => void
  onClear: () => void
}) {
  return (
    <section className="hero-panel">
      <div className="hero-copy">
        <p className="eyebrow">Upload a CSV or XLSX file</p>
        <h2>Get a trustworthy diagnosis before you train your model.</h2>
        <p>Dataset Doctor checks missing values, duplicates, outliers, imbalance, possible leakage and more.</p>

        <div className="upload-card">
          <label className="upload-zone" htmlFor="dataset-upload">
            <input
              id="dataset-upload"
              type="file"
              accept=".csv,.xlsx,.xls"
              onChange={(event) => {
                const file = event.target.files?.[0] ?? null
                onFileChange(file)
              }}
            />
            <span className="upload-title">Choose a dataset file</span>
            <span className="upload-caption">CSV or Excel files are supported.</span>
          </label>

          <div className="upload-actions">
            <button className="primary-btn" type="button" onClick={onUpload} disabled={isUploading}>
              {isUploading ? 'Analyzing…' : 'Analyze dataset'}
            </button>
            <button className="secondary-btn" type="button" onClick={onClear} disabled={!selectedFile}>
              Clear
            </button>
          </div>

          {selectedFile ? (
            <p className="upload-status">Selected file: {selectedFile.name}</p>
          ) : (
            <p className="upload-status">No file selected yet.</p>
          )}

          {error ? <p className="upload-error">{error}</p> : null}
        </div>

        <div className="hero-actions">
          <Link className="primary-btn" to={analysis ? `/analysis/${analysis.analysisId}` : '/'}>
            Open latest analysis
          </Link>
          <Link className="secondary-btn" to="/about">
            Learn the methodology
          </Link>
        </div>

        <ul className="checklist">
          <li>Supports CSV and Excel uploads</li>
          <li>Shows a health score and top issues in one view</li>
          <li>Provides recommendations and report export</li>
        </ul>
      </div>

      <div className="summary-card">
        <p className="eyebrow">Latest analysis</p>
        {analysis ? (
          <>
            <h3>{analysis.datasetName}</h3>
            <div className="score-circle">{analysis.healthScore}</div>
            <p className="score-label">{readinessLabel}</p>
            <div className="metrics-grid">
              <div>
                <strong>{analysis.rowCount.toLocaleString()}</strong>
                <span>Rows</span>
              </div>
              <div>
                <strong>{analysis.columnCount}</strong>
                <span>Columns</span>
              </div>
              <div>
                <strong>{analysis.topIssues.length}</strong>
                <span>Top issues</span>
              </div>
            </div>
          </>
        ) : (
          <>
            <h3>No analysis yet</h3>
            <p className="muted">Upload a dataset to see its health score, issues and recommendations.</p>
          </>
        )}
      </div>
    </section>
  )
}

function OverviewPage({ analysis, readinessLabel }: { analysis: AnalysisSummary | null; readinessLabel: string }) {
  if (!analysis) {
    return (
      <section className="panel centered">
        <h2>No analysis loaded</h2>
        <p>Upload a dataset to create a new analysis.</p>
        <Link className="primary-btn" to="/">
          Go to upload
        </Link>
      </section>
    )
  }

  return (
    <section className="page-grid">
      <div className="panel panel-large">
        <div className="panel-header">
          <div>
            <p className="eyebrow">Analysis overview</p>
            <h2>{analysis.datasetName}</h2>
          </div>
          <span className="pill">{analysis.status}</span>
        </div>

        <div className="score-row">
          <div className="score-card">
            <div className="score-circle large">{analysis.healthScore}</div>
            <div>
              <h3>{readinessLabel}</h3>
              <p>Balanced across completeness, consistency and possible leakage.</p>
            </div>
          </div>
          <div className="kpis">
            <div className="kpi-card">
              <strong>{analysis.rowCount.toLocaleString()}</strong>
              <span>Rows</span>
            </div>
            <div className="kpi-card">
              <strong>{analysis.columnCount}</strong>
              <span>Columns</span>
            </div>
            <div className="kpi-card">
              <strong>{analysis.targetColumn ?? 'n/a'}</strong>
              <span>Target</span>
            </div>
          </div>
        </div>

        <div className="panel-grid">
          {analysis.factors.map((factor) => (
            <div className="detail-card" key={factor.name}>
              <div className="detail-title-row">
                <h3>{factor.name}</h3>
                <span className={`pill ${severityTone[factor.severity]}`}>{factor.severity}</span>
              </div>
              <p className="score-value">{factor.score}/100</p>
              <p>{factor.explanation}</p>
            </div>
          ))}
        </div>
      </div>

      <aside className="panel">
        <div className="panel-header">
          <div>
            <p className="eyebrow">Top issues</p>
            <h2>Immediate findings</h2>
          </div>
        </div>
        <div className="stack-list">
          {analysis.topIssues.map((issue) => (
            <article className="issue-card" key={issue.id}>
              <div className="detail-title-row">
                <h3>{issue.title}</h3>
                <span className={`pill ${severityTone[issue.severity]}`}>{issue.severity}</span>
              </div>
              <p>{issue.summary}</p>
              <p className="muted">{issue.evidence}</p>
            </article>
          ))}
        </div>
      </aside>
    </section>
  )
}

function ColumnsPage({ analysis }: { analysis: AnalysisSummary | null }) {
  if (!analysis) {
    return (
      <section className="panel centered">
        <h2>No analysis loaded</h2>
        <p>Upload a dataset to inspect its column diagnostics.</p>
      </section>
    )
  }

  return (
    <section className="panel">
      <div className="panel-header">
        <div>
          <p className="eyebrow">Column diagnostics</p>
          <h2>Inspect per-column quality signals</h2>
        </div>
      </div>

      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Column</th>
              <th>Type</th>
              <th>Missing %</th>
              <th>Unique</th>
              <th>Outliers</th>
              <th>Leakage risk</th>
              <th>Severity</th>
            </tr>
          </thead>
          <tbody>
            {analysis.columns.map((column: ColumnDiagnostic) => (
              <tr key={column.name}>
                <td>{column.name}</td>
                <td>{column.inferredType}</td>
                <td>{column.missingPercent.toFixed(1)}%</td>
                <td>{column.uniqueCount}</td>
                <td>{column.outlierCount}</td>
                <td>{column.leakageRisk.toFixed(2)}</td>
                <td>
                  <span className={`pill ${severityTone[column.severity]}`}>{column.severity}</span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  )
}

function RecommendationsPage({ analysis }: { analysis: AnalysisSummary | null }) {
  if (!analysis) {
    return (
      <section className="panel centered">
        <h2>No analysis loaded</h2>
        <p>Upload a dataset to view prioritized recommendations.</p>
      </section>
    )
  }

  return (
    <section className="panel">
      <div className="panel-header">
        <div>
          <p className="eyebrow">Recommendations</p>
          <h2>Prioritized preprocessing actions</h2>
        </div>
      </div>
      <div className="stack-list">
        {analysis.recommendations.map((recommendation: Recommendation) => (
          <article className="issue-card" key={recommendation.id}>
            <div className="detail-title-row">
              <h3>{recommendation.title}</h3>
              <span className="pill">{recommendation.priority}</span>
            </div>
            <p>{recommendation.rationale}</p>
            <p className="muted">Action: {recommendation.action}</p>
            <p className="muted">Affected columns: {recommendation.affectedColumns.join(', ')}</p>
          </article>
        ))}
      </div>
    </section>
  )
}

function ReportPage({ analysis }: { analysis: AnalysisSummary | null }) {
  if (!analysis) {
    return (
      <section className="panel centered">
        <h2>No analysis loaded</h2>
        <p>Upload a dataset to generate a report.</p>
      </section>
    )
  }

  return (
    <section className="panel">
      <div className="panel-header">
        <div>
          <p className="eyebrow">Report preview</p>
          <h2>Download-ready diagnosis summary</h2>
        </div>
        <button className="primary-btn" type="button" onClick={() => window.print()}>
          Generate report
        </button>
      </div>
      <div className="report-card">
        <h3>Summary</h3>
        <p>{analysis.datasetName} scored {analysis.healthScore}/100 and was labeled {analysis.scoreLabel}.</p>
        <h3>Key findings</h3>
        <ul>
          {analysis.topIssues.map((issue) => (
            <li key={issue.id}>{issue.title}</li>
          ))}
        </ul>
        <h3>Recommended next steps</h3>
        <ul>
          {analysis.recommendations.map((recommendation) => (
            <li key={recommendation.id}>{recommendation.title}</li>
          ))}
        </ul>
      </div>
    </section>
  )
}

function AboutPage() {
  return (
    <section className="panel">
      <div className="panel-header">
        <div>
          <p className="eyebrow">Methodology</p>
          <h2>How Dataset Doctor evaluates data quality</h2>
        </div>
      </div>
      <div className="report-card">
        <p>
          The analysis blends completeness, consistency, leakage risk and target distribution into a single diagnostic score.
          It is designed to help students and practitioners understand whether a dataset is ready for training.
        </p>
        <p>
          The interface keeps the evidence visible, shows clear recommendations and preserves context when users move between overview, columns and reports.
        </p>
      </div>
    </section>
  )
}

function NotFoundPage() {
  return (
    <section className="panel centered">
      <h2>Page not found</h2>
      <p>Return to the upload flow or open the latest analysis.</p>
      <Link className="primary-btn" to="/">
        Go back home
      </Link>
    </section>
  )
}

export default App
