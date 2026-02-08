import { useQuery } from '@tanstack/react-query'

import { api } from '../lib/api/client'
import { StatusBadge } from '../components/ui/StatusBadge'

export function SourcesPage() {
  const capabilitiesQuery = useQuery({ queryKey: ['capabilities'], queryFn: api.getCapabilities })
  const statusQuery = useQuery({ queryKey: ['sources-status'], queryFn: api.getSourcesStatus, refetchInterval: 8000 })

  if (capabilitiesQuery.isLoading || statusQuery.isLoading) {
    return <p className="text-mute">Cargando estado de motores...</p>
  }

  if (capabilitiesQuery.isError || statusQuery.isError) {
    return <p className="text-rose-300">No se pudo cargar la información de los motores.</p>
  }

  if (!capabilitiesQuery.data || !statusQuery.data) {
    return <p className="text-mute">Sin datos de capacidades disponibles.</p>
  }

  return (
    <section className="space-y-4">
      <h2 className="text-2xl font-semibold text-ink">Data Sources</h2>
      <div className="grid gap-4 lg:grid-cols-2">
        {statusQuery.data.sources.map((sourceStatus) => {
          const capability = capabilitiesQuery.data.capabilities[sourceStatus.source]
          return (
            <article key={sourceStatus.source} className="rounded-2xl border border-white/10 bg-panel/70 p-5">
              <div className="flex items-center justify-between">
                <h3 className="text-xl font-semibold capitalize text-ink">{sourceStatus.source}</h3>
                <StatusBadge ok={sourceStatus.connected} />
              </div>
              <div className="mt-4 grid gap-3 text-sm">
                <div>
                  <p className="text-mute">Embedding models</p>
                  <p className="text-ink">{capability.embedding_models.join(', ')}</p>
                </div>
                <div>
                  <p className="text-mute">Search algorithms</p>
                  <p className="text-ink">{capability.search_algorithms.join(', ')}</p>
                </div>
              </div>
            </article>
          )
        })}
      </div>
    </section>
  )
}
