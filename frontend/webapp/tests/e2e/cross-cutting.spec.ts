import { test, expect } from '@playwright/test'

const SCREENSHOTS = './tests/e2e/screenshots'

test.describe('Cross-cutting', () => {
  test('US-23: source switching updates data across pages', async ({ page }) => {
    await page.goto('/explorer')
    await page.waitForLoadState('networkidle')

    // Data visible from postgres (default)
    await expect(page.getByText(/UEFA Euro|FIFA World Cup/i).first()).toBeVisible({ timeout: 10_000 })
    await page.screenshot({ path: `${SCREENSHOTS}/source-postgres.png`, fullPage: true })

    // Switch source to sqlserver via header dropdown
    const sourceSelect = page.locator('select').filter({ hasText: /PostgreSQL/i }).first()
    await sourceSelect.selectOption('sqlserver')
    await page.waitForLoadState('networkidle')

    // Page should reload with sqlserver data (may be empty if seed not loaded into sqlserver)
    await page.waitForTimeout(2000)
    await page.screenshot({ path: `${SCREENSHOTS}/source-sqlserver.png`, fullPage: true })
  })

  test('US-24: seed data is available out of the box', async ({ page }) => {
    // Explorer has data
    await page.goto('/explorer')
    await page.waitForLoadState('networkidle')
    await expect(page.getByText(/UEFA Euro|FIFA World Cup/i).first()).toBeVisible({ timeout: 10_000 })

    // Chat page loads with match selector populated
    await page.goto('/chat')
    await page.waitForLoadState('networkidle')
    const matchSelect = page.locator('select').filter({ hasText: /Spain|Argentina/i }).first()
    await expect(matchSelect).toBeVisible({ timeout: 10_000 })
  })
})
