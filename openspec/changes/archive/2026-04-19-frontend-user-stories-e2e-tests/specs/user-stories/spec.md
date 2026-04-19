## ADDED Requirements

### Requirement: User stories document exists
The system SHALL maintain a `docs/user-stories.md` file documenting all user stories with ID, page, profile, description, and acceptance criteria.

#### Scenario: User stories cover all pages
- **WHEN** a developer reads `docs/user-stories.md`
- **THEN** every page (Home, Dashboard, Catalog, Operations, Explorer, Embeddings, Chat) SHALL have at least one user story

#### Scenario: User stories cover both profiles
- **WHEN** a developer reads `docs/user-stories.md`
- **THEN** both profiles (`user` and `developer`) SHALL have user stories defined

### Requirement: Home page — fan view (US-01)
The Home page SHALL display an introduction to the platform, feature cards (Catalog, Explorer, Chat), and a 3-step quick start guide when the fan view is selected.

#### Scenario: Fan view displays features and guide
- **GIVEN** user navigates to `/`
- **WHEN** the fan view toggle is active
- **THEN** the page SHALL show a hero section, 3 feature cards, and a numbered quick start guide

### Requirement: Home page — developer view (US-02)
The Home page SHALL display the technical architecture (backend/frontend stacks), RAG data flow diagram, and API endpoint reference when the developer view is selected.

#### Scenario: Developer view displays architecture
- **GIVEN** user navigates to `/`
- **WHEN** the developer view toggle is active
- **THEN** the page SHALL show backend stack, frontend stack, RAG flow diagram, and API endpoints

### Requirement: Dashboard — system health (US-03)
The Dashboard SHALL display the health status of the API, PostgreSQL, and SQL Server.

#### Scenario: Dashboard shows all health checks green
- **GIVEN** user navigates to `/dashboard`
- **WHEN** all services are running
- **THEN** the page SHALL show health status as alive, readiness as ready, and both DB sources as connected

### Requirement: Dashboard — capabilities (US-04)
The Dashboard SHALL display the capabilities matrix for each source (embedding models, search algorithms).

#### Scenario: Dashboard shows capabilities per source
- **GIVEN** user navigates to `/dashboard`
- **WHEN** capabilities are loaded
- **THEN** the page SHALL show the available embedding models and search algorithms for postgres and sqlserver

### Requirement: Dashboard — recent jobs (US-05)
The Dashboard SHALL display the most recent ingestion jobs with their status.

#### Scenario: Dashboard shows empty jobs when none executed
- **GIVEN** user navigates to `/dashboard`
- **WHEN** no jobs have been executed
- **THEN** the jobs section SHALL be visible but indicate no recent jobs

### Requirement: Catalog — browse competitions (US-06)
The Catalog page SHALL display all StatsBomb competitions grouped by competition, allowing the user to browse seasons and matches.

#### Scenario: Catalog loads competitions from StatsBomb
- **GIVEN** user navigates to `/catalog`
- **WHEN** the page loads
- **THEN** the page SHALL display competitions from the StatsBomb Open Data API with at least 50 entries

### Requirement: Catalog — select matches (US-07)
The Catalog page SHALL allow selecting matches for download, persisting the selection in localStorage.

#### Scenario: User selects matches from a competition
- **GIVEN** user is on `/catalog` with competitions loaded
- **WHEN** the user selects a competition and season
- **THEN** the page SHALL display available matches for that season

### Requirement: Operations — step-by-step pipeline (US-08)
The Operations page SHALL allow executing the ingestion pipeline step by step (download, load, aggregate, summaries, embeddings).

#### Scenario: Operations shows pipeline controls
- **GIVEN** user navigates to `/operations`
- **WHEN** the page loads
- **THEN** the page SHALL display pipeline action buttons (download, load, aggregate, etc.)

### Requirement: Operations — full pipeline (US-09)
The Operations page SHALL allow executing the full pipeline in a single action.

#### Scenario: Full pipeline button is available
- **GIVEN** user navigates to `/operations`
- **WHEN** the page loads
- **THEN** a full-pipeline action SHALL be available

### Requirement: Operations — job terminal (US-10)
The Operations page SHALL display real-time job progress in a terminal-like output.

#### Scenario: Job progress displays in terminal
- **GIVEN** a pipeline job is running
- **WHEN** the user views the operations page
- **THEN** the job status, progress, and logs SHALL be visible with auto-refresh

### Requirement: Operations — cleanup (US-11)
The Operations page SHALL allow clearing completed jobs and cleaning up download files.

#### Scenario: Clear jobs button works
- **GIVEN** user navigates to `/operations`
- **WHEN** the page loads
- **THEN** a clear jobs action SHALL be available

