import { useState } from 'react'
import type { MunicipalityResponse } from '../lib/api'
import { MunicipalityChart } from './Charts'

type Mode = 'volume' | 'normalized'

export function MunicipalityAnalysis({
  volume,
  normalized,
}: {
  volume: MunicipalityResponse
  normalized?: MunicipalityResponse
}) {
  const canNormalize = Boolean(
    normalized?.normalization_available && normalized.items.length,
  )
  const [mode, setMode] = useState<Mode>('volume')
  const activeMode = mode === 'normalized' && canNormalize ? 'normalized' : 'volume'
  const active = activeMode === 'normalized' ? normalized : volume

  return (
    <article className="panel panel--wide">
      <div className="panel__heading panel__heading--municipality">
        <div>
          <p className="eyebrow">Municípios</p>
          <h2>
            {activeMode === 'normalized'
              ? 'Admissões tech por 100 mil habitantes'
              : 'Admissões tech por município'}
          </h2>
        </div>
        {canNormalize ? (
          <div className="segmented-control" aria-label="Métrica municipal">
            <button
              type="button"
              className={activeMode === 'volume' ? 'is-active' : ''}
              onClick={() => setMode('volume')}
              aria-pressed={activeMode === 'volume'}
            >
              Volume
            </button>
            <button
              type="button"
              className={activeMode === 'normalized' ? 'is-active' : ''}
              onClick={() => setMode('normalized')}
              aria-pressed={activeMode === 'normalized'}
            >
              Por 100 mil
            </button>
          </div>
        ) : (
          <span>Top 12</span>
        )}
      </div>

      <MunicipalityChart
        items={active?.items ?? []}
        metric={activeMode === 'normalized' ? 'admissions_per_100k' : 'admissions'}
      />

      {activeMode === 'normalized' && active?.population_reference_year ? (
        <p className="panel__note">
          Taxa calculada com Estimativas da População do IBGE,
          referência de 1º de julho de {active.population_reference_year}.
        </p>
      ) : null}
    </article>
  )
}
