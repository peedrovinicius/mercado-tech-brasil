type EmptyStateProps = {
  title: string
  message: string
}

export function EmptyState({ title, message }: EmptyStateProps) {
  return (
    <section className="empty-state" role="status">
      <div className="empty-state__mark">MT</div>
      <div>
        <p className="eyebrow">Pipeline aguardando dados</p>
        <h2>{title}</h2>
        <p>{message}</p>
        <p className="empty-state__hint">
          A interface não usa valores demonstrativos. Assim que a competência oficial passar pela validação,
          os indicadores aparecerão automaticamente.
        </p>
      </div>
    </section>
  )
}
