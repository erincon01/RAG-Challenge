import { createContext, useContext, useEffect, useMemo, useState, type PropsWithChildren } from 'react'

import type { Source } from '../lib/api/types'

type UIMode = 'user' | 'developer'

interface UISettingsState {
  source: Source
  mode: UIMode
  setSource: (source: Source) => void
  setMode: (mode: UIMode) => void
}

const STORAGE_KEY = 'rag-webapp-ui-settings'

const UISettingsContext = createContext<UISettingsState | null>(null)

export function UISettingsProvider({ children }: PropsWithChildren) {
  const [source, setSource] = useState<Source>('postgres')
  const [mode, setMode] = useState<UIMode>('user')

  useEffect(() => {
    const raw = window.localStorage.getItem(STORAGE_KEY)
    if (!raw) {
      return
    }

    try {
      const parsed = JSON.parse(raw) as { source?: Source; mode?: UIMode }
      if (parsed.source === 'postgres' || parsed.source === 'sqlserver') {
        setSource(parsed.source)
      }
      if (parsed.mode === 'user' || parsed.mode === 'developer') {
        setMode(parsed.mode)
      }
    } catch {
      window.localStorage.removeItem(STORAGE_KEY)
    }
  }, [])

  useEffect(() => {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify({ source, mode }))
  }, [source, mode])

  const value = useMemo(() => ({ source, mode, setSource, setMode }), [source, mode])

  return <UISettingsContext.Provider value={value}>{children}</UISettingsContext.Provider>
}

export function useUISettings() {
  const ctx = useContext(UISettingsContext)
  if (!ctx) {
    throw new Error('useUISettings must be used within UISettingsProvider')
  }
  return ctx
}
