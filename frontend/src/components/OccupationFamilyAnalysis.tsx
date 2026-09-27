import type { OccupationFamilyTrend } from '../lib/api'
import { formatCompetence, formatNumber, formatPercent } from '../lib/format'
import { OccupationFamilyTrendChart } from './Charts'

export function OccupationFamilyAnalysis({
  data,
}: {
  data: OccupationFamilyTrend
}) {
  return (
    <section className="occupation-family-section">
      <div className="occupation-family-section__heading">
        <div>
          <p className="eyebrow">Estrutura ocupacional</p>
          <h2>Como as famílias CBO evoluem ao longo da série</h2>
          <p>
            A leitura agrupa os códigos ocupacionais pelas cinco famílias do recorte
            CBO v2 e compara seus fluxos mês a mês. Admissões, desligamentos e saldo
            são somados. Medianas salariais não são agregadas entre ocupações.
          </p>
        </div>
        <span>
          {formatCompetence(data.published_from)} a {formatCompetence(data.published_to)}
        </span>
      </div>

      <div className="occupation-family-layout">
        <article className="panel occupation-family-chart-panel">
          <div className="panel__heading">
            <div>
              <p className="eyebrow">Saldo mensal por família</p>
              <h3>Trajetória das cinco famílias tech</h3>
            </div>
            <span>{data.published_months} competências</span>
          </div>
          <OccupationFamilyTrendChart families={data.families} />
        </article>

        <div className="occupation-family-list">
          {data.families.map((family) => (
            <article className="occupation-family-card" key={family.cbo_familia}>
              <div className="occupation-family-card__head">
                <span>{family.cbo_familia}</span>
                <strong>{formatPercent(family.share_of_tech_admissions)}</strong>
              </div>
              <h3>{family.cbo_familia_nome}</h3>
              <small>participação nas admissões tech do período</small>
              <dl>
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
              </dl>
            </article>
          ))}
        </div>
      </div>

      <p className="occupation-family-section__note">
        Fonte: {data.source}. O recorte é ocupacional e permanece restrito às famílias
        versionadas em config/cbo_tech.yml.
      </p>
    </section>
  )
}
