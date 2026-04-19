import { test, expect } from '@playwright/test'

const SCREENSHOTS = './tests/e2e/screenshots'

async function setMode(page: any, mode: 'user' | 'developer') {
  // Use the global Mode dropdown in the header
  const modeSelect = page.locator('select').filter({ hasText: /User|Developer/i }).first()
  await modeSelect.selectOption(mode)
  await page.waitForLoadState('networkidle')
}

test.describe('Chat Page', () => {
  test('US-19: user mode allows selecting a match and asking a question', async ({ page }) => {
    await page.goto('/chat')
    await page.waitForLoadState('networkidle')
    await setMode(page, 'user')

    // Match selector
    const matchSelect = page.locator('select').filter({ hasText: /Spain|Argentina/i }).first()
    await expect(matchSelect).toBeVisible({ timeout: 10_000 })

    // Question textarea
    await expect(page.locator('textarea').first()).toBeVisible()

    await page.screenshot({ path: `${SCREENSHOTS}/chat-user-question.png`, fullPage: true })
  })

  test('US-20: chat returns an answer from RAG pipeline', async ({ page }) => {
    test.setTimeout(60_000)
    await page.goto('/chat')
    await page.waitForLoadState('networkidle')
    await setMode(page, 'user')

    const matchSelect = page.locator('select').filter({ hasText: /Spain|Argentina/i }).first()
    await expect(matchSelect).toBeVisible({ timeout: 10_000 })

    await page.locator('textarea').first().fill('Who scored the first goal?')

    const submitBtn = page.getByRole('button', { name: /búsqueda|search/i }).first()
    await expect(submitBtn).toBeEnabled({ timeout: 5000 })
    await submitBtn.click()

    // Wait for RAG answer — look for the answer article section that appears after response
    // The answer section contains a <p> or <article> with the LLM response text
    await expect(page.locator('article').filter({ hasText: /goal|scored|Williams|Nico|first/i }).first()).toBeVisible({ timeout: 45_000 })

    await page.screenshot({ path: `${SCREENSHOTS}/chat-user-answer.png`, fullPage: true })
  })

  test('US-21: developer mode shows model and algorithm selectors', async ({ page }) => {
    await page.goto('/chat')
    await page.waitForLoadState('networkidle')
    await setMode(page, 'developer')

    // Developer controls: "Embedding model" and "Algorithm" labels
    await expect(page.getByText('Embedding model')).toBeVisible({ timeout: 10_000 })
    await expect(page.locator('label', { hasText: 'Algorithm' }).first()).toBeVisible()

    await page.screenshot({ path: `${SCREENSHOTS}/chat-developer-controls.png`, fullPage: true })
  })

  test('US-22: developer mode shows similarity scores after search', async ({ page }) => {
    await page.goto('/chat')
    await page.waitForLoadState('networkidle')
    await setMode(page, 'developer')

    const matchSelect = page.locator('select').filter({ hasText: /Spain|Argentina/i }).first()
    await expect(matchSelect).toBeVisible({ timeout: 10_000 })

    await page.locator('textarea').first().fill('Who scored the first goal?')

    const submitBtn = page.getByRole('button', { name: /búsqueda|search/i }).first()
    await expect(submitBtn).toBeEnabled({ timeout: 5000 })
    await submitBtn.click()

    // Developer mode shows similarity scores in results
    await expect(page.getByText(/similarity|score|0\.\d/i).first()).toBeVisible({ timeout: 45_000 })

    await page.screenshot({ path: `${SCREENSHOTS}/chat-developer-results.png`, fullPage: true })
  })
})
