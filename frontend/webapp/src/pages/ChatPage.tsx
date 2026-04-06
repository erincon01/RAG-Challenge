import { useEffect, useMemo, useState, type FormEvent } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'

import { api, ApiError } from '../lib/api/client'
import type { SearchRequestPayload } from '../lib/api/types'
import { useUISettings } from '../state/ui-settings'

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

export function ChatPage() {
  const { source, mode } = useUISettings()

  const [selectedMatchId, setSelectedMatchId] = useState<number | null>(null)
  const [question, setQuestion] = useState('')
  const [algorithm, setAlgorithm] = useState('cosine')
  const [embeddingModel, setEmbeddingModel] = useState('text-embedding-3-small')
  const [topN, setTopN] = useState(10)
  const [temperature, setTemperature] = useState(0.1)

  const capabilitiesQuery = useQuery({
    queryKey: ['chat-capabilities', source],
    queryFn: api.getCapabilities,
  })

  const matchesQuery = useQuery({
    queryKey: ['chat-matches', source],
    queryFn: () => api.listMatches(source, 250),
  })

  const capabilities = useMemo(() => {
    if (!capabilitiesQuery.data) {
      return null
    }
    return capabilitiesQuery.data.capabilities[source]
  }, [capabilitiesQuery.data, source])

  useEffect(() => {
    if (!matchesQuery.data || matchesQuery.data.length === 0) {
      setSelectedMatchId(null)
      return
    }

    if (selectedMatchId === null) {
      setSelectedMatchId(matchesQuery.data[0].match_id)
      return
    }

    if (!matchesQuery.data.some((match) => match.match_id === selectedMatchId)) {
      setSelectedMatchId(matchesQuery.data[0].match_id)
    }
  }, [matchesQuery.data, selectedMatchId])

  useEffect(() => {
    if (!capabilities) {
      return
    }
    if (!capabilities.embedding_models.includes(embeddingModel)) {
      setEmbeddingModel(capabilities.embedding_models[0])
    }
    if (!capabilities.search_algorithms.includes(algorithm)) {
      setAlgorithm(capabilities.search_algorithms[0])
    }
  }, [capabilities, embeddingModel, algorithm])

  const searchMutation = useMutation({
    mutationFn: (payload: SearchRequestPayload) => api.search(source, payload),
  })

  const submit = (event: FormEvent) => {
    event.preventDefault()
    if (!selectedMatchId || !question.trim()) {
      return
    }

    const payload: SearchRequestPayload = {
      match_id: selectedMatchId,
      query: question.trim(),
      include_match_info: true,
      language: 'spanish',
      search_algorithm: algorithm,
      embedding_model: embeddingModel,
      top_n: topN,
      temperature,
    }

    searchMutation.mutate(payload)
  }

  return (
    <section className="grid gap-4 xl:grid-cols-[1.1fr_1fr]">
      <article className="space-y-4 rounded-2xl border border-white/10 bg-panel/70 p-5">
        <h2 className="text-2xl font-semibold text-ink">Chat RAG</h2>
        <p className="text-sm text-mute">
          Source: <span className="font-semibold capitalize text-ink">{source}</span> | Mode:{' '}
          <span className="font-semibold capitalize text-ink">{mode}</span>
        </p>

        <form className="space-y-3" onSubmit={submit}>
          <label className="block text-sm text-mute">
            Match
            <select
              value={selectedMatchId ?? ''}
              onChange={(event) => setSelectedMatchId(event.target.value ? Number(event.target.value) : null)}
              className="mt-1 w-full rounded-xl border border-white/10 bg-canvas/80 px-3 py-2 text-ink"
            >
              {(matchesQuery.data ?? []).map((match) => (
                <option key={match.match_id} value={match.match_id}>
                  {match.match_id} | {match.display_name}
                </option>
              ))}
            </select>
          </label>

          <label className="block text-sm text-mute">
            Pregunta
            <textarea
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
              placeholder="Ejemplo: ¿Quién dominó la segunda parte?"
              className="mt-1 min-h-28 w-full rounded-xl border border-white/10 bg-canvas/80 px-3 py-2 text-ink"
            />
          </label>

          {mode === 'developer' && capabilities ? (
            <div className="grid gap-3 rounded-xl border border-white/10 bg-canvas/60 p-4 md:grid-cols-2">
              <label className="text-sm text-mute">
                Embedding model
                <select
                  value={embeddingModel}
                  onChange={(event) => setEmbeddingModel(event.target.value)}
                  className="mt-1 w-full rounded-lg border border-white/10 bg-canvas/80 px-3 py-2 text-ink"
                >
                  {capabilities.embedding_models.map((model) => (
                    <option key={model} value={model}>
                      {model}
                    </option>
                  ))}
                </select>
              </label>

              <label className="text-sm text-mute">
                Algorithm
                <select
                  value={algorithm}
                  onChange={(event) => setAlgorithm(event.target.value)}
                  className="mt-1 w-full rounded-lg border border-white/10 bg-canvas/80 px-3 py-2 text-ink"
                >
                  {capabilities.search_algorithms.map((alg) => (
                    <option key={alg} value={alg}>
                      {alg}
                    </option>
                  ))}
                </select>
              </label>

              <label className="text-sm text-mute">
                Top N
                <input
                  type="number"
                  min={1}
                  max={100}
                  value={topN}
                  onChange={(event) => setTopN(Number(event.target.value))}
                  className="mt-1 w-full rounded-lg border border-white/10 bg-canvas/80 px-3 py-2 text-ink"
                />
              </label>

              <label className="text-sm text-mute">
                Temperature
                <input
                  type="number"
                  min={0}
                  max={2}
                  step={0.1}
                  value={temperature}
                  onChange={(event) => setTemperature(Number(event.target.value))}
                  className="mt-1 w-full rounded-lg border border-white/10 bg-canvas/80 px-3 py-2 text-ink"
                />
              </label>
            </div>
          ) : null}

          <button
            type="submit"
            disabled={searchMutation.isPending || !selectedMatchId || !question.trim()}
            className="rounded-xl border border-accent/50 bg-accent/15 px-4 py-2 text-sm font-semibold text-accent disabled:opacity-60"
          >
            Ejecutar búsqueda semántica
          </button>

          {searchMutation.isError ? <p className="text-sm text-rose-300">{asErrorMessage(searchMutation.error)}</p> : null}
        </form>
      </article>

      <article className="space-y-4 rounded-2xl border border-white/10 bg-panel/70 p-5">
        <h3 className="text-lg font-semibold text-ink">Respuesta</h3>

        {searchMutation.isPending ? <p className="text-mute">Consultando contexto y generando respuesta...</p> : null}

        {searchMutation.data ? (
          <>
            <div className="rounded-xl border border-white/10 bg-canvas/60 p-4">
              <p className="whitespace-pre-wrap text-sm leading-6 text-ink">{searchMutation.data.answer}</p>
            </div>

            <div className="space-y-2">
              <p className="text-sm font-semibold text-ink">Contexto recuperado</p>
              <ul className="space-y-2">
                {searchMutation.data.search_results.map((item) => (
                  <li key={`${item.rank}-${item.event.id}`} className="rounded-lg border border-white/10 bg-canvas/60 p-3">
                    <p className="text-xs text-mute">
                      Rank {item.rank} | Score {item.similarity_score.toFixed(4)} | {item.event.time_description}
                    </p>
                    <p className="mt-1 text-sm text-ink">{item.event.summary ?? '-'}</p>
                  </li>
                ))}
              </ul>
            </div>

            {mode === 'developer' ? (
              <details className="rounded-xl border border-white/10 bg-canvas/60 p-3 text-xs text-mute">
                <summary className="cursor-pointer font-semibold text-ink">Metadata</summary>
                <pre className="mt-2 overflow-auto">{JSON.stringify(searchMutation.data.metadata, null, 2)}</pre>
              </details>
            ) : null}
          </>
        ) : (
          <p className="text-mute">Lanza una consulta para ver la respuesta aquí.</p>
        )}
      </article>
    </section>
  )
}
