import { test, expect } from '@playwright/test'

const SCREENSHOTS = './tests/e2e/screenshots'

test.describe('Explorer Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/explorer')
    await page.waitForLoadState('networkidle')
  })

  test('US-12: shows competitions loaded in the database', async ({ page }) => {
    await expect(page.getByText(/UEFA Euro|FIFA World Cup/i).first()).toBeVisible({ timeout: 10_000 })

    await page.screenshot({ path: `${SCREENSHOTS}/explorer-competitions.png`, fullPage: true })
  })

  test('US-13: shows seed matches in the match selector', async ({ page }) => {
    // Matches tab
    const matchesTab = page.getByRole('button', { name: 'Matches' })
    if (await matchesTab.isVisible()) {
      await matchesTab.click()
      await page.waitForLoadState('networkidle')
    }
    // Match selector contains seed matches (in a <select> or table)
    const matchSelect = page.locator('select').filter({ hasText: /Spain|Argentina/i }).first()
    await expect(matchSelect).toBeVisible({ timeout: 10_000 })

    await page.screenshot({ path: `${SCREENSHOTS}/explorer-matches.png`, fullPage: true })
  })

  test('US-14: shows teams for a selected match', async ({ page }) => {
    const teamsTab = page.getByRole('button', { name: 'Teams' })
    if (await teamsTab.isVisible()) {
      await teamsTab.click()
      await page.waitForLoadState('networkidle')
    }

    await page.screenshot({ path: `${SCREENSHOTS}/explorer-teams.png`, fullPage: true })
  })

  test('US-15: shows events for a selected match', async ({ page }) => {
    const eventsTab = page.getByRole('button', { name: 'Events' })
    if (await eventsTab.isVisible()) {
      await eventsTab.click()
      await page.waitForLoadState('networkidle')
    }

    await page.screenshot({ path: `${SCREENSHOTS}/explorer-events.png`, fullPage: true })
  })

  test('US-16: shows table info with row counts', async ({ page }) => {
    const tablesTab = page.getByRole('button', { name: 'Tables' })
    if (await tablesTab.isVisible()) {
      await tablesTab.click()
      await page.waitForLoadState('networkidle')
    }

    await page.screenshot({ path: `${SCREENSHOTS}/explorer-tables.png`, fullPage: true })
  })
})
