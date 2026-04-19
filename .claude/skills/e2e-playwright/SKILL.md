---
name: e2e-playwright
description: End-to-end tests with Playwright for the React frontend. Run E2E tests, create new tests, generate screenshots.
argument-hint: <action> [arguments]
---

# E2E Testing con Playwright

El usuario ha invocado `/e2e` con los argumentos: $ARGUMENTS

Actua como experto en Playwright para TypeScript/React. El proyecto usa un frontend React 18 + TypeScript + Vite corriendo en Docker Compose.

**Acciones disponibles:**
- `run` — Ejecutar todos los tests E2E
- `run <page>` — Ejecutar tests de una pagina (home, dashboard, catalog, operations, explorer, embeddings, chat)
- `screenshots` — Generar capturas de todas las paginas
- `new <page> <descripcion>` — Crear un test E2E nuevo
- `status` — Verificar que los containers estan running y healthy
- `help` — Mostrar esta ayuda

---

## Prerequisitos

Los containers de backend + frontend + bases de datos DEBEN estar corriendo:

```bash
docker compose up --build -d
# Frontend: http://localhost:5173
# Backend: http://localhost:8000
```

---

## Stack E2E

- **Playwright** for TypeScript (via `npx playwright`)
- **Test location:** `frontend/webapp/tests/e2e/`
- **Config:** `frontend/webapp/playwright.config.ts`

---

## Comandos

```bash
# 1. Levantar servicios (si no estan)
docker compose up --build -d

# 2. Instalar Playwright (primera vez)
cd frontend/webapp && npx playwright install --with-deps chromium

# 3. Ejecutar todos los E2E
cd frontend/webapp && npx playwright test

# 4. Ejecutar tests de una pagina
cd frontend/webapp && npx playwright test tests/e2e/test_catalog.spec.ts

# 5. Ejecutar con UI mode (debug)
cd frontend/webapp && npx playwright test --ui

# 6. Generar capturas
cd frontend/webapp && npx playwright test --update-snapshots
```

---

## Estructura

```
frontend/webapp/
  tests/e2e/
    home.spec.ts          Home page
    dashboard.spec.ts     Dashboard: health, DB status, jobs
    catalog.spec.ts       Catalog: competitions, matches
    operations.spec.ts    Operations: download, load, process
    explorer.spec.ts      Explorer: teams, players, events
    embeddings.spec.ts    Embeddings: coverage, rebuild
    chat.spec.ts          Chat: RAG semantic search
  playwright.config.ts    Config: baseURL, timeouts, projects
```

---

## Selectores preferidos

```typescript
page.getByRole('button', { name: 'Download' })    // Por rol (mejor)
page.getByText('Total Matches')                     // Por texto
page.getByLabel('Source')                            // Por label
page.getByTestId('sidebar')                          // Por test-id
```

---

## Plantilla para test nuevo

```typescript
import { test, expect } from '@playwright/test';

test.describe('<Page> Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/<route>');
    await page.waitForLoadState('networkidle');
  });

  test('loads without errors', async ({ page }) => {
    await expect(page.getByRole('heading')).toBeVisible();
    await expect(page.locator('text=Error')).toHaveCount(0);
  });

  test('main content visible', async ({ page }) => {
    await expect(page.getByText('<expected text>')).toBeVisible();
  });
});
```

---

## Reglas

- **NUNCA** usar `page.waitForTimeout()` — usar `waitForLoadState` o `waitForSelector`
- **SIEMPRE** usar selectores semánticos (role, text, label) sobre CSS selectors
- Tests deben ser independientes — no depender del orden de ejecución
- Cada test debe limpiar su estado si modifica datos
- Capturas van en `frontend/webapp/tests/e2e/screenshots/`

---

## Comportamiento por accion

### `run`
1. Verificar containers healthy: `docker compose ps`
2. Ejecutar: `cd frontend/webapp && npx playwright test`

### `screenshots`
1. Verificar containers healthy
2. Ejecutar tests con `--update-snapshots`
3. Listar capturas generadas

### `new <page> <descripcion>`
1. Generar test siguiendo plantilla y convenciones del proyecto
2. Ejecutar para verificar que pasa

### `status`
1. `docker compose ps` — verificar servicios
2. `curl http://localhost:8000/api/v1/health/live` — backend health
3. `curl http://localhost:5173` — frontend health
