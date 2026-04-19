## Context

The React frontend (7 pages, React 18 + TypeScript + Vite + Tailwind) has zero automated tests. The backend has 529 unit/API tests with 80%+ coverage, but the frontend — which is the primary user interface — has no Playwright config, no test files, and no formal user stories. Two user profiles exist (`user` and `developer`) toggled via a global `Mode` dropdown, but only the Chat page reacts to it today. The seed dataset (2 matches) is loaded and the backend API is fully functional, so E2E tests can validate real end-to-end flows.

## Goals / Non-Goals

**Goals:**
- Document 24 user stories covering all 7 pages x 2 profiles as acceptance criteria
- Set up Playwright infrastructure (config, install, npm scripts)
- Create E2E test suites that validate each user story with real backend data (seed)
- Auto-generate a visual user manual (`docs/user-manual.md`) with screenshots from test runs
- Clean up phantom `match_id=900001` that pollutes Explorer/Matches views
- Add E2E step to CI pipeline

**Non-Goals:**
- Component-level unit tests (Vitest/Testing Library) — separate effort
- Fixing frontend bugs found during testing — file issues, don't fix inline
- Changing page behavior or layout
- Adding new pages or features

## Decisions

### 1. Playwright over Cypress
Playwright supports multi-browser, is faster, has built-in screenshot/video APIs, and the project already has a `/e2e-playwright` skill defined. No contest.

### 2. Tests run against real Docker stack (not mocked)
E2E tests hit the real backend + DBs with seed data loaded. This validates the true user experience. Tests require `docker compose up` as a prerequisite (same as development).

### 3. User stories as test descriptions
Each `test()` block maps 1:1 to a user story ID (e.g., `test('US-12: fan sees competitions loaded in DB')`). This makes test output a living requirements document.

### 4. Screenshot-based user manual
Each test captures a screenshot at key moments. A post-test script assembles screenshots + descriptions into `docs/user-manual.md`. This keeps the manual always in sync with the actual UI.

### 5. User stories stored in `docs/user-stories.md`
A single markdown file with a table of all stories, their page, profile, and acceptance criteria. Tests reference the story IDs. This is the source of truth for "what should the app do".

## File change list

| File | Status | Description |
|------|--------|-------------|
| `docs/user-stories.md` | (new) | 24 user stories with acceptance criteria |
| `docs/user-manual.md` | (new) | Auto-generated visual manual with screenshots |
| `frontend/webapp/playwright.config.ts` | (new) | Playwright configuration |
| `frontend/webapp/package.json` | (modified) | Add Playwright devDependency + scripts |
| `frontend/webapp/tests/e2e/home.spec.ts` | (new) | US-01, US-02 |
| `frontend/webapp/tests/e2e/dashboard.spec.ts` | (new) | US-03, US-04, US-05 |
| `frontend/webapp/tests/e2e/catalog.spec.ts` | (new) | US-06, US-07 |
| `frontend/webapp/tests/e2e/operations.spec.ts` | (new) | US-08 to US-11 |
| `frontend/webapp/tests/e2e/explorer.spec.ts` | (new) | US-12 to US-16 |
| `frontend/webapp/tests/e2e/embeddings.spec.ts` | (new) | US-17, US-18 |
| `frontend/webapp/tests/e2e/chat.spec.ts` | (new) | US-19 to US-22 |
| `frontend/webapp/tests/e2e/cross-cutting.spec.ts` | (new) | US-23, US-24 |
| `frontend/webapp/tests/e2e/generate-manual.ts` | (new) | Script to assemble screenshots into markdown |
| `.github/workflows/ci.yml` | (modified) | Add E2E test job |
| `.devcontainer/post-create.sh` | (modified) | Remove phantom match_id=900001 |

## Risks / Trade-offs

- **[Flaky tests from network timing]** → Use `waitForLoadState('networkidle')` and explicit selectors with `waitForSelector`. Avoid `waitForTimeout`.
- **[CI requires full Docker stack]** → E2E job needs `services:` for postgres + sqlserver + backend. Increases CI time ~2-3 min. Acceptable for E2E coverage.
- **[Screenshots break on UI changes]** → Screenshots are regenerated on every test run. The manual is auto-generated, not hand-maintained. UI changes automatically update the manual.
- **[Seed data dependency]** → Tests assume seed matches (3943043, 3869685) are loaded. CI must run `make seed` before E2E. If seed changes, tests need updating.

## Rollback strategy

All changes are additive (new files + minor modifications). To rollback:
1. Remove `frontend/webapp/tests/e2e/` directory
2. Revert `package.json` Playwright dependencies
3. Revert CI workflow changes
4. No database or backend changes to roll back
