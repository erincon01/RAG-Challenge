import { useEffect, useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'

import { api } from '../lib/api/client'
import { readCatalogSelection, writeCatalogSelection } from '../lib/storage/catalogSelection'

export function CatalogPage() {
  const initialSelection = readCatalogSelection()
  const [competitionId, setCompetitionId] = useState<number | null>(initialSelection.competitionId)
  const [seasonId, setSeasonId] = useState<number | null>(initialSelection.seasonId)
  const [selectedMatchIds, setSelectedMatchIds] = useState<number[]>(initialSelection.matchIds)

  const competitionsQuery = useQuery({
    queryKey: ['statsbomb-competitions'],
    queryFn: api.listStatsBombCompetitions,
  })

  const matchesQuery = useQuery({
    queryKey: ['statsbomb-matches', competitionId, seasonId],
    queryFn: () => api.listStatsBombMatches(competitionId as number, seasonId as number),
    enabled: competitionId !== null && seasonId !== null,
  })

  useEffect(() => {
    writeCatalogSelection({
      competitionId,
      seasonId,
      matchIds: selectedMatchIds,
    })
  }, [competitionId, seasonId, selectedMatchIds])

  const selectedCatalogKey = useMemo(() => {
    if (competitionId === null || seasonId === null) {
      return ''
    }
    return `${competitionId}:${seasonId}`
  }, [competitionId, seasonId])

  const catalogOptions = competitionsQuery.data ?? []

  const toggleMatch = (matchId: number) => {
    setSelectedMatchIds((current) =>
      current.includes(matchId)
        ? current.filter((item) => item !== matchId)
        : [...current, matchId].sort((a, b) => a - b),
    )
  }

  const selectAllVisibleMatches = () => {
    const matchIds = (matchesQuery.data ?? []).map((match) => match.match_id)
    setSelectedMatchIds(matchIds)
  }

  const clearSelectedMatches = () => {
    setSelectedMatchIds([])
  }

  return (
    <section className="space-y-4">
      <header className="rounded-2xl border border-white/10 bg-panel/70 p-5">
        <h2 className="text-2xl font-semibold text-ink">Catalogo StatsBomb</h2>
        <p className="mt-1 text-sm text-mute">
          Selecciona competición y temporada para preparar descarga/carga. La selección queda guardada para la pantalla
          de operaciones.
        </p>

        <div className="mt-4 grid gap-3 md:grid-cols-[1fr_auto]">
          <select
            value={selectedCatalogKey}
            onChange={(event) => {
              if (!event.target.value) {
                setCompetitionId(null)
                setSeasonId(null)
                setSelectedMatchIds([])
                return
              }
              const [competition, season] = event.target.value.split(':').map((item) => Number(item))
              setCompetitionId(competition)
              setSeasonId(season)
              setSelectedMatchIds([])
            }}
            className="rounded-xl border border-white/10 bg-canvas/80 px-3 py-3 text-sm text-ink outline-none"
          >
            <option value="">Selecciona competición + temporada...</option>
            {catalogOptions.map((item) => (
              <option key={`${item.competition_id}-${item.season_id}`} value={`${item.competition_id}:${item.season_id}`}>
                {item.country_name ?? 'Unknown'} | {item.competition_name} | {item.season_name}
              </option>
            ))}
          </select>
          <div className="rounded-xl border border-white/10 bg-canvas/60 px-4 py-3 text-xs text-mute">
            <p>Competiciones: {catalogOptions.length}</p>
            <p>Partidos seleccionados: {selectedMatchIds.length}</p>
          </div>
        </div>
      </header>

      <article className="rounded-2xl border border-white/10 bg-panel/70 p-5">
        <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
          <h3 className="text-lg font-semibold text-ink">Partidos disponibles</h3>
          <div className="flex gap-2">
            <button
              type="button"
              onClick={selectAllVisibleMatches}
              className="rounded-xl border border-accent/40 bg-accent/10 px-3 py-2 text-xs font-semibold text-accent"
              disabled={!matchesQuery.data || matchesQuery.data.length === 0}
            >
              Seleccionar todos
            </button>
            <button
              type="button"
              onClick={clearSelectedMatches}
              className="rounded-xl border border-white/20 bg-white/5 px-3 py-2 text-xs font-semibold text-ink"
            >
              Limpiar
            </button>
          </div>
        </div>

        {competitionsQuery.isLoading && <p className="text-mute">Cargando catálogo de competiciones...</p>}
        {competitionsQuery.isError && (
          <p className="text-rose-300">No se pudo leer el catálogo de competiciones de StatsBomb.</p>
        )}

        {!competitionId || !seasonId ? (
          <p className="text-mute">Selecciona competición y temporada para ver los partidos.</p>
        ) : null}

        {competitionId && seasonId && matchesQuery.isLoading ? <p className="text-mute">Cargando partidos...</p> : null}
        {competitionId && seasonId && matchesQuery.isError ? (
          <p className="text-rose-300">No se pudieron cargar los partidos para esta competición.</p>
        ) : null}

        {matchesQuery.data && matchesQuery.data.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-white/10 text-sm">
              <thead>
                <tr className="text-left text-mute">
                  <th className="px-2 py-2">Select</th>
                  <th className="px-2 py-2">Match ID</th>
                  <th className="px-2 py-2">Date</th>
                  <th className="px-2 py-2">Home</th>
                  <th className="px-2 py-2">Away</th>
                  <th className="px-2 py-2">Score</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {matchesQuery.data.map((match) => {
                  const selected = selectedMatchIds.includes(match.match_id)
                  const homeTeam = String((match.home_team?.home_team_name ?? match.home_team?.name ?? 'Home Team') as string)
                  const awayTeam = String((match.away_team?.away_team_name ?? match.away_team?.name ?? 'Away Team') as string)
                  const score =
                    match.home_score !== null && match.away_score !== null
                      ? `${match.home_score} - ${match.away_score}`
                      : 'N/A'

                  return (
                    <tr key={match.match_id} className={selected ? 'bg-accent/10' : ''}>
                      <td className="px-2 py-2">
                        <input
                          type="checkbox"
                          checked={selected}
                          onChange={() => toggleMatch(match.match_id)}
                          className="h-4 w-4 rounded border-white/20 bg-canvas"
                        />
                      </td>
                      <td className="px-2 py-2 font-medium text-ink">{match.match_id}</td>
                      <td className="px-2 py-2 text-mute">{match.match_date ?? '-'}</td>
                      <td className="px-2 py-2 text-ink">{homeTeam}</td>
                      <td className="px-2 py-2 text-ink">{awayTeam}</td>
                      <td className="px-2 py-2 text-mute">{score}</td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        ) : null}
      </article>
    </section>
  )
}
