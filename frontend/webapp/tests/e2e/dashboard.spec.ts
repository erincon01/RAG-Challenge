import { test, expect } from '@playwright/test'

const SCREENSHOTS = './tests/e2e/screenshots'

test.describe('Dashboard Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/dashboard')
    await page.waitForLoadState('networkidle')
  })

  test('US-03: shows system health status for API and databases', async ({ page }) => {
    await expect(page.getByText('API')).toBeVisible({ timeout: 15_000 })
    await expect(page.getByText('Readiness')).toBeVisible()
    await expect(page.getByText('Sources', { exact: true })).toBeVisible()
    await expect(page.getByText('Estado de sources')).toBeVisible()

    await page.screenshot({ path: `${SCREENSHOTS}/dashboard-health.png`, fullPage: true })
  })

  test('US-04: shows capabilities matrix per source', async ({ page }) => {
    await expect(page.getByText('Capabilities')).toBeVisible({ timeout: 15_000 })
    await expect(page.getByText('Data Sources')).toBeVisible()
    // The capabilities section shows "N modelos - N algoritmos" per source
    await expect(page.getByText(/algoritmos/i).first()).toBeVisible({ timeout: 10_000 })
  })

  test('US-05: shows recent jobs section', async ({ page }) => {
    await expect(page.getByText('Recent Jobs')).toBeVisible({ timeout: 15_000 })
  })
})
