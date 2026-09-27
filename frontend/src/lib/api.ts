const API_BASE = import.meta.env.VITE_API_BASE_URL ?? '/api/v1'

export type SalaryFields = {
  salary_mean_admissions: number | null
  salary_median_admissions: number | null
  salary_mean_admissions_real?: number | null
  salary_median_admissions_real?: number | null
}

export type Overview = SalaryFields & {
  competence: string
  scope: string
  admissions: number
  dismissals: number
  balance: number
  salary_real_base_competence?: string | null
  records_tech: number
  source: string
  status: string
}

export type UfItem = SalaryFields & {
  uf: string
  admissions: number
  dismissals: number
  balance: number
}

export type OccupationItem = SalaryFields & {
  cbo_familia: string
  cbo_codigo: string
  admissions: number
  dismissals: number
  balance: number
}

export type OccupationFamilyMonthly = {
  competence: string
  admissions: number
  dismissals: number
  balance: number
}

export type OccupationFamilyTrendItem = {
  cbo_familia: string
  cbo_familia_nome: string
  admissions: number
  dismissals: number
  balance: number
  share_of_tech_admissions: number
  monthly: OccupationFamilyMonthly[]
}

export type OccupationFamilyTrend = {
  source: string
  scope: string
  dimension: 'familia_cbo'
  published_from: string
  published_to: string
  published_months: number
  families: OccupationFamilyTrendItem[]
}

export type StockFlowFamilyItem = {
  cbo_familia: string
  cbo_familia_nome: string
  active_stock: number
  share_of_tech_stock: number
  admissions: number
  dismissals: number
  balance: number
  share_of_tech_admissions: number
  admissions_per_100_prior_stock: number
  dismissals_per_100_prior_stock: number
  balance_per_100_prior_stock: number
  composition_gap_pp: number
}

export type StockFlowContext = {
  stock_source: string
  flow_source: string
  scope: string
  interpretation: 'descriptive_scale_context'
  rais_year: number
  stock_reference_date: string
  caged_year: number
  caged_from: string
  caged_to: string
  published_months: number
  totals: {
    active_stock: number
    admissions: number
    dismissals: number
    balance: number
    admissions_per_100_prior_stock: number
    dismissals_per_100_prior_stock: number
    balance_per_100_prior_stock: number
  }
  families: StockFlowFamilyItem[]
  methodological_warning: string
}

export type MunicipalityItem = SalaryFields & {
  municipio_codigo_caged: string
  municipio_codigo_ibge?: string | null
  municipio_nome?: string | null
  uf?: string | null
  admissions: number
  dismissals: number
  balance: number
  population_estimate?: number | null
  population_reference_year?: number | null
  admissions_per_100k?: number | null
  dismissals_per_100k?: number | null
  balance_per_100k?: number | null
}

export type MunicipalityResponse = {
  competence: string
  source: string
  code_system?: string
  salary_real_base_competence?: string | null
  population_source?: string | null
  population_reference_year?: number | null
  population_reference_date?: string | null
  ranking_metric: 'admissions' | 'admissions_per_100k'
  normalization_available: boolean
  items: MunicipalityItem[]
}

export type TerritorialComparisonItem = {
  key: 'BR' | 'NE' | 'CE'
  label: string
  admissions: number
  dismissals: number
  balance: number
  share_national_admissions: number
}

export type TerritorialComparison = {
  competence: string
  source: string
  scope: string
  items: TerritorialComparisonItem[]
  ceara_share_northeast_admissions: number
}

export type TrendItem = SalaryFields & {
  competence: string
  admissions: number
  dismissals: number
  balance: number
  salary_real_base_competence?: string | null
}

export type TemporalPeriod = {
  key: string
  label: string
  year: number
  quarter: number
  competencies: string[]
  start_competence: string
  end_competence: string
  published_months: number
  complete: boolean
  admissions: number
  dismissals: number
  balance: number
  average_monthly_balance: number
}

export type TemporalSummary = {
  source: string
  scope: string
  published_from: string
  published_to: string
  published_months: number
  cumulative: {
    admissions: number
    dismissals: number
    balance: number
  }
  periods: TemporalPeriod[]
}

