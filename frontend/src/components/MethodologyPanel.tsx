import { useEffect, useRef } from 'react'

type MethodologyPanelProps = {
  open: boolean
  onClose: () => void
  competence?: string
}

export function MethodologyPanel({ open, onClose, competence }: MethodologyPanelProps) {
  const dialogRef = useRef<HTMLElement>(null)

  useEffect(() => {
    if (!open) return undefined

    const previousOverflow = document.body.style.overflow
    const previouslyFocused = document.activeElement instanceof HTMLElement
      ? document.activeElement
      : null
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        event.preventDefault()
        onClose()
        return
      }
      if (event.key !== 'Tab' || !dialogRef.current) return

      const focusable = Array.from(dialogRef.current.querySelectorAll<HTMLElement>(
        'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), '
        + 'textarea:not([disabled]), [tabindex]:not([tabindex="-1"])',
      )).filter((element) => element.getClientRects().length > 0)

      if (focusable.length === 0) {
        event.preventDefault()
        dialogRef.current.focus()
        return
      }

      const first = focusable[0]
      const last = focusable[focusable.length - 1]
      if (event.shiftKey && (document.activeElement === first
        || !dialogRef.current.contains(document.activeElement))) {
        event.preventDefault()
        last.focus()
      } else if (!event.shiftKey && (document.activeElement === last
        || !dialogRef.current.contains(document.activeElement))) {
        event.preventDefault()
        first.focus()
      }
    }

    document.body.style.overflow = 'hidden'
    document.addEventListener('keydown', handleKeyDown)

    return () => {
      document.body.style.overflow = previousOverflow
      document.removeEventListener('keydown', handleKeyDown)
      previouslyFocused?.focus()
    }
  }, [open, onClose])

  if (!open) return null

  return (
    <div className="modal-backdrop" role="presentation" onMouseDown={onClose}>
      <section
        className="methodology-panel"
        ref={dialogRef}
        tabIndex={-1}
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
          <button className="icon-button" type="button" onClick={onClose} aria-label="Fechar" autoFocus>
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
            ficam auditáveis em uma saída separada e não são descartados silenciosamente. Quando disponível,
            o valor real é corrigido pelo IPCA/IBGE para a competência base informada no painel.
          </p>
          <h3>Ajustes posteriores</h3>
          <p>
            Arquivos FOR e EXC são aplicados à competência original antes da reconstrução dos agregados,
            preservando a rastreabilidade das revisões oficiais.
          </p>
        </div>
      </section>
    </div>
  )
}
