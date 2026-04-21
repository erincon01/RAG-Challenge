## 1. Rewrite OperationsPage layout

- [ ] 1.1 Restructure OperationsPage.tsx with 5 numbered pipeline step cards: Download, Load, Aggregate, Summaries, Embeddings
- [ ] 1.2 Each card shows: step number, title, one-line description, action button, error state
- [ ] 1.3 Steps 1-2 (Download, Load) include dataset checkboxes inside their card
- [ ] 1.4 Match selection panel at the top (shared across all steps)
- [ ] 1.5 Move cleanup to a collapsible `<details>` section below the pipeline
- [ ] 1.6 Terminal stays at the bottom of the left column
- [ ] 1.7 Jobs panel stays on the right (unchanged)

## 2. Update E2E tests

- [ ] 2.1 Update `operations.spec.ts` to verify all 5 pipeline steps are visible
- [ ] 2.2 Run E2E tests: `npx playwright test operations.spec.ts`

## 3. Validation

- [ ] 3.1 Run full E2E suite
- [ ] 3.2 Update CHANGELOG.md
