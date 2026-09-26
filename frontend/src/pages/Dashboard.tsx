import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { api } from '../lib/api'
import { formatCompetence, formatCurrency, formatNumber, formatPercent } from '../lib/format'
import { MetricCard } from '../components/MetricCard'
import { EmptyState } from '../components/EmptyState'
import { MethodologyPanel } from '../components/MethodologyPanel'
import {
  MunicipalityChart,
  OccupationChart,
  TrendChart,
  UfChart,
} from '../components/Charts'
import { ProvenanceCard } from '../components/ProvenanceCard'
import { ReferenceContext } from '../components/ReferenceContext'
import { PipelineVisual } from '../components/PipelineVisual'
import { TerritorialComparison } from '../components/TerritorialComparison'

export function Dashboard() {
  const [methodologyOpen, setMethodologyOpen] = useState(false)

  const readiness = useQuery({ queryKey: ['readiness'], queryFn: api.readiness })
  const releases = useQuery({
    queryKey: ['releases'],
    queryFn: api.releases,
    retry: false,
  })
  const officialReference = useQuery({
    queryKey: ['official-reference-202607'],
    queryFn: api.officialReferenceJuly2026,
    retry: false,
  })
  const overview = useQuery({
    queryKey: ['overview'],
    queryFn: api.overview,
    retry: false,
    enabled: readiness.data?.data_loaded === true,
  })
  const byUf = useQuery({
    queryKey: ['by-uf'],
    queryFn: api.byUf,
    retry: false,
    enabled: overview.isSuccess,
  })
  const byOccupation = useQuery({
    queryKey: ['by-occupation'],
    queryFn: api.byOccupation,
    retry: false,
    enabled: overview.isSuccess,
  })
  const territorialComparison = useQuery({
    queryKey: ['territorial-comparison'],
    queryFn: api.territorialComparison,
    retry: false,
    enabled: overview.isSuccess,
  })
  const byMunicipality = useQuery({
    queryKey: ['by-municipality'],
    queryFn: api.byMunicipality,
    retry: false,
    enabled: overview.isSuccess,
  })
  const trend = useQuery({
    queryKey: ['trend'],
    queryFn: api.trend,
    retry: false,
    enabled: overview.isSuccess,
  })
  const quality = useQuery({
    queryKey: ['quality'],
    queryFn: api.quality,
    retry: false,
    enabled: readiness.data?.data_loaded === true,
  })
  const provenance = useQuery({
    queryKey: ['provenance'],
    queryFn: api.provenance,
    retry: false,
    enabled: readiness.data?.data_loaded === true,
  })

  const isLoading = readiness.isLoading || (readiness.data?.data_loaded && overview.isLoading)
  const noData = readiness.isSuccess && readiness.data.data_loaded === false
  const hasTechData = overview.isSuccess
  const publishedCompetencies = releases.data?.published_competencies ?? []
  const firstPublished = publishedCompetencies[0]
  const lastPublished = publishedCompetencies[publishedCompetencies.length - 1]
  const coverageLabel = publishedCompetencies.length
    ? (
        publishedCompetencies.length === 1
          ? formatCompetence(lastPublished)
          : `${formatCompetence(firstPublished)} a ${formatCompetence(lastPublished)}`
      )
    : 'Aguardando publicação'
  const latestCompetenceLabel = overview.data
    ? formatCompetence(overview.data.competence)
    : lastPublished
      ? formatCompetence(lastPublished)
      : null

  return (
    <main>
      <header className="topbar">
        <a className="brand" href="#top" aria-label="Mercado Tech Brasil">
          <span className="brand__mark">MT</span>
          <span>
            <strong>Mercado Tech Brasil</strong>
            <small>Dados oficiais. Metodologia aberta.</small>
          </span>
        </a>
        <nav className="topbar__actions" aria-label="Navegação principal">
          <a href="#contexto">Contexto</a>
          <a href="#analise">Análise</a>
          <a href="#qualidade">Qualidade</a>
          <button className="button button--secondary" onClick={() => setMethodologyOpen(true)}>
            Metodologia
          </button>
        </nav>
      </header>

      <section className="hero hero--visual" id="top">
        <div className="hero__copy">
          <div className="hero__badges">
            <span className="status-badge status-badge--dark">Open data</span>
            <span className="status-badge">Brasil</span>
            <span className="status-badge">CBO v2</span>
            {latestCompetenceLabel ? (
              <span className="status-badge status-badge--accent">
                Atualizado {latestCompetenceLabel}
              </span>
            ) : null}
          </div>
          <h1>O mercado formal de tecnologia, explicado com dados verificáveis.</h1>
          <p>
            Uma aplicação de dados que transforma microdados públicos do Novo CAGED em indicadores
            auditáveis de contratação, desligamento e remuneração em ocupações de tecnologia.
          </p>
          <div className="hero__cta-row">
            <a className="button" href="#contexto">Explorar dados</a>
            <button className="button button--ghost" onClick={() => setMethodologyOpen(true)}>
              Ver metodologia
            </button>
          </div>
        </div>

        <div className="hero__visual-card" aria-label="Fluxo de dados do produto">
          <div className="hero__visual-head">
            <span>Pipeline auditável</span>
            <span className={hasTechData ? 'live-dot live-dot--on' : 'live-dot'} />
          </div>
          <div className="hero__pipeline">
            <div><span>01</span><strong>Fonte oficial</strong><small>MTE / CBO</small></div>
            <i>→</i>
            <div><span>02</span><strong>Bronze</strong><small>SHA-256</small></div>
            <i>→</i>
            <div><span>03</span><strong>Silver</strong><small>qualidade</small></div>
            <i>→</i>
            <div><span>04</span><strong>Gold</strong><small>indicadores</small></div>
          </div>
          <div className="hero__meta hero__meta--card">
            <div><span>Fonte primária</span><strong>Novo CAGED / MTE</strong></div>
            <div><span>Competência tech</span><strong>{overview.data ? formatCompetence(overview.data.competence) : 'Aguardando microdados'}</strong></div>
            <div><span>Cobertura publicada</span><strong>{coverageLabel}</strong></div>
            <div>
              <span>Serving</span>
              <strong>
                FastAPI + {readiness.data?.backend === 'postgres' ? 'PostgreSQL' : 'Gold publicado'}
              </strong>
            </div>
          </div>
        </div>
      </section>

      <PipelineVisual hasTechData={hasTechData} />

      {officialReference.data ? (
        <ReferenceContext data={officialReference.data} />
      ) : null}

      {isLoading ? (
        <section className="loading-grid" aria-label="Carregando indicadores">
          {Array.from({ length: 4 }).map((_, index) => <div className="skeleton" key={index} />)}
        </section>
      ) : null}

      {noData ? (
        <EmptyState
          title="O dashboard tech está pronto para receber o primeiro mês oficial."
          message="O contexto oficial do mercado formal já está visível acima. Os indicadores específicos de tecnologia só serão liberados quando o CAGEDMOV passar pelo pipeline, reconciliação e gate de publicação."
        />
      ) : null}

      {overview.data ? (
        <>
          <section className="section-heading" id="analise">
            <div>
              <p className="eyebrow">Recorte de tecnologia</p>
              <h2>Indicadores do mercado tech formal</h2>
            </div>
            <span className="section-heading__meta">
              {publishedCompetencies.length > 1
                ? `${publishedCompetencies.length} competências · ${coverageLabel} · CBO v2`
                : `${formatCompetence(overview.data.competence)} · CBO v2`}
            </span>
          </section>

          <section className="metric-grid" aria-label="Indicadores principais">
            <MetricCard label="Admissões" value={formatNumber(overview.data.admissions)} detail="movimentações de entrada" />
            <MetricCard label="Desligamentos" value={formatNumber(overview.data.dismissals)} detail="movimentações de saída" />
            <MetricCard
              label="Saldo"
              value={`${overview.data.balance >= 0 ? '+' : ''}${formatNumber(overview.data.balance)}`}
              detail="admissões menos desligamentos"
              tone={overview.data.balance >= 0 ? 'positive' : 'negative'}
            />
            <MetricCard
              label={
                overview.data.salary_median_admissions_real != null
                  ? 'Salário mediano real'
                  : 'Salário mediano de admissão'
              }
              value={formatCurrency(
                overview.data.salary_median_admissions_real
                  ?? overview.data.salary_median_admissions,
              )}
              detail={
                overview.data.salary_real_base_competence
                  ? `valores de ${formatCompetence(
                      overview.data.salary_real_base_competence,
                    )}, IPCA/IBGE`
                  : 'metodologia salarial MTE'
              }
            />
          </section>

          {territorialComparison.data ? (
            <TerritorialComparison data={territorialComparison.data} />
          ) : null}

          <section className="analysis-grid">
            <article className="panel panel--wide">
              <div className="panel__heading">
                <div><p className="eyebrow">Distribuição territorial</p><h2>Admissões tech por UF</h2></div>
                <span>Top 10</span>
              </div>
              {byUf.data ? <UfChart items={byUf.data.items} /> : <div className="chart-placeholder" />}
            </article>

            <article className="panel">
              <div className="panel__heading">
                <div><p className="eyebrow">Ocupações</p><h2>Saldo por CBO</h2></div>
              </div>
              {byOccupation.data ? <OccupationChart items={byOccupation.data.items} /> : <div className="chart-placeholder" />}
            </article>
          </section>

          {(byMunicipality.data || (trend.data?.items.length ?? 0) > 1) ? (
            <section className="analysis-grid">
              {byMunicipality.data ? (
                <article className="panel panel--wide">
                  <div className="panel__heading">
                    <div>
                      <p className="eyebrow">Municípios</p>
                      <h2>Admissões tech por município</h2>
                    </div>
                    <span>Top 12</span>
                  </div>
                  <MunicipalityChart items={byMunicipality.data.items} />
                </article>
              ) : null}

              {(trend.data?.items.length ?? 0) > 1 ? (
                <article className="panel">
                  <div className="panel__heading">
                    <div>
                      <p className="eyebrow">Série histórica</p>
                      <h2>Evolução mensal</h2>
                    </div>
                    <span>{trend.data?.items.length} competências</span>
                  </div>
                  <TrendChart items={trend.data?.items ?? []} />
                </article>
              ) : null}
            </section>
          ) : null}

          <section className="quality-section" id="qualidade">
            <div>
              <p className="eyebrow">Qualidade dos dados</p>
              <h2>O número só entra no dashboard depois de passar pelas validações.</h2>
              <p>
                O pipeline mantém registros rejeitados auditáveis e expõe a taxa de validade da competência.
                Nenhum dado problemático é descartado silenciosamente.
              </p>
            </div>
            <article className="quality-card">
              <span>Taxa de registros válidos</span>
              <strong>{quality.data ? formatPercent(quality.data.valid_rate) : 'N/D'}</strong>
              <div className="quality-card__rows">
                <span>Linhas lidas</span><b>{quality.data ? formatNumber(quality.data.rows_read) : 'N/D'}</b>
                <span>Rejeitadas</span><b>{quality.data ? formatNumber(quality.data.rows_rejected) : 'N/D'}</b>
                <span>Recorte tech</span><b>{quality.data ? formatNumber(quality.data.rows_tech) : 'N/D'}</b>
              </div>
            </article>
          </section>
        </>
      ) : null}

      {readiness.isError ? (
        <section className="error-state">
          <p className="eyebrow">API indisponível</p>
          <h2>Não foi possível conectar ao backend.</h2>
          <p>Verifique sua conexão e recarregue a página. Os dados publicados permanecem preservados no pipeline.</p>
        </section>
      ) : null}

      {provenance.data ? (
        <section className="provenance-section" aria-label="Proveniência dos dados">
          <ProvenanceCard data={provenance.data} />
        </section>
      ) : null}

      <footer className="footer">
        <div className="footer__identity">
          <strong>Mercado Tech Brasil</strong>
          <span>Fonte principal: Novo CAGED / Ministério do Trabalho e Emprego</span>
        </div>
        <nav className="footer__links" aria-label="Links técnicos">
          <a href="/docs" target="_blank" rel="noreferrer">API / OpenAPI</a>
          <a
            href="https://github.com/peedrovinicius/mercado-tech-brasil"
            target="_blank"
            rel="noreferrer"
          >
            Código-fonte
          </a>
          <button type="button" onClick={() => setMethodologyOpen(true)}>Metodologia</button>
        </nav>
      </footer>

      <MethodologyPanel
        open={methodologyOpen}
        onClose={() => setMethodologyOpen(false)}
        competence={overview.data ? formatCompetence(overview.data.competence) : undefined}
      />
    </main>
  )
}
