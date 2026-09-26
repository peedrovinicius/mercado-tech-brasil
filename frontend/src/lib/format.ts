export function formatNumber(value: number): string {
  return new Intl.NumberFormat('pt-BR').format(value)
}

export function formatCurrency(value: number | null): string {
  if (value === null) return 'N/D'
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL',
    maximumFractionDigits: 0,
  }).format(value)
}

export function formatCurrencyPrecise(value: number | null): string {
  if (value === null) return 'N/D'
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value)
}

export function formatCompetence(value: string): string {
  if (!/^\d{6}$/.test(value)) return value
  const year = value.slice(0, 4)
  const month = value.slice(4, 6)
  return `${month}/${year}`
}

export function formatPercent(value: number): string {
  return new Intl.NumberFormat('pt-BR', {
    style: 'percent',
    maximumFractionDigits: 2,
  }).format(value)
}
