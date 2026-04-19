import { test, expect } from '@playwright/test'

const SCREENSHOTS = './tests/e2e/screenshots'

test.describe('Tutorials Page', () => {
  test('tutorials page shows 3 tutorial cards and resources', async ({ page }) => {
    await page.goto('/tutorials')
    await page.waitForLoadState('networkidle')

    await expect(page.getByText('Your First Semantic Search')).toBeVisible({ timeout: 10_000 })
    await expect(page.getByText('Comparing Search Algorithms')).toBeVisible()
    await expect(page.getByText('Understanding Embeddings')).toBeVisible()
    await expect(page.getByText('Resources')).toBeVisible()
    await expect(page.getByText('Golden Set')).toBeVisible()

    await page.screenshot({ path: `${SCREENSHOTS}/tutorials.png`, fullPage: true })
  })
})
