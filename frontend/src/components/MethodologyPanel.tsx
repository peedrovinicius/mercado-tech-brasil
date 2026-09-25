type MethodologyPanelProps = {
  open: boolean
  onClose: () => void
  competence?: string
}

export function MethodologyPanel({ open, onClose, competence }: MethodologyPanelProps) {
  if (!open) return null

  return (
    <div className="modal-backdrop" role="presentation" onMouseDown={onClose}>
      <section
        className="methodology-panel"
        role="dialog"
        aria-modal="true"
        aria-labelledby="methodology-title"
        onMouseDown={(event) => event.stopPropagation()}
      >
        <div className="methodology-panel__header">
          <div>
            <p className="eyebrow">Rastreabilidade</p>
            <h2 id="methodology-title">Como este número foi calculado?</h2>
          </div>
          <button className="icon-button" onClick={onClose} aria-label="Fechar">
            ×
          </button>
        </div>

        <div className="methodology-grid">
          <div><span>Fonte</span><strong>Novo CAGED / MTE</strong></div>
          <div><span>Competência</span><strong>{competence ?? 'Aguardando processamento'}</strong></div>
          <div><span>Recorte</span><strong>CBO de tecnologia versionado</strong></div>
          <div><span>Pipeline</span><strong>Bronze → Silver → Gold → API</strong></div>
        </div>

        <div className="methodology-copy">
          <h3>Admissões e desligamentos</h3>
          <p>
            O projeto trata as movimentações do Novo CAGED como fluxo. Admissões e desligamentos não são
            apresentados como estoque total de trabalhadores.
          </p>
          <h3>Saldo</h3>
          <p>Calculado como admissões menos desligamentos após as regras de qualidade da competência.</p>
          <h3>Salário</h3>
          <p>
            Média e mediana são calculadas apenas sobre admissões com salário válido. Registros inválidos
            ficam auditáveis em uma saída separada; não são descartados silenciosamente.
          </p>
        </div>
      </section>
    </div>
  )
}
