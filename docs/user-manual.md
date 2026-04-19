# User Manual — Football Analytics Platform

> Auto-generated from E2E test screenshots. Do not edit manually.
> Regenerate with: `cd frontend/webapp && npx tsx tests/e2e/generate-manual.ts`

---

## Home

Landing page with two views: fan (football enthusiast) and developer (learning RAG architecture).

### Fan view — hero section, feature cards, and quick start guide

![Fan view — hero section, feature cards, and quick start guide](../frontend/webapp/tests/e2e/screenshots/home-fan.png)

### Developer view — architecture, RAG data flow, and API endpoints

![Developer view — architecture, RAG data flow, and API endpoints](../frontend/webapp/tests/e2e/screenshots/home-developer.png)

---

## Dashboard

System health monitor showing API status, database connectivity, capabilities, and recent jobs.

### System health: API status, readiness, sources, capabilities matrix

![System health: API status, readiness, sources, capabilities matrix](../frontend/webapp/tests/e2e/screenshots/dashboard-health.png)

---

## Catalog (StatsBomb)

Browse the StatsBomb Open Data catalog. Select competitions and seasons to see available matches.

### Competitions browser with season grouping

![Competitions browser with season grouping](../frontend/webapp/tests/e2e/screenshots/catalog-competitions.png)

### Matches list for a selected competition/season

![Matches list for a selected competition/season](../frontend/webapp/tests/e2e/screenshots/catalog-matches.png)

---

## Operations (Pipeline)

Execute the ingestion pipeline: download, load, aggregate, generate summaries, and create embeddings.

### Pipeline controls: step-by-step or full pipeline execution

![Pipeline controls: step-by-step or full pipeline execution](../frontend/webapp/tests/e2e/screenshots/operations-controls.png)

---

## Explorer

Browse data loaded in the database: competitions, matches, teams, players, events, and table info.

### Competitions loaded in the selected database

![Competitions loaded in the selected database](../frontend/webapp/tests/e2e/screenshots/explorer-competitions.png)

### Matches with results and match selector

![Matches with results and match selector](../frontend/webapp/tests/e2e/screenshots/explorer-matches.png)

### Teams participating in the selected match

![Teams participating in the selected match](../frontend/webapp/tests/e2e/screenshots/explorer-teams.png)

### Detailed events for the selected match

![Detailed events for the selected match](../frontend/webapp/tests/e2e/screenshots/explorer-events.png)

### Database tables with row counts and embedding columns

![Database tables with row counts and embedding columns](../frontend/webapp/tests/e2e/screenshots/explorer-tables.png)

---

## Embeddings

Monitor embedding coverage and rebuild embeddings for specific matches.

### Embedding coverage by model with status counts

![Embedding coverage by model with status counts](../frontend/webapp/tests/e2e/screenshots/embeddings-coverage.png)

---

## Chat (RAG Search)

Ask natural language questions about football matches. User mode shows clean Q&A; developer mode exposes model selection, algorithm choice, and similarity scores.

### User mode — match selector and question input

![User mode — match selector and question input](../frontend/webapp/tests/e2e/screenshots/chat-user-question.png)

### User mode — RAG answer from real match data

![User mode — RAG answer from real match data](../frontend/webapp/tests/e2e/screenshots/chat-user-answer.png)

### Developer mode — embedding model and algorithm selectors

![Developer mode — embedding model and algorithm selectors](../frontend/webapp/tests/e2e/screenshots/chat-developer-controls.png)

### Developer mode — similarity scores and retrieved fragments

![Developer mode — similarity scores and retrieved fragments](../frontend/webapp/tests/e2e/screenshots/chat-developer-results.png)

---

## Source Switching

Switch between PostgreSQL and SQL Server at any time using the Source dropdown in the header.

### PostgreSQL as active source

![PostgreSQL as active source](../frontend/webapp/tests/e2e/screenshots/source-postgres.png)

### SQL Server as active source

![SQL Server as active source](../frontend/webapp/tests/e2e/screenshots/source-sqlserver.png)

---

