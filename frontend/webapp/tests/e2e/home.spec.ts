import { test, expect } from '@playwright/test'

const SCREENSHOTS = './tests/e2e/screenshots'

test.describe('Home Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/')
    await page.waitForLoadState('networkidle')
  })

  test('US-01: fan view shows hero, feature cards, and quick start guide', async ({ page }) => {
    // Fan view is the default
    await expect(page.getByText('Analiza el fútbol como nunca antes')).toBeVisible()
    await expect(page.getByText('Catálogo Completo')).toBeVisible()
    await expect(page.getByText('Explorador Visual')).toBeVisible()
    await expect(page.getByText('Chat Inteligente')).toBeVisible()
    await expect(page.getByText('Guía Rápida')).toBeVisible()
    await expect(page.getByText('Selecciona una competición')).toBeVisible()

    await page.screenshot({ path: `${SCREENSHOTS}/home-fan.png`, fullPage: true })
  })

  test('US-02: developer view shows architecture, RAG flow, and API endpoints', async ({ page }) => {
    await page.getByRole('button', { name: /Developer/i }).click()
    await expect(page.getByText('Arquitectura del Sistema')).toBeVisible()
    await expect(page.getByText('Backend Stack')).toBeVisible()
    await expect(page.getByText('Frontend Stack')).toBeVisible()
    await expect(page.getByText('Flujo de Datos RAG')).toBeVisible()
    await expect(page.getByText('API Endpoints Principales')).toBeVisible()

    await page.screenshot({ path: `${SCREENSHOTS}/home-developer.png`, fullPage: true })
  })
})
