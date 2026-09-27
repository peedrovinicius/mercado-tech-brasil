import type { StockFlowContext } from '../lib/api'
import { formatCompetence, formatNumber, formatPercent } from '../lib/format'

function formatPer100(value: number) {
  return value.toLocaleString('pt-BR', {
    minimumFractionDigits: 1,
    maximumFractionDigits: 1,
  })
}

function formatPp(value: number) {
  const formatted = Math.abs(value).toLocaleString('pt-BR', {
    minimumFractionDigits: 1,
    maximumFractionDigits: 1,
  })
  return `${value >= 0 ? '+' : '-'}${formatted} p.p.`
}

export function StockFlowContextAnalysis({
  data,
}: {
  data: StockFlowContext
}) {
  return (
    <section className="stock-flow-section">
      <div className="stock-flow-section__heading">
        <div>
          <p className="eyebrow">Estoque x movimentação</p>
          <h2>RAIS e Novo CAGED no mesmo recorte ocupacional</h2>
          <p>
            A RAIS mostra quantos vínculos tech estavam ativos em 31/12/{data.rais_year}.
            O Novo CAGED mostra admissões e desligamentos publicados entre{' '}
            {formatCompetence(data.caged_from)} e {formatCompetence(data.caged_to)}.
            A comparação abaixo serve para dimensionar os fluxos em relação ao estoque anterior,
            não para medir turnover ou crescimento direto do estoque.
          </p>
        </div>
        <span>{data.published_months} competências CAGED</span>
      </div>

      <div className="stock-flow-metrics">
        <article>
          <span>Estoque tech RAIS</span>
          <strong>{formatNumber(data.totals.active_stock)}</strong>
          <small>vínculos ativos em {data.stock_reference_date}</small>
        </article>
        <article>
          <span>Admissões acumuladas</span>
          <strong>{formatNumber(data.totals.admissions)}</strong>
          <small>{formatPer100(data.totals.admissions_per_100_prior_stock)} por 100 vínculos do estoque anterior</small>
        </article>
        <article>
          <span>Desligamentos acumulados</span>
          <strong>{formatNumber(data.totals.dismissals)}</strong>
          <small>{formatPer100(data.totals.dismissals_per_100_prior_stock)} por 100 vínculos do estoque anterior</small>
        </article>
        <article>
          <span>Saldo acumulado</span>
          <strong className={data.totals.balance >= 0 ? 'is-positive' : 'is-negative'}>
            {data.totals.balance >= 0 ? '+' : ''}{formatNumber(data.totals.balance)}
          </strong>
          <small>{formatPer100(data.totals.balance_per_100_prior_stock)} por 100 vínculos do estoque anterior</small>
        </article>
      </div>

      <div className="stock-flow-family-list">
        {data.families.map((family) => (
          <article className="stock-flow-family" key={family.cbo_familia}>
            <div className="stock-flow-family__heading">
              <div>
                <span>{family.cbo_familia}</span>
                <h3>{family.cbo_familia_nome}</h3>
              </div>
              <strong className={family.composition_gap_pp >= 0 ? 'is-positive' : 'is-negative'}>
                {formatPp(family.composition_gap_pp)}
              </strong>
            </div>

            <div className="stock-flow-family__comparison">
              <div>
                <div className="stock-flow-family__label">
                  <span>Participação no estoque</span>
                  <strong>{formatPercent(family.share_of_tech_stock)}</strong>
                </div>
                <div className="stock-flow-track">
                  <span style={{ width: `${family.share_of_tech_stock * 100}%` }} />
                </div>
              </div>
              <div>
                <div className="stock-flow-family__label">
                  <span>Participação nas admissões</span>
                  <strong>{formatPercent(family.share_of_tech_admissions)}</strong>
                </div>
                <div className="stock-flow-track stock-flow-track--admissions">
                  <span style={{ width: `${family.share_of_tech_admissions * 100}%` }} />
                </div>
              </div>
            </div>

            <dl>
              <div>
                <dt>Estoque RAIS</dt>
                <dd>{formatNumber(family.active_stock)}</dd>
              </div>
              <div>
                <dt>Admissões</dt>
                <dd>{formatNumber(family.admissions)}</dd>
              </div>
              <div>
                <dt>Desligamentos</dt>
                <dd>{formatNumber(family.dismissals)}</dd>
              </div>
              <div>
                <dt>Saldo</dt>
                <dd className={family.balance >= 0 ? 'is-positive' : 'is-negative'}>
                  {family.balance >= 0 ? '+' : ''}{formatNumber(family.balance)}
                </dd>
              </div>
              <div>
                <dt>Admissões / 100 estoque</dt>
                <dd>{formatPer100(family.admissions_per_100_prior_stock)}</dd>
              </div>
              <div>
                <dt>Saldo / 100 estoque</dt>
                <dd>{formatPer100(family.balance_per_100_prior_stock)}</dd>
              </div>
            </dl>
          </article>
        ))}
      </div>

      <div className="stock-flow-warning">
        <strong>Leitura correta</strong>
        <p>{data.methodological_warning}</p>
      </div>
    </section>
  )
}
