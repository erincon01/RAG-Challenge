import { useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { api, ApiError } from '../lib/api/client'
import { readCatalogSelection } from '../lib/storage/catalogSelection'
import { useUISettings } from '../state/ui-settings'

const AVAILABLE_DATASETS = ['matches', 'lineups', 'events'] as const

function asErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    const detail = (error.detail as { detail?: string } | null)?.detail
    return detail ? `${error.message}: ${detail}` : error.message
  }
  if (error instanceof Error) {
    return error.message
  }
  return 'Unknown error'
}

export function OperationsPage() {
  const { source } = useUISettings()
  const queryClient = useQueryClient()

  const [selection, setSelection] = useState(readCatalogSelection())
  const [downloadDatasets, setDownloadDatasets] = useState<string[]>(['matches', 'events'])
  const [loadDatasets, setLoadDatasets] = useState<string[]>(['matches', 'events'])
  const [selectedJobId, setSelectedJobId] = useState<string | null>(null)

  const jobsQuery = useQuery({
    queryKey: ['jobs-list'],
    queryFn: () => api.listJobs(100),
    refetchInterval: 2500,
  })

  const selectedJob = useMemo(() => {
    if (!selectedJobId || !jobsQuery.data) {
      return null
    }
    return jobsQuery.data.items.find((job) => job.id === selectedJobId) ?? null
  }, [selectedJobId, jobsQuery.data])

  const refreshJobs = () => {
    void queryClient.invalidateQueries({ queryKey: ['jobs-list'] })
  }

  const toggleDataset = (
    dataset: string,
    current: string[],
    setter: (value: string[]) => void,
  ) => {
    if (current.includes(dataset)) {
      setter(current.filter((item) => item !== dataset))
      return
    }
    setter([...current, dataset])
  }

  const downloadMutation = useMutation({
    mutationFn: () =>
      api.startDownload({
        datasets: downloadDatasets,
        match_ids: selection.matchIds,
        competition_id: selection.competitionId ?? undefined,
        season_id: selection.seasonId ?? undefined,
        overwrite: false,
      }),
    onSuccess: (response) => {
      setSelectedJobId(response.job_id)
      refreshJobs()
    },
  })

  const loadMutation = useMutation({
    mutationFn: () =>
      api.startLoad({
        source,
        datasets: loadDatasets,
        match_ids: selection.matchIds,
      }),
    onSuccess: (response) => {
      setSelectedJobId(response.job_id)
      refreshJobs()
    },
  })

  const aggregateMutation = useMutation({
    mutationFn: () =>
      api.startAggregate({
        source,
        match_ids: selection.matchIds,
      }),
    onSuccess: (response) => {
      setSelectedJobId(response.job_id)
      refreshJobs()
    },
  })

  const embeddingsMutation = useMutation({
    mutationFn: () =>
      api.startRebuildEmbeddings({
        source,
        match_ids: selection.matchIds,
      }),
    onSuccess: (response) => {
      setSelectedJobId(response.job_id)
      refreshJobs()
    },
  })

  return (
    <section className="grid gap-4 xl:grid-cols-[1.1fr_1fr]">
      <article className="space-y-4 rounded-2xl border border-white/10 bg-panel/70 p-5">
        <div className="flex items-center justify-between">
          <h2 className="text-2xl font-semibold text-ink">Descarga y Carga</h2>
          <button
            type="button"
            onClick={() => setSelection(readCatalogSelection())}
            className="rounded-lg border border-white/20 bg-white/5 px-3 py-1 text-xs text-ink"
          >
            Recargar selección
          </button>
        </div>

        <div className="rounded-xl border border-white/10 bg-canvas/60 p-4 text-sm">
          <p className="text-mute">Source destino</p>
          <p className="font-medium capitalize text-ink">{source}</p>
          <p className="mt-3 text-mute">Competition ID / Season ID</p>
          <p className="font-medium text-ink">
            {selection.competitionId ?? '-'} / {selection.seasonId ?? '-'}
          </p>
          <p className="mt-3 text-mute">Match IDs seleccionados</p>
          <p className="text-ink">{selection.matchIds.length > 0 ? selection.matchIds.join(', ') : 'ninguno'}</p>
        </div>

        <div className="space-y-3 rounded-xl border border-white/10 bg-canvas/60 p-4">
          <p className="text-sm font-semibold text-ink">Datasets para descarga</p>
          <div className="flex flex-wrap gap-3">
            {AVAILABLE_DATASETS.map((dataset) => (
              <label key={`download-${dataset}`} className="flex items-center gap-2 rounded-lg border border-white/10 px-3 py-2 text-sm">
                <input
                  type="checkbox"
                  checked={downloadDatasets.includes(dataset)}
                  onChange={() => toggleDataset(dataset, downloadDatasets, setDownloadDatasets)}
                />
                {dataset}
              </label>
            ))}
          </div>
          <button
            type="button"
            onClick={() => downloadMutation.mutate()}
            disabled={downloadMutation.isPending || downloadDatasets.length === 0}
            className="rounded-xl border border-accent/50 bg-accent/15 px-4 py-2 text-sm font-semibold text-accent disabled:opacity-60"
          >
            Lanzar descarga
          </button>
          {downloadMutation.isError ? <p className="text-sm text-rose-300">{asErrorMessage(downloadMutation.error)}</p> : null}
        </div>

        <div className="space-y-3 rounded-xl border border-white/10 bg-canvas/60 p-4">
          <p className="text-sm font-semibold text-ink">Datasets para carga</p>
          <div className="flex flex-wrap gap-3">
            {AVAILABLE_DATASETS.map((dataset) => (
              <label key={`load-${dataset}`} className="flex items-center gap-2 rounded-lg border border-white/10 px-3 py-2 text-sm">
                <input
                  type="checkbox"
                  checked={loadDatasets.includes(dataset)}
                  onChange={() => toggleDataset(dataset, loadDatasets, setLoadDatasets)}
                />
                {dataset}
              </label>
            ))}
          </div>
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              onClick={() => loadMutation.mutate()}
              disabled={loadMutation.isPending || loadDatasets.length === 0}
              className="rounded-xl border border-accentWarm/50 bg-accentWarm/15 px-4 py-2 text-sm font-semibold text-accentWarm disabled:opacity-60"
            >
              Lanzar carga
            </button>
            <button
              type="button"
              onClick={() => aggregateMutation.mutate()}
              disabled={aggregateMutation.isPending}
              className="rounded-xl border border-white/20 bg-white/5 px-4 py-2 text-sm font-semibold text-ink disabled:opacity-60"
            >
              Construir agregaciones
            </button>
            <button
              type="button"
              onClick={() => embeddingsMutation.mutate()}
              disabled={embeddingsMutation.isPending}
              className="rounded-xl border border-white/20 bg-white/5 px-4 py-2 text-sm font-semibold text-ink disabled:opacity-60"
            >
              Rebuild embeddings
            </button>
          </div>
          {loadMutation.isError ? <p className="text-sm text-rose-300">{asErrorMessage(loadMutation.error)}</p> : null}
          {aggregateMutation.isError ? <p className="text-sm text-rose-300">{asErrorMessage(aggregateMutation.error)}</p> : null}
          {embeddingsMutation.isError ? <p className="text-sm text-rose-300">{asErrorMessage(embeddingsMutation.error)}</p> : null}
        </div>
      </article>

      <article className="space-y-4 rounded-2xl border border-white/10 bg-panel/70 p-5">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-ink">Jobs</h3>
          <button
            type="button"
            onClick={refreshJobs}
            className="rounded-lg border border-white/20 bg-white/5 px-3 py-1 text-xs text-ink"
          >
            Refresh
          </button>
        </div>

        {jobsQuery.isLoading ? <p className="text-mute">Cargando jobs...</p> : null}
        {jobsQuery.isError ? <p className="text-rose-300">No se pudo consultar el estado de jobs.</p> : null}

        <div className="max-h-[360px] overflow-auto rounded-xl border border-white/10">
          <table className="min-w-full divide-y divide-white/10 text-sm">
            <thead className="bg-canvas/70 text-left text-xs uppercase tracking-[0.16em] text-mute">
              <tr>
                <th className="px-3 py-2">Type</th>
                <th className="px-3 py-2">Status</th>
                <th className="px-3 py-2">Progress</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {(jobsQuery.data?.items ?? []).map((job) => {
                const progress = job.total > 0 ? `${job.progress}/${job.total}` : String(job.progress)
                return (
                  <tr
                    key={job.id}
                    onClick={() => setSelectedJobId(job.id)}
                    className={[
                      'cursor-pointer transition hover:bg-white/5',
                      selectedJobId === job.id ? 'bg-accent/10' : '',
                    ].join(' ')}
                  >
                    <td className="px-3 py-2 text-ink">{job.type}</td>
                    <td className="px-3 py-2 text-mute">{job.status}</td>
                    <td className="px-3 py-2 text-mute">{progress}</td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>

        {selectedJob ? (
          <div className="rounded-xl border border-white/10 bg-canvas/60 p-4 text-sm">
            <p className="text-mute">Job ID</p>
            <p className="break-all text-ink">{selectedJob.id}</p>
            <p className="mt-2 text-mute">Message</p>
            <p className="text-ink">{selectedJob.message}</p>
            {selectedJob.error ? (
              <>
                <p className="mt-2 text-mute">Error</p>
                <p className="text-rose-300">{selectedJob.error}</p>
              </>
            ) : null}
            <p className="mt-2 text-mute">Result</p>
            <pre className="mt-1 overflow-auto rounded bg-black/30 p-2 text-xs text-slate-100">
              {JSON.stringify(selectedJob.result, null, 2)}
            </pre>
          </div>
        ) : null}
      </article>
    </section>
  )
}
