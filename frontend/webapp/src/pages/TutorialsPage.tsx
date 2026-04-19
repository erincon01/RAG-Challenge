const REPO_BASE = 'https://github.com/erincon01/RAG-Challenge/blob/develop'

const tutorials = [
  {
    id: '01',
    title: 'Your First Semantic Search',
    description:
      'End-to-end RAG walkthrough: ask a question about the Euro 2024 Final, understand how the pipeline normalizes, embeds, searches, and generates an answer.',
    path: '/docs/tutorials/01-first-semantic-search.md',
    tags: ['RAG', 'curl', 'cosine', 'beginner'],
  },
  {
    id: '02',
    title: 'Comparing Search Algorithms',
    description:
      'Run the same question with cosine, inner product, and L2 Euclidean distance. See how scores differ but rankings stay the same with normalized embeddings.',
    path: '/docs/tutorials/02-comparing-search-algorithms.md',
    tags: ['cosine', 'inner product', 'L2', 'intermediate'],
  },
  {
    id: '03',
    title: 'Understanding Embeddings',
    description:
      'What are 1536-dimensional vectors? How does text become numbers? How the project splits matches into 15-second buckets and embeds each one.',
    path: '/docs/tutorials/03-understanding-embeddings.md',
    tags: ['embeddings', 'vectors', 'OpenAI', 'conceptual'],
  },
]

const resources = [
  { label: 'Golden Set (12 evaluation questions)', path: '/data/golden_set.json' },
  { label: 'User Stories (24 acceptance criteria)', path: '/docs/user-stories.md' },
  { label: 'User Manual (screenshots)', path: '/docs/user-manual.md' },
  { label: 'SQL Server Setup Guide', path: '/docs/sql-server-setup.md' },
  { label: 'Getting Started', path: '/docs/getting-started.md' },
]

export function TutorialsPage() {
  return (
    <div className="space-y-6">
      <header className="rounded-2xl border border-white/10 bg-panel/70 p-6">
        <h1 className="text-2xl font-bold text-ink">Tutorials</h1>
        <p className="mt-2 text-sm text-mute">
          Learn how the RAG pipeline works with step-by-step guides using the seed data (Euro 2024 Final + WC 2022
          Final).
        </p>
      </header>

      <div className="grid gap-4 lg:grid-cols-3">
        {tutorials.map((t) => (
          <a
            key={t.id}
            href={`${REPO_BASE}${t.path}`}
            target="_blank"
            rel="noopener noreferrer"
            className="group rounded-2xl border border-white/10 bg-panel/70 p-6 transition hover:border-accent/40 hover:bg-panel/80"
          >
            <div className="mb-3 flex items-center gap-2">
              <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-accent/15 text-sm font-bold text-accent">
                {t.id}
              </span>
              <h2 className="text-lg font-semibold text-ink">{t.title}</h2>
            </div>
            <p className="mb-4 text-sm text-mute">{t.description}</p>
            <div className="flex flex-wrap gap-2">
              {t.tags.map((tag) => (
                <span
                  key={tag}
                  className="rounded-full border border-white/10 bg-canvas/60 px-2 py-0.5 text-xs text-mute"
                >
                  {tag}
                </span>
              ))}
            </div>
          </a>
        ))}
      </div>

      <article className="rounded-2xl border border-white/10 bg-panel/70 p-6">
        <h2 className="mb-4 text-lg font-semibold text-ink">Resources</h2>
        <ul className="space-y-2">
          {resources.map((r) => (
            <li key={r.path}>
              <a
                href={`${REPO_BASE}${r.path}`}
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm text-accent hover:underline"
              >
                {r.label}
              </a>
            </li>
          ))}
        </ul>
      </article>
    </div>
  )
}
