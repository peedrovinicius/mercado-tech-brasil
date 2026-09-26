const API_BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api/v1'

export type Overview = {
  competence: string
  scope: string
  admissions: number
  dismissals: number
  balance: number
  salary_mean_admissions: number | null
  salary_median_admissions: number | null
  records_tech: number
  source: string
  status: string
}

export type UfItem = {
  uf: string
  admissions: number
  dismissals: number
  balance: number
  salary_median_admissions: number | null
}

export type OccupationItem = {
  cbo_familia: string
  cbo_codigo: string
  admissions: number
  dismissals: number
  balance: number
  salary_median_admissions: number | null
}

export type Readiness = {
  api: string
  data_loaded: boolean
  backend?: string
  note: string
}

export type Coverage = {
  status: string
  competencies: string[]
  message?: string
}

export type Provenance = {
  source: string
  competence: string
  original_name: string
  size_bytes: number
  sha256: string
  ingested_at_utc: string
  manifest_path: string
}

export type QualityReport = {
  source: string
  file_kind: string
  competence: string
  rows_read: number
  rows_valid: number
  rows_rejected: number
  rows_tech: number
  valid_rate: number
  rejection_counts: Record<string, number>
  publication_ready: boolean
  publication_gate?: string
  note?: string
}

type ReferenceMetric = {
  admissions: number
  dismissals: number
  balance: number
}

type ReferenceUfMetric = ReferenceMetric & {
  salary_mean_admission_brl: number
}

export type OfficialReference = {
  competence: string
  source: {
    owner: string
    document: string
    url: string
    published_at: string
  }
  salary_methodology: {
    minimum_wage_brl: number
    minimum_multiple: number
    maximum_multiple: number
    minimum_salary_brl: number
    maximum_salary_brl: number
    exclude_intermittent: boolean
    metric: string
  }
  national: ReferenceMetric & {
    salary_mean_admission_brl: number
  }
  non_identified: ReferenceMetric
  regions: Record<string, ReferenceMetric>
  ufs: Record<string, ReferenceUfMetric>
}

type ApiError = Error & { status?: number }

async function get<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`)
  if (!response.ok) {
    const error: ApiError = new Error(`Erro ${response.status}`)
    error.status = response.status
    try {
      const body = await response.json()
      error.message = body.detail ?? body.message ?? error.message
    } catch {
      // Mantém mensagem padrão.
    }
    throw error
  }
  return response.json() as Promise<T>
}

export const api = {
  overview: () => get<Overview>('/indicators/overview'),
  byUf: () => get<{ competence: string; source: string; items: UfItem[] }>('/analytics/by-uf'),
  byOccupation: () => get<{ competence: string; source: string; items: OccupationItem[] }>('/analytics/by-occupation?limit=10'),
  readiness: () => get<Readiness>('/system/readiness'),
  coverage: () => get<Coverage>('/metadata/coverage'),
  officialReferenceJuly2026: () => get<OfficialReference>('/metadata/official-reference/202607'),
  quality: () => get<QualityReport>('/quality/latest'),
  provenance: () => get<Provenance>('/provenance/latest'),
}
