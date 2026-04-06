---
applyTo: '**'
---

# Git Workflow — RAG-Challenge

## Ramas

### Modelo de ramificación

```
main ──────────────────────────────────────── producción (tags versionados)
  │
  └─ develop ─────────────────────────────── integración continua
       │
       ├─ feature/NNN-descripcion ────────── nuevas funcionalidades
       ├─ fix/NNN-descripcion ────────────── correcciones de bugs
       ├─ hotfix/NNN-descripcion ─────────── correcciones urgentes en producción
       ├─ chore/descripcion ──────────────── tareas de mantenimiento
       └─ refactor/descripcion ───────────── refactorizaciones
```

### Branch naming

- Formato: `<tipo>/<NNN>-<descripcion-kebab-case>`
- `NNN` es un número secuencial de 3 dígitos (e.g., `001`, `002`, `010`).
- El número se obtiene del siguiente disponible en el repo.
- Ejemplos:
  - `feature/011-fix-dependency-injection`
  - `fix/012-cors-wildcard`
  - `chore/013-update-changelog`

### Reglas de ramas

1. **Nunca** hacer push directo a `main` o `develop`.
2. Todo cambio va en una rama de feature/fix → PR → merge a `develop`.
3. `main` solo recibe merges desde `develop` (release) o `hotfix/*`.
4. Las ramas se borran tras el merge (remote y local).

## Commits

### Conventional Commits (obligatorio)

Formato: `<type>(<scope>): <description>`

| Type | Cuándo usar |
|------|------------|
| `feat` | Nueva funcionalidad |
| `fix` | Corrección de bug |
| `docs` | Solo documentación |
| `style` | Formato, semicolons, whitespace (sin cambio funcional) |
| `refactor` | Refactorización sin cambiar comportamiento |
| `test` | Añadir o corregir tests |
| `chore` | Tareas de mantenimiento, CI/CD, dependencies |
| `perf` | Mejora de rendimiento |

### Reglas de commits

1. Primera línea ≤ 72 caracteres.
2. Empieza en minúscula tras el `:`.
3. No termina en punto.
4. Cuerpo opcional para explicar el *por qué*, no el *qué*.
5. **Idioma:** Inglés para mensajes de commit.

Ejemplos correctos:
```
feat(api): add token budget guard to RAG pipeline
fix(di): replace module-level service singletons with Depends()
test(search): add test for empty query scenario
chore(ci): update ruff to 0.15.8
```

## CHANGELOG

### Reglas

1. **Todo PR que modifica código DEBE** añadir una entrada bajo `## [Unreleased]`.
2. Formato: `- <tipo>: <descripción> (#PR)`.
3. Al hacer release a `main`, mover `[Unreleased]` a `[X.Y.Z] - YYYY-MM-DD`.
4. Seguir [Keep a Changelog](https://keepachangelog.com/).

## Pull Requests

### Checklist para PRs

```markdown
## PR Checklist

- [ ] Branch naming sigue `<tipo>/NNN-descripcion`
- [ ] Todos los commits son Conventional Commits
- [ ] Tests pasan (`pytest`)
- [ ] Cobertura ≥ 80%
- [ ] Lint limpio (`ruff check .`)
- [ ] Type check limpio (`mypy`)
- [ ] CHANGELOG actualizado bajo `## [Unreleased]`
- [ ] `docs/conversation_log.md` actualizado si fue sesión AI-assisted
- [ ] Specs actualizadas si hay cambio de comportamiento (`openspec/`)
```

### Workflow de PR

1. Crear PR desde feature branch → `develop`.
2. CI debe pasar (lint, typecheck, tests).
3. Al menos 1 reviewer aprueba (cuando haya >1 dev).
4. Merge con "Squash and merge" si hay muchos commits intermedios.
5. Borrar rama tras merge.

## Tags y releases

- Al mergear `develop` → `main`, crear tag: `vX.Y.Z`.
- Seguir [Semantic Versioning](https://semver.org/):
  - **MAJOR:** cambios breaking en API pública.
  - **MINOR:** nueva funcionalidad backwards-compatible.
  - **PATCH:** correcciones de bugs.

## Conversation log

- Toda sesión significativa con un agente AI se registra en `docs/conversation_log.md`.
- Formato:

```markdown
## YYYY-MM-DD — Objetivo de la sesión

**Participantes:** Eladio Rincon + GitHub Copilot (Claude Opus 4.6)
**Rama:** feature/NNN-descripcion

### Decisiones tomadas
- ...

### Archivos modificados
- ...
```
