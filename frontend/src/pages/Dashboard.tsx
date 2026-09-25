import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { api } from '../lib/api'
import { formatCompetence, formatCurrency, formatNumber, formatPercent } from '../lib/format'
import { MetricCard } from '../components/MetricCard'
import { EmptyState } from '../components/EmptyState'
import { MethodologyPanel } from '../components/MethodologyPanel'
import { OccupationChart, UfChart } from '../components/Charts'
import { ProvenanceCard } from '../components/ProvenanceCard'

export function Dashboard() {
  const [methodologyOpen, setMethodologyOpen] = useState(false)

  const readiness = useQuery({ queryKey: ['readiness'], queryFn: api.readiness })
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
        <nav className="topbar__actions">
          <a href="#analise">Análise</a>
          <a href="#qualidade">Qualidade</a>
          <button className="button button--secondary" onClick={() => setMethodologyOpen(true)}>
            Metodologia
          </button>
        </nav>
      </header>

      <section className="hero" id="top">
        <div className="hero__copy">
          <p className="eyebrow">Open data · Brasil</p>
          <h1>O mercado formal de tecnologia, explicado com dados verificáveis.</h1>
          <p>
            Uma aplicação de dados que transforma microdados públicos do Novo CAGED em indicadores
            auditáveis de contratação, desligamento e remuneração em ocupações de tecnologia.
          </p>
        </div>
        <div className="hero__meta">
          <div><span>Fonte primária</span><strong>Novo CAGED / MTE</strong></div>
          <div><span>Atualização</span><strong>{overview.data ? formatCompetence(overview.data.competence) : 'Aguardando pipeline'}</strong></div>
          <div><span>Rastreabilidade</span><strong>Bronze → Silver → Gold</strong></div>
        </div>
      </section>

      {isLoading ? (
        <section className="loading-grid" aria-label="Carregando indicadores">
          {Array.from({ length: 4 }).map((_, index) => <div className="skeleton" key={index} />)}
        </section>
      ) : null}

      {noData ? (
        <EmptyState
          title="A interface está pronta; os dados ainda não foram publicados."
          message="O primeiro conjunto oficial precisa passar pelo pipeline e pelos gates de qualidade antes de aparecer aqui."
        />
      ) : null}

      {overview.data ? (
        <>
          <section className="metric-grid" aria-label="Indicadores principais">
            <MetricCard label="Admissões" value={formatNumber(overview.data.admissions)} detail="movimentações de entrada" />
            <MetricCard label="Desligamentos" value={formatNumber(overview.data.dismissals)} detail="movimentações de saída" />
            <MetricCard
              label="Saldo"
              value={`${overview.data.balance >= 0 ? '+' : ''}${formatNumber(overview.data.balance)}`}
              detail="admissões − desligamentos"
              tone={overview.data.balance >= 0 ? 'positive' : 'negative'}
            />
            <MetricCard
              label="Salário mediano de admissão"
              value={formatCurrency(overview.data.salary_median_admissions)}
              detail="somente registros válidos"
            />
          </section>

          <section className="analysis-grid" id="analise">
            <article className="panel panel--wide">
              <div className="panel__heading">
                <div><p className="eyebrow">Distribuição territorial</p><h2>Admissões por UF</h2></div>
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

          <section className="quality-section" id="qualidade">
            <div>
              <p className="eyebrow">Data quality</p>
              <h2>O número só entra no dashboard depois de passar pelas validações.</h2>
              <p>
                O pipeline mantém registros rejeitados auditáveis e expõe a taxa de validade da competência.
                Nenhum dado problemático é descartado silenciosamente.
              </p>
            </div>
            <article className="quality-card">
              <span>Taxa de registros válidos</span>
              <strong>{quality.data ? formatPercent(quality.data.valid_rate) : '—'}</strong>
              <div className="quality-card__rows">
                <span>Linhas lidas</span><b>{quality.data ? formatNumber(quality.data.rows_read) : '—'}</b>
                <span>Rejeitadas</span><b>{quality.data ? formatNumber(quality.data.rows_rejected) : '—'}</b>
                <span>Recorte tech</span><b>{quality.data ? formatNumber(quality.data.rows_tech) : '—'}</b>
              </div>
            </article>
          </section>
        </>
      ) : null}

      {readiness.isError ? (
        <section className="error-state">
          <p className="eyebrow">API indisponível</p>
          <h2>Não foi possível conectar ao backend.</h2>
          <p>Inicie a API FastAPI em <code>localhost:8000</code> e recarregue a página.</p>
        </section>
      ) : null}

      {provenance.data ? (
        <section className="provenance-section" aria-label="Proveniência dos dados">
          <ProvenanceCard data={provenance.data} />
        </section>
      ) : null}

      <footer className="footer">
        <span>Mercado Tech Brasil</span>
        <span>Fonte principal: Ministério do Trabalho e Emprego</span>
        <button onClick={() => setMethodologyOpen(true)}>Como os números são calculados?</button>
      </footer>

      <MethodologyPanel
        open={methodologyOpen}
        onClose={() => setMethodologyOpen(false)}
        competence={overview.data ? formatCompetence(overview.data.competence) : undefined}
      />
    </main>
  )
}
