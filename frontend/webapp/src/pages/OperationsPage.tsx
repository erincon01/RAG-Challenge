import { useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { api, ApiError } from '../lib/api/client'
import type { DownloadCleanupResponse, JobRecord, MatchPipelineStatus } from '../lib/api/types'
import { readCatalogSelection } from '../lib/storage/catalogSelection'
import { useUISettings } from '../state/ui-settings'

const AVAILABLE_DATASETS = ['matches', 'lineups', 'events'] as const
const TERMINAL_JOB_TYPES = new Set(['download', 'load', 'aggregate', 'summaries_generate', 'embeddings_rebuild'])

function asErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    const detail = (error.detail as { detail?: string } | null)?.detail
    return detail ? `${error.message}: ${detail}` : error.message
  }
  if (error instanceof Error) return error.message
  return 'Unknown error'
}

export function OperationsPage() {
  const { source } = useUISettings()
  const queryClient = useQueryClient()

  const initialSelection = readCatalogSelection()
  const [selection, setSelection] = useState(initialSelection)

  const [downloadDatasets, setDownloadDatasets] = useState<string[]>(['matches', 'events'])
  const [loadDatasets, setLoadDatasets] = useState<string[]>(['matches', 'events'])
  const [selectedMatchIds, setSelectedMatchIds] = useState<number[]>([])
  const [cleanupDatasets, setCleanupDatasets] = useState<string[]>(['matches', 'lineups', 'events'])
  const [cleanupResult, setCleanupResult] = useState<DownloadCleanupResponse | null>(null)
  const [selectedJobId, setSelectedJobId] = useState<string | null>(null)
  const [terminalJobId, setTerminalJobId] = useState<string | null>(null)

  // Pipeline status query
  const pipelineQuery = useQuery({
    queryKey: ['pipeline-status', source],
    queryFn: () => api.getPipelineStatus(source),
    refetchInterval: 5000,
  })

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
    return jobsQuery.data.items.find((j) => j.id === selectedJobId) ?? null
  }, [jobsQuery.data, selectedJobId, selectedJobQuery.data])

  const terminalJob = useMemo(() => {
    if (terminalJobQuery.data) return terminalJobQuery.data
    if (!terminalJobId || !jobsQuery.data) return null
    return jobsQuery.data.items.find((j) => j.id === terminalJobId) ?? null
  }, [jobsQuery.data, terminalJobId, terminalJobQuery.data])

  const refreshJobs = () => {
    void queryClient.invalidateQueries({ queryKey: ['jobs-list'] })
    void queryClient.invalidateQueries({ queryKey: ['pipeline-status'] })
  }

  const onJobCreated = (response: { job_id: string }) => {
    setSelectedJobId(response.job_id)
    setTerminalJobId(response.job_id)
    refreshJobs()
  }

  const toggleDataset = (d: string, cur: string[], set: (v: string[]) => void) => {
    set(cur.includes(d) ? cur.filter((x) => x !== d) : [...cur, d])
  }

  const toggleMatch = (matchId: number) => {
    setSelectedMatchIds((cur) =>
      cur.includes(matchId) ? cur.filter((id) => id !== matchId) : [...cur, matchId],
    )
  }

  const toggleAllMatches = () => {
    const all = (pipelineQuery.data ?? []).map((m) => m.match_id)
    setSelectedMatchIds((cur) => (cur.length === all.length ? [] : all))
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
      api.startAggregate({ source, match_ids: selectedMatchIds }),
    onSuccess: onJobCreated,
  })

  const summariesMutation = useMutation({
    mutationFn: () =>
      api.startGenerateSummaries({ source, match_ids: selectedMatchIds }),
    onSuccess: onJobCreated,
  })

  const embeddingsMutation = useMutation({
    mutationFn: () =>
      api.startRebuildEmbeddings({ source, match_ids: selectedMatchIds }),
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
      <div className="space-y-4">
        {/* Header */}
        <article className="rounded-2xl border border-white/10 bg-panel/70 p-5">
          <h2 className="text-2xl font-semibold text-ink">Pipeline de Ingesta</h2>
          <p className="mt-1 text-xs text-mute">
            Source: <span className="font-semibold capitalize text-ink">{source}</span>
          </p>
        </article>

        {/* Step 1: Download (uses catalog selection) */}
        <PipelineStep step={1} title="Download" description="Download match data from StatsBomb to local storage.">
          <div className="mb-2 flex items-center gap-2">
            <button
              type="button"
              onClick={() => setSelection(readCatalogSelection())}
              className="rounded-lg border border-white/10 px-2 py-1 text-xs text-mute hover:text-ink"
            >
              Reload catalog selection
            </button>
            <span className="text-xs text-mute">
              {selection.matchIds.length > 0 ? `${selection.matchIds.length} matches from catalog` : 'No matches selected in catalog'}
            </span>
          </div>
          <DatasetCheckboxes datasets={downloadDatasets} toggle={(d) => toggleDataset(d, downloadDatasets, setDownloadDatasets)} prefix="dl" />
          <ActionButton label="Download" onClick={() => downloadMutation.mutate()} isPending={downloadMutation.isPending} disabled={downloadDatasets.length === 0 || selection.matchIds.length === 0} />
          {downloadMutation.isError ? <p className="mt-1 text-sm text-rose-300">{asErrorMessage(downloadMutation.error)}</p> : null}
        </PipelineStep>

        {/* Step 2: Load (uses catalog selection) */}
        <PipelineStep step={2} title="Load" description={`Load downloaded JSON files into ${source} database.`}>
          <DatasetCheckboxes datasets={loadDatasets} toggle={(d) => toggleDataset(d, loadDatasets, setLoadDatasets)} prefix="ld" />
          <ActionButton label="Load" onClick={() => loadMutation.mutate()} isPending={loadMutation.isPending} disabled={loadDatasets.length === 0 || selection.matchIds.length === 0} />
          {loadMutation.isError ? <p className="mt-1 text-sm text-rose-300">{asErrorMessage(loadMutation.error)}</p> : null}
        </PipelineStep>

        {/* Match status table (for steps 3-5) */}
        <article className="rounded-2xl border border-white/10 bg-panel/70 p-4">
          <div className="mb-3 flex items-center justify-between">
            <h3 className="text-sm font-semibold text-ink">Matches in {source} — select for steps 3-5</h3>
            <span className="text-xs text-mute">{selectedMatchIds.length} selected</span>
          </div>
          {pipelineQuery.isLoading ? <p className="text-xs text-mute">Loading...</p> : null}
          {pipelineQuery.data && pipelineQuery.data.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-white/10 text-xs">
                <thead>
                  <tr className="text-left text-mute">
                    <th className="px-2 py-1">
                      <input type="checkbox" checked={selectedMatchIds.length === pipelineQuery.data.length} onChange={toggleAllMatches} />
                    </th>
                    <th className="px-2 py-1">Match</th>
                    <th className="px-2 py-1 text-right">Events</th>
                    <th className="px-2 py-1 text-right">Agg</th>
                    <th className="px-2 py-1 text-right">Summ</th>
                    <th className="px-2 py-1 text-right">Emb</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5">
                  {pipelineQuery.data.map((m) => (
                    <tr key={m.match_id} className={selectedMatchIds.includes(m.match_id) ? 'bg-accent/10' : ''}>
                      <td className="px-2 py-1">
                        <input type="checkbox" checked={selectedMatchIds.includes(m.match_id)} onChange={() => toggleMatch(m.match_id)} />
                      </td>
                      <td className="px-2 py-1 text-ink">{m.display_name}</td>
                      <td className="px-2 py-1 text-right text-mute">{m.events_count}</td>
                      <td className="px-2 py-1 text-right">{m.agg_count > 0 ? <span className="text-emerald-400">{m.agg_count}</span> : <span className="text-mute">0</span>}</td>
                      <td className="px-2 py-1 text-right">{m.summary_count > 0 ? <span className="text-emerald-400">{m.summary_count}</span> : <span className="text-mute">0</span>}</td>
                      <td className="px-2 py-1 text-right">{m.embedding_count > 0 ? <span className="text-emerald-400">{m.embedding_count}</span> : <span className="text-mute">0</span>}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : pipelineQuery.data?.length === 0 ? (
            <p className="text-xs text-mute">No matches loaded in {source}. Run Download + Load first.</p>
          ) : null}
        </article>

        {/* Step 3: Aggregate */}
        <PipelineStep step={3} title="Aggregate" description="Build 15-second bucket aggregations from raw events.">
          <ActionButton label="Aggregate" onClick={() => aggregateMutation.mutate()} isPending={aggregateMutation.isPending} disabled={selectedMatchIds.length === 0} />
          {aggregateMutation.isError ? <p className="mt-1 text-sm text-rose-300">{asErrorMessage(aggregateMutation.error)}</p> : null}
        </PipelineStep>

        {/* Step 4: Summaries */}
        <PipelineStep step={4} title="Summaries" description="Generate narrative summaries per 15-second bucket using LLM. Requires OpenAI key.">
          <ActionButton label="Generate summaries" onClick={() => summariesMutation.mutate()} isPending={summariesMutation.isPending} disabled={selectedMatchIds.length === 0} />
          {summariesMutation.isError ? <p className="mt-1 text-sm text-rose-300">{asErrorMessage(summariesMutation.error)}</p> : null}
        </PipelineStep>

        {/* Step 5: Embeddings */}
        <PipelineStep step={5} title="Embeddings" description="Create vector embeddings (text-embedding-3-small, 1536 dims) for each summary. Requires OpenAI key.">
          <ActionButton label="Generate embeddings" onClick={() => embeddingsMutation.mutate()} isPending={embeddingsMutation.isPending} disabled={selectedMatchIds.length === 0} />
          {embeddingsMutation.isError ? <p className="mt-1 text-sm text-rose-300">{asErrorMessage(embeddingsMutation.error)}</p> : null}
        </PipelineStep>

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
          <summary className="cursor-pointer text-sm font-semibold text-mute hover:text-ink">Cleanup downloaded files</summary>
          <div className="mt-3 space-y-2">
            <DatasetCheckboxes datasets={cleanupDatasets} toggle={(d) => toggleDataset(d, cleanupDatasets, setCleanupDatasets)} prefix="cl" />
            <button type="button" onClick={() => cleanupAllMutation.mutate()} disabled={cleanupAllMutation.isPending} className="rounded-xl border border-rose-400/40 bg-rose-500/10 px-3 py-2 text-xs font-semibold text-rose-300 disabled:opacity-60">
              Delete all downloaded files
            </button>
            {cleanupResult ? <p className="text-xs text-mute">Deleted: {cleanupResult.deleted_count} items</p> : null}
          </div>
        </details>
      </div>

      {/* Right: Jobs */}
      <article className="space-y-4 rounded-2xl border border-white/10 bg-panel/70 p-5">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-ink">Jobs</h3>
          <div className="flex gap-2">
            <button type="button" onClick={refreshJobs} className="rounded-lg border border-white/20 bg-white/5 px-3 py-1 text-xs text-ink">Refresh</button>
            <button type="button" onClick={() => clearJobsMutation.mutate()} disabled={clearJobsMutation.isPending} className="rounded-lg border border-rose-400/40 bg-rose-500/10 px-3 py-1 text-xs text-rose-300 disabled:opacity-60">Clear</button>
          </div>
        </div>
        {jobsQuery.isLoading ? <p className="text-mute">Loading jobs...</p> : null}
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
                <tr key={job.id} onClick={() => setActiveJob(job)} className={`cursor-pointer transition hover:bg-white/5 ${selectedJobId === job.id ? 'bg-accent/10' : ''}`}>
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
            <p className="mt-2 text-mute">Message</p>
            <p className="text-ink">{selectedJob.message}</p>
            {selectedJob.error ? <><p className="mt-2 text-mute">Error</p><p className="text-rose-300">{selectedJob.error}</p></> : null}
            {selectedJob.result ? <><p className="mt-2 text-mute">Result</p><pre className="mt-1 overflow-auto rounded bg-black/30 p-2 text-xs text-slate-100">{JSON.stringify(selectedJob.result, null, 2)}</pre></> : null}
          </div>
        ) : null}
      </article>
    </section>
  )
}

function PipelineStep({ step, title, description, children }: { step: number; title: string; description: string; children: React.ReactNode }) {
  return (
    <article className="rounded-2xl border border-white/10 bg-panel/70 p-4">
      <div className="flex items-start gap-3">
        <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-accent/15 text-sm font-bold text-accent">{step}</span>
        <div className="flex-1">
          <h3 className="text-sm font-semibold text-ink">{title}</h3>
          <p className="mt-1 text-xs text-mute">{description}</p>
          <div className="mt-2">{children}</div>
        </div>
      </div>
    </article>
  )
}

function ActionButton({ label, onClick, isPending, disabled }: { label: string; onClick: () => void; isPending: boolean; disabled?: boolean }) {
  return (
    <button type="button" onClick={onClick} disabled={isPending || disabled} className="mt-2 rounded-xl border border-accent/50 bg-accent/15 px-4 py-2 text-sm font-semibold text-accent disabled:opacity-60">
      {isPending ? 'Running...' : label}
    </button>
  )
}

function DatasetCheckboxes({ datasets, toggle, prefix }: { datasets: string[]; toggle: (d: string) => void; prefix: string }) {
  return (
    <div className="flex flex-wrap gap-2">
      {AVAILABLE_DATASETS.map((d) => (
        <label key={`${prefix}-${d}`} className="flex items-center gap-2 rounded-lg border border-white/10 px-2 py-1 text-xs">
          <input type="checkbox" checked={datasets.includes(d)} onChange={() => toggle(d)} />
          {d}
        </label>
      ))}
    </div>
  )
}
