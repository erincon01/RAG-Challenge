export type Source = 'postgres' | 'sqlserver'

export interface HealthResponse {
  status: string
  timestamp: string
  environment: string
  version: string
  checks: Record<string, string>
}

export interface ReadinessResponse {
  ready: boolean
  checks: Record<string, boolean>
}

export interface SourceStatusItem {
  source: Source
  connected: boolean
}

export interface SourceStatusResponse {
  timestamp: string
  sources: SourceStatusItem[]
}

export interface SourceCapabilities {
  source: Source
  embedding_models: string[]
  search_algorithms: string[]
}

export interface CapabilitiesResponse {
  capabilities: Record<Source, SourceCapabilities>
}

export interface StatsBombCompetition {
  competition_id: number
  competition_name: string
  season_id: number
  season_name: string
  country_name: string | null
}

export interface StatsBombMatch {
  match_id: number
  match_date: string | null
  competition?: Record<string, unknown>
  season?: Record<string, unknown>
  home_team?: Record<string, unknown>
  away_team?: Record<string, unknown>
  home_score: number | null
  away_score: number | null
}

export interface JobCreateResponse {
  job_id: string
  status: string
  type: string
}

export interface JobRecord {
  id: string
  type: string
  status: string
  source: Source | null
  payload: Record<string, unknown>
  created_at: string
  updated_at: string
  progress: number
  total: number
  message: string
  error: string | null
  result: Record<string, unknown>
}

export interface JobListResponse {
  items: JobRecord[]
}

export interface EmbeddingsStatusResponse {
  source: Source
  table: string
  total_rows: number
  coverage: Record<string, number>
}

export interface MatchSummary {
  match_id: number
  match_date: string
  competition_name: string
  season_name: string
  home_team_name: string
  away_team_name: string
  home_score: number
  away_score: number
  result: string
  display_name: string
}

export interface EventDetail {
  id: number
  match_id: number
  period: number
  minute: number
  quarter_minute: number
  count: number
  summary: string | null
  time_description: string
}

export interface SearchRequestPayload {
  match_id: number
  query: string
  language?: string
  search_algorithm?: string
  embedding_model?: string
  top_n?: number
  temperature?: number
  max_input_tokens?: number
  max_output_tokens?: number
  include_match_info?: boolean
  system_message?: string | null
}

export interface SearchResponse {
  question: string
  normalized_question: string
  answer: string
  search_results: Array<{
    event: EventDetail
    similarity_score: number
    rank: number
  }>
  metadata: Record<string, unknown>
}

export interface DownloadRequestPayload {
  datasets: string[]
  match_ids: number[]
  competition_id?: number
  season_id?: number
  overwrite?: boolean
}

export interface LoadRequestPayload {
  source: Source
  datasets: string[]
  match_ids: number[]
}

export interface AggregateRequestPayload {
  source: Source
  match_ids: number[]
}

export interface EmbeddingsRebuildRequestPayload {
  source: Source
  match_ids: number[]
  embedding_models?: string[]
}
