# User Stories — RAG-Challenge

User stories for the Football Analytics Platform, organized by page and user profile.

**Profiles:**
- **User** — football fan exploring data and asking questions
- **Developer** — learning RAG architecture, managing pipeline, comparing algorithms

## Stories

| ID | Page | Profile | Description | Acceptance Criteria |
|----|------|---------|-------------|---------------------|
| US-01 | Home | User | See introduction, feature cards, and 3-step quick start guide | Hero section, 3 feature cards (Catalog, Explorer, Chat), numbered guide visible |
| US-02 | Home | Developer | See technical architecture, RAG flow, and API reference | Backend/frontend stacks, RAG data flow diagram, API endpoints section visible |
| US-03 | Dashboard | Developer | See system health status (API, PostgreSQL, SQL Server) | Health alive, readiness ready, both sources connected |
| US-04 | Dashboard | Developer | See capabilities matrix per source | Embedding models and search algorithms shown for postgres and sqlserver |
| US-05 | Dashboard | Developer | See recent ingestion jobs | Jobs section visible (empty or with entries) |
| US-06 | Catalog | Developer | Browse StatsBomb competitions | Competitions list loads with 50+ entries |
| US-07 | Catalog | Developer | Select competition/season to see matches | Selecting a competition+season shows available matches |
| US-08 | Operations | Developer | Execute pipeline step by step | Pipeline buttons visible (download, load, aggregate, summaries, embeddings) |
| US-09 | Operations | Developer | Execute full pipeline in one step | Full-pipeline action available |
| US-10 | Operations | Developer | See real-time job progress in terminal | Job status, progress, and logs visible with auto-refresh |
| US-11 | Operations | Developer | Clean up jobs and downloads | Clear jobs and cleanup actions available |
| US-12 | Explorer | Both | See competitions loaded in the database | At least 2 competitions visible (UEFA Euro, FIFA World Cup) after seed |
| US-13 | Explorer | Both | See matches with results | Seed matches visible (Spain vs England, Argentina vs France) |
| US-14 | Explorer | Both | See teams and players for a match | Teams tab shows participating teams for selected match |
| US-15 | Explorer | Both | See detailed events for a match | Events tab shows event details for selected match |
| US-16 | Explorer | Developer | See database table info (row counts, columns) | Tables tab shows table names, row counts, embedding columns |
| US-17 | Embeddings | Developer | See embedding coverage by model | Total rows, coverage per model, status counts (done/pending/error) |
| US-18 | Embeddings | Developer | Rebuild embeddings for a match | Rebuild action with model and match selectors |
| US-19 | Chat | User | Select a match and ask a question | Match selector and question input enabled, submit button works |
| US-20 | Chat | User | Receive RAG answer from real match data | Answer displayed referencing actual match events |
| US-21 | Chat | Developer | Choose embedding model and search algorithm | Model and algorithm dropdowns visible in developer mode |
| US-22 | Chat | Developer | See similarity scores and retrieved fragments | Scores and event summaries shown per result in developer mode |
| US-23 | Cross-cutting | Both | Switch between PostgreSQL and SQL Server | Source dropdown changes data on all pages |
| US-24 | Cross-cutting | Both | App works with seed data out of the box | Explorer and Chat functional after `make seed` without extra config |