export type ReleaseState = {
  project: string
  version: string
  environment: string
  data_backend: string
  monthly: {
    published_count: number
    first_competence: string | null
    latest_competence: string | null
    competencies: string[]
    policy_mode: string
    policy_max_competence: string | null
  }
  rais: {
    latest_published_year: number | null
  }
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

export type ReleaseItem = {
  competence: string
  automatic_checks_passed: boolean
  manual_approval_valid: boolean
  publishable: boolean
  source_sha256?: string | null
  generated_at_utc?: string | null
}

export type Releases = {
  total: number
  published_count: number
  published_competencies: string[]
  latest_published_competence?: string | null
  items: ReleaseItem[]
}

export type Provenance = {
  source: string
  competence: string
  original_name: string
  size_bytes: number
  sha256: string
  ingested_at_utc: string
  manifest_path: string
  transport?: string
  source_url?: string
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

export type RaisReleaseItem = {
  year: number
  automatic_checks_passed: boolean
  manual_approval_valid: boolean
  publishable: boolean
  release_sha256?: string | null
  generated_at_utc?: string | null
}

export type RaisReleases = {
  latest_published_year: number | null
  published_years: number[]
  items: RaisReleaseItem[]
}

export type RaisOverview = {
  year: number
  reference_date: string
  source: string
  scope: string
  active_stock_tech: number
  active_stock_national_reference: number
  share_tech_of_national_active: number
  cbo_scope_version: number
  cbo_families: string[]
  uf_count: number
  market_rows: number
  status: string
  publication_ready: boolean
}

export type RaisUfItem = {
  uf: string
  active_stock: number
  share_of_tech_stock: number
}

export type RaisUfResponse = {
  year: number
  reference_date: string
  source: string
  scope: string
  items: RaisUfItem[]
  publication_ready: boolean
}

export type RaisCboFamilyItem = {
  cbo_familia: string
  cbo_familia_nome: string
  active_stock: number
  share_of_tech_stock: number
}

export type RaisCboFamilyResponse = {
  year: number
  reference_date: string
  source: string
  scope: string
  items: RaisCboFamilyItem[]
  publication_ready: boolean
}

export type RaisMunicipalityItem = {
  municipio_codigo_rais: string
  municipio_codigo_ibge: string | null
  municipio_nome: string
  uf: string
  active_stock: number
  share_of_tech_stock: number
}

export type RaisMunicipalityResponse = {
  year: number
  reference_date: string
  source: string
  municipality_reference: string
  scope: string
  code_system: string
  municipality_count: number
  active_stock_tech: number
  items: RaisMunicipalityItem[]
  publication_ready: boolean
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
  byUf: () => get<{ competence: string; source: string; items: UfItem[] }>(
    '/analytics/by-uf',
  ),
  byOccupation: () =>
    get<{ competence: string; source: string; items: OccupationItem[] }>(
      '/analytics/by-occupation?limit=10',
    ),
  occupationFamilyTrend: () =>
    get<OccupationFamilyTrend>('/analytics/occupation-family-trend'),
  stockFlowContext: () =>
    get<StockFlowContext>('/analytics/stock-flow-context'),
  byMunicipality: () =>
    get<MunicipalityResponse>('/analytics/by-municipality?limit=15'),
  byMunicipalityNormalized: () =>
    get<MunicipalityResponse>(
      '/analytics/by-municipality?limit=15&metric=admissions_per_100k',
    ),
  territorialComparison: () =>
    get<TerritorialComparison>('/analytics/territorial-comparison'),
  trend: () =>
    get<{ source: string; scope: string; items: TrendItem[] }>(
      '/analytics/trend',
    ),
  temporalSummary: () =>
    get<TemporalSummary>('/analytics/temporal-summary'),
  readiness: () => get<Readiness>('/system/readiness'),
  releaseState: () => get<ReleaseState>('/system/release'),
  coverage: () => get<Coverage>('/metadata/coverage'),
  releases: () => get<Releases>('/metadata/releases'),
  raisReleases: () => get<RaisReleases>('/rais/releases'),
  raisOverview: () => get<RaisOverview>('/rais/overview'),
  raisByUf: () => get<RaisUfResponse>('/rais/by-uf?limit=10'),
  raisByCboFamily: () =>
    get<RaisCboFamilyResponse>('/rais/by-cbo-family?limit=5'),
  raisByMunicipality: () =>
    get<RaisMunicipalityResponse>('/rais/by-municipality?limit=10'),
  officialReferenceJuly2026: () =>
    get<OfficialReference>('/metadata/official-reference/202607'),
  quality: () => get<QualityReport>('/quality/latest'),
  provenance: () => get<Provenance>('/provenance/latest'),
}
