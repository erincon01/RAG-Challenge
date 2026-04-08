## Context

Today, the devcontainer and the production backend image are the same thing.
`.devcontainer/devcontainer.json` declares:

```json
"dockerComposeFile": ["../docker-compose.yml", "docker-compose.override.yml"],
"service": "backend"
```

and the override only does:

```yaml
services:
  backend:
    command: sleep infinity
    working_dir: /workspace
```

So when VS Code "Reopens in Container", it literally builds and runs the same image
that `docker-compose.yml` would start with `uvicorn` — but idled with `sleep infinity`.
The image is built from `backend/Dockerfile`, which today includes a lot of
development-only tools (see proposal for the full list).

## Goals / Non-Goals

**Goals:**
- Make `backend/Dockerfile` produce an image that contains **only** what production needs.
- Move all dev-only tooling to a separate `.devcontainer/Dockerfile` that extends the
  runtime image.
- Keep `docker compose up` behavior unchanged for plain-shell developers and CI.
- Keep `"Reopen in Container"` behavior unchanged from the developer's point of view
  (same mounts, same ports, same user, same `sleep infinity`, same `features`).
- Keep the `appuser` UID/GID (1000) stable across both images so bind-mount permissions
  on `.`, `backend/`, and `config/` don't break.

**Non-Goals:**
- Not optimizing the runtime image aggressively (no Alpine migration, no distroless,
  no `pip install --no-deps`). The goal is separation, not minimization.
- Not changing the frontend Dockerfile (`frontend/webapp/Dockerfile` is already
  multi-stage and well-separated).
- Not introducing `devcontainer.json` "image" mode. We stay on compose-based devcontainers
  so the full stack (postgres, sqlserver, frontend) still comes up together.
- Not changing the `features` block, the VS Code extensions list, or the post-create /
  post-start scripts.

## Decisions

### 1. Explain the "why" in plain terms first

The user is not a Docker expert. The mental model to keep in mind while implementing:

> A Docker image is a box of software. Right now, the box we ship to production is the
> same box we work inside. Every time we add a tool for ourselves (a Node.js runtime,
> git, a debugger) the production box gets bigger and has more moving parts that could
> break or be attacked. We want two boxes: a small one for production, and a bigger one
> we only use on our laptops that **reuses the small one as its starting point** — so
> production never sees the dev tools, and we never accidentally ship them.

This framing drives every decision below.

### 2. Multi-stage `backend/Dockerfile` with an explicit `runtime` target

The new structure:

```dockerfile
# ---- Stage 1: runtime (production image) ----
FROM python:3.11-slim-bookworm AS runtime

WORKDIR /app

# Only what the running FastAPI app needs:
# - libpq-dev + gcc: build psycopg2 from source
# - msodbcsql18 + unixodbc-dev: pyodbc driver for SQL Server
# - ca-certificates: TLS for outbound calls (OpenAI, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
      ca-certificates \
      libpq-dev gcc \
      gnupg2 curl apt-transport-https \
    && curl -fsSL https://packages.microsoft.com/keys/microsoft.asc \
         | gpg --dearmor -o /usr/share/keyrings/microsoft-prod.gpg \
    && curl -fsSL https://packages.microsoft.com/config/debian/12/prod.list \
         > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y --no-install-recommends msodbcsql18 unixodbc-dev \
    # Remove build-only packages and the apt key tooling after msodbcsql18 is installed
    && apt-get purge -y --auto-remove gnupg2 apt-transport-https \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY config/ /config/
COPY backend/ .

RUN groupadd --gid 1000 appuser \
 && useradd --uid 1000 --gid 1000 --create-home appuser \
 && chown -R appuser:appuser /app /config \
 && mkdir -p /home/appuser/.local/bin \
 && chown -R appuser:appuser /home/appuser

ENV PATH="/home/appuser/.local/bin:${PATH}"
USER appuser
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--loop", "asyncio"]
```

**Key differences from today:**

- **No `git`.** The running backend never needs git. Developers get it in the dev image.
- **No Node.js.** Removed the `curl -fsSL https://deb.nodesource.com/setup_lts.x | bash -`
  and the `apt-get install nodejs` line. This is the biggest win — Node.js was only
  there for the Claude CLI, which is a developer tool.
- **`gnupg2` and `apt-transport-https` are purged** after they're used to add the
  Microsoft apt key and install `msodbcsql18`. They are not part of the runtime surface.
- **`curl` is kept in runtime** because `msodbcsql18` installation needs it and
  removing it would complicate the dev image. Acceptable trade-off — curl alone is small
  and comes with the slim image anyway.
