import { useEffect, useMemo, useState } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'

import { api, ApiError } from '../lib/api/client'
import { useUISettings } from '../state/ui-settings'

function renderError(error: unknown) {
  if (error instanceof ApiError) {
    const detail = (error.detail as { detail?: string } | null)?.detail
    return detail ? `${error.message}: ${detail}` : error.message
  }
  if (error instanceof Error) {
    return error.message
  }
  return 'Unknown error'
}

export function EmbeddingsPage() {
  const { source } = useUISettings()

  const [selectedMatchId, setSelectedMatchId] = useState<number | null>(null)
  const [selectedModels, setSelectedModels] = useState<string[]>([])
  const [jobId, setJobId] = useState<string | null>(null)

  const statusQuery = useQuery({
    queryKey: ['embeddings-status', source],
    queryFn: () => api.getEmbeddingsStatus(source),
    refetchInterval: 7000,
  })

  const capabilitiesQuery = useQuery({
    queryKey: ['embeddings-capabilities', source],
    queryFn: api.getCapabilities,
  })

  const matchesQuery = useQuery({
    queryKey: ['embeddings-matches', source],
    queryFn: () => api.listMatches(source, 250),
  })

  const jobQuery = useQuery({
    queryKey: ['embeddings-job', jobId],
    queryFn: () => api.getJob(jobId as string),
    enabled: jobId !== null,
    refetchInterval: 2500,
  })

  const availableModels = useMemo(() => {
    if (!capabilitiesQuery.data) {
      return []
    }
    return capabilitiesQuery.data.capabilities[source].embedding_models
  }, [capabilitiesQuery.data, source])

  useEffect(() => {
    if (availableModels.length === 0) {
      setSelectedModels([])
      return
    }

    setSelectedModels((current) => {
      const filtered = current.filter((model) => availableModels.includes(model))
      if (filtered.length > 0) {
        return filtered
      }
      return [availableModels[0]]
    })
  }, [availableModels])

  const mutation = useMutation({
    mutationFn: () =>
      api.startRebuildEmbeddings({
        source,
        match_ids: selectedMatchId ? [selectedMatchId] : [],
        embedding_models: selectedModels,
      }),
    onSuccess: (result) => {
      setJobId(result.job_id)
    },
  })

  const toggleModel = (model: string) => {
    setSelectedModels((current) =>
      current.includes(model) ? current.filter((item) => item !== model) : [...current, model],
    )
  }

  if (statusQuery.isLoading) {
    return <p className="text-mute">Cargando estado de embeddings...</p>
  }

  if (statusQuery.isError || !statusQuery.data) {
    return <p className="text-rose-300">No se pudo consultar el estado de embeddings para {source}.</p>
  }

  const totalRows = statusQuery.data.total_rows

  return (
    <section className="grid gap-4 xl:grid-cols-[1.1fr_1fr]">
      <article className="space-y-4 rounded-2xl border border-white/10 bg-panel/70 p-5">
        <h2 className="text-2xl font-semibold text-ink">Embeddings</h2>
        <p className="text-sm text-mute">
          Source activo: <span className="font-semibold capitalize text-ink">{source}</span>
        </p>

        <div className="rounded-xl border border-white/10 bg-canvas/60 p-4">
          <p className="text-sm text-mute">Tabla</p>
          <p className="text-ink">{statusQuery.data.table}</p>
          <p className="mt-3 text-sm text-mute">Filas totales</p>
          <p className="text-ink">{totalRows}</p>
        </div>

        <div className="space-y-3 rounded-xl border border-white/10 bg-canvas/60 p-4">
          <p className="text-sm font-semibold text-ink">Cobertura por modelo</p>
          <div className="grid gap-3 md:grid-cols-2">
            {Object.entries(statusQuery.data.coverage).map(([model, covered]) => {
              const pct = totalRows > 0 ? ((covered / totalRows) * 100).toFixed(1) : '0.0'
              return (
                <article key={model} className="rounded-xl border border-white/10 bg-black/20 p-3">
                  <p className="text-xs uppercase tracking-[0.2em] text-mute">{model}</p>
                  <p className="text-xl font-semibold text-ink">{covered}</p>
                  <p className="text-xs text-mute">{pct}% cobertura</p>
                </article>
              )
            })}
          </div>
        </div>
      </article>

      <article className="space-y-4 rounded-2xl border border-white/10 bg-panel/70 p-5">
        <h3 className="text-lg font-semibold text-ink">Rebuild manual</h3>

        <label className="block text-sm text-mute">
          Match (opcional)
          <select
            value={selectedMatchId ?? ''}
            onChange={(event) => setSelectedMatchId(event.target.value ? Number(event.target.value) : null)}
            className="mt-1 w-full rounded-xl border border-white/10 bg-canvas/80 px-3 py-2 text-ink"
          >
            <option value="">Todos los partidos</option>
            {(matchesQuery.data ?? []).map((match) => (
              <option key={match.match_id} value={match.match_id}>
                {match.match_id} | {match.display_name}
              </option>
            ))}
          </select>
        </label>

        <div className="space-y-2">
          <p className="text-sm text-mute">Modelos soportados para {source}</p>
          <div className="flex flex-wrap gap-2">
            {availableModels.map((model) => (
              <label key={model} className="flex items-center gap-2 rounded-lg border border-white/10 px-3 py-2 text-sm">
                <input
                  type="checkbox"
                  checked={selectedModels.includes(model)}
                  onChange={() => toggleModel(model)}
                />
                {model}
              </label>
            ))}
          </div>
        </div>

        <button
          type="button"
          onClick={() => mutation.mutate()}
          disabled={mutation.isPending || selectedModels.length === 0}
          className="rounded-xl border border-accent/50 bg-accent/15 px-4 py-2 text-sm font-semibold text-accent disabled:opacity-60"
        >
          Ejecutar rebuild
        </button>

        {mutation.isError ? <p className="text-sm text-rose-300">{renderError(mutation.error)}</p> : null}

        {jobQuery.data ? (
          <div className="rounded-xl border border-white/10 bg-canvas/60 p-4 text-sm">
            <p className="text-mute">Job ID</p>
            <p className="break-all text-ink">{jobQuery.data.id}</p>
            <p className="mt-2 text-mute">Status</p>
            <p className="text-ink">{jobQuery.data.status}</p>
            <p className="mt-2 text-mute">Progress</p>
            <p className="text-ink">
              {jobQuery.data.progress}/{jobQuery.data.total}
            </p>
            <p className="mt-2 text-mute">Message</p>
            <p className="text-ink">{jobQuery.data.message}</p>
          </div>
        ) : null}
      </article>
    </section>
  )
}
