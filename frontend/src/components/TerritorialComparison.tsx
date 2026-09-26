import type { TerritorialComparison as TerritorialComparisonData } from '../lib/api'
import { formatCompetence, formatNumber, formatPercent } from '../lib/format'

export function TerritorialComparison({
  data,
}: {
  data: TerritorialComparisonData
}) {
  const nordeste = data.items.find((item) => item.key === 'NE')

  return (
    <section className="territorial-comparison" aria-label="Comparação territorial tech">
      <div className="territorial-comparison__heading">
        <div>
          <p className="eyebrow">Comparação territorial</p>
          <h2>Ceará, Nordeste e Brasil</h2>
          <p>
            Comparação da competência mais recente publicada no recorte CBO de
            tecnologia. Os valores representam movimentações do emprego formal.
          </p>
        </div>
        <span>{formatCompetence(data.competence)}</span>
      </div>

      <div className="territorial-comparison__grid">
        {data.items.map((item) => (
          <article
            className={`territorial-card territorial-card--${item.key.toLowerCase()}`}
            key={item.key}
          >
            <div className="territorial-card__top">
              <span>{item.label}</span>
              <strong>
                {formatPercent(item.share_national_admissions)}
              </strong>
            </div>
            <small>participação nas admissões tech nacionais</small>

            <div className="territorial-card__bar">
              <span
                style={{
                  width: `${Math.max(
                    2,
                    item.share_national_admissions * 100,
                  )}%`,
                }}
              />
            </div>

            <div className="territorial-card__metrics">
              <div>
                <small>Admissões</small>
                <strong>{formatNumber(item.admissions)}</strong>
              </div>
              <div>
                <small>Desligamentos</small>
                <strong>{formatNumber(item.dismissals)}</strong>
              </div>
              <div>
                <small>Saldo</small>
                <strong>
                  {item.balance >= 0 ? '+' : ''}
                  {formatNumber(item.balance)}
                </strong>
              </div>
            </div>
          </article>
        ))}
      </div>

      <p className="territorial-comparison__note">
        Ceará representa {formatPercent(data.ceara_share_northeast_admissions)}
        {' '}das admissões tech do Nordeste nesta competência. O Nordeste
        representa {nordeste ? formatPercent(nordeste.share_national_admissions) : 'N/D'}
        {' '}das admissões tech do Brasil.
      </p>
    </section>
  )
}
