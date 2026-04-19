## Why

The frontend has 7 pages and 2 user profiles (user/developer) but zero tests — no E2E, no Playwright, no user stories. Several pages appear empty or broken (Catalog, Explorer, Operations) with no way to know if it's a bug or expected behavior. Without defined user stories and E2E tests, every change risks silent regressions. The seed dataset (#48) made the app functional out of the box, but there's no automated verification that the happy paths actually work.

## What Changes

- Define **24 user stories** covering all 7 pages across both user profiles (user and developer)
- Set up **Playwright** for E2E testing (config, dependencies, CI integration)
- Create **E2E test suites** for each page validating the user stories
- Generate a **visual user manual** (`docs/user-manual.md`) with annotated screenshots captured by Playwright during test runs
- Fix the **phantom match_id=900001** still present in the database (legacy placeholder)

## Capabilities

### New Capabilities
- `e2e-testing`: Playwright E2E test infrastructure, test suites for all 7 pages, screenshot capture, and visual manual generation
- `user-stories`: Documented user stories for both profiles (user/developer) across all pages, serving as acceptance criteria for E2E tests

### Modified Capabilities
- `api`: No requirement changes — API endpoints are correct; frontend integration issues are UI-side only

## Impact

- **Frontend** (`frontend/webapp/`): new `tests/e2e/` directory, `playwright.config.ts`, Playwright dependencies in `package.json`
- **Docs** (`docs/user-manual.md`): auto-generated visual manual with screenshots
- **CI** (`.github/workflows/ci.yml`): add E2E test step (requires Docker services for backend)
- **Data**: remove phantom `match_id=900001` from seed/init scripts
- **Backward compatibility**: fully backward-compatible — adds tests and docs, no behavior changes
- **Affected layers**: Frontend only (no API, Service, Repository, or Domain changes)
- **Test impact**: adds ~24 E2E tests; existing 529 backend tests unaffected
