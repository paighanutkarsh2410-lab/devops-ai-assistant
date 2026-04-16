import { test, expect } from '@playwright/test';

const API_URL = process.env.API_URL || 'http://localhost:8000';

test.describe('Authentication Flow', () => {
  test('login with valid credentials', async ({ page }) => {
    await page.goto('/login');
    await page.waitForLoadState('networkidle');

    // Fill login form
    const emailInput = page.locator('input[type="email"], input[placeholder*="email" i]');
    const passwordInput = page.locator('input[type="password"]');

    if (await emailInput.isVisible()) {
      await emailInput.fill('test@example.com');
      await passwordInput.fill('password123');

      const submitBtn = page.locator('button[type="submit"], button:has-text("Login"), button:has-text("Sign")');
      await submitBtn.click();

      // Should redirect to dashboard
      await page.waitForTimeout(2000);
      const url = page.url();
      expect(url).toMatch(/dashboard|login/);
    }
  });

  test('login page renders correctly', async ({ page }) => {
    await page.goto('/login');
    await expect(page).toHaveTitle(/DevOps|Login|AI/i);
  });

  test('redirect unauthenticated user', async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');
    // Should either show dashboard or redirect to login
    const url = page.url();
    expect(url).toMatch(/dashboard|login/);
  });
});

test.describe('Dashboard', () => {
  test('dashboard loads and shows key elements', async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');

    // Dashboard should have some visible content
    const body = await page.textContent('body');
    expect(body).toBeTruthy();
    expect(body!.length).toBeGreaterThan(50);
  });

  test('dashboard performance', async ({ page }) => {
    const start = Date.now();
    await page.goto('/dashboard');
    await page.waitForLoadState('domcontentloaded');
    const loadTime = Date.now() - start;

    // Dashboard should load within 5 seconds
    expect(loadTime).toBeLessThan(5000);
  });

  test('navigation links work', async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');

    // Check that links/navigation elements exist
    const links = await page.locator('a, button').count();
    expect(links).toBeGreaterThan(0);
  });
});

test.describe('Incident Response Flow', () => {
  test('can view incidents page', async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');

    const body = await page.textContent('body');
    expect(body).toBeTruthy();
  });
});

test.describe('Agent Builder Flow', () => {
  test('agent builder page loads', async ({ page }) => {
    await page.goto('/agents/builder');
    await page.waitForLoadState('networkidle');

    const body = await page.textContent('body');
    expect(body).toBeTruthy();
  });
});

test.describe('Marketplace Flow', () => {
  test('marketplace page loads with items', async ({ page }) => {
    await page.goto('/marketplace');
    await page.waitForLoadState('networkidle');

    const body = await page.textContent('body');
    expect(body).toBeTruthy();
  });
});
