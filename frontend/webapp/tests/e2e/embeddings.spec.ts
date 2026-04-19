import { test, expect } from '@playwright/test'

const SCREENSHOTS = './tests/e2e/screenshots'

test.describe('Embeddings Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/embeddings')
    await page.waitForLoadState('networkidle')
  })

  test('US-17: shows embedding coverage statistics', async ({ page }) => {
    await expect(page.getByText(/text-embedding-3-small/i).first()).toBeVisible({ timeout: 10_000 })
    // Should show total rows or coverage percentage
    await expect(page.getByText(/717|done|coverage/i).first()).toBeVisible()

    await page.screenshot({ path: `${SCREENSHOTS}/embeddings-coverage.png`, fullPage: true })
  })

  test('US-18: rebuild controls are available', async ({ page }) => {
    // Rebuild button or model selector should be present
    await expect(page.getByText(/rebuild|reconstruir|generar/i).first()).toBeVisible({ timeout: 10_000 })
  })
})
