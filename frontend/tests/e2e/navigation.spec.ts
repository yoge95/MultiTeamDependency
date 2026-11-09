import { test, expect } from '@playwright/test';

test.describe('Navigation', () => {
  test.beforeEach(async ({ page }) => {
    // Login before each test
    await page.goto('/login');
    await page.waitForLoadState('networkidle');
    
    const emailInput = page.locator('input[type="email"], input#email');
    await emailInput.clear();
    await emailInput.fill('admin@example.com');
    
    const passwordInput = page.locator('input[type="password"], input#password');
    await passwordInput.clear();
    await passwordInput.fill('admin123');
    
    await page.click('button[type="submit"]');
    
    // Wait for redirect
    await page.waitForURL(/\/(question|\?|$)/, { timeout: 15000 });
  });

  test('should redirect unauthenticated users to login', async ({ page, context }) => {
    // Clear authentication by clearing storage
    await context.clearCookies();
    await page.evaluate(() => localStorage.clear());
    
    // Try to access protected route
    await page.goto('/question');
    
    // Should redirect to login
    await expect(page).toHaveURL(/\/login/, { timeout: 5000 });
  });

  test('should navigate to home page', async ({ page }) => {
    // Go to root path
    await page.goto('/');
    
    // Should redirect to question page (home redirects to question)
    await page.waitForURL(/\/(question|\?|$)/, { timeout: 5000 });
  });

  test('should show application header', async ({ page }) => {
    // Should see header with app name
    const header = page.locator('header, nav, [class*="header"]').first();
    await expect(header).toBeVisible();
    
    // Should contain app name or logo
    await expect(page.locator('text=/knowledge|assistant/i').first()).toBeVisible();
  });
});
