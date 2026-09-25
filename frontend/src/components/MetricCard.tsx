type MetricCardProps = {
  label: string
  value: string
  detail?: string
  tone?: 'default' | 'positive' | 'negative'
}

export function MetricCard({ label, value, detail, tone = 'default' }: MetricCardProps) {
  return (
    <article className={`metric-card metric-card--${tone}`}>
      <span className="metric-card__label">{label}</span>
      <strong className="metric-card__value">{value}</strong>
      {detail ? <span className="metric-card__detail">{detail}</span> : null}
    </article>
  )
}
