import { useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { api, ApiError } from '../lib/api/client'
import type { DownloadCleanupResponse, JobRecord } from '../lib/api/types'
import { readCatalogSelection } from '../lib/storage/catalogSelection'
import { useUISettings } from '../state/ui-settings'

const AVAILABLE_DATASETS = ['matches', 'lineups', 'events'] as const
const TERMINAL_JOB_TYPES = new Set(['download', 'load', 'aggregate', 'summaries_generate', 'embeddings_rebuild'])

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

  const initialSelection = readCatalogSelection()
  const [selection, setSelection] = useState(initialSelection)

  const [downloadDatasets, setDownloadDatasets] = useState<string[]>(['matches', 'events'])
  const [loadDatasets, setLoadDatasets] = useState<string[]>(['matches', 'events'])

  // Cleanup state
  const [cleanupDatasets, setCleanupDatasets] = useState<string[]>(['matches', 'lineups', 'events'])
  const [cleanupResult, setCleanupResult] = useState<DownloadCleanupResponse | null>(null)

  const [selectedJobId, setSelectedJobId] = useState<string | null>(null)
  const [terminalJobId, setTerminalJobId] = useState<string | null>(null)

  // Queries
  const jobsQuery = useQuery({
    queryKey: ['jobs-list'],
    queryFn: () => api.listJobs(100),
    refetchInterval: 2500,
  })

  const selectedJobQuery = useQuery({
    queryKey: ['job-detail', selectedJobId],
    queryFn: () => api.getJob(selectedJobId as string),
    enabled: selectedJobId !== null,
    refetchInterval: 2500,
  })

  const terminalJobQuery = useQuery({
    queryKey: ['terminal-job-detail', terminalJobId],
    queryFn: () => api.getJob(terminalJobId as string),
    enabled: terminalJobId !== null,
    refetchInterval: 2000,
  })

  const selectedJob = useMemo(() => {
    if (selectedJobQuery.data) return selectedJobQuery.data
    if (!selectedJobId || !jobsQuery.data) return null
    return jobsQuery.data.items.find((job) => job.id === selectedJobId) ?? null
  }, [jobsQuery.data, selectedJobId, selectedJobQuery.data])

  const terminalJob = useMemo(() => {
    if (terminalJobQuery.data) return terminalJobQuery.data
    if (!terminalJobId || !jobsQuery.data) return null
    return jobsQuery.data.items.find((job) => job.id === terminalJobId) ?? null
  }, [jobsQuery.data, terminalJobId, terminalJobQuery.data])

  const refreshJobs = () => {
    void queryClient.invalidateQueries({ queryKey: ['jobs-list'] })
  }

  const onJobCreated = (response: { job_id: string }) => {
    setSelectedJobId(response.job_id)
    setTerminalJobId(response.job_id)
    refreshJobs()
  }

  const toggleDataset = (dataset: string, current: string[], setter: (v: string[]) => void) => {
    setter(current.includes(dataset) ? current.filter((d) => d !== dataset) : [...current, dataset])
  }

  const setActiveJob = (job: JobRecord) => {
    setSelectedJobId(job.id)
    if (TERMINAL_JOB_TYPES.has(job.type)) setTerminalJobId(job.id)
  }

  // Mutations
  const downloadMutation = useMutation({
    mutationFn: () =>
      api.startDownload({
        datasets: downloadDatasets,
        match_ids: selection.matchIds,
        competition_id: selection.competitionId ?? undefined,
        season_id: selection.seasonId ?? undefined,
        overwrite: false,
      }),
    onSuccess: onJobCreated,
  })

  const loadMutation = useMutation({
    mutationFn: () =>
      api.startLoad({ source, datasets: loadDatasets, match_ids: selection.matchIds }),
    onSuccess: onJobCreated,
  })

  const aggregateMutation = useMutation({
    mutationFn: () =>
      api.startAggregate({ source, match_ids: selection.matchIds }),
    onSuccess: onJobCreated,
  })

  const summariesMutation = useMutation({
    mutationFn: () =>
      api.startGenerateSummaries({ source, match_ids: selection.matchIds }),
    onSuccess: onJobCreated,
  })

  const embeddingsMutation = useMutation({
    mutationFn: () =>
      api.startRebuildEmbeddings({ source, match_ids: selection.matchIds }),
    onSuccess: onJobCreated,
  })

  const cleanupAllMutation = useMutation({
    mutationFn: () =>
      api.cleanupDownloadFiles({ datasets: cleanupDatasets, match_ids: [], delete_all: true }),
    onSuccess: (result) => setCleanupResult(result),
  })

  const clearJobsMutation = useMutation({
    mutationFn: api.clearJobs,
    onSuccess: () => {
      setSelectedJobId(null)
      setTerminalJobId(null)
      refreshJobs()
    },
  })

  const terminalLines = terminalJob?.logs ?? []

  return (
    <section className="grid gap-4 xl:grid-cols-[1.1fr_1fr]">
      {/* Left column: Pipeline */}
      <div className="space-y-4">
        {/* Match selection header */}
        <article className="rounded-2xl border border-white/10 bg-panel/70 p-5">
          <div className="flex items-center justify-between">
            <h2 className="text-2xl font-semibold text-ink">Pipeline de Ingesta</h2>
            <button
              type="button"
              onClick={() => {
                const refreshed = readCatalogSelection()
                setSelection(refreshed)
              }}
              className="rounded-lg border border-white/20 bg-white/5 px-3 py-1 text-xs text-ink"
            >
              Recargar selección
            </button>
          </div>
          <div className="mt-3 grid gap-2 text-sm md:grid-cols-3">
            <div className="rounded-lg border border-white/10 bg-canvas/60 px-3 py-2">
              <p className="text-xs text-mute">Source</p>
              <p className="font-medium capitalize text-ink">{source}</p>
            </div>
            <div className="rounded-lg border border-white/10 bg-canvas/60 px-3 py-2">
              <p className="text-xs text-mute">Competition / Season</p>
              <p className="font-medium text-ink">{selection.competitionId ?? '-'} / {selection.seasonId ?? '-'}</p>
            </div>
            <div className="rounded-lg border border-white/10 bg-canvas/60 px-3 py-2">
              <p className="text-xs text-mute">Matches</p>
              <p className="font-medium text-ink">{selection.matchIds.length > 0 ? `${selection.matchIds.length} selected` : 'none'}</p>
            </div>
          </div>
        </article>

        {/* Step 1: Download */}
        <PipelineStep
          step={1}
          title="Download"
          description="Download match data from StatsBomb Open Data to local storage."
          actionLabel="Download"
          onAction={() => downloadMutation.mutate()}
          isPending={downloadMutation.isPending}
          error={downloadMutation.isError ? asErrorMessage(downloadMutation.error) : null}
          disabled={downloadDatasets.length === 0}
        >
          <DatasetCheckboxes datasets={downloadDatasets} toggle={(d) => toggleDataset(d, downloadDatasets, setDownloadDatasets)} prefix="dl" />
        </PipelineStep>

        {/* Step 2: Load */}
        <PipelineStep
          step={2}
          title="Load"
          description={`Load downloaded JSON files into ${source} database.`}
          actionLabel="Load"
          onAction={() => loadMutation.mutate()}
          isPending={loadMutation.isPending}
          error={loadMutation.isError ? asErrorMessage(loadMutation.error) : null}
          disabled={loadDatasets.length === 0}
        >
          <DatasetCheckboxes datasets={loadDatasets} toggle={(d) => toggleDataset(d, loadDatasets, setLoadDatasets)} prefix="ld" />
        </PipelineStep>

        {/* Step 3: Aggregate */}
        <PipelineStep
          step={3}
          title="Aggregate"
          description="Build 15-second bucket aggregations from raw events."
          actionLabel="Aggregate"
          onAction={() => aggregateMutation.mutate()}
          isPending={aggregateMutation.isPending}
          error={aggregateMutation.isError ? asErrorMessage(aggregateMutation.error) : null}
        />

        {/* Step 4: Summaries */}
        <PipelineStep
          step={4}
          title="Summaries"
          description="Generate narrative summaries for each 15-second bucket using the LLM. Requires OpenAI key."
          actionLabel="Generate summaries"
          onAction={() => summariesMutation.mutate()}
          isPending={summariesMutation.isPending}
          error={summariesMutation.isError ? asErrorMessage(summariesMutation.error) : null}
        />

        {/* Step 5: Embeddings */}
        <PipelineStep
          step={5}
          title="Embeddings"
          description="Create vector embeddings (text-embedding-3-small, 1536 dims) for each summary. Requires OpenAI key."
          actionLabel="Generate embeddings"
          onAction={() => embeddingsMutation.mutate()}
          isPending={embeddingsMutation.isPending}
          error={embeddingsMutation.isError ? asErrorMessage(embeddingsMutation.error) : null}
        />

        {/* Terminal */}
        <div className="rounded-2xl border border-white/10 bg-panel/70 p-4">
          <p className="mb-2 text-xs uppercase tracking-[0.2em] text-mute">Terminal</p>
          <div className="max-h-56 overflow-auto rounded-lg bg-black/80 p-3 font-mono text-xs leading-5 text-emerald-300">
            {terminalLines.length > 0 ? (
              terminalLines.map((line, idx) => <p key={`${idx}-${line}`}>{line}</p>)
            ) : (
              <p className="text-slate-400">Run any pipeline step to see logs here.</p>
            )}
          </div>
        </div>

        {/* Cleanup (collapsible) */}
        <details className="rounded-2xl border border-white/10 bg-panel/70 p-4">
          <summary className="cursor-pointer text-sm font-semibold text-mute hover:text-ink">
            Cleanup downloaded files
          </summary>
          <div className="mt-3 space-y-2">
            <DatasetCheckboxes datasets={cleanupDatasets} toggle={(d) => toggleDataset(d, cleanupDatasets, setCleanupDatasets)} prefix="cl" />
            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => cleanupAllMutation.mutate()}
                disabled={cleanupAllMutation.isPending || cleanupDatasets.length === 0}
                className="rounded-xl border border-rose-400/40 bg-rose-500/10 px-3 py-2 text-xs font-semibold text-rose-300 disabled:opacity-60"
              >
                Delete all downloaded files
              </button>
            </div>
            {cleanupAllMutation.isError ? <p className="text-sm text-rose-300">{asErrorMessage(cleanupAllMutation.error)}</p> : null}
            {cleanupResult ? (
              <p className="text-xs text-mute">Deleted: {cleanupResult.deleted_count} items</p>
            ) : null}
          </div>
        </details>
      </div>

      {/* Right column: Jobs */}
      <article className="space-y-4 rounded-2xl border border-white/10 bg-panel/70 p-5">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-ink">Jobs</h3>
          <div className="flex gap-2">
            <button type="button" onClick={refreshJobs} className="rounded-lg border border-white/20 bg-white/5 px-3 py-1 text-xs text-ink">
              Refresh
            </button>
            <button
              type="button"
              onClick={() => clearJobsMutation.mutate()}
              disabled={clearJobsMutation.isPending}
              className="rounded-lg border border-rose-400/40 bg-rose-500/10 px-3 py-1 text-xs text-rose-300 disabled:opacity-60"
            >
              Clear
            </button>
          </div>
        </div>

        {jobsQuery.isLoading ? <p className="text-mute">Loading jobs...</p> : null}
        {jobsQuery.isError ? <p className="text-rose-300">Failed to load jobs.</p> : null}

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
              {(jobsQuery.data?.items ?? []).map((job) => (
                <tr
                  key={job.id}
                  onClick={() => setActiveJob(job)}
                  className={`cursor-pointer transition hover:bg-white/5 ${selectedJobId === job.id ? 'bg-accent/10' : ''}`}
                >
                  <td className="px-3 py-2 text-ink">{job.type}</td>
                  <td className="px-3 py-2 text-mute">{job.status}</td>
                  <td className="px-3 py-2 text-mute">{job.total > 0 ? `${job.progress}/${job.total}` : String(job.progress)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {selectedJob ? (
          <div className="rounded-xl border border-white/10 bg-canvas/60 p-4 text-sm">
            <p className="text-mute">Job ID</p>
            <p className="break-all text-ink">{selectedJob.id}</p>
            <p className="mt-2 text-mute">Status</p>
            <p className="text-ink">{selectedJob.status}</p>
            <p className="mt-2 text-mute">Message</p>
            <p className="text-ink">{selectedJob.message}</p>
            {selectedJob.error ? (
              <>
                <p className="mt-2 text-mute">Error</p>
                <p className="text-rose-300">{selectedJob.error}</p>
              </>
            ) : null}
            {selectedJob.result ? (
              <>
                <p className="mt-2 text-mute">Result</p>
                <pre className="mt-1 overflow-auto rounded bg-black/30 p-2 text-xs text-slate-100">
                  {JSON.stringify(selectedJob.result, null, 2)}
                </pre>
              </>
            ) : null}
          </div>
        ) : null}
      </article>
    </section>
  )
}

// ---------------------------------------------------------------------------
// Pipeline step card component
// ---------------------------------------------------------------------------

function PipelineStep({
  step,
  title,
  description,
  actionLabel,
  onAction,
  isPending,
  error,
  disabled,
  children,
}: {
  step: number
  title: string
  description: string
  actionLabel: string
  onAction: () => void
  isPending: boolean
  error: string | null
  disabled?: boolean
  children?: React.ReactNode
}) {
  return (
    <article className="rounded-2xl border border-white/10 bg-panel/70 p-4">
      <div className="flex items-start gap-3">
        <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-accent/15 text-sm font-bold text-accent">
          {step}
        </span>
        <div className="flex-1">
          <h3 className="text-sm font-semibold text-ink">{title}</h3>
          <p className="mt-1 text-xs text-mute">{description}</p>
          {children ? <div className="mt-2">{children}</div> : null}
          <div className="mt-3 flex items-center gap-3">
            <button
              type="button"
              onClick={onAction}
              disabled={isPending || disabled}
              className="rounded-xl border border-accent/50 bg-accent/15 px-4 py-2 text-sm font-semibold text-accent disabled:opacity-60"
            >
              {isPending ? 'Running...' : actionLabel}
            </button>
          </div>
          {error ? <p className="mt-2 text-sm text-rose-300">{error}</p> : null}
        </div>
      </div>
    </article>
  )
}

// ---------------------------------------------------------------------------
// Dataset checkboxes component
// ---------------------------------------------------------------------------

function DatasetCheckboxes({
  datasets,
  toggle,
  prefix,
}: {
  datasets: string[]
  toggle: (d: string) => void
  prefix: string
}) {
  return (
    <div className="flex flex-wrap gap-2">
      {AVAILABLE_DATASETS.map((dataset) => (
        <label key={`${prefix}-${dataset}`} className="flex items-center gap-2 rounded-lg border border-white/10 px-2 py-1 text-xs">
          <input type="checkbox" checked={datasets.includes(dataset)} onChange={() => toggle(dataset)} />
          {dataset}
        </label>
      ))}
    </div>
  )
}