- **`USER appuser` is set at the end** so the container actually runs as non-root by
  default (today this is only done via the devcontainer). Production compose will also
  benefit.

The stage is explicitly named `AS runtime` so the devcontainer Dockerfile can depend on it.

### 3. New `.devcontainer/Dockerfile` extending the runtime stage

```dockerfile
# Build on top of the backend runtime image. This must be built by Docker Compose
# with build context set to the repo root so it can reference ../backend/Dockerfile.
ARG BACKEND_IMAGE=rag-backend-runtime
FROM ${BACKEND_IMAGE} AS devcontainer

USER root

# Dev-only tooling. This layer is never pulled in by production.
RUN apt-get update && apt-get install -y --no-install-recommends \
      bash \
      git \
      gnupg2 \
      apt-transport-https \
      openssh-client \
      less \
      procps \
 && curl -fsSL https://deb.nodesource.com/setup_lts.x | bash - \
 && apt-get install -y --no-install-recommends nodejs \
 && apt-get clean && rm -rf /var/lib/apt/lists/*

# Back to non-root for interactive use
USER appuser
WORKDIR /workspace
```

**Notes:**

- Uses the same `appuser` (UID/GID 1000) that the runtime stage created, so bind mounts
  work without permission hacks.
- Re-adds the tools that were yanked out of runtime: `git`, `gnupg2`, `apt-transport-https`,
  `openssh-client`, `less`, `procps`, and the Node.js LTS runtime for the Claude CLI.
- The `ghcr.io/devcontainers/features/{git,github-cli}:1` features in `devcontainer.json`
  still apply — they layer on top of this image at devcontainer-start time. We keep
  them for now to avoid touching too much at once.

### 4. Compose override: tell devcontainer to build from `.devcontainer/Dockerfile`

The trick is that `.devcontainer/docker-compose.override.yml` is only loaded when VS Code
starts the devcontainer (via `dockerComposeFile` array in `devcontainer.json`). A plain
`docker compose up` from the shell does **not** load it. So we can freely override
`build:` there without affecting production.

New override:

```yaml
services:
  backend:
    build:
      context: ..
      dockerfile: .devcontainer/Dockerfile
      args:
        BACKEND_IMAGE: rag-backend-runtime
    image: rag-backend-devcontainer
    command: sleep infinity
    working_dir: /workspace
```

**How the two build paths coexist:**

| Invocation | Loads override? | Image built | Tool |
|---|---|---|---|
| `docker compose up --build` (shell) | No | `backend/Dockerfile` → `runtime` stage | Production runtime |
| VS Code "Reopen in Container" | Yes | `.devcontainer/Dockerfile` (FROM `rag-backend-runtime`) | Devcontainer image |

**Prerequisite:** for the devcontainer build to work, the `rag-backend-runtime` image
must exist locally first. VS Code runs `docker compose build` using both compose files,
which builds all services — but because the override changes `backend.build.dockerfile`,
compose will build the devcontainer directly and the `FROM rag-backend-runtime` inside
it will fail unless we either:

- **(Option A)** Explicitly build the runtime stage first, tagged as `rag-backend-runtime`.
- **(Option B)** Make `.devcontainer/Dockerfile` reference the upstream image by building
  it inline in a multi-step compose setup.

We pick **Option A** and add a `postCreateCommand` hook — or better, a script invoked
from `post-create.sh` — that runs:

```bash
docker compose -f docker-compose.yml build backend
docker tag rag-challenge-backend rag-backend-runtime  # idempotent
```

No — that can't work because the devcontainer needs the image **before** it can run
`post-create.sh` (which runs inside the container).

Revised approach — **Option A'**: use a **`target:`** in the override so the devcontainer
build chain itself invokes the runtime stage:

```yaml
services:
  backend:
    build:
      context: ..
      dockerfile: .devcontainer/Dockerfile
      args:
        BACKEND_IMAGE_STAGE: runtime
    command: sleep infinity
    working_dir: /workspace
```

And the new `.devcontainer/Dockerfile` becomes:

```dockerfile
# syntax=docker/dockerfile:1.7
# First bring in the runtime stage from backend/Dockerfile
FROM scratch AS _placeholder
# Actual base: the runtime stage of backend/Dockerfile.
# We achieve this by copying backend/Dockerfile's runtime stage via multi-stage cross-file
# is NOT supported directly — so instead we simply inline a FROM on the same base and
# re-do the COPY. This would duplicate work.
```

This doesn't work cleanly either — Docker can't `FROM` a stage defined in a **different**
Dockerfile. So we need a third option.

**Option C (chosen)**: use **two stages inside `backend/Dockerfile`** — `runtime` and
`devcontainer` — and let the override select the `devcontainer` target. This keeps
everything in one file that Docker Compose can build with a simple `target:` switch.

