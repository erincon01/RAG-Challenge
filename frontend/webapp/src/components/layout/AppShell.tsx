import { NavLink, Outlet } from 'react-router-dom'

import { useUISettings } from '../../state/ui-settings'

const navigation = [
  { to: '/', label: 'Dashboard' },
  { to: '/sources', label: 'Sources' },
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
  const { source, setSource, mode, setMode } = useUISettings()

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
