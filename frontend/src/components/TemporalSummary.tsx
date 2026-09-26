import type { TemporalSummary as TemporalSummaryData } from '../lib/api'
import { formatCompetence, formatNumber } from '../lib/format'

function signed(value: number): string {
  return `${value >= 0 ? '+' : ''}${formatNumber(value)}`
}

export function TemporalSummary({ data }: { data: TemporalSummaryData }) {
  return (
    <section className="temporal-summary" aria-labelledby="temporal-summary-title">
      <div className="temporal-summary__heading">
        <div>
          <p className="eyebrow">Consolidação temporal</p>
          <h2 id="temporal-summary-title">Leitura por trimestre</h2>
          <p>
            Os períodos abaixo usam somente competências efetivamente publicadas.
            Trimestres incompletos permanecem identificados como parciais.
          </p>
        </div>
        <span>
          {formatCompetence(data.published_from)} a {formatCompetence(data.published_to)}
        </span>
      </div>

      <div className="temporal-summary__grid">
        {data.periods.map((period) => (
          <article
            className={`temporal-period ${period.complete ? '' : 'temporal-period--partial'}`}
            key={period.key}
          >
            <div className="temporal-period__top">
              <div>
                <span>{period.label}</span>
                <small>
                  {period.complete
                    ? 'Período completo'
                    : `${period.published_months} competência${period.published_months === 1 ? '' : 's'} publicada${period.published_months === 1 ? '' : 's'}`}
                </small>
              </div>
              <strong>{signed(period.balance)}</strong>
            </div>

            <div className="temporal-period__metrics">
              <div>
                <small>Admissões</small>
                <strong>{formatNumber(period.admissions)}</strong>
              </div>
              <div>
                <small>Desligamentos</small>
                <strong>{formatNumber(period.dismissals)}</strong>
              </div>
              <div>
                <small>Média mensal do saldo</small>
                <strong>{signed(Math.round(period.average_monthly_balance))}</strong>
              </div>
            </div>

            <p>
              {formatCompetence(period.start_competence)}
              {period.start_competence !== period.end_competence
                ? ` a ${formatCompetence(period.end_competence)}`
                : ''}
            </p>
          </article>
        ))}
      </div>
    </section>
  )
}