Revised `backend/Dockerfile`:

```dockerfile
FROM python:3.11-slim-bookworm AS runtime
# ... (lean runtime as above) ...
USER appuser
CMD ["uvicorn", ...]

FROM runtime AS devcontainer
USER root
RUN apt-get update && apt-get install -y --no-install-recommends \
      git gnupg2 apt-transport-https openssh-client less procps \
 && curl -fsSL https://deb.nodesource.com/setup_lts.x | bash - \
 && apt-get install -y --no-install-recommends nodejs \
 && apt-get clean && rm -rf /var/lib/apt/lists/*
USER appuser
WORKDIR /workspace
```

And `.devcontainer/docker-compose.override.yml` becomes:

```yaml
services:
  backend:
    build:
      target: devcontainer
    command: sleep infinity
    working_dir: /workspace
```

This is clean because:
- `docker compose up` (no override) builds the default target → `runtime` → lean prod image.
- VS Code loads the override → `target: devcontainer` → the second stage, which is built
  on top of `runtime` and adds the dev tools.
- **Both images share the same base layers**, so rebuilds are fast and disk usage is low.
- No separate `.devcontainer/Dockerfile` file is needed, which sidesteps the "Docker
  can't FROM across files" limitation.

**Trade-off:** the dev tools live inside `backend/Dockerfile` instead of under
`.devcontainer/`. That is a minor cosmetic loss — we clearly mark the stage with a
comment banner, and the separation of concerns is enforced by the `target:` selector,
which is what actually matters.

### 5. Keep `.devcontainer/Dockerfile` or not?

Given Option C above, we do **not** create a separate `.devcontainer/Dockerfile`.
The proposal.md mentioned one, but the design decision is to put both stages in
`backend/Dockerfile`. Update proposal.md to match at implementation time — or keep it
for future if we ever want to fully detach. For this change: single file, two stages.

### 6. Non-root at the runtime stage

Today `backend/Dockerfile` creates `appuser` but never `USER appuser`s to it. The running
container is root-by-default unless the devcontainer override intercepts. That's a
security smell the cleanup should fix: add `USER appuser` at the end of the `runtime`
stage so `docker compose up` also runs non-root in production.

The `devcontainer` stage must `USER root` to install packages and `USER appuser` again
before finishing. VS Code will then honor `remoteUser: appuser` from `devcontainer.json`
as before.

## File changes

| File | Action | Description |
|------|--------|-------------|
| `backend/Dockerfile` | (modified) | Split into `runtime` and `devcontainer` stages. Strip git/nodejs/gnupg2/apt-transport-https from runtime. Add `USER appuser` at end of runtime. |
| `.devcontainer/docker-compose.override.yml` | (modified) | Add `build.target: devcontainer` so VS Code builds the dev stage |
| `CHANGELOG.md` | (modified) | Add entry under `## [Unreleased]` |
| `docs/conversation_log.md` | (modified) | Session entry |

(No new files — the single Dockerfile with two stages replaces the originally planned
`.devcontainer/Dockerfile`.)

## Risks / Trade-offs

- **[Risk]** Switching `backend/Dockerfile` to `USER appuser` at the end of `runtime`
  may break anything that currently assumes root inside the running container (e.g.,
  writing to paths outside `/app`, `/config`, `/home/appuser`). **Mitigation:**
  verify the backend still starts under `docker compose up` and that `/app/data`,
  `/config` etc. are readable/writable as owned by `appuser:appuser` (they already are
  per the existing `chown`).

- **[Risk]** First devcontainer rebuild after this change will be slower for everyone,
  because the `devcontainer` stage is new. **Mitigation:** one-time cost. Document in
  CHANGELOG.

- **[Risk]** The `features` block (`ghcr.io/devcontainers/features/git`,
  `github-cli`) may layer duplicate tooling on top of the dev stage. **Mitigation:**
  Accept the overlap for this PR. Removing the features block is out of scope — it
  would change devcontainer behavior subtly (the features do more than install binaries).
  Track as future cleanup.

- **[Trade-off]** The devcontainer stage lives inside `backend/Dockerfile`, not under
  `.devcontainer/`. Accepted for simplicity (see Decision §4).

- **[Risk]** `post-create.sh` / `post-start.sh` may rely on tools that were only in the
  old single-image layout. **Mitigation:** read both scripts during implementation and
  verify every command they run is available in the `devcontainer` stage; add missing
  tools to the dev stage if needed.

## Rollback strategy

Revert the single commit. The change is infra-only, one Dockerfile plus a one-line
override bump. No database, no data, no API change. Rollback is trivial.
