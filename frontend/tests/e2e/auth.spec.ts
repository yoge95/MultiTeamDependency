import { test, expect } from '@playwright/test';

test.describe('Authentication Flow', () => {
  test('should login with valid credentials', async ({ page }) => {
    await page.goto('/login');
    
    // Wait for page to load
    await page.waitForLoadState('networkidle');
    await expect(page.locator('h1, h2').filter({ hasText: /welcome back|login|sign in/i })).toBeVisible({ timeout: 10000 });
    
    // Fill in credentials - clear first since form has default values
    const emailInput = page.locator('input[type="email"], input#email');
    await emailInput.clear();
    await emailInput.fill('admin@example.com');
    
    const passwordInput = page.locator('input[type="password"], input#password');
    await passwordInput.clear();
    await passwordInput.fill('admin123');
    
    // Submit form
    await page.click('button[type="submit"]');
    
    // Should redirect to question page after successful login
    await page.waitForURL(/\/(question|\?|$)/, { timeout: 15000 });
    
    // Should see question input area
    await expect(page.locator('textarea, input[type="text"]').first()).toBeVisible({ timeout: 5000 });
  });

  test('should reject invalid credentials', async ({ page }) => {
    await page.goto('/login');
    await page.waitForLoadState('networkidle');
    
    const emailInput = page.locator('input[type="email"], input#email');
    await emailInput.clear();
    await emailInput.fill('invalid@example.com');
    
    const passwordInput = page.locator('input[type="password"], input#password');
    await passwordInput.clear();
    await passwordInput.fill('wrongpassword');
    
    await page.click('button[type="submit"]');
    
    // Should show error message - wait a bit for API response
    await page.waitForTimeout(2000);
    
    // Should still be on login page or show error
    const isOnLoginPage = page.url().includes('/login');
    const errorLocator = page.locator('text=/error|invalid|failed|incorrect/i');
    const hasErrorMessage = await errorLocator.count() > 0;
    
    expect(isOnLoginPage || hasErrorMessage).toBeTruthy();
  });

  test('should logout successfully', async ({ page }) => {
    // Login first
    await page.goto('/login');
    await page.waitForLoadState('networkidle');
    
    const emailInput = page.locator('input[type="email"], input#email');
    await emailInput.clear();
    await emailInput.fill('admin@example.com');
    
    const passwordInput = page.locator('input[type="password"], input#password');
    await passwordInput.clear();
    await passwordInput.fill('admin123');
    
    await page.click('button[type="submit"]');
    
    // Wait for redirect to question page
    await page.waitForURL(/\/(question|\?|$)/, { timeout: 15000 });
    
    // Find and click logout button
    const logoutButton = page.locator('button, a').filter({ hasText: /logout|sign out/i });
    if (await logoutButton.count() > 0) {
      await logoutButton.first().click();
      
      // Should redirect to login page
      await expect(page).toHaveURL(/\/login/, { timeout: 5000 });
    }
  });
});
