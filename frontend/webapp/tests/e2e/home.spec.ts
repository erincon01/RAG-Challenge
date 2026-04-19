import { test, expect } from '@playwright/test'

const SCREENSHOTS = './tests/e2e/screenshots'

async function setMode(page: any, mode: 'user' | 'developer') {
  const modeSelect = page.locator('select').filter({ hasText: /User|Developer/i }).first()
  await modeSelect.selectOption(mode)
  await page.waitForLoadState('networkidle')
}

test.describe('Home Page', () => {
  test('US-01: user mode shows hero, feature cards, and quick start guide', async ({ page }) => {
    await page.goto('/')
    await page.waitForLoadState('networkidle')
    await setMode(page, 'user')

    await expect(page.getByText('Analiza el fútbol como nunca antes')).toBeVisible()
    await expect(page.getByText('Catálogo Completo')).toBeVisible()
    await expect(page.getByText('Explorador Visual')).toBeVisible()
    await expect(page.getByText('Chat Inteligente')).toBeVisible()
    await expect(page.getByText('Guía Rápida')).toBeVisible()
    await expect(page.getByText('Selecciona una competición')).toBeVisible()

    await page.screenshot({ path: `${SCREENSHOTS}/home-fan.png`, fullPage: true })
  })

  test('US-02: developer mode shows architecture, RAG flow, and API endpoints', async ({ page }) => {
    await page.goto('/')
    await page.waitForLoadState('networkidle')
    await setMode(page, 'developer')

    await expect(page.getByText('Arquitectura del Sistema')).toBeVisible({ timeout: 10_000 })
    await expect(page.getByText('Backend Stack')).toBeVisible()
    await expect(page.getByText('Frontend Stack')).toBeVisible()
    await expect(page.getByText('Flujo de Datos RAG')).toBeVisible()
    await expect(page.getByText('API Endpoints Principales')).toBeVisible()

    await page.screenshot({ path: `${SCREENSHOTS}/home-developer.png`, fullPage: true })
  })
})
