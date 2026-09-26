import { ReferenceRegionChart } from './Charts'
import type { OfficialReference } from '../lib/api'
import { formatCurrencyPrecise, formatNumber } from '../lib/format'

export function ReferenceContext({ data }: { data: OfficialReference }) {
  const ceara = data.ufs.CE
  const regions = Object.entries(data.regions).map(([region, metrics]) => ({
    region,
    ...metrics,
  }))

  return (
    <section className="reference-section" id="contexto">
      <div className="reference-section__heading">
        <div>
          <p className="eyebrow">Contexto oficial · julho/2026</p>
          <h2>Antes do recorte tech, o retrato do mercado formal brasileiro.</h2>
          <p>
            Estes números são a referência publicada pelo MTE para todo o mercado formal.
            Eles servem como contexto e reconciliação — não são apresentados como indicadores de tecnologia.
          </p>
        </div>
        <a
          className="source-link"
          href={data.source.url}
          target="_blank"
          rel="noreferrer"
        >
          Fonte oficial ↗
        </a>
      </div>

      <div className="reference-grid">
        <article className="reference-card reference-card--primary">
          <span className="reference-card__kicker">Brasil</span>
          <strong>{formatNumber(data.national.balance)}</strong>
          <span>saldo de empregos formais</span>
          <div className="reference-card__mini">
            <div><small>Admissões</small><b>{formatNumber(data.national.admissions)}</b></div>
            <div><small>Desligamentos</small><b>{formatNumber(data.national.dismissals)}</b></div>
          </div>
        </article>

        <article className="reference-card">
          <span className="reference-card__kicker">Ceará</span>
          <strong>+{formatNumber(ceara.balance)}</strong>
          <span>saldo no mês</span>
          <div className="reference-card__mini">
            <div><small>Admissões</small><b>{formatNumber(ceara.admissions)}</b></div>
            <div><small>Desligamentos</small><b>{formatNumber(ceara.dismissals)}</b></div>
          </div>
        </article>

        <article className="reference-card">
          <span className="reference-card__kicker">Salário de admissão · CE</span>
          <strong>{formatCurrencyPrecise(ceara.salary_mean_admission_brl)}</strong>
          <span>média nominal oficial</span>
          <div className="reference-card__rule">
            Regra MTE: 0,3–150 salários mínimos, sem intermitentes
          </div>
        </article>

        <article className="reference-chart-card">
          <div className="panel__heading">
            <div>
              <p className="eyebrow">Brasil por região</p>
              <h3>Saldo de empregos formais</h3>
            </div>
            <span>mercado total</span>
          </div>
          <ReferenceRegionChart items={regions} />
        </article>
      </div>
    </section>
  )
}
