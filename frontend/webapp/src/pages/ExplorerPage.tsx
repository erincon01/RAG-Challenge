import { useEffect, useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'

import { api } from '../lib/api/client'
import type { EventDetail } from '../lib/api/types'
import { useUISettings } from '../state/ui-settings'

type ExplorerTab = 'competitions' | 'matches' | 'teams' | 'players' | 'events' | 'tables'

const tabs: Array<{ key: ExplorerTab; label: string }> = [
  { key: 'competitions', label: 'Competitions' },
  { key: 'matches', label: 'Matches' },
  { key: 'teams', label: 'Teams' },
  { key: 'players', label: 'Players' },
  { key: 'events', label: 'Events' },
  { key: 'tables', label: 'Tables Info' },
]

export function ExplorerPage() {
  const { source } = useUISettings()
  const [activeTab, setActiveTab] = useState<ExplorerTab>('competitions')
  const [selectedMatchId, setSelectedMatchId] = useState<number | null>(null)

  const competitionsQuery = useQuery({
    queryKey: ['explorer-competitions', source],
    queryFn: () => api.listCompetitions(source),
  })

  const matchesQuery = useQuery({
    queryKey: ['explorer-matches', source],
    queryFn: () => api.listMatches(source, 250),
  })

  const teamsQuery = useQuery({
    queryKey: ['explorer-teams', source, selectedMatchId],
    queryFn: () => api.listTeams(source, selectedMatchId ?? undefined),
    enabled: activeTab === 'teams',
  })

  const playersQuery = useQuery({
    queryKey: ['explorer-players', source, selectedMatchId],
    queryFn: () => api.listPlayers(source, selectedMatchId ?? undefined),
    enabled: activeTab === 'players',
  })

  const eventsQuery = useQuery({
    queryKey: ['explorer-events', source, selectedMatchId],
    queryFn: () => api.listEvents(source, selectedMatchId as number, 400),
    enabled: activeTab === 'events' && selectedMatchId !== null,
  })

  const tablesQuery = useQuery({
    queryKey: ['explorer-tables', source],
    queryFn: () => api.listTablesInfo(source),
    enabled: activeTab === 'tables',
  })

  // Reset match selection when source changes
  useEffect(() => {
    setSelectedMatchId(null)
  }, [source])

  useEffect(() => {
    if (!matchesQuery.data || matchesQuery.data.length === 0) {
      setSelectedMatchId(null)
      return
    }
    if (selectedMatchId === null) {
      setSelectedMatchId(matchesQuery.data[0].match_id)
      return
    }
    const exists = matchesQuery.data.some((match) => match.match_id === selectedMatchId)
    if (!exists) {
      setSelectedMatchId(matchesQuery.data[0].match_id)
    }
  }, [matchesQuery.data, selectedMatchId])

  return (
    <section className="space-y-4">
      <header className="rounded-2xl border border-white/10 bg-panel/70 p-5">
        <h2 className="text-2xl font-semibold text-ink">Explorador de Datos</h2>
        <p className="mt-1 text-sm text-mute">
          Vista operativa por source para inspeccionar competiciones, partidos, equipos, jugadores, eventos y tablas.
        </p>
        <div className="mt-3 grid gap-3 md:grid-cols-[1fr_auto]">
          <select
            className="rounded-xl border border-white/10 bg-canvas/80 px-3 py-2 text-sm text-ink"
            value={selectedMatchId ?? ''}
            onChange={(event) => setSelectedMatchId(event.target.value ? Number(event.target.value) : null)}
          >
            {(matchesQuery.data ?? []).map((match) => (
              <option key={match.match_id} value={match.match_id}>
                {match.match_id} | {match.display_name}
              </option>
            ))}
          </select>
          <div className="rounded-xl border border-white/10 bg-canvas/60 px-4 py-2 text-xs text-mute">
            Source activo: <span className="font-semibold capitalize text-ink">{source}</span>
          </div>
        </div>
      </header>

      <div className="flex flex-wrap gap-2">
        {tabs.map((tab) => (
          <button
            key={tab.key}
            type="button"
            onClick={() => setActiveTab(tab.key)}
            className={[
              'rounded-xl px-3 py-2 text-sm transition',
              activeTab === tab.key
                ? 'bg-accent/20 font-semibold text-accent'
                : 'border border-white/10 bg-panel/40 text-mute hover:text-ink',
            ].join(' ')}
          >
            {tab.label}
          </button>
        ))}
      </div>

      <article className="rounded-2xl border border-white/10 bg-panel/70 p-5">
        {activeTab === 'competitions' ? (
          <>
            {competitionsQuery.isLoading ? <p className="text-mute">Cargando competiciones...</p> : null}
            {competitionsQuery.isError ? <p className="text-rose-300">Error cargando competiciones.</p> : null}
            <ul className="grid gap-2 md:grid-cols-2 xl:grid-cols-3">
              {(competitionsQuery.data ?? []).map((competition) => (
                <li key={`${competition.competition_id}-${competition.name}`} className="rounded-xl bg-canvas/60 p-3">
                  <p className="font-semibold text-ink">{competition.name}</p>
                  <p className="text-xs text-mute">
                    #{competition.competition_id} | {competition.country}
                  </p>
                </li>
              ))}
            </ul>
          </>
        ) : null}

        {activeTab === 'matches' ? (
          <>
            {matchesQuery.isLoading ? <p className="text-mute">Cargando partidos...</p> : null}
            {matchesQuery.isError ? <p className="text-rose-300">Error cargando partidos.</p> : null}
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-white/10 text-sm">
                <thead>
                  <tr className="text-left text-mute">
                    <th className="px-2 py-2">Match ID</th>
                    <th className="px-2 py-2">Date</th>
                    <th className="px-2 py-2">Competition</th>
                    <th className="px-2 py-2">Display</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5">
                  {(matchesQuery.data ?? []).map((match) => (
                    <tr key={match.match_id} className={match.match_id === selectedMatchId ? 'bg-accent/10' : ''}>
                      <td className="px-2 py-2 text-ink">{match.match_id}</td>
                      <td className="px-2 py-2 text-mute">{match.match_date}</td>
                      <td className="px-2 py-2 text-mute">{match.competition_name}</td>
                      <td className="px-2 py-2 text-ink">{match.display_name}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        ) : null}

        {activeTab === 'teams' ? (
          <>
            {teamsQuery.isLoading ? <p className="text-mute">Cargando teams...</p> : null}
            {teamsQuery.isError ? <p className="text-rose-300">Error cargando teams.</p> : null}
            <ul className="grid gap-2 md:grid-cols-2">
              {(teamsQuery.data ?? []).map((team) => (
                <li key={`${team.team_id}-${team.name}`} className="rounded-xl bg-canvas/60 p-3">
                  <p className="font-semibold text-ink">{team.name}</p>
                  <p className="text-xs text-mute">
                    #{team.team_id} | {team.gender ?? '-'} | {team.country ?? '-'}
                  </p>
                </li>
              ))}
            </ul>
          </>
        ) : null}

        {activeTab === 'players' ? (
          <>
            {playersQuery.isLoading ? <p className="text-mute">Cargando players...</p> : null}
            {playersQuery.isError ? <p className="text-rose-300">Error cargando players.</p> : null}
            {(playersQuery.data ?? []).length === 0 ? <p className="text-mute">No hay players para este source/filtro.</p> : null}
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-white/10 text-sm">
                <thead>
                  <tr className="text-left text-mute">
                    <th className="px-2 py-2">Player ID</th>
                    <th className="px-2 py-2">Name</th>
                    <th className="px-2 py-2">Team</th>
                    <th className="px-2 py-2">Position</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5">
                  {(playersQuery.data ?? []).map((player) => (
                    <tr key={player.player_id}>
                      <td className="px-2 py-2 text-mute">{player.player_id}</td>
                      <td className="px-2 py-2 text-ink">{player.player_name}</td>
                      <td className="px-2 py-2 text-mute">{player.team_name ?? '-'}</td>
                      <td className="px-2 py-2 text-mute">{player.position_name ?? '-'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        ) : null}

        {activeTab === 'events' ? (
          <EventsTab
            events={eventsQuery.data ?? []}
            isLoading={eventsQuery.isLoading}
            isError={eventsQuery.isError}
            noMatch={selectedMatchId === null}
          />
        ) : null}

        {activeTab === 'tables' ? (
          <>
            {tablesQuery.isLoading ? <p className="text-mute">Cargando metadata de tablas...</p> : null}
            {tablesQuery.isError ? <p className="text-rose-300">Error cargando tables-info.</p> : null}
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-white/10 text-sm">
                <thead>
                  <tr className="text-left text-mute">
                    <th className="px-2 py-2">Table</th>
                    <th className="px-2 py-2">Rows</th>
                    <th className="px-2 py-2">Embedding Columns</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5">
                  {(tablesQuery.data ?? []).map((tableInfo) => (
                    <tr key={tableInfo.table}>
                      <td className="px-2 py-2 text-ink">{tableInfo.table}</td>
                      <td className="px-2 py-2 text-mute">{tableInfo.row_count}</td>
                      <td className="px-2 py-2 text-mute">
                        {tableInfo.embedding_columns.length > 0
                          ? tableInfo.embedding_columns.join(', ')
                          : 'No embedding columns'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        ) : null}
      </article>
    </section>
  )
}

// ---------------------------------------------------------------------------
// Events tab with filters, sorting, and search
// ---------------------------------------------------------------------------

type SortField = 'id' | 'period' | 'minute' | 'count'
type SortDir = 'asc' | 'desc'

function EventsTab({
  events,
  isLoading,
  isError,
  noMatch,
}: {
  events: EventDetail[]
  isLoading: boolean
  isError: boolean
  noMatch: boolean
}) {
  const [periodFilter, setPeriodFilter] = useState<number | ''>('')
  const [minuteFrom, setMinuteFrom] = useState<string>('')
  const [minuteTo, setMinuteTo] = useState<string>('')
  const [searchText, setSearchText] = useState('')
  const [sortField, setSortField] = useState<SortField>('id')
  const [sortDir, setSortDir] = useState<SortDir>('asc')

  const periods = useMemo(() => {
    const set = new Set(events.map((e) => e.period))
    return Array.from(set).sort()
  }, [events])

  const filtered = useMemo(() => {
    let result = events

    if (periodFilter !== '') {
      result = result.filter((e) => e.period === periodFilter)
    }
    if (minuteFrom !== '') {
      const from = Number(minuteFrom)
      result = result.filter((e) => e.minute >= from)
    }
    if (minuteTo !== '') {
      const to = Number(minuteTo)
      result = result.filter((e) => e.minute <= to)
    }
    if (searchText.trim()) {
      const q = searchText.toLowerCase()
      result = result.filter((e) => e.summary?.toLowerCase().includes(q))
    }

    result = [...result].sort((a, b) => {
      const av = a[sortField] ?? 0
      const bv = b[sortField] ?? 0
      return sortDir === 'asc' ? (av < bv ? -1 : av > bv ? 1 : 0) : av > bv ? -1 : av < bv ? 1 : 0
    })

    return result
  }, [events, periodFilter, minuteFrom, minuteTo, searchText, sortField, sortDir])

  const toggleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'))
    } else {
      setSortField(field)
      setSortDir('asc')
    }
  }

  const sortIcon = (field: SortField) => {
    if (sortField !== field) return ''
    return sortDir === 'asc' ? ' \u25B2' : ' \u25BC'
  }

  if (noMatch) return <p className="text-mute">Selecciona un partido para ver eventos.</p>
  if (isLoading) return <p className="text-mute">Cargando eventos...</p>
  if (isError) return <p className="text-rose-300">Error cargando eventos.</p>

  return (
    <div className="space-y-3">
      {/* Filters */}
      <div className="flex flex-wrap items-end gap-3">
        <label className="text-sm text-mute">
          Period
          <select
            className="ml-2 rounded-lg border border-white/10 bg-canvas/80 px-2 py-1 text-sm text-ink"
            value={periodFilter}
            onChange={(e) => setPeriodFilter(e.target.value === '' ? '' : Number(e.target.value))}
          >
            <option value="">All</option>
            {periods.map((p) => (
              <option key={p} value={p}>
                {p}
              </option>
            ))}
          </select>
        </label>

        <label className="text-sm text-mute">
          Minute from
          <input
            type="number"
            min={0}
            className="ml-2 w-16 rounded-lg border border-white/10 bg-canvas/80 px-2 py-1 text-sm text-ink"
            value={minuteFrom}
            onChange={(e) => setMinuteFrom(e.target.value)}
          />
        </label>

        <label className="text-sm text-mute">
          to
          <input
            type="number"
            min={0}
            className="ml-2 w-16 rounded-lg border border-white/10 bg-canvas/80 px-2 py-1 text-sm text-ink"
            value={minuteTo}
            onChange={(e) => setMinuteTo(e.target.value)}
          />
        </label>

        <label className="text-sm text-mute">
          Search
          <input
            type="text"
            placeholder="Search in summaries..."
            className="ml-2 w-48 rounded-lg border border-white/10 bg-canvas/80 px-2 py-1 text-sm text-ink"
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
          />
        </label>

        <span className="text-xs text-mute">
          {filtered.length} / {events.length} rows
        </span>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-white/10 text-sm">
          <thead>
            <tr className="text-left text-mute">
              <th className="cursor-pointer px-2 py-2 hover:text-ink" onClick={() => toggleSort('id')}>
                ID{sortIcon('id')}
              </th>
              <th className="cursor-pointer px-2 py-2 hover:text-ink" onClick={() => toggleSort('period')}>
                Period{sortIcon('period')}
              </th>
              <th className="cursor-pointer px-2 py-2 hover:text-ink" onClick={() => toggleSort('minute')}>
                Minute{sortIcon('minute')}
              </th>
              <th className="px-2 py-2">Time</th>
              <th className="cursor-pointer px-2 py-2 hover:text-ink" onClick={() => toggleSort('count')}>
                Count{sortIcon('count')}
              </th>
              <th className="px-2 py-2">Summary</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/5">
            {filtered.map((event) => (
              <tr key={event.id} className="hover:bg-white/5">
                <td className="px-2 py-2 text-mute">{event.id}</td>
                <td className="px-2 py-2 text-ink">{event.period}</td>
                <td className="px-2 py-2 text-ink">{event.minute}</td>
                <td className="whitespace-nowrap px-2 py-2 text-mute">{event.time_description}</td>
                <td className="px-2 py-2 text-center text-ink">{event.count}</td>
                <td className="max-w-xl px-2 py-2 text-ink">
                  <p className="line-clamp-3">{event.summary ?? '-'}</p>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
