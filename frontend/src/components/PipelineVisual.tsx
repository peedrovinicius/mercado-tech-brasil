export function PipelineVisual({ hasTechData }: { hasTechData: boolean }) {
  const steps = [
    { label: 'Fonte oficial', detail: 'MTE + CBO', state: 'done' },
    { label: 'Ingestão', detail: 'Bronze + SHA-256', state: hasTechData ? 'done' : 'waiting' },
    { label: 'Qualidade', detail: 'Silver + rejeições', state: hasTechData ? 'done' : 'waiting' },
    { label: 'Indicadores', detail: 'Gold + gate', state: hasTechData ? 'done' : 'waiting' },
    { label: 'Produto', detail: 'API + dashboard', state: hasTechData ? 'done' : 'ready' },
  ]

  return (
    <section className="pipeline-visual" aria-label="Status do pipeline">
      <div className="pipeline-visual__title">
        <div>
          <p className="eyebrow">Estado do produto</p>
          <h2>{hasTechData ? 'Dados tech publicados' : 'Interface pronta, aguardando o microdado tech'}</h2>
        </div>
        <span className={hasTechData ? 'status-badge status-badge--success' : 'status-badge'}>
          {hasTechData ? 'Online' : 'Pipeline preparado'}
        </span>
      </div>
      <div className="pipeline-steps">
        {steps.map((step, index) => (
          <div className={`pipeline-step pipeline-step--${step.state}`} key={step.label}>
            <span className="pipeline-step__index">{String(index + 1).padStart(2, '0')}</span>
            <div>
              <strong>{step.label}</strong>
              <small>{step.detail}</small>
            </div>
          </div>
        ))}
      </div>
    </section>
  )
}
