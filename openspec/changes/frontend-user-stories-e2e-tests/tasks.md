## 1. User stories document

- [x] 1.1 Create `docs/user-stories.md` with the 24 user stories table (ID, page, profile, description, acceptance criteria)

## 2. Cleanup phantom data

- [x] 2.1 Remove `match_id=900001` from database init scripts and post-create.sh
- [x] 2.2 Verify `/api/v1/matches` only returns seed match_ids (3943043, 3869685)

## 3. Playwright infrastructure

- [x] 3.1 Add `@playwright/test` devDependency to `frontend/webapp/package.json`
- [x] 3.2 Create `frontend/webapp/playwright.config.ts` (baseURL: `http://localhost:5173`, chromium only, screenshots dir, networkidle timeout)
- [x] 3.3 Add npm scripts: `test:e2e`, `test:e2e:headed`, `test:e2e:screenshots`
- [x] 3.4 Install Playwright browsers: `npx playwright install --with-deps chromium`
- [x] 3.5 Verify `npx playwright test --list` works with an empty test dir

## 4. E2E tests — Home page

- [x] 4.1 Create `frontend/webapp/tests/e2e/home.spec.ts` with US-01 (fan view: hero, features, guide) and US-02 (developer view: stacks, RAG flow, endpoints)
- [x] 4.2 Capture screenshots: `home-fan.png`, `home-developer.png`
- [x] 4.3 Run test and verify passing: `npx playwright test home.spec.ts`

## 5. E2E tests — Dashboard page

- [x] 5.1 Create `frontend/webapp/tests/e2e/dashboard.spec.ts` with US-03 (health), US-04 (capabilities), US-05 (jobs)
- [x] 5.2 Capture screenshots: `dashboard-health.png`
- [x] 5.3 Run test and verify passing: `npx playwright test dashboard.spec.ts`

## 6. E2E tests — Catalog page

- [x] 6.1 Create `frontend/webapp/tests/e2e/catalog.spec.ts` with US-06 (browse competitions), US-07 (select matches)
- [x] 6.2 Capture screenshots: `catalog-competitions.png`, `catalog-matches.png`
- [x] 6.3 Run test and verify passing: `npx playwright test catalog.spec.ts`

## 7. E2E tests — Operations page

- [x] 7.1 Create `frontend/webapp/tests/e2e/operations.spec.ts` with US-08 (pipeline controls), US-09 (full pipeline — skipped, not in UI), US-10 (terminal), US-11 (cleanup)
- [x] 7.2 Capture screenshots: `operations-controls.png`
- [x] 7.3 Run test and verify passing: `npx playwright test operations.spec.ts`

## 8. E2E tests — Explorer page

- [x] 8.1 Create `frontend/webapp/tests/e2e/explorer.spec.ts` with US-12 (competitions), US-13 (matches), US-14 (teams/players), US-15 (events), US-16 (tables info)
- [x] 8.2 Capture screenshots: `explorer-competitions.png`, `explorer-matches.png`, `explorer-teams.png`, `explorer-events.png`, `explorer-tables.png`
- [x] 8.3 Run test and verify passing: `npx playwright test explorer.spec.ts`

## 9. E2E tests — Embeddings page

- [x] 9.1 Create `frontend/webapp/tests/e2e/embeddings.spec.ts` with US-17 (coverage), US-18 (rebuild controls)
- [x] 9.2 Capture screenshots: `embeddings-coverage.png`
- [x] 9.3 Run test and verify passing: `npx playwright test embeddings.spec.ts`

## 10. E2E tests — Chat page

- [x] 10.1 Create `frontend/webapp/tests/e2e/chat.spec.ts` with US-19 (ask question), US-20 (answer from RAG), US-21 (developer controls), US-22 (similarity scores)
- [x] 10.2 Capture screenshots: `chat-user-question.png`, `chat-user-answer.png`, `chat-developer-controls.png`, `chat-developer-results.png`
- [x] 10.3 Run test and verify passing: `npx playwright test chat.spec.ts`

## 11. E2E tests — Cross-cutting

- [x] 11.1 Create `frontend/webapp/tests/e2e/cross-cutting.spec.ts` with US-23 (source switching), US-24 (seed data out of the box)
- [x] 11.2 Capture screenshots: `source-postgres.png`, `source-sqlserver.png`
- [x] 11.3 Run test and verify passing: `npx playwright test cross-cutting.spec.ts`

## 12. Visual user manual

- [x] 12.1 Create `frontend/webapp/tests/e2e/generate-manual.ts` script that reads screenshots dir and generates `docs/user-manual.md` with sections per page, embedded images, and profile annotations
- [x] 12.2 Run the script and verify `docs/user-manual.md` is generated with all screenshots embedded
- [x] 12.3 Verify the manual has sections for all 7 pages and covers both profiles where applicable

## 13. CI integration

- [x] 13.1 Add E2E test job to `.github/workflows/ci.yml` (requires Docker services, seed load, Playwright)
- [x] 13.2 Verify the job definition is correct (dry-run with `act` or review YAML)

## 14. Final validation

- [x] 14.1 Run full E2E suite: `cd frontend/webapp && npx playwright test`
- [x] 14.2 Verify all screenshots are generated in `frontend/webapp/tests/e2e/screenshots/`
- [x] 14.3 Verify `docs/user-manual.md` is complete and images render
- [x] 14.4 Run backend tests to verify no regressions: `cd backend && pytest tests/ -v`
- [x] 14.5 Update CHANGELOG.md under `## [Unreleased]`
