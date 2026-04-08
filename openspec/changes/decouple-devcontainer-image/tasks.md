## 1. Branch & prep

- [x] 1.1 From `develop`, create branch `chore/decouple-devcontainer-image`
- [x] 1.2 Read `backend/Dockerfile`, `.devcontainer/devcontainer.json`, `.devcontainer/docker-compose.override.yml`, `.devcontainer/post-create.sh`, `.devcontainer/post-start.sh`, and `docker-compose.yml` end-to-end to confirm no hidden dependency on current tooling layout

## 2. Refactor `backend/Dockerfile` into multi-stage

- [x] 2.1 Rewrite `backend/Dockerfile` with an explicit `FROM python:3.11-slim-bookworm AS runtime` stage containing ONLY: `ca-certificates`, `curl`, `libpq-dev`, `gcc`, `gnupg2` (transient), `apt-transport-https` (transient), `unixodbc-dev`, `msodbcsql18`, Python deps, `/config/`, `/app/` code, `appuser` (UID/GID 1000)
- [x] 2.2 Purge `gnupg2` and `apt-transport-https` with `apt-get purge -y --auto-remove` at the end of the runtime layer, after the MS key has been added and `msodbcsql18` installed
- [x] 2.3 Remove ALL Node.js installation from the `runtime` stage (the `curl ... setup_lts.x | bash -` line and the `nodejs` apt package)
- [x] 2.4 Remove `git` from the `runtime` stage
- [x] 2.5 Add `USER appuser` at the end of the `runtime` stage so the production image runs non-root by default
- [x] 2.6 Append a second stage `FROM runtime AS devcontainer` that `USER root`s, installs dev tools (`git`, `gnupg2`, `apt-transport-https`, `openssh-client`, `less`, `procps`, Node.js LTS via the NodeSource script), cleans apt lists, then switches back to `USER appuser` and sets `WORKDIR /workspace`
- [x] 2.7 Add a comment banner above each stage: `# =========== RUNTIME (production) ===========` and `# =========== DEVCONTAINER (dev only) ===========`

## 3. Update `.devcontainer/docker-compose.override.yml`

- [x] 3.1 Add a `build:` block to the `backend` service with `target: devcontainer` so VS Code builds the second stage. Keep `command: sleep infinity` and `working_dir: /workspace`
- [x] 3.2 Do NOT add `build.context` or `build.dockerfile` — compose will inherit them from the base `docker-compose.yml` and only override the `target`

## 4. Sanity-check the devcontainer scripts

- [x] 4.1 Re-read `.devcontainer/post-create.sh` and confirm every binary it uses (`pip`, `python`, `bash`) is present in the `devcontainer` stage — all present (inherited from `runtime`)
- [x] 4.2 Re-read `.devcontainer/post-start.sh` and confirm every binary it uses (`nohup`, `uvicorn` via pip-installed deps, `python`, `requests` via requirements.txt) is present — all present
- [x] 4.3 `nohup` is part of coreutils which is present in `python:3.11-slim-bookworm` — no action needed

## 5. Verify `docker compose up` (production path) — **DEFERRED: requires user to run on host**

> The session environment has no docker socket, so these verifications are deferred to the user before merging.

- [ ] 5.1 Run `docker compose build backend` with NO devcontainer override and confirm the default target is `runtime`
- [ ] 5.2 Inspect the resulting image: `docker run --rm rag-challenge-backend which git` MUST fail (git absent) and `docker run --rm rag-challenge-backend which node` MUST fail (node absent)
- [ ] 5.3 Run `docker compose up backend postgres sqlserver` and confirm uvicorn starts normally and `GET /api/v1/health/live` returns 200
- [ ] 5.4 Confirm the container runs as `appuser` (not root): `docker compose exec backend id` MUST show `uid=1000(appuser)`

## 6. Verify VS Code "Reopen in Container" (dev path) — **DEFERRED: requires user to run on host**

> The session environment has no docker socket, so these verifications are deferred to the user before merging.

- [ ] 6.1 From a clean state, run: `docker compose -f docker-compose.yml -f .devcontainer/docker-compose.override.yml build backend` and confirm the `devcontainer` target is built
- [ ] 6.2 Start the stack with both compose files and exec into the backend container: `which git` MUST succeed, `which node` MUST succeed, `id` MUST still show `appuser`
- [ ] 6.3 Inside that container, run `cd /app && pytest tests/ -v` and confirm the full suite still passes (this is the dev-environment smoke test)
- [ ] 6.4 Confirm volume mounts still work: `touch /workspace/_sanity_check && rm /workspace/_sanity_check` must succeed as `appuser`

## 7. Update CHANGELOG & docs

- [x] 7.1 Add entry under `## [Unreleased]` in `CHANGELOG.md`
- [x] 7.2 Append a session entry to `docs/conversation_log.md` describing the decoupling and linking to this OpenSpec change

## 8. Lint, format, and final verification

- [x] 8.1 Run `ruff check backend/app` and `ruff format --check backend/app` — both clean (33 files already formatted)
- [x] 8.2 Run `pytest tests/ -v` against the current code (smoke test, not against rebuilt image) — **470/470 tests passing**
- [ ] 8.3 Confirm `docker compose up` (plain) still boots the full stack and `/api/v1/health/ready` returns 200 — **DEFERRED (see §5)**

## 9. Commit & PR

- [ ] 9.1 Stage only the changed files: `backend/Dockerfile`, `.devcontainer/docker-compose.override.yml`, `CHANGELOG.md`, `docs/conversation_log.md`, `openspec/changes/decouple-devcontainer-image/**`
- [ ] 9.2 Commit with Conventional Commits, e.g. `chore(infra): split backend Dockerfile into runtime and devcontainer stages`. **No AI attribution**.
- [ ] 9.3 Push the branch and open a PR against `develop` with a body linking to this OpenSpec change and summarizing the motivation
- [ ] 9.4 After merge, run `/opsx:archive decouple-devcontainer-image`

---

### Verification rules (from project config)

- **Never mark a task `[x]` without running the verification it implies.** For §5 and §6, that means the actual `docker` and `pytest` commands, not just reading the file.
- If §6.3 (`pytest tests/ -v`) fails, STOP. Do not continue to §7. Fix the cause first — most likely a tool missing from the `devcontainer` stage.
- Run `ruff check` and `ruff format --check` before §9.1 even though no Python changed (defensive).
