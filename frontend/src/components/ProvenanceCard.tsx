import type { Provenance } from '../lib/api'

export function ProvenanceCard({ data }: { data: Provenance }) {
  const shortHash = `${data.sha256.slice(0, 12)}…${data.sha256.slice(-8)}`
  const transport = data.transport
    ? data.transport.replaceAll('_', ' ')
    : 'não informado'

  return (
    <article className="provenance-card">
      <p className="eyebrow">Proveniência</p>
      <h3>Do arquivo oficial até este painel</h3>
      <dl>
        <div><dt>Arquivo</dt><dd>{data.original_name}</dd></div>
        <div><dt>Competência</dt><dd>{data.competence}</dd></div>
        <div><dt>SHA-256</dt><dd><code title={data.sha256}>{shortHash}</code></dd></div>
        <div><dt>Origem</dt><dd>{data.source}</dd></div>
        <div>
          <dt>Transporte</dt>
          <dd title={data.source_url}>{transport}</dd>
        </div>
      </dl>
    </article>
  )
}
