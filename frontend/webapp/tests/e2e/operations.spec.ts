import { test, expect } from '@playwright/test'

const SCREENSHOTS = './tests/e2e/screenshots'

test.describe('Operations Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/operations')
    await page.waitForLoadState('networkidle')
  })

  test('US-08: shows pipeline step controls', async ({ page }) => {
    await expect(page.getByText(/download|descarg/i).first()).toBeVisible({ timeout: 10_000 })
    await expect(page.getByText(/load|carg/i).first()).toBeVisible()

    await page.screenshot({ path: `${SCREENSHOTS}/operations-controls.png`, fullPage: true })
  })

  test.skip('US-09: full pipeline action is available', async ({ page }) => {
    // SKIP: full-pipeline endpoint exists in backend but UI button not yet implemented
    await expect(page.getByText(/pipeline|completo|full/i).first()).toBeVisible({ timeout: 10_000 })
  })

  test('US-08b: shows generate summaries button', async ({ page }) => {
    await expect(page.getByRole('button', { name: /summar|resumen/i })).toBeVisible({ timeout: 10_000 })
  })

  test('US-10: job terminal area is visible', async ({ page }) => {
    // Terminal or log area should exist
    await expect(page.getByText(/job|terminal|log/i).first()).toBeVisible({ timeout: 10_000 })
  })

  test('US-11: cleanup actions are available', async ({ page }) => {
    await expect(page.getByText(/clear|limpiar|cleanup/i).first()).toBeVisible({ timeout: 10_000 })
  })
})
