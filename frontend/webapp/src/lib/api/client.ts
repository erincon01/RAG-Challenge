import type {
  AggregateRequestPayload,
  CapabilitiesResponse,
  ClearJobsResponse,
  CompetitionSummary,
  DownloadCleanupRequestPayload,
  DownloadCleanupResponse,
  DownloadRequestPayload,
  EmbeddingsRebuildRequestPayload,
  EmbeddingsStatusResponse,
  EventDetail,
  HealthResponse,
  JobCreateResponse,
  JobListResponse,
  JobRecord,
  LoadRequestPayload,
  MatchSummary,
  PlayerSummary,
  ReadinessResponse,
  MatchPipelineStatus,
  SearchRequestPayload,
  SearchResponse,
  Source,
  SummariesGenerateRequestPayload,
  SourceStatusResponse,
  StatsBombCompetition,
  StatsBombMatch,
  TableInfoSummary,
  TeamSummary,
} from './types'

const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api/v1'

export class ApiError extends Error {
  status: number
  detail: unknown

  constructor(status: number, detail: unknown) {
    super(`API request failed (${status})`)
    this.status = status
    this.detail = detail
  }
}

function withQuery(path: string, query: Record<string, string | number | undefined>) {
  const qs = new URLSearchParams()
  for (const [key, value] of Object.entries(query)) {
    if (value !== undefined && value !== null && value !== '') {
      qs.set(key, String(value))
    }
  }
  const suffix = qs.toString()
  return suffix ? `${path}?${suffix}` : path
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...(init?.headers || {}),
    },
  })

  const text = await response.text()
  let data: unknown = null
  if (text) {
    try {
      data = JSON.parse(text)
    } catch {
      data = text
    }
  }

  if (!response.ok) {
    throw new ApiError(response.status, data)
  }

  return data as T
}

export const api = {
  getHealth: () => request<HealthResponse>('/health'),
  getReadiness: () => request<ReadinessResponse>('/health/ready'),
  getCapabilities: () => request<CapabilitiesResponse>('/capabilities'),
  getSourcesStatus: () => request<SourceStatusResponse>('/sources/status'),

  listStatsBombCompetitions: () => request<StatsBombCompetition[]>('/statsbomb/competitions'),
  listStatsBombMatches: (competitionId: number, seasonId: number) =>
    request<StatsBombMatch[]>(
      withQuery('/statsbomb/matches', {
        competition_id: competitionId,
        season_id: seasonId,
      }),
    ),

  startDownload: (payload: DownloadRequestPayload) =>
    request<JobCreateResponse>('/ingestion/download', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  cleanupDownloadFiles: (payload: DownloadCleanupRequestPayload) =>
    request<DownloadCleanupResponse>('/ingestion/download/cleanup', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  startLoad: (payload: LoadRequestPayload) =>
    request<JobCreateResponse>('/ingestion/load', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  startAggregate: (payload: AggregateRequestPayload) =>
    request<JobCreateResponse>('/ingestion/aggregate', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  getPipelineStatus: (source: Source) =>
    request<MatchPipelineStatus[]>(withQuery('/ingestion/pipeline-status', { source })),

  startGenerateSummaries: (payload: SummariesGenerateRequestPayload) =>
    request<JobCreateResponse>('/ingestion/summaries/generate', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  startRebuildEmbeddings: (payload: EmbeddingsRebuildRequestPayload) =>
    request<JobCreateResponse>('/ingestion/embeddings/rebuild', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  listJobs: (limit = 100) => request<JobListResponse>(withQuery('/ingestion/jobs', { limit })),
  getJob: (jobId: string) => request<JobRecord>(`/ingestion/jobs/${jobId}`),
  clearJobs: () => request<ClearJobsResponse>('/ingestion/jobs', { method: 'DELETE' }),

  getEmbeddingsStatus: (source: Source) =>
    request<EmbeddingsStatusResponse>(withQuery('/embeddings/status', { source })),

  listCompetitions: (source: Source) => request<CompetitionSummary[]>(withQuery('/competitions', { source })),

  listMatches: (source: Source, limit = 200) => request<MatchSummary[]>(withQuery('/matches', { source, limit })),

  listTeams: (source: Source, matchId?: number) => request<TeamSummary[]>(withQuery('/teams', { source, match_id: matchId })),

  listPlayers: (source: Source, matchId?: number) =>
    request<PlayerSummary[]>(withQuery('/players', { source, match_id: matchId })),

  listTablesInfo: (source: Source) => request<TableInfoSummary[]>(withQuery('/tables-info', { source })),

  listEvents: (source: Source, matchId: number, limit = 300) =>
    request<EventDetail[]>(withQuery('/events', { source, match_id: matchId, limit })),

  search: (source: Source, payload: SearchRequestPayload) =>
    request<SearchResponse>(withQuery('/chat/search', { source }), {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
}
