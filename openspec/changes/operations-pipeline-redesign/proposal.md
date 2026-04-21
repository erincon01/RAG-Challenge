## Why

The Operations page (`/operations`) mixes download controls, cleanup, load, aggregate, summaries, and embeddings in two poorly separated sections. The 5 pipeline steps (download → load → aggregate → summaries → embeddings) are buried as plain buttons without visual hierarchy. A user doesn't know which step to run next or what each step does. The "Datasets para carga" section contains steps 2-5 even though only step 2 uses datasets checkboxes. The result: users skip summaries (the button was missing until PR #65), run embeddings on empty summaries, and get 0/0 results.

## What Changes

- Reorganize the Operations page into a **clear 5-step pipeline** with visual step indicators
- Each step is its own card with: step number, title, description, match selection context, action button, and status
- Steps 1-2 (download, load) show dataset checkboxes; steps 3-5 don't need them
- Shared terminal at the bottom shows logs from any active job
- Move cleanup/borrado to a collapsible section (secondary action, not the main flow)
- Jobs panel stays on the right side

## Capabilities

### New Capabilities
_(none)_

### Modified Capabilities
_(none — frontend-only restructure, no API changes)_

## Impact

- **Frontend**: `frontend/webapp/src/pages/OperationsPage.tsx` (rewritten)
- **E2E tests**: `frontend/webapp/tests/e2e/operations.spec.ts` (updated)
- **Backward compatibility**: fully backward-compatible — same API calls, different layout
- **Affected layers**: Frontend only
- **Test impact**: E2E operations tests updated to match new structure
