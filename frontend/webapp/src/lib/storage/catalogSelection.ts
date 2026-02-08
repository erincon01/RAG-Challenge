export interface CatalogSelection {
  competitionId: number | null
  seasonId: number | null
  matchIds: number[]
}

const STORAGE_KEY = 'rag-webapp-catalog-selection'

const DEFAULT_SELECTION: CatalogSelection = {
  competitionId: null,
  seasonId: null,
  matchIds: [],
}

export function readCatalogSelection(): CatalogSelection {
  const raw = window.localStorage.getItem(STORAGE_KEY)
  if (!raw) {
    return DEFAULT_SELECTION
  }

  try {
    const parsed = JSON.parse(raw) as Partial<CatalogSelection>
    const matchIds = Array.isArray(parsed.matchIds)
      ? parsed.matchIds.filter((item): item is number => Number.isInteger(item))
      : []

    const competitionId =
      typeof parsed.competitionId === 'number' && Number.isInteger(parsed.competitionId)
        ? parsed.competitionId
        : null

    const seasonId =
      typeof parsed.seasonId === 'number' && Number.isInteger(parsed.seasonId)
        ? parsed.seasonId
        : null

    return {
      competitionId,
      seasonId,
      matchIds,
    }
  } catch {
    return DEFAULT_SELECTION
  }
}

export function writeCatalogSelection(selection: CatalogSelection) {
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(selection))
}
