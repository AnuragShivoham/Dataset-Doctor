import type { AnalysisSummary } from './types'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8002'

export async function uploadDataset(file: File): Promise<AnalysisSummary> {
  const formData = new FormData()
  formData.append('file', file)

  const response = await fetch(`${API_BASE_URL}/api/v1/analyses`, {
    method: 'POST',
    body: formData,
  })

  if (!response.ok) {
    const errorPayload = await response.json().catch(() => ({ message: 'Upload failed.' }))
    throw new Error(errorPayload.message ?? 'Upload failed.')
  }

  return response.json() as Promise<AnalysisSummary>
}

export async function getAnalysis(analysisId: string): Promise<AnalysisSummary> {
  const response = await fetch(`${API_BASE_URL}/api/v1/analyses/${analysisId}`)

  if (!response.ok) {
    const errorPayload = await response.json().catch(() => ({ message: 'Failed to load analysis.' }))
    throw new Error(errorPayload.detail ?? errorPayload.message ?? 'Failed to load analysis.')
  }

  return response.json() as Promise<AnalysisSummary>
}
