import { useQuery } from '@tanstack/react-query'

import { api } from '../lib/api/client'
import { StatusBadge } from '../components/ui/StatusBadge'

function StatCard({ label, value }: { label: string; value: string }) {
  return (
    <article className="rounded-2xl border border-white/10 bg-panel/70 p-4">
      <p className="text-xs uppercase tracking-[0.2em] text-mute">{label}</p>
      <p className="mt-2 text-2xl font-semibold text-ink">{value}</p>
    </article>
  )
}

export function DashboardPage() {
  const healthQuery = useQuery({ queryKey: ['health'], queryFn: api.getHealth })
  const readyQuery = useQuery({ queryKey: ['ready'], queryFn: api.getReadiness })
  const sourcesQuery = useQuery({ queryKey: ['source-status'], queryFn: api.getSourcesStatus })
  const capabilitiesQuery = useQuery({ queryKey: ['capabilities'], queryFn: api.getCapabilities })
  const jobsQuery = useQuery({ queryKey: ['jobs'], queryFn: () => api.listJobs(10), refetchInterval: 5000 })

  const loading =
    healthQuery.isLoading ||
    readyQuery.isLoading ||
    sourcesQuery.isLoading ||
    capabilitiesQuery.isLoading ||
    jobsQuery.isLoading

  if (loading) {
    return <p className="text-mute">Cargando dashboard...</p>
  }

  const capabilities = capabilitiesQuery.data?.capabilities
  const ready = readyQuery.data?.ready ?? false

  return (
    <section className="space-y-6">
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <StatCard label="API" value={healthQuery.data?.status ?? 'unknown'} />
        <StatCard label="Readiness" value={ready ? 'Ready' : 'Not Ready'} />
        <StatCard label="Sources" value={String(sourcesQuery.data?.sources.length ?? 0)} />
        <StatCard label="Recent Jobs" value={String(jobsQuery.data?.items.length ?? 0)} />
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <article className="rounded-2xl border border-white/10 bg-panel/70 p-4">
          <h2 className="text-lg font-semibold text-ink">Estado de sources</h2>
          <ul className="mt-3 space-y-2">
            {sourcesQuery.data?.sources.map((source) => (
              <li key={source.source} className="flex items-center justify-between rounded-xl bg-canvas/60 p-3">
                <span className="capitalize text-ink">{source.source}</span>
                <StatusBadge ok={source.connected} />
              </li>
            ))}
          </ul>
        </article>

        <article className="rounded-2xl border border-white/10 bg-panel/70 p-4">
          <h2 className="text-lg font-semibold text-ink">Capabilities</h2>
          <ul className="mt-3 space-y-2">
            {capabilities &&
              Object.values(capabilities).map((capability) => (
                <li key={capability.source} className="rounded-xl bg-canvas/60 p-3">
                  <p className="font-medium capitalize text-ink">{capability.source}</p>
                  <p className="mt-1 text-xs text-mute">
                    {capability.embedding_models.length} modelos - {capability.search_algorithms.length} algoritmos
                  </p>
                </li>
              ))}
          </ul>
        </article>
      </div>
    </section>
  )
}
