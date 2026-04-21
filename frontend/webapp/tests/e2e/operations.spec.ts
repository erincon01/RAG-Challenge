import { test, expect } from '@playwright/test'

const SCREENSHOTS = './tests/e2e/screenshots'

test.describe('Operations Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/operations')
    await page.waitForLoadState('networkidle')
  })

  test('US-08: shows all 5 pipeline steps with action buttons', async ({ page }) => {
    await expect(page.getByRole('heading', { name: 'Download', exact: true })).toBeVisible({ timeout: 10_000 })
    await expect(page.getByRole('heading', { name: 'Load', exact: true })).toBeVisible()
    await expect(page.getByRole('heading', { name: 'Aggregate', exact: true })).toBeVisible()
    await expect(page.getByRole('heading', { name: 'Summaries', exact: true })).toBeVisible()
    await expect(page.getByRole('heading', { name: 'Embeddings', exact: true })).toBeVisible()

    await page.screenshot({ path: `${SCREENSHOTS}/operations-controls.png`, fullPage: true })
  })

  test('US-08b: each pipeline step has an action button', async ({ page }) => {
    const buttons = page.getByRole('button')
    await expect(buttons.filter({ hasText: /download|descarg/i }).first()).toBeVisible({ timeout: 10_000 })
    await expect(buttons.filter({ hasText: /load|carg/i }).first()).toBeVisible()
    await expect(buttons.filter({ hasText: /aggregat|agregac/i }).first()).toBeVisible()
    await expect(buttons.filter({ hasText: /summar|resumen/i }).first()).toBeVisible()
    await expect(buttons.filter({ hasText: /embedding/i }).first()).toBeVisible()
  })

  test.skip('US-09: full pipeline action is available', async ({ page }) => {
    await expect(page.getByText(/pipeline|completo|full/i).first()).toBeVisible({ timeout: 10_000 })
  })

  test('US-10: job terminal area is visible', async ({ page }) => {
    await expect(page.getByText(/terminal/i).first()).toBeVisible({ timeout: 10_000 })
  })

  test('US-11: cleanup actions are available', async ({ page }) => {
    await expect(page.getByText(/clean|limpiar|borr/i).first()).toBeVisible({ timeout: 10_000 })
  })
})
