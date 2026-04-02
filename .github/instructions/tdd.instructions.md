---
applyTo: 'backend/**'
---

# Test-Driven Development — RAG-Challenge

## Filosofía

1. **Red → Green → Refactor**: Escribir el test primero (que falle), implementar el mínimo para que pase, luego refactorizar.
2. En brownfield, aplicar TDD a todo código nuevo y a cualquier código que se modifique.

## Cobertura

- **Mínimo obligatorio:** 80% de cobertura de líneas.
- CI falla si la cobertura baja del umbral.
- Comando: `pytest --cov=app --cov-report=term-missing --cov-fail-under=80`

## Naming de tests

### Formato obligatorio

```
test_<método_o_función>_<escenario>_<resultado_esperado>
```

### Ejemplos correctos

```python
def test_search_and_chat_empty_query_returns_validation_error():
def test_get_match_by_id_not_found_raises_404():
def test_create_embedding_valid_text_returns_vector():
def test_ingest_events_duplicate_match_skips_insertion():
```

### Ejemplos incorrectos (NO usar)

```python
def test_search():          # ❌ too vague
def test_create():          # ❌ no scenario
def test_defaults():        # ❌ no method, no expected
def test_str_enum():        # ❌ no scenario, no expected
```

## Estructura de tests

```
backend/tests/
├── conftest.py          # Fixtures y factories compartidas
├── api/                 # Tests de endpoints (integration-level)
│   ├── test_chat.py
│   ├── test_health.py
│   └── ...
├── unit/                # Tests unitarios de services, domain, adapters
│   ├── test_search_service.py
│   ├── test_domain.py
│   └── ...
└── integration/         # Tests con BD real (Docker)
    └── ...
```

## Mocks

### `MagicMock(spec=...)` obligatorio

```python
# ✅ Correcto — detecta attribute drift
mock_repo = MagicMock(spec=MatchRepository)

# ❌ Incorrecto — acepta cualquier atributo
mock_repo = MagicMock()
```

### Dependency overrides para API tests

```python
# En el test
app.dependency_overrides[get_match_repository] = lambda: mock_repo

# En teardown (obligatorio)
app.dependency_overrides.clear()
```

O usar fixture:

```python
@pytest.fixture(autouse=True)
def cleanup_overrides():
    yield
    app.dependency_overrides.clear()
```

## Factories (conftest.py)

### Obligatorio: usar factories para datos de test

```python
# ✅ Correcto — usar factory
match = make_match(match_id=123, home_team="Real Madrid")

# ❌ Incorrecto — inline dict
match = {"match_id": 123, "home_team": "Real Madrid", ...}
```

Las factories están definidas en `backend/tests/conftest.py`:
- `make_match()` — crea un `Match` con defaults sensatos
- `make_event()` — crea un `Event` con defaults sensatos
- `make_search_request()` — crea un `SearchRequest`
- `make_search_result()` — crea un `SearchResult`
- `make_mock_match_repo()` — crea mock de `MatchRepository`
- `make_mock_event_repo()` — crea mock de `EventRepository`

## Reglas de SQL en tests

- **NUNCA** usar f-strings para construir SQL con datos de test.
- Siempre usar los mismos parámetros bind que la aplicación (`%s` para PostgreSQL, `?` para SQL Server).
- Los tests de integración con BD real deben limpiar sus datos en teardown.

## CI Integration

El pipeline de CI (`.github/workflows/ci.yml`) ejecuta:
1. `ruff check .` — lint
2. `mypy --strict` — type check
3. `pytest --cov=app --cov-fail-under=80` — tests + cobertura

Todos deben pasar antes de poder mergear un PR.