### Requirement: Explorer — competitions (US-12)
The Explorer page SHALL display competitions loaded in the selected database source.

#### Scenario: Explorer shows seed competitions
- **GIVEN** user navigates to `/explorer` with seed data loaded
- **WHEN** the page loads on the Competitions tab
- **THEN** the page SHALL display at least 2 competitions (UEFA Euro, FIFA World Cup)

### Requirement: Explorer — matches (US-13)
The Explorer page SHALL display matches with their results from the selected source.

#### Scenario: Explorer shows seed matches
- **GIVEN** user navigates to `/explorer` with seed data loaded
- **WHEN** the user views the Matches tab
- **THEN** the page SHALL display the seed matches (Spain vs England, Argentina vs France)

### Requirement: Explorer — teams and players (US-14)
The Explorer page SHALL display teams and players for a selected match.

#### Scenario: Explorer shows teams for a match
- **GIVEN** user is on `/explorer` with a match selected
- **WHEN** the user views the Teams tab
- **THEN** the page SHALL display teams that participated in the selected match

### Requirement: Explorer — events (US-15)
The Explorer page SHALL display detailed events for a selected match.

#### Scenario: Explorer shows events for a match
- **GIVEN** user is on `/explorer` with a match selected
- **WHEN** the user views the Events tab
- **THEN** the page SHALL display event details for the match

### Requirement: Explorer — tables info (US-16)
The Explorer page SHALL display database table information (row counts, columns) for the developer profile.

#### Scenario: Explorer shows table info
- **GIVEN** user is on `/explorer`
- **WHEN** the user views the Tables tab
- **THEN** the page SHALL display table names, row counts, and embedding columns

### Requirement: Embeddings — coverage (US-17)
The Embeddings page SHALL display embedding coverage statistics by model.

#### Scenario: Embeddings shows coverage for seed data
- **GIVEN** user navigates to `/embeddings` with seed data loaded
- **WHEN** the page loads
- **THEN** the page SHALL show total rows, coverage per model, and status counts (done/pending/error)

### Requirement: Embeddings — rebuild (US-18)
The Embeddings page SHALL allow rebuilding embeddings for a selected match and model.

#### Scenario: Rebuild button is available
- **GIVEN** user navigates to `/embeddings`
- **WHEN** the page loads with matches available
- **THEN** a rebuild action SHALL be available with model and match selectors

### Requirement: Chat — user asks question (US-19)
The Chat page in user mode SHALL allow selecting a match and asking a natural language question.

#### Scenario: User submits a question in user mode
- **GIVEN** user navigates to `/chat` in user mode
- **WHEN** the user selects a match and types a question
- **THEN** a submit button SHALL be enabled

### Requirement: Chat — answer from RAG (US-20)
The Chat page SHALL display an answer generated by the RAG pipeline based on real match data.

#### Scenario: Chat returns an answer for seed data
- **GIVEN** user is on `/chat` with a seed match selected
- **WHEN** the user asks "Who scored the first goal?"
- **THEN** the page SHALL display an answer referencing actual match events

### Requirement: Chat — developer controls (US-21)
The Chat page in developer mode SHALL allow selecting embedding model and search algorithm.

#### Scenario: Developer mode shows model and algorithm selectors
- **GIVEN** user navigates to `/chat` with mode set to developer
- **WHEN** the page loads
- **THEN** the page SHALL show dropdown selectors for embedding model and search algorithm

### Requirement: Chat — similarity scores (US-22)
The Chat page in developer mode SHALL display similarity scores and retrieved fragments alongside the answer.

#### Scenario: Developer mode shows search results with scores
- **GIVEN** user is on `/chat` in developer mode with a search completed
- **WHEN** the answer is displayed
- **THEN** the page SHALL show similarity scores and event summaries for each retrieved result

### Requirement: Source switching (US-23)
The system SHALL allow switching between PostgreSQL and SQL Server at any time via the Source dropdown, and all pages SHALL reflect the selected source.

#### Scenario: Source switch updates data
- **GIVEN** user is on any data page (Explorer, Embeddings, Chat)
- **WHEN** the user changes the Source dropdown from postgres to sqlserver
- **THEN** the page SHALL reload data from the newly selected source

### Requirement: Seed data available out of the box (US-24)
The system SHALL display functional data on Explorer and Chat pages without any additional configuration after running `make seed`.

#### Scenario: Explorer has data after seed load
- **GIVEN** Docker stack is running and `make seed` has been executed
- **WHEN** user navigates to `/explorer`
- **THEN** the page SHALL display at least 2 matches with competitions, teams, and events
