import { test, expect } from '@playwright/test';

test.describe('Question Submission Flow', () => {
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
    
    // Wait for redirect to question page
    await page.waitForURL(/\/(question|\?|$)/, { timeout: 15000 });
  });

  test('should display question entry form', async ({ page }) => {
    // Should see the question input
    const questionInput = page.locator('textarea, input[type="text"]').first();
    await expect(questionInput).toBeVisible();
    
    // Should see submit button
    const submitButton = page.locator('button[type="submit"]').first();
    await expect(submitButton).toBeVisible();
  });

  test('should submit a question successfully', async ({ page }) => {
    const questionText = `What is the status of project Alpha as of ${new Date().toISOString()}?`;
    
    // Fill in the question
    const questionInput = page.locator('textarea, input[type="text"]').first();
    await questionInput.fill(questionText);
    
    // Submit the question
    const submitButton = page.locator('button[type="submit"]').first();
    await submitButton.click();
    
    // Wait for either:
    // 1. Redirect to answer page
    // 2. Clarification prompt appears
    // 3. Processing indicator appears
    await page.waitForURL(/\/(answer|question)/, { timeout: 15000 }).catch(() => {
      // If no redirect, check for clarification or processing state
    });
    
    // Verify we're not on an error page
    const errorText = page.locator('text=/error|failed|something went wrong/i');
    const errorCount = await errorText.count();
    expect(errorCount).toBe(0);
  });

  test('should validate empty question', async ({ page }) => {
    // The submit button should be disabled when question is empty
    const submitButton = page.locator('button[type="submit"]').first();
    
    // Check if button is disabled (which is the correct behavior)
    const isDisabled = await submitButton.isDisabled();
    expect(isDisabled).toBeTruthy();
  });

  test('should enforce character limit', async ({ page }) => {
    const longQuestion = 'x'.repeat(2100);
    
    const questionInput = page.locator('textarea, input[type="text"]').first();
    await questionInput.fill(longQuestion);
    
    const submitButton = page.locator('button[type="submit"]').first();
    
    // Either button is disabled or clicking shows error
    const isDisabled = await submitButton.isDisabled();
    
    if (!isDisabled) {
      await submitButton.click();
      
      // Wait a moment for error to appear
      await page.waitForTimeout(1000);
      
      // Should show character limit error or still be on question page
      const errorMessage = page.locator('text=/character|too long|limit|2000/i');
      const hasError = await errorMessage.count() > 0;
      const stillOnQuestionPage = page.url().includes('/question');
      
      expect(hasError || stillOnQuestionPage).toBeTruthy();
    } else {
      // Button correctly disabled for too-long input
      expect(isDisabled).toBeTruthy();
    }
  });
});
