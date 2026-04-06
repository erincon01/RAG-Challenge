import { useState } from 'react'

type ViewMode = 'fan' | 'developer'

export function HomePage() {
  const [view, setView] = useState<ViewMode>('fan')

  return (
    <div className="space-y-4">
      {/* Header with view toggle */}
      <header className="rounded-2xl border border-white/10 bg-panel/70 p-6">
        <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div>
            <h1 className="text-3xl font-bold text-ink">Football Analytics Platform</h1>
            <p className="mt-2 text-sm text-mute">
              Análisis profesional de datos de fútbol con tecnología RAG y vectorización semántica
            </p>
          </div>
          <div className="flex gap-2">
            <button
              type="button"
              onClick={() => setView('fan')}
              className={`rounded-xl px-4 py-2 text-sm font-semibold transition ${
                view === 'fan'
                  ? 'bg-accent/20 text-accent shadow-glow'
                  : 'border border-white/10 bg-canvas/60 text-mute hover:text-ink'
              }`}
            >
              ⚽ Vista Fan
            </button>
            <button
              type="button"
              onClick={() => setView('developer')}
              className={`rounded-xl px-4 py-2 text-sm font-semibold transition ${
                view === 'developer'
                  ? 'bg-accent/20 text-accent shadow-glow'
                  : 'border border-white/10 bg-canvas/60 text-mute hover:text-ink'
              }`}
            >
              💻 Vista Developer
            </button>
          </div>
        </div>
      </header>

      {/* Fan View */}
      {view === 'fan' && (
        <div className="space-y-4">
          {/* Hero section */}
          <article className="rounded-2xl border border-white/10 bg-gradient-to-br from-accent/10 to-transparent p-8">
            <div className="flex flex-col gap-6 md:flex-row md:items-center">
              <div className="flex-1">
                <h2 className="text-2xl font-bold text-ink">Analiza el fútbol como nunca antes</h2>
                <p className="mt-3 text-mute">
                  Accede a datos profesionales de StatsBomb Open Data y descubre insights profundos sobre tus equipos y
                  jugadores favoritos usando inteligencia artificial.
                </p>
              </div>
              <div className="flex items-center justify-center text-6xl">⚽</div>
            </div>
          </article>

          {/* Features grid */}
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {/* Feature 1: Catálogo */}
            <article className="group rounded-2xl border border-white/10 bg-panel/70 p-6 transition hover:border-accent/40 hover:bg-panel/80">
              <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-accent/10 text-2xl">
                📚
              </div>
              <h3 className="mb-2 text-lg font-semibold text-ink">Catálogo Completo</h3>
              <p className="text-sm text-mute">
                Explora competiciones internacionales, ligas nacionales y cientos de partidos con datos completos de
                eventos.
              </p>
              <div className="mt-4 text-xs font-medium text-accent">Ir a Catálogo →</div>
            </article>

            {/* Feature 2: Explorador */}
            <article className="group rounded-2xl border border-white/10 bg-panel/70 p-6 transition hover:border-accent/40 hover:bg-panel/80">
              <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-accent/10 text-2xl">
                🔍
              </div>
              <h3 className="mb-2 text-lg font-semibold text-ink">Explorador Visual</h3>
              <p className="text-sm text-mute">
                Consulta datos en tiempo real con filtros inteligentes. Pases, tiros, regates... todo al alcance de un
                clic.
              </p>
              <div className="mt-4 text-xs font-medium text-accent">Explorar Datos →</div>
            </article>

            {/* Feature 3: Chat */}
            <article className="group rounded-2xl border border-white/10 bg-panel/70 p-6 transition hover:border-accent/40 hover:bg-panel/80">
              <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-accent/10 text-2xl">
                💬
              </div>
              <h3 className="mb-2 text-lg font-semibold text-ink">Chat Inteligente</h3>
              <p className="text-sm text-mute">
                Pregunta en lenguaje natural. "¿Cuántos goles marcó Messi en 2015?" La IA te responde con datos reales.
              </p>
              <div className="mt-4 text-xs font-medium text-accent">Probar Chat →</div>
            </article>
          </div>

          {/* Quick start guide */}
          <article className="rounded-2xl border border-white/10 bg-panel/70 p-6">
            <h3 className="mb-4 text-xl font-semibold text-ink">🚀 Guía Rápida</h3>
            <div className="space-y-4">
              <div className="flex gap-4">
                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-accent/20 text-sm font-bold text-accent">
                  1
                </div>
                <div>
                  <h4 className="font-medium text-ink">Selecciona una competición</h4>
                  <p className="text-sm text-mute">Ve al Catálogo y elige tu liga o torneo favorito</p>
                </div>
              </div>
              <div className="flex gap-4">
                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-accent/20 text-sm font-bold text-accent">
                  2
                </div>
                <div>
                  <h4 className="font-medium text-ink">Descarga los datos</h4>
                  <p className="text-sm text-mute">En Descarga y Carga, procesa los partidos que te interesan</p>
                </div>
              </div>
              <div className="flex gap-4">
                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-accent/20 text-sm font-bold text-accent">
                  3
                </div>
                <div>
                  <h4 className="font-medium text-ink">Explora y pregunta</h4>
                  <p className="text-sm text-mute">
                    Usa el Explorador para visualizar o el Chat para preguntar lo que quieras
                  </p>
                </div>
              </div>
            </div>
          </article>

          {/* Data source info */}
          <article className="rounded-2xl border border-white/10 bg-panel/70 p-6">
            <h3 className="mb-3 text-lg font-semibold text-ink">📊 Sobre los Datos</h3>
            <p className="text-sm text-mute">
              Esta plataforma utiliza{' '}
              <a
                href="https://github.com/statsbomb/open-data"
                target="_blank"
                rel="noopener noreferrer"
                className="font-medium text-accent hover:underline"
              >
                StatsBomb Open Data
              </a>
              , una de las fuentes más completas y precisas de datos de fútbol profesional. Incluye eventos detallados
              como pases, tiros, regates, presiones y mucho más de ligas de todo el mundo.
            </p>
          </article>
        </div>
      )}

      {/* Developer View */}
      {view === 'developer' && (
        <div className="space-y-4">
          {/* Architecture overview */}
          <article className="rounded-2xl border border-white/10 bg-panel/70 p-6">
            <h2 className="mb-4 text-2xl font-bold text-ink">🏗️ Arquitectura del Sistema</h2>
            <p className="mb-6 text-sm text-mute">
              Plataforma RAG (Retrieval-Augmented Generation) multi-base de datos con vectorización semántica y chat
              inteligente
            </p>

            <div className="grid gap-4 lg:grid-cols-2">
              {/* Backend Stack */}
              <div className="rounded-xl border border-white/10 bg-canvas/60 p-4">
                <h3 className="mb-3 flex items-center gap-2 font-semibold text-ink">
                  <span className="text-xl">🐍</span>
                  Backend Stack
                </h3>
                <ul className="space-y-2 text-sm">
                  <li className="flex items-start gap-2">
                    <span className="text-accent">•</span>
                    <div>
                      <span className="font-medium text-ink">FastAPI</span>
                      <span className="text-mute"> - API REST asíncrona</span>
                    </div>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-accent">•</span>
                    <div>
                      <span className="font-medium text-ink">PostgreSQL + pgvector</span>
                      <span className="text-mute"> - Búsqueda vectorial nativa</span>
                    </div>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-accent">•</span>
                    <div>
                      <span className="font-medium text-ink">SQL Server</span>
                      <span className="text-mute"> - Almacenamiento alternativo</span>
                    </div>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-accent">•</span>
                    <div>
                      <span className="font-medium text-ink">OpenAI Embeddings</span>
                      <span className="text-mute"> - text-embedding-3-small</span>
                    </div>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-accent">•</span>
                    <div>
                      <span className="font-medium text-ink">LangChain</span>
                      <span className="text-mute"> - Orquestación RAG</span>
                    </div>
                  </li>
                </ul>
              </div>

              {/* Frontend Stack */}
              <div className="rounded-xl border border-white/10 bg-canvas/60 p-4">
                <h3 className="mb-3 flex items-center gap-2 font-semibold text-ink">
                  <span className="text-xl">⚛️</span>
                  Frontend Stack
                </h3>
                <ul className="space-y-2 text-sm">
                  <li className="flex items-start gap-2">
                    <span className="text-accent">•</span>
                    <div>
                      <span className="font-medium text-ink">React 18 + TypeScript</span>
                      <span className="text-mute"> - UI moderna y tipada</span>
                    </div>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-accent">•</span>
                    <div>
                      <span className="font-medium text-ink">Vite</span>
                      <span className="text-mute"> - Build tool ultrarrápido</span>
                    </div>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-accent">•</span>
                    <div>
                      <span className="font-medium text-ink">TanStack Query</span>
                      <span className="text-mute"> - Estado del servidor</span>
                    </div>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-accent">•</span>
                    <div>
                      <span className="font-medium text-ink">React Router</span>
                      <span className="text-mute"> - Navegación SPA</span>
                    </div>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-accent">•</span>
                    <div>
                      <span className="font-medium text-ink">TailwindCSS</span>
                      <span className="text-mute"> - Estilos utility-first</span>
                    </div>
                  </li>
                </ul>
              </div>
            </div>
          </article>

          {/* Data flow diagram */}
          <article className="rounded-2xl border border-white/10 bg-panel/70 p-6">
            <h3 className="mb-4 text-xl font-semibold text-ink">🔄 Flujo de Datos RAG</h3>
            <div className="overflow-x-auto">
              <div className="inline-flex min-w-full items-center justify-center gap-4 py-4">
                <div className="flex flex-col items-center gap-2">
                  <div className="rounded-xl border border-accent/40 bg-accent/10 px-4 py-3 text-center">
                    <div className="text-xs font-semibold uppercase tracking-wide text-accent">1. Ingesta</div>
                    <div className="mt-1 text-sm text-ink">StatsBomb JSON</div>
                  </div>
                </div>
                <div className="text-2xl text-accent">→</div>
                <div className="flex flex-col items-center gap-2">
                  <div className="rounded-xl border border-accent/40 bg-accent/10 px-4 py-3 text-center">
                    <div className="text-xs font-semibold uppercase tracking-wide text-accent">2. Transform</div>
                    <div className="mt-1 text-sm text-ink">Normalización SQL</div>
                  </div>
                </div>
                <div className="text-2xl text-accent">→</div>
                <div className="flex flex-col items-center gap-2">
                  <div className="rounded-xl border border-accent/40 bg-accent/10 px-4 py-3 text-center">
                    <div className="text-xs font-semibold uppercase tracking-wide text-accent">3. Embedding</div>
                    <div className="mt-1 text-sm text-ink">OpenAI API</div>
                  </div>
                </div>
                <div className="text-2xl text-accent">→</div>
                <div className="flex flex-col items-center gap-2">
                  <div className="rounded-xl border border-accent/40 bg-accent/10 px-4 py-3 text-center">
                    <div className="text-xs font-semibold uppercase tracking-wide text-accent">4. Vector DB</div>
                    <div className="mt-1 text-sm text-ink">pgvector</div>
                  </div>
                </div>
                <div className="text-2xl text-accent">→</div>
                <div className="flex flex-col items-center gap-2">
                  <div className="rounded-xl border border-accent/40 bg-accent/10 px-4 py-3 text-center">
                    <div className="text-xs font-semibold uppercase tracking-wide text-accent">5. RAG Query</div>
                    <div className="mt-1 text-sm text-ink">LangChain + LLM</div>
                  </div>
                </div>
              </div>
            </div>
          </article>

          {/* Technical features */}
          <div className="grid gap-4 lg:grid-cols-3">
            {/* Feature: Multi-DB */}
            <article className="rounded-2xl border border-white/10 bg-panel/70 p-6">
              <div className="mb-3 text-2xl">🗄️</div>
              <h3 className="mb-2 text-lg font-semibold text-ink">Multi-Database</h3>
              <p className="mb-3 text-sm text-mute">
                Switch dinámico entre PostgreSQL y SQL Server en runtime sin reinicios
              </p>
              <div className="rounded-lg bg-canvas/60 p-3 font-mono text-xs text-mute">
                <div>source: postgres | sqlserver</div>
                <div className="mt-1 text-accent"># Hot-swap capability</div>
              </div>
            </article>

            {/* Feature: Async Processing */}
            <article className="rounded-2xl border border-white/10 bg-panel/70 p-6">
              <div className="mb-3 text-2xl">⚡</div>
              <h3 className="mb-2 text-lg font-semibold text-ink">Async Jobs</h3>
              <p className="mb-3 text-sm text-mute">
                Sistema de trabajos en background con SSE para updates en tiempo real
              </p>
              <div className="rounded-lg bg-canvas/60 p-3 font-mono text-xs text-mute">
                <div>POST /ingestion/download</div>
                <div className="mt-1">GET /jobs/stream/:id</div>
                <div className="mt-1 text-accent"># Server-Sent Events</div>
              </div>
            </article>

            {/* Feature: Vector Search */}
            <article className="rounded-2xl border border-white/10 bg-panel/70 p-6">
              <div className="mb-3 text-2xl">🎯</div>
              <h3 className="mb-2 text-lg font-semibold text-ink">Semantic Search</h3>
              <p className="mb-3 text-sm text-mute">Búsqueda semántica con cosine similarity sobre 1536 dimensiones</p>
              <div className="rounded-lg bg-canvas/60 p-3 font-mono text-xs text-mute">
                <div>embedding &lt;=&gt; query</div>
                <div className="mt-1">ORDER BY similarity DESC</div>
                <div className="mt-1 text-accent"># Top-K retrieval</div>
              </div>
            </article>
          </div>

          {/* API endpoints */}
          <article className="rounded-2xl border border-white/10 bg-panel/70 p-6">
            <h3 className="mb-4 text-xl font-semibold text-ink">📡 API Endpoints Principales</h3>
            <div className="grid gap-3 md:grid-cols-2">
              <div className="rounded-lg border border-white/10 bg-canvas/60 p-3">
                <div className="mb-2 flex items-center gap-2">
                  <span className="rounded bg-blue-500/20 px-2 py-0.5 font-mono text-xs font-semibold text-blue-300">
                    GET
                  </span>
                  <span className="font-mono text-sm text-ink">/api/v1/health</span>
                </div>
                <p className="text-xs text-mute">Health check con info de capabilities</p>
              </div>

              <div className="rounded-lg border border-white/10 bg-canvas/60 p-3">
                <div className="mb-2 flex items-center gap-2">
                  <span className="rounded bg-green-500/20 px-2 py-0.5 font-mono text-xs font-semibold text-green-300">
                    POST
                  </span>
                  <span className="font-mono text-sm text-ink">/api/v1/ingestion/download</span>
                </div>
                <p className="text-xs text-mute">Descarga y procesa partidos de StatsBomb</p>
              </div>

              <div className="rounded-lg border border-white/10 bg-canvas/60 p-3">
                <div className="mb-2 flex items-center gap-2">
                  <span className="rounded bg-blue-500/20 px-2 py-0.5 font-mono text-xs font-semibold text-blue-300">
                    GET
                  </span>
                  <span className="font-mono text-sm text-ink">/api/v1/explorer/query</span>
                </div>
                <p className="text-xs text-mute">Consulta SQL con filtros dinámicos</p>
              </div>

              <div className="rounded-lg border border-white/10 bg-canvas/60 p-3">
                <div className="mb-2 flex items-center gap-2">
                  <span className="rounded bg-green-500/20 px-2 py-0.5 font-mono text-xs font-semibold text-green-300">
                    POST
                  </span>
                  <span className="font-mono text-sm text-ink">/api/v1/embeddings/rebuild</span>
                </div>
                <p className="text-xs text-mute">Re-genera embeddings de eventos</p>
              </div>

              <div className="rounded-lg border border-white/10 bg-canvas/60 p-3">
                <div className="mb-2 flex items-center gap-2">
                  <span className="rounded bg-green-500/20 px-2 py-0.5 font-mono text-xs font-semibold text-green-300">
                    POST
                  </span>
                  <span className="font-mono text-sm text-ink">/api/v1/chat/query</span>
                </div>
                <p className="text-xs text-mute">Chat RAG con contexto vectorial</p>
              </div>

              <div className="rounded-lg border border-white/10 bg-canvas/60 p-3">
                <div className="mb-2 flex items-center gap-2">
                  <span className="rounded bg-blue-500/20 px-2 py-0.5 font-mono text-xs font-semibold text-blue-300">
                    GET
                  </span>
                  <span className="font-mono text-sm text-ink">/api/v1/statsbomb/competitions</span>
                </div>
                <p className="text-xs text-mute">Lista catálogo de competiciones</p>
              </div>
            </div>
          </article>

          {/* Docker & DevContainer */}
          <article className="rounded-2xl border border-white/10 bg-panel/70 p-6">
            <h3 className="mb-4 text-xl font-semibold text-ink">🐳 Desarrollo y Deploy</h3>
            <div className="grid gap-4 lg:grid-cols-2">
              <div>
                <h4 className="mb-2 flex items-center gap-2 font-semibold text-ink">
                  <span>📦</span>
                  DevContainer
                </h4>
                <p className="mb-3 text-sm text-mute">Entorno completo con VS Code Remote Containers</p>
                <ul className="space-y-1 text-xs text-mute">
                  <li>• Python 3.11 + Node 22</li>
                  <li>• PostgreSQL 16 + pgvector</li>
                  <li>• SQL Server 2022</li>
                  <li>• Hot reload para desarrollo</li>
                </ul>
              </div>
              <div>
                <h4 className="mb-2 flex items-center gap-2 font-semibold text-ink">
                  <span>🚀</span>
                  Docker Compose
                </h4>
                <p className="mb-3 text-sm text-mute">Orquestación multi-servicio</p>
                <ul className="space-y-1 text-xs text-mute">
                  <li>• Backend FastAPI (8000)</li>
                  <li>• Frontend React (3000)</li>
                  <li>• Postgres + SQL Server</li>
                  <li>• Networks aisladas</li>
                </ul>
              </div>
            </div>
          </article>

          {/* Repository link */}
          <article className="rounded-2xl border border-white/10 bg-panel/70 p-6">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="mb-1 text-lg font-semibold text-ink">📂 Código Fuente</h3>
                <p className="text-sm text-mute">Explora la implementación completa en el repositorio</p>
              </div>
              <a
                href="https://github.com/statsbomb/open-data"
                target="_blank"
                rel="noopener noreferrer"
                className="rounded-xl border border-accent/40 bg-accent/10 px-4 py-2 text-sm font-semibold text-accent transition hover:bg-accent/20"
              >
                Ver en GitHub →
              </a>
            </div>
          </article>
        </div>
      )}
    </div>
  )
}
