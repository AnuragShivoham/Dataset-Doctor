export type Severity = 'Critical' | 'Warning' | 'Moderate' | 'Healthy'

export interface HealthFactor {
  name: string
  score: number
  weight: number
  severity: Severity
  explanation: string
}

export interface QualityIssue {
  id: string
  type: string
  severity: Severity
  title: string
  summary: string
  affectedRows: number
  affectedColumns: string[]
  evidence: string
  recommendationId: string
}

export interface ColumnDiagnostic {
  name: string
  inferredType: string
  missingPercent: number
  uniqueCount: number
  outlierCount: number
  imbalanceMetric: number
  leakageRisk: number
  severity: Severity
}

export interface Recommendation {
  id: string
  priority: string
  issueType: string
  title: string
  rationale: string
  action: string
  affectedColumns: string[]
  caution: string
}

export interface AnalysisSummary {
  analysisId: string
  status: 'ready' | 'processing'
  datasetName: string
  rowCount: number
  columnCount: number
  targetColumn?: string
  healthScore: number
  scoreLabel: string
  factors: HealthFactor[]
  topIssues: QualityIssue[]
  columns: ColumnDiagnostic[]
  recommendations: Recommendation[]
}
