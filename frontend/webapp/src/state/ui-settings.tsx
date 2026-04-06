import { createContext, useContext, useEffect, useMemo, useState, type PropsWithChildren } from 'react'

import type { Source } from '../lib/api/types'

type UIMode = 'user' | 'developer'
type Theme = 'light' | 'dark'

interface UISettingsState {
  source: Source
  mode: UIMode
  theme: Theme
  setSource: (source: Source) => void
  setMode: (mode: UIMode) => void
  setTheme: (theme: Theme) => void
}

const STORAGE_KEY = 'rag-webapp-ui-settings'

const UISettingsContext = createContext<UISettingsState | null>(null)

export function UISettingsProvider({ children }: PropsWithChildren) {
  const [source, setSource] = useState<Source>('postgres')
  const [mode, setMode] = useState<UIMode>('user')
  const [theme, setTheme] = useState<Theme>('dark')

  useEffect(() => {
    const raw = window.localStorage.getItem(STORAGE_KEY)
    if (!raw) {
      return
    }

    try {
      const parsed = JSON.parse(raw) as { source?: Source; mode?: UIMode; theme?: Theme }
      if (parsed.source === 'postgres' || parsed.source === 'sqlserver') {
        setSource(parsed.source)
      }
      if (parsed.mode === 'user' || parsed.mode === 'developer') {
        setMode(parsed.mode)
      }
      if (parsed.theme === 'light' || parsed.theme === 'dark') {
        setTheme(parsed.theme)
      }
    } catch {
      window.localStorage.removeItem(STORAGE_KEY)
    }
  }, [])

  // Apply theme class to <html>
  useEffect(() => {
    const root = document.documentElement
    if (theme === 'light') {
      root.classList.add('light')
    } else {
      root.classList.remove('light')
    }
  }, [theme])

  useEffect(() => {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify({ source, mode, theme }))
  }, [source, mode, theme])

  const value = useMemo(() => ({ source, mode, theme, setSource, setMode, setTheme }), [source, mode, theme])

  return <UISettingsContext.Provider value={value}>{children}</UISettingsContext.Provider>
}

export function useUISettings() {
  const ctx = useContext(UISettingsContext)
  if (!ctx) {
    throw new Error('useUISettings must be used within UISettingsProvider')
  }
  return ctx
}
