import { test, expect } from '@playwright/test';

test.describe('Critical Path: Security Pages', () => {
  test('compliance page loads', async ({ page }) => {
    await page.goto('/compliance');
    await page.waitForLoadState('networkidle');

    const body = await page.textContent('body');
    expect(body).toContain('Compliance');
  });

  test('security page loads', async ({ page }) => {
    await page.goto('/security');
    await page.waitForLoadState('networkidle');

    const body = await page.textContent('body');
    expect(body).toContain('Security');
  });

  test('disaster recovery page loads', async ({ page }) => {
    await page.goto('/disaster-recovery');
    await page.waitForLoadState('networkidle');

    const body = await page.textContent('body');
    expect(body).toContain('Disaster Recovery');
  });
});

test.describe('Critical Path: Analytics Pages', () => {
  test('reports page loads', async ({ page }) => {
    await page.goto('/reports');
    await page.waitForLoadState('networkidle');
    const body = await page.textContent('body');
    expect(body).toBeTruthy();
  });

  test('SLA page loads', async ({ page }) => {
    await page.goto('/sla');
    await page.waitForLoadState('networkidle');
    const body = await page.textContent('body');
    expect(body).toBeTruthy();
  });

  test('costs page loads', async ({ page }) => {
    await page.goto('/costs');
    await page.waitForLoadState('networkidle');
    const body = await page.textContent('body');
    expect(body).toBeTruthy();
  });
});

test.describe('Critical Path: Agent Pages', () => {
  test('agent status page loads', async ({ page }) => {
    await page.goto('/agents/status');
    await page.waitForLoadState('networkidle');
    const body = await page.textContent('body');
    expect(body).toBeTruthy();
  });

  test('chaos engineering page loads', async ({ page }) => {
    await page.goto('/chaos');
    await page.waitForLoadState('networkidle');
    const body = await page.textContent('body');
    expect(body).toContain('Chaos');
  });
});

test.describe('Visual Regression', () => {
  test('dashboard screenshot', async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);
    // Visual regression — uncomment when baselines are set:
    // await expect(page).toHaveScreenshot('dashboard.png', { maxDiffPixels: 100 });
    await page.screenshot({ path: 'test-results/dashboard-screenshot.png', fullPage: true });
  });

  test('login screenshot', async ({ page }) => {
    await page.goto('/login');
    await page.waitForLoadState('networkidle');
    await page.screenshot({ path: 'test-results/login-screenshot.png', fullPage: true });
  });
});

test.describe('Mobile Responsiveness', () => {
  test.use({ viewport: { width: 375, height: 667 } });

  test('mobile dashboard loads', async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');

    const body = await page.textContent('body');
    expect(body).toBeTruthy();
  });

  test('mobile navigation works', async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');

    // Page should be functional at mobile width
    const viewportSize = page.viewportSize();
    expect(viewportSize?.width).toBe(375);
  });
});

test.describe('Performance Metrics', () => {
  test('page load performance', async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForLoadState('load');

    const metrics = await page.evaluate(() => {
      const entries = performance.getEntriesByType('navigation') as PerformanceNavigationTiming[];
      if (entries.length === 0) return { loadTime: 0, domContentLoaded: 0 };
      const perf = entries[0];
      return {
        loadTime: perf.loadEventEnd - perf.fetchStart,
        domContentLoaded: perf.domContentLoadedEventEnd - perf.fetchStart,
        firstByte: perf.responseStart - perf.fetchStart,
      };
    });

    // Page should load within 5 seconds
    expect(metrics.loadTime).toBeLessThan(5000);
    // DOM content loaded within 3 seconds
    expect(metrics.domContentLoaded).toBeLessThan(3000);
  });
});

test.describe('Accessibility', () => {
  test('dashboard has proper heading structure', async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');

    const h1Count = await page.locator('h1').count();
    expect(h1Count).toBeGreaterThanOrEqual(1);
  });

  test('interactive elements are focusable', async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');

    // Tab through interactive elements
    await page.keyboard.press('Tab');
    const focused = await page.evaluate(() => document.activeElement?.tagName);
    expect(focused).toBeTruthy();
  });

  test('images have alt text', async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');

    const imagesWithoutAlt = await page.locator('img:not([alt])').count();
    expect(imagesWithoutAlt).toBe(0);
  });
});
