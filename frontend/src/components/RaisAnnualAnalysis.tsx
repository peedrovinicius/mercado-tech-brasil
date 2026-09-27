import type {
  RaisCboFamilyResponse,
  RaisMunicipalityResponse,
  RaisOverview,
  RaisUfResponse,
} from '../lib/api'
import { formatNumber, formatPercent } from '../lib/format'

type Props = {
  overview: RaisOverview
  byUf: RaisUfResponse
  byFamily: RaisCboFamilyResponse
  byMunicipality: RaisMunicipalityResponse
}

export function RaisAnnualAnalysis({
  overview,
  byUf,
  byFamily,
  byMunicipality,
}: Props) {
  const topUf = byUf.items.slice(0, 10)
  const topFamilies = byFamily.items.slice(0, 5)
  const topMunicipalities = byMunicipality.items.slice(0, 10)

  return (
    <section className="rais-section" id="rais">
      <div className="rais-section__heading">
        <div>
          <p className="eyebrow">Estoque anual RAIS</p>
          <h2>Vínculos formais de tecnologia ativos em 31/12.</h2>
          <p>
            A RAIS mede estoque anual, não movimentação mensal. Este bloco mostra
            vínculos formais ativos e não abandonados no encerramento de {overview.year},
            usando o mesmo recorte ocupacional CBO v2 do projeto.
          </p>
        </div>
        <div className="rais-section__meta">
          <span>{overview.year}</span>
          <small>RAIS / MTE</small>
        </div>
      </div>

      <div className="rais-metrics">
        <article className="rais-metric rais-metric--primary">
          <span>Estoque tech</span>
          <strong>{formatNumber(overview.active_stock_tech)}</strong>
          <small>vínculos ativos em 31/12</small>
        </article>
        <article className="rais-metric">
          <span>Participação no emprego formal</span>
          <strong>{formatPercent(overview.share_tech_of_national_active)}</strong>
          <small>do estoque nacional ativo</small>
        </article>
        <article className="rais-metric">
          <span>Estoque formal nacional</span>
          <strong>{formatNumber(overview.active_stock_national_reference)}</strong>
          <small>referência oficial reconciliada</small>
        </article>
      </div>

      <div className="rais-grid">
        <article className="rais-panel">
          <div className="rais-panel__heading">
            <div>
              <p className="eyebrow">Distribuição territorial</p>
              <h3>Maiores estoques tech por UF</h3>
            </div>
            <span>Top 10</span>
          </div>
          <div className="rais-ranking">
            {topUf.map((item) => (
              <div className="rais-ranking__row" key={item.uf}>
                <div className="rais-ranking__label">
                  <strong>{item.uf}</strong>
                  <span>{formatNumber(item.active_stock)}</span>
                </div>
                <div className="rais-ranking__track" aria-hidden="true">
                  <span
                    style={{
                      width: `${Math.max(1, item.share_of_tech_stock * 100)}%`,
                    }}
                  />
                </div>
                <small>{formatPercent(item.share_of_tech_stock)}</small>
              </div>
            ))}
          </div>
        </article>

        <article className="rais-panel">
          <div className="rais-panel__heading">
            <div>
              <p className="eyebrow">Estrutura ocupacional</p>
              <h3>Estoque por família CBO</h3>
            </div>
            <span>CBO v2</span>
          </div>
          <div className="rais-family-list">
            {topFamilies.map((item) => (
              <div className="rais-family" key={item.cbo_familia}>
                <div>
                  <span>{item.cbo_familia}</span>
                  <strong>{item.cbo_familia_nome}</strong>
                </div>
                <div className="rais-family__value">
                  <strong>{formatNumber(item.active_stock)}</strong>
                  <small>{formatPercent(item.share_of_tech_stock)}</small>
                </div>
              </div>
            ))}
          </div>
        </article>
        <article className="rais-panel rais-panel--municipality">
          <div className="rais-panel__heading">
            <div>
              <p className="eyebrow">Concentração municipal</p>
              <h3>Maiores estoques tech por município</h3>
            </div>
            <span>Top 10</span>
          </div>
          <div className="rais-family-list">
            {topMunicipalities.map((item) => (
              <div className="rais-family" key={item.municipio_codigo_rais}>
                <div>
                  <span>{item.uf}</span>
                  <strong>{item.municipio_nome}</strong>
                </div>
                <div className="rais-family__value">
                  <strong>{formatNumber(item.active_stock)}</strong>
                  <small>{formatPercent(item.share_of_tech_stock)}</small>
                </div>
              </div>
            ))}
          </div>
        </article>
      </div>

      <p className="rais-section__note">
        Série anual separada do Novo CAGED. A RAIS só aparece aqui quando a release
        anual possui reconciliação oficial, fingerprint íntegro e gate de publicação aprovado.
      </p>
    </section>
  )
}
