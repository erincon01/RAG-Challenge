import { NavLink, Outlet } from 'react-router-dom'

import { useUISettings } from '../../state/ui-settings'

const navigation = [
  { to: '/', label: 'Home' },
  { to: '/dashboard', label: 'Dashboard' },
  { to: '/catalog', label: 'Catalogo StatsBomb' },
  { to: '/operations', label: 'Descarga y Carga' },
  { to: '/explorer', label: 'Explorador' },
  { to: '/embeddings', label: 'Embeddings' },
  { to: '/chat', label: 'Chat RAG' },
]

function navClass(isActive: boolean) {
  const base = 'rounded-xl px-3 py-2 text-sm font-medium transition'
  return isActive
    ? `${base} bg-accent/20 text-accent shadow-glow`
    : `${base} text-mute hover:bg-white/5 hover:text-ink`
}

export function AppShell() {
  const { source, setSource, mode, setMode, theme, setTheme } = useUISettings()

  return (
    <div className="mx-auto flex min-h-screen max-w-[1400px] flex-col gap-6 px-4 pb-8 pt-6 md:px-8">
      <header className="rounded-2xl border border-white/10 bg-panel/80 p-4 backdrop-blur">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <p className="text-xs uppercase tracking-[0.2em] text-accent">RAG Challenge</p>
            <h1 className="text-2xl font-bold text-ink">Football Data Control Center</h1>
          </div>
          <div className="flex flex-wrap items-center gap-3 text-sm">
            <label className="flex items-center gap-2 rounded-xl border border-white/10 bg-canvas/70 px-3 py-2">
              <span className="text-mute">Source</span>
              <select
                className="bg-transparent text-ink outline-none"
                value={source}
                onChange={(event) => setSource(event.target.value as typeof source)}
              >
                <option className="bg-panel" value="postgres">
                  PostgreSQL
                </option>
                <option className="bg-panel" value="sqlserver">
                  SQL Server
                </option>
              </select>
            </label>
            <label className="flex items-center gap-2 rounded-xl border border-white/10 bg-canvas/70 px-3 py-2">
              <span className="text-mute">Mode</span>
              <select
                className="bg-transparent text-ink outline-none"
                value={mode}
                onChange={(event) => setMode(event.target.value as typeof mode)}
              >
                <option className="bg-panel" value="user">
                  User
                </option>
                <option className="bg-panel" value="developer">
                  Developer
                </option>
              </select>
            </label>
            <button
              type="button"
              onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
              className="flex items-center gap-2 rounded-xl border border-white/10 bg-canvas/70 px-3 py-2 text-mute transition hover:text-ink"
              title={theme === 'dark' ? 'Cambiar a tema claro' : 'Cambiar a tema oscuro'}
            >
              {theme === 'dark' ? (
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="h-4 w-4">
                  <path
                    fillRule="evenodd"
                    d="M7.455 2.004a.75.75 0 0 1 .26.77 7 7 0 0 0 9.958 7.967.75.75 0 0 1 1.067.853A8.5 8.5 0 1 1 6.647 1.921a.75.75 0 0 1 .808.083Z"
                    clipRule="evenodd"
                  />
                </svg>
              ) : (
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="h-4 w-4">
                  <path d="M10 2a.75.75 0 0 1 .75.75v1.5a.75.75 0 0 1-1.5 0v-1.5A.75.75 0 0 1 10 2ZM10 15a.75.75 0 0 1 .75.75v1.5a.75.75 0 0 1-1.5 0v-1.5A.75.75 0 0 1 10 15ZM10 7a3 3 0 1 0 0 6 3 3 0 0 0 0-6ZM15.657 5.404a.75.75 0 1 0-1.06-1.06l-1.061 1.06a.75.75 0 0 0 1.06 1.06l1.06-1.06ZM6.464 14.596a.75.75 0 1 0-1.06-1.06l-1.06 1.06a.75.75 0 0 0 1.06 1.06l1.06-1.06ZM18 10a.75.75 0 0 1-.75.75h-1.5a.75.75 0 0 1 0-1.5h1.5A.75.75 0 0 1 18 10ZM5 10a.75.75 0 0 1-.75.75h-1.5a.75.75 0 0 1 0-1.5h1.5A.75.75 0 0 1 5 10ZM14.596 15.657a.75.75 0 0 0 1.06-1.06l-1.06-1.061a.75.75 0 1 0-1.06 1.06l1.06 1.06ZM5.404 6.464a.75.75 0 0 0 1.06-1.06l-1.06-1.06a.75.75 0 1 0-1.06 1.06l1.06 1.06Z" />
                </svg>
              )}
              <span>{theme === 'dark' ? 'Dark' : 'Light'}</span>
            </button>
          </div>
        </div>
        <nav className="mt-4 flex flex-wrap gap-2">
          {navigation.map((item) => (
            <NavLink key={item.to} to={item.to} className={({ isActive }) => navClass(isActive)} end={item.to === '/'}>
              {item.label}
            </NavLink>
          ))}
        </nav>
      </header>

      <main className="flex-1">
        <Outlet />
      </main>
    </div>
  )
}
