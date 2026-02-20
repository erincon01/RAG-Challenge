import { useEffect, useMemo, useState } from 'react'
import { useQueries, useQuery } from '@tanstack/react-query'

import { api } from '../lib/api/client'
import { readCatalogSelection, writeCatalogSelection } from '../lib/storage/catalogSelection'
import type { StatsBombMatch } from '../lib/api/types'

// ── helpers ──

function teamName(team: Record<string, unknown> | undefined): string {
  if (!team) return 'Unknown'
  return String((team.home_team_name ?? team.away_team_name ?? team.name ?? 'Unknown') as string)
}

function uniqueTeams(matches: StatsBombMatch[]): string[] {
  const set = new Set<string>()
  for (const m of matches) {
    set.add(teamName(m.home_team))
    set.add(teamName(m.away_team))
  }
  return [...set].sort((a, b) => a.localeCompare(b))
}

interface UniqueCompetition {
  competition_id: number
  competition_name: string
  country_name: string | null
}

interface SeasonOption {
  season_id: number
  season_name: string
}

const ALL_SEASONS = '__all__'

// ── component ──

export function CatalogPage() {
  const initial = readCatalogSelection()
  const [competitionId, setCompetitionId] = useState<number | null>(initial.competitionId)
  const [seasonFilter, setSeasonFilter] = useState<string>(initial.seasonId !== null ? String(initial.seasonId) : ALL_SEASONS)
  const [selectedMatchIds, setSelectedMatchIds] = useState<number[]>(initial.matchIds)
  const [teamFilter, setTeamFilter] = useState<string[]>([])
  const [sortBy, setSortBy] = useState<'season' | 'date' | 'home' | 'away'>('date')
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc')

  // ── queries ──

  const competitionsQuery = useQuery({
    queryKey: ['statsbomb-competitions'],
    queryFn: api.listStatsBombCompetitions,
  })

  // derive unique competitions
  const competitions = useMemo<UniqueCompetition[]>(() => {
    const map = new Map<number, UniqueCompetition>()
    for (const c of competitionsQuery.data ?? []) {
      if (!map.has(c.competition_id)) {
        map.set(c.competition_id, {
          competition_id: c.competition_id,
          competition_name: c.competition_name,
          country_name: c.country_name,
        })
      }
    }
    return [...map.values()].sort((a, b) => {
      const cmp = (a.country_name ?? '').localeCompare(b.country_name ?? '')
      return cmp !== 0 ? cmp : a.competition_name.localeCompare(b.competition_name)
    })
  }, [competitionsQuery.data])

  // derive seasons for selected competition
  const seasons = useMemo<SeasonOption[]>(() => {
    if (competitionId === null) return []
    return (competitionsQuery.data ?? [])
      .filter((c) => c.competition_id === competitionId)
      .map((c) => ({ season_id: c.season_id, season_name: c.season_name }))
      .sort((a, b) => b.season_name.localeCompare(a.season_name))
  }, [competitionsQuery.data, competitionId])

  // fetch matches for ALL seasons of the selected competition in parallel
  const matchQueries = useQueries({
    queries: seasons.map((s) => ({
      queryKey: ['statsbomb-matches', competitionId, s.season_id],
      queryFn: () => api.listStatsBombMatches(competitionId as number, s.season_id),
      enabled: competitionId !== null,
      staleTime: 5 * 60 * 1000,
    })),
  })

  const allMatchesLoading = matchQueries.some((q) => q.isLoading)
  const allMatchesError = matchQueries.some((q) => q.isError) && !matchQueries.some((q) => q.isSuccess)

  // merge all season matches with season metadata
  const allMatches = useMemo<(StatsBombMatch & { _season_id: number; _season_name: string })[]>(() => {
    const result: (StatsBombMatch & { _season_id: number; _season_name: string })[] = []
    for (let i = 0; i < seasons.length; i++) {
      const data = matchQueries[i]?.data
      if (data) {
        for (const m of data) {
          result.push({ ...m, _season_id: seasons[i].season_id, _season_name: seasons[i].season_name })
        }
      }
    }
    return result
  }, [seasons, matchQueries])

  // teams from ALL matches
  const availableTeams = useMemo(() => uniqueTeams(allMatches), [allMatches])

  // filtered matches (by season + team)
  const filteredMatches = useMemo(() => {
    let list = allMatches
    if (seasonFilter !== ALL_SEASONS) {
      const sid = Number(seasonFilter)
      list = list.filter((m) => m._season_id === sid)
    }
    if (teamFilter.length > 0) {
      list = list.filter((m) => {
        const home = teamName(m.home_team)
        const away = teamName(m.away_team)
        return teamFilter.includes(home) || teamFilter.includes(away)
      })
    }

    // Apply sorting
    list = [...list].sort((a, b) => {
      let comparison = 0

      switch (sortBy) {
        case 'season':
          comparison = a._season_name.localeCompare(b._season_name)
          break
        case 'date':
          comparison = (a.match_date ?? '').localeCompare(b.match_date ?? '')
          break
        case 'home':
          comparison = teamName(a.home_team).localeCompare(teamName(b.home_team))
          break
        case 'away':
          comparison = teamName(a.away_team).localeCompare(teamName(b.away_team))
          break
      }

      return sortOrder === 'asc' ? comparison : -comparison
    })

    return list
  }, [allMatches, seasonFilter, teamFilter, sortBy, sortOrder])

  // ── persistence ──

  useEffect(() => {
    const sid = seasonFilter === ALL_SEASONS ? null : Number(seasonFilter)
    writeCatalogSelection({ competitionId, seasonId: sid, matchIds: selectedMatchIds })
  }, [competitionId, seasonFilter, selectedMatchIds])

  // reset filters on competition change
  useEffect(() => {
    setTeamFilter([])
    setSeasonFilter(ALL_SEASONS)
  }, [competitionId])

  // ── actions ──

  const toggleTeam = (t: string) =>
    setTeamFilter((prev) => (prev.includes(t) ? prev.filter((x) => x !== t) : [...prev, t]))

  const toggleMatch = (id: number) =>
    setSelectedMatchIds((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id].sort((a, b) => a - b),
    )

  const selectAllVisible = () => {
    const ids = filteredMatches.map((m) => m.match_id)
    setSelectedMatchIds((prev) => [...new Set([...prev, ...ids])].sort((a, b) => a - b))
  }

  const clearSelected = () => setSelectedMatchIds([])

  // ── loaded seasons counter ──
  const loadedSeasons = matchQueries.filter((q) => q.isSuccess).length

  // ── sorting handlers ──
  const handleSort = (column: 'season' | 'date' | 'home' | 'away') => {
    if (sortBy === column) {
      setSortOrder((prev) => (prev === 'asc' ? 'desc' : 'asc'))
    } else {
      setSortBy(column)
      setSortOrder('asc')
    }
  }

  const SortIcon = ({ column }: { column: 'season' | 'date' | 'home' | 'away' }) => {
    if (sortBy !== column) return <span className="ml-1 text-mute/40">⇅</span>
    return <span className="ml-1">{sortOrder === 'asc' ? '↑' : '↓'}</span>
  }

  return (
    <section className="space-y-4">
      {/* ── Header ── */}
      <header className="rounded-2xl border border-white/10 bg-panel/70 p-5">
        <h2 className="text-2xl font-semibold text-ink">Catalogo StatsBomb</h2>
        <p className="mt-1 text-sm text-mute">
          Selecciona competición para cargar equipos y partidos de todas las temporadas.
        </p>

        <div className="mt-4 grid gap-3 md:grid-cols-[1fr_1fr_auto]">
          {/* Competition */}
          <select
            value={competitionId ?? ''}
            onChange={(e) => {
              const val = e.target.value ? Number(e.target.value) : null
              setCompetitionId(val)
              setSelectedMatchIds([])
            }}
            className="rounded-xl border border-white/10 bg-canvas/80 px-3 py-3 text-sm text-ink outline-none"
          >
            <option value="">Selecciona competición...</option>
            {competitions.map((c) => (
              <option key={c.competition_id} value={c.competition_id}>
                {c.country_name ?? 'International'} | {c.competition_name}
              </option>
            ))}
          </select>

          {/* Season */}
          <select
            value={seasonFilter}
            onChange={(e) => setSeasonFilter(e.target.value)}
            disabled={competitionId === null}
            className="rounded-xl border border-white/10 bg-canvas/80 px-3 py-3 text-sm text-ink outline-none disabled:opacity-40"
          >
            <option value={ALL_SEASONS}>Todas las temporadas</option>
            {seasons.map((s) => (
              <option key={s.season_id} value={s.season_id}>
                {s.season_name}
              </option>
            ))}
          </select>

          {/* Stats */}
          <div className="rounded-xl border border-white/10 bg-canvas/60 px-4 py-3 text-xs text-mute">
            <p>Competiciones: {competitions.length}</p>
            <p>Temporadas: {seasons.length}{allMatchesLoading ? ` (cargando ${loadedSeasons}/${seasons.length})` : ''}</p>
            <p>Partidos totales: {allMatches.length}</p>
            <p>Seleccionados: {selectedMatchIds.length}</p>
          </div>
        </div>
      </header>

      {/* ── Team filter ── */}
      {availableTeams.length > 0 && (
        <article className="rounded-2xl border border-white/10 bg-panel/70 p-5">
          <div className="mb-3 flex items-center justify-between">
            <h3 className="text-lg font-semibold text-ink">
              Filtrar por equipos
              {teamFilter.length > 0 && (
                <span className="ml-2 text-sm font-normal text-mute">({teamFilter.length} seleccionados)</span>
              )}
            </h3>
            {teamFilter.length > 0 && (
              <button
                type="button"
                onClick={() => setTeamFilter([])}
                className="rounded-xl border border-white/20 bg-white/5 px-3 py-1.5 text-xs font-semibold text-ink"
              >
                Limpiar filtro
              </button>
            )}
          </div>
          <div className="flex flex-wrap gap-2">
            {availableTeams.map((team) => {
              const active = teamFilter.includes(team)
              return (
                <button
                  key={team}
                  type="button"
                  onClick={() => toggleTeam(team)}
                  className={`rounded-lg border px-3 py-1.5 text-xs font-medium transition-colors ${
                    active
                      ? 'border-accent/60 bg-accent/20 text-accent'
                      : 'border-white/10 bg-canvas/60 text-mute hover:border-white/30 hover:text-ink'
                  }`}
                >
                  {team}
                </button>
              )
            })}
          </div>
        </article>
      )}

      {/* ── Matches table ── */}
      <article className="rounded-2xl border border-white/10 bg-panel/70 p-5">
        <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
          <h3 className="text-lg font-semibold text-ink">
            Partidos disponibles
            <span className="ml-2 text-sm font-normal text-mute">
              ({filteredMatches.length} {(teamFilter.length > 0 || seasonFilter !== ALL_SEASONS) ? `de ${allMatches.length}` : 'cargados'})
            </span>
          </h3>
          <div className="flex gap-2">
            <button
              type="button"
              onClick={selectAllVisible}
              className="rounded-xl border border-accent/40 bg-accent/10 px-3 py-2 text-xs font-semibold text-accent"
              disabled={filteredMatches.length === 0}
            >
              Seleccionar todos
            </button>
            <button
              type="button"
              onClick={clearSelected}
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

        {competitionId === null && <p className="text-mute">Selecciona una competición para ver los partidos.</p>}

        {competitionId !== null && allMatchesLoading && (
          <p className="text-mute">Cargando partidos ({loadedSeasons}/{seasons.length} temporadas)...</p>
        )}
        {competitionId !== null && allMatchesError && (
          <p className="text-rose-300">No se pudieron cargar los partidos para esta competición.</p>
        )}

        {filteredMatches.length > 0 && (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-white/10 text-sm">
              <thead>
                <tr className="text-left text-mute">
                  <th className="px-2 py-2">Select</th>
                  <th className="px-2 py-2">Match ID</th>
                  <th
                    className="cursor-pointer px-2 py-2 hover:text-ink"
                    onClick={() => handleSort('season')}
                  >
                    Temporada
                    <SortIcon column="season" />
                  </th>
                  <th
                    className="cursor-pointer px-2 py-2 hover:text-ink"
                    onClick={() => handleSort('date')}
                  >
                    Date
                    <SortIcon column="date" />
                  </th>
                  <th
                    className="cursor-pointer px-2 py-2 hover:text-ink"
                    onClick={() => handleSort('home')}
                  >
                    Home
                    <SortIcon column="home" />
                  </th>
                  <th
                    className="cursor-pointer px-2 py-2 hover:text-ink"
                    onClick={() => handleSort('away')}
                  >
                    Away
                    <SortIcon column="away" />
                  </th>
                  <th className="px-2 py-2">Score</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {filteredMatches.map((match) => {
                  const selected = selectedMatchIds.includes(match.match_id)
                  const home = teamName(match.home_team)
                  const away = teamName(match.away_team)
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
                      <td className="px-2 py-2 text-mute">{match._season_name}</td>
                      <td className="px-2 py-2 text-mute">{match.match_date ?? '-'}</td>
                      <td className="px-2 py-2 text-ink">{home}</td>
                      <td className="px-2 py-2 text-ink">{away}</td>
                      <td className="px-2 py-2 text-mute">{score}</td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </article>
    </section>
  )
}
