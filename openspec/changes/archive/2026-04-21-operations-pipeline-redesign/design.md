## Context

The Operations page currently has two sections: "Datasets para descarga" (download + cleanup) and "Datasets para carga" (load + aggregate + summaries + embeddings mixed together). The 5-step pipeline is not visually evident. Users don't know the correct order or what each step does.

## Goals / Non-Goals

**Goals:**
- Make the 5-step pipeline visually clear with numbered steps
- Each step self-contained: description, config (if any), action button
- Steps that need datasets (download, load) show checkboxes; others don't
- Match selection visible at the top, shared across all steps
- Cleanup as a collapsible secondary section
- Terminal and jobs panel unchanged

**Non-Goals:**
- Changing the backend API
- Adding a "full pipeline" button (deferred — US-09 still skipped)
- Adding progress bars per step (just button + status text)
- Changing the Jobs panel layout

## Decisions

### 1. Pipeline as numbered step cards
Each step is a visual card with a number badge (1-5), title, one-line description, and action button. Cards flow top-to-bottom in the left column. This makes the order unmistakable.

### 2. Match selection stays at top, shared
The match IDs from catalog selection are shown once at the top (current behavior). All steps use the same match IDs. No per-step match selection.

### 3. Steps 1-2 have dataset checkboxes, steps 3-5 don't
Download and Load need to know which datasets (matches, events, lineups). Aggregate, Summaries, and Embeddings operate on all aggregation rows for the selected matches — no dataset config needed.

### 4. Cleanup moves to collapsible section
Cleanup is a secondary/destructive action. It doesn't belong in the main pipeline flow. Move it to a collapsible `<details>` element below the pipeline steps.

## File change list

| File | Status | Description |
|------|--------|-------------|
| `frontend/webapp/src/pages/OperationsPage.tsx` | (modified) | Rewrite layout with 5 pipeline step cards |
| `frontend/webapp/tests/e2e/operations.spec.ts` | (modified) | Update selectors for new structure |
| `CHANGELOG.md` | (modified) | Update Unreleased |

## Rollback strategy

Revert OperationsPage.tsx to previous version. No backend changes.
