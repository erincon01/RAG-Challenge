/**
 * Generate a visual user manual from E2E test screenshots.
 *
 * Reads screenshots from tests/e2e/screenshots/ and generates
 * docs/user-manual.md with embedded images and descriptions.
 *
 * Usage: npx tsx tests/e2e/generate-manual.ts
 */

import { readdirSync, writeFileSync } from 'fs'
import { resolve, dirname } from 'path'
import { fileURLToPath } from 'url'

const __filename = fileURLToPath(import.meta.url)
const __dirname = dirname(__filename)

const SCREENSHOTS_DIR = resolve(__dirname, 'screenshots')
const OUTPUT_PATH = resolve(__dirname, '..', '..', '..', '..', 'docs', 'user-manual.md')
const IMG_REL_PATH = '../frontend/webapp/tests/e2e/screenshots'

interface Section {
  title: string
  description: string
  screenshots: { file: string; caption: string }[]
}

const sections: Section[] = [
  {
    title: 'Home',
    description: 'Landing page with two views: fan (football enthusiast) and developer (learning RAG architecture).',
    screenshots: [
      { file: 'home-fan.png', caption: 'Fan view — hero section, feature cards, and quick start guide' },
      { file: 'home-developer.png', caption: 'Developer view — architecture, RAG data flow, and API endpoints' },
    ],
  },
  {
    title: 'Dashboard',
    description: 'System health monitor showing API status, database connectivity, capabilities, and recent jobs.',
    screenshots: [
      { file: 'dashboard-health.png', caption: 'System health: API status, readiness, sources, capabilities matrix' },
    ],
  },
  {
    title: 'Catalog (StatsBomb)',
    description: 'Browse the StatsBomb Open Data catalog. Select competitions and seasons to see available matches.',
    screenshots: [
      { file: 'catalog-competitions.png', caption: 'Competitions browser with season grouping' },
      { file: 'catalog-matches.png', caption: 'Matches list for a selected competition/season' },
    ],
  },
  {
    title: 'Operations (Pipeline)',
    description: 'Execute the ingestion pipeline: download, load, aggregate, generate summaries, and create embeddings.',
    screenshots: [
      { file: 'operations-controls.png', caption: 'Pipeline controls: step-by-step or full pipeline execution' },
    ],
  },
  {
    title: 'Explorer',
    description: 'Browse data loaded in the database: competitions, matches, teams, players, events, and table info.',
    screenshots: [
      { file: 'explorer-competitions.png', caption: 'Competitions loaded in the selected database' },
      { file: 'explorer-matches.png', caption: 'Matches with results and match selector' },
      { file: 'explorer-teams.png', caption: 'Teams participating in the selected match' },
      { file: 'explorer-events.png', caption: 'Detailed events for the selected match' },
      { file: 'explorer-tables.png', caption: 'Database tables with row counts and embedding columns' },
    ],
  },
  {
    title: 'Embeddings',
    description: 'Monitor embedding coverage and rebuild embeddings for specific matches.',
    screenshots: [
      { file: 'embeddings-coverage.png', caption: 'Embedding coverage by model with status counts' },
    ],
  },
  {
    title: 'Chat (RAG Search)',
    description:
      'Ask natural language questions about football matches. User mode shows clean Q&A; developer mode exposes model selection, algorithm choice, and similarity scores.',
    screenshots: [
      { file: 'chat-user-question.png', caption: 'User mode — match selector and question input' },
      { file: 'chat-user-answer.png', caption: 'User mode — RAG answer from real match data' },
      { file: 'chat-developer-controls.png', caption: 'Developer mode — embedding model and algorithm selectors' },
      { file: 'chat-developer-results.png', caption: 'Developer mode — similarity scores and retrieved fragments' },
    ],
  },
  {
    title: 'Source Switching',
    description: 'Switch between PostgreSQL and SQL Server at any time using the Source dropdown in the header.',
    screenshots: [
      { file: 'source-postgres.png', caption: 'PostgreSQL as active source' },
      { file: 'source-sqlserver.png', caption: 'SQL Server as active source' },
    ],
  },
]

function generate(): void {
  const existingFiles = new Set(readdirSync(SCREENSHOTS_DIR).filter((f) => f.endsWith('.png')))

  let md = '# User Manual — Football Analytics Platform\n\n'
  md += '> Auto-generated from E2E test screenshots. Do not edit manually.\n'
  md += '> Regenerate with: `cd frontend/webapp && npx tsx tests/e2e/generate-manual.ts`\n\n'
  md += '---\n\n'

  for (const section of sections) {
    md += `## ${section.title}\n\n`
    md += `${section.description}\n\n`

    for (const shot of section.screenshots) {
      if (existingFiles.has(shot.file)) {
        md += `### ${shot.caption}\n\n`
        md += `![${shot.caption}](${IMG_REL_PATH}/${shot.file})\n\n`
      } else {
        md += `### ${shot.caption}\n\n`
        md += `> Screenshot not yet captured: \`${shot.file}\`\n\n`
      }
    }

    md += '---\n\n'
  }

  writeFileSync(OUTPUT_PATH, md, 'utf-8')
  console.log(`Generated: ${OUTPUT_PATH}`)
  console.log(`Sections: ${sections.length}`)
  console.log(`Screenshots: ${sections.reduce((n, s) => n + s.screenshots.length, 0)} defined, ${existingFiles.size} available`)
}

generate()
