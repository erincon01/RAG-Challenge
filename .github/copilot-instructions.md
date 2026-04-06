---
applyTo: '**'
---

# RAG-Challenge — Instrucciones para GitHub Copilot

## Proyecto

RAG-Challenge es un sistema de **Retrieval Augmented Generation** (RAG) para datos de fútbol de StatsBomb.
Permite ingestar datos de competiciones/partidos, generar embeddings, y responder preguntas
en lenguaje natural usando búsqueda vectorial + LLM.

## Stack tecnológico

- **Backend:** FastAPI (Python 3.11+), uvicorn
- **Frontend:** React 18 + TypeScript + Vite + Tailwind CSS
- **Bases de datos:** PostgreSQL (pgvector) y SQL Server (dual-repo pattern)
- **IA:** OpenAI API (embeddings + chat completion)
- **Infra:** Docker Compose, DevContainers, GitHub Actions CI/CD
- **Tests:** pytest + pytest-cov (cobertura mínima 80%)

## Arquitectura por capas

```
API (FastAPI routers)  →  Services  →  Repositories  →  Domain
     ↓ Depends()           ↓                ↓              ↓
  Request/Response    Business logic    DB access     Entities/Exceptions
```

### Reglas de arquitectura

1. **Route handlers** (`app/api/v1/`) NO deben contener lógica de negocio, acceso directo a BD,
   ni importar adapters. Solo orquestan: validar entrada → llamar servicio → devolver respuesta.
2. **Services** (`app/services/`) contienen la lógica de negocio. Solo ellos pueden llamar a adapters.
3. **Repositories** (`app/repositories/`) encapsulan todo acceso a BD. Extienden `BaseRepository` (ABC).
4. **Domain** (`app/domain/`) contiene entidades (`entities.py`) y excepciones (`exceptions.py`).
   No importa nada de FastAPI, DB drivers, ni HTTP.
5. **Adapters** (`app/adapters/`) encapsulan clientes externos (OpenAI). Solo llamados desde services.

### Inyección de dependencias

- TODA dependencia externa se inyecta vía `FastAPI Depends()`.
- Prohibido instanciar servicios o repos a nivel de módulo (`_service = XxxService()`).
- Los providers viven en `app/core/dependencies.py`.
- En tests, usar `app.dependency_overrides[provider] = lambda: mock` + `app.dependency_overrides.clear()` en teardown.

### Configuración

- TODA configuración vía `config/settings.py` (Pydantic `BaseSettings`).
- Variables de entorno documentadas en `.env.example`.
- Prohibido `os.getenv()` fuera de `settings.py`.

## Convenciones de código

- **Python:** seguir ruff, mypy en modo estricto.
- **Imports:** ordenados por ruff (`isort`).
- **Docstrings:** solo en funciones/clases públicas, formato Google-style.
- **SQL:** NUNCA f-strings ni `str.format()` con datos de usuario. Siempre parámetros bind (`%s` / `?`).
- **Frontend TypeScript:** strict mode, no `any` salvo justificación.

## Workflow con OpenSpec

Este proyecto usa [OpenSpec](https://github.com/Fission-AI/OpenSpec) para gobernanza spec-driven.

- Antes de implementar una feature, ejecutar `/opsx:propose <nombre>`.
- Implementar con `/opsx:apply`.
- Verificar con `/opsx:verify`.
- Archivar con `/opsx:archive`.
- Las specs del sistema viven en `openspec/specs/`.
- Los cambios activos viven en `openspec/changes/`.

## Instrucciones específicas

Consulta estos archivos para reglas detalladas:
- `.github/instructions/git-workflow.instructions.md` — Ramas, commits, CHANGELOG
- `.github/instructions/tdd.instructions.md` — Tests, cobertura, naming

## Conversation log

Toda sesión significativa con un agente AI DEBE registrarse en `docs/conversation_log.md`
con fecha, objetivo, decisiones tomadas, y archivos modificados.
