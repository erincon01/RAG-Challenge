import { useQuery } from '@tanstack/react-query'

import { api } from '../lib/api/client'
import { useUISettings } from '../state/ui-settings'

export function EmbeddingsPage() {
  const { source } = useUISettings()

  const embeddingsQuery = useQuery({
    queryKey: ['embeddings-status', source],
    queryFn: () => api.getEmbeddingsStatus(source),
    refetchInterval: 7000,
  })

  if (embeddingsQuery.isLoading) {
    return <p className="text-mute">Cargando estado de embeddings...</p>
  }

  if (embeddingsQuery.isError || !embeddingsQuery.data) {
    return <p className="text-rose-300">No se pudo consultar el estado de embeddings para {source}.</p>
  }

  return (
    <section className="space-y-4 rounded-2xl border border-white/10 bg-panel/70 p-5">
      <h2 className="text-2xl font-semibold text-ink">Embeddings</h2>
      <p className="text-sm text-mute">Fuente activa: {source}</p>
      <p className="text-sm text-ink">Tabla: {embeddingsQuery.data.table}</p>
      <p className="text-sm text-ink">Total filas: {embeddingsQuery.data.total_rows}</p>
      <div className="grid gap-3 md:grid-cols-2">
        {Object.entries(embeddingsQuery.data.coverage).map(([model, covered]) => (
          <article key={model} className="rounded-xl bg-canvas/60 p-3">
            <p className="text-xs uppercase tracking-[0.2em] text-mute">{model}</p>
            <p className="text-xl font-semibold text-ink">{covered}</p>
          </article>
        ))}
      </div>
    </section>
  )
}
