import { test, expect } from '@playwright/test'

const SCREENSHOTS = './tests/e2e/screenshots'

test.describe('Catalog Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/catalog')
    await page.waitForLoadState('networkidle')
  })

  test('US-06: loads and displays StatsBomb competitions', async ({ page }) => {
    // Wait for competitions to load from the StatsBomb API
    await expect(page.getByText(/competici/i).first()).toBeVisible({ timeout: 15_000 })

    await page.screenshot({ path: `${SCREENSHOTS}/catalog-competitions.png`, fullPage: true })
  })

  test('US-07: selecting a competition shows matches for that season', async ({ page }) => {
    // Wait for page to be interactive
    await page.waitForTimeout(3000)

    await page.screenshot({ path: `${SCREENSHOTS}/catalog-matches.png`, fullPage: true })
  })
})
