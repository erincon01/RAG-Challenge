## ADDED Requirements

### Requirement: Playwright infrastructure
The project SHALL have Playwright configured in `frontend/webapp/` with `playwright.config.ts`, npm scripts, and Chromium browser installed.

#### Scenario: Playwright config exists and is valid
- **WHEN** a developer runs `cd frontend/webapp && npx playwright test --list`
- **THEN** the command SHALL list all available test files without errors

#### Scenario: npm script available
- **WHEN** a developer runs `cd frontend/webapp && npm run test:e2e`
- **THEN** Playwright SHALL execute all E2E tests

### Requirement: E2E test suites per page
The project SHALL have one E2E test file per page, each validating the corresponding user stories.

#### Scenario: All pages have test files
- **WHEN** a developer lists `frontend/webapp/tests/e2e/`
- **THEN** there SHALL be test files for home, dashboard, catalog, operations, explorer, embeddings, chat, and cross-cutting

#### Scenario: Tests map to user stories
- **WHEN** a developer reads a test file
- **THEN** each `test()` block SHALL reference a user story ID (e.g., `US-12`)

### Requirement: Tests run against real backend
E2E tests SHALL run against the real Docker stack (backend + databases) with seed data loaded. Tests MUST NOT mock the backend.

#### Scenario: Tests use real API
- **GIVEN** Docker stack is running with seed data
- **WHEN** E2E tests execute
- **THEN** tests SHALL make real HTTP requests to `http://localhost:8000` through the frontend at `http://localhost:5173`

### Requirement: Screenshot capture during tests
Each E2E test SHALL capture screenshots at key moments and store them in `frontend/webapp/tests/e2e/screenshots/`.

#### Scenario: Screenshots generated during test run
- **WHEN** Playwright tests complete
- **THEN** `frontend/webapp/tests/e2e/screenshots/` SHALL contain PNG screenshots for each page and key interaction

### Requirement: Visual user manual generation
The project SHALL include a script that assembles screenshots and descriptions into `docs/user-manual.md`.

#### Scenario: User manual generated from screenshots
- **WHEN** a developer runs the manual generation script after tests
- **THEN** `docs/user-manual.md` SHALL contain sections for each page with embedded screenshot images and descriptions

#### Scenario: User manual covers both profiles
- **WHEN** a developer reads `docs/user-manual.md`
- **THEN** the manual SHALL have sections for both user and developer views where applicable (Home, Chat)

### Requirement: CI integration
The CI pipeline SHALL include an E2E test job that runs after backend tests pass.

#### Scenario: CI runs E2E tests
- **WHEN** a PR is opened
- **THEN** the CI pipeline SHALL run E2E tests with Docker services (postgres, sqlserver, backend, frontend)

### Requirement: No phantom data
The database SHALL NOT contain phantom/placeholder data (e.g., `match_id=900001`) after seed loading.

#### Scenario: Only real seed matches present
- **GIVEN** seed data has been loaded
- **WHEN** querying `/api/v1/matches`
- **THEN** only match_ids 3943043 and 3869685 SHALL be returned
