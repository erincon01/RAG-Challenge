import { useUISettings } from '../state/ui-settings'

export function ExplorerPage() {
  const { source } = useUISettings()

  return (
    <section className="space-y-3 rounded-2xl border border-white/10 bg-panel/70 p-5">
      <h2 className="text-2xl font-semibold text-ink">Explorador de Datos</h2>
      <p className="text-mute">
        Esta vista se completa en Fase 4 con visores de competiciones, partidos, teams, players y events.
      </p>
      <p className="text-sm text-ink">
        Source actual: <span className="font-semibold capitalize">{source}</span>
      </p>
    </section>
  )
}
