## Why

The VS Code Dev Container is currently mounted directly on the **production backend image**.
`.devcontainer/devcontainer.json` points to the root `docker-compose.yml` and selects
`service: backend`, and `.devcontainer/docker-compose.override.yml` only changes the
command to `sleep infinity`. There is no separate dev image.

As a consequence, `backend/Dockerfile` — the image that is supposed to ship to production —
has been polluted with dev-only tooling to satisfy the devcontainer:

- `git`, `curl`, `gnupg2`, `apt-transport-https` (kept as permanent layers, not build-only)
- **Full Node.js LTS runtime** installed with an explicit comment `"for Claude CLI and tooling"`
- A self-describing comment on the non-root user: `"switched at runtime via devcontainer.json remoteUser"`

This is a real problem, not a cosmetic one:

1. **Production image size & attack surface.** Every dev tool inside the runtime image
   is a potential CVE target in production (Node.js alone is ~150 MB + ecosystem).
2. **Coupling dev and prod concerns.** Any new dev tool (debugpy, ipython, ssh keys,
   language servers, SDKs) has to be added to the production Dockerfile or awkwardly
   worked around.
3. **Clarity.** New contributors can't tell which lines of `backend/Dockerfile` are
   required for production versus which exist only for the devcontainer.

Fixing now because we are approaching production readiness and v5 planning is in motion.

## What Changes

- Refactor `backend/Dockerfile` into a **multi-stage build** with a lean `runtime` stage
  that contains only what production needs (Python deps, `libpq-dev`, `msodbcsql18`,
  app code, non-root user). Remove `git`, `curl` (as permanent tool), `gnupg2`,
  `apt-transport-https`, and Node.js from `runtime`.
- Add a new **`.devcontainer/Dockerfile`** that builds `FROM` the runtime stage and
  adds dev-only tooling (git, curl, gnupg2, Node.js LTS, anything Claude CLI needs,
  plus whatever the `features` block assumes).
- Update **`.devcontainer/docker-compose.override.yml`** so the `backend` service, when
  launched through VS Code Dev Containers, is rebuilt from `.devcontainer/Dockerfile`.
  Plain `docker compose up --build` from a shell must continue to use the lean runtime
  image unchanged.
- Keep everything else identical: `remoteUser: appuser`, UID/GID 1000, volume mounts
  (`.:/workspace`, `./backend:/app`, `./config:/config`), forwarded ports, networks,
  env vars, and the `sleep infinity` pattern for the devcontainer.
- Update CHANGELOG `## [Unreleased]`.

## Capabilities

### New Capabilities

(none — this is an infra refactor, not a feature)

### Modified Capabilities

- `infra`: The backend Docker image split into a production `runtime` stage and a
  separate devcontainer image that extends it. The two images diverge cleanly.

## Impact

- **Affected layers:** Infra only. No Python, no tests, no API changes.
- **Affected files:**
  - `backend/Dockerfile` (modified → multi-stage)
  - `.devcontainer/Dockerfile` (new)
  - `.devcontainer/docker-compose.override.yml` (modified → adds `build:` override)
  - `CHANGELOG.md` (modified → `## [Unreleased]`)
  - `docs/conversation_log.md` (modified → session entry)
- **Test impact:** No new Python tests. Verification is manual/operational:
  1. `docker compose build backend` produces the lean runtime image.
  2. `docker compose up backend` starts uvicorn normally.
  3. Rebuilding the devcontainer in VS Code produces the dev image and `pytest tests/ -v`
     still passes inside it.
- **Backwards compatibility:** Fully compatible for anyone running `docker compose up`.
  For devcontainer users, the **first** "Reopen in Container" after this change will
  trigger a rebuild — that is the only user-visible disruption.
- **Breaking:** None.
