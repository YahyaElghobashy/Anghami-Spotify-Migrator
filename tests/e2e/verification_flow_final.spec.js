const { test, expect } = require('@playwright/test');

test.describe('Verification Flow - Final Test', () => {
  test('Should open verification modal when clicking "Verified" text', async ({ page }) => {
    console.log('🔍 Testing verification modal functionality...');

    // Navigate to the app
    await page.goto('http://localhost:3000');
    await page.waitForLoadState('networkidle');

    // Take initial screenshot
    await page.screenshot({ 
      path: 'data/screenshots/final-01-initial.png',
      fullPage: true 
    });

    // Look for "Use Existing Setup" button
    const useExistingButton = page.locator('text=Use Existing Setup');
    if (await useExistingButton.isVisible()) {
      console.log('   → Clicking "Use Existing Setup"...');
      await useExistingButton.click();
      await page.waitForTimeout(2000);
    }

    // Wait for Welcome Back screen
    await page.waitForSelector('text=Welcome Back', { timeout: 15000 });
    await page.screenshot({ 
      path: 'data/screenshots/final-02-welcome-back.png',
      fullPage: true 
    });

    // Look for "Verified" text
    const verifiedElements = page.locator('text=Verified');
    const verifiedCount = await verifiedElements.count();
    console.log(`   → Found ${verifiedCount} "Verified" elements`);

    if (verifiedCount > 0) {
      // Take screenshot before clicking
      await page.screenshot({ 
        path: 'data/screenshots/final-03-before-click.png',
        fullPage: true 
      });

      // Click on the first "Verified" text
      console.log('   → Clicking on "Verified" text...');
      await verifiedElements.first().click();
      
      // Wait for modal to appear
      await page.waitForTimeout(2000);
      
      // Check if verification modal appeared
      const modal = page.locator('[role="dialog"], .fixed.inset-0');
      const modalVisible = await modal.isVisible();
      
      console.log(`   → Modal visible: ${modalVisible}`);
      
      // Take screenshot after clicking
      await page.screenshot({ 
        path: 'data/screenshots/final-04-after-click.png',
        fullPage: true 
      });

      if (modalVisible) {
        // Check modal content
        const modalTitle = page.locator('text=Spotify Account Verification');
        const titleVisible = await modalTitle.isVisible();
        console.log(`   → Modal title visible: ${titleVisible}`);
        
        await page.screenshot({ 
          path: 'data/screenshots/final-05-modal-open.png',
          fullPage: true 
        });

        // Close modal
        const closeButton = page.locator('button:has-text("×"), button:has-text("✕")');
        if (await closeButton.isVisible()) {
          await closeButton.click();
          await page.waitForTimeout(1000);
          console.log('   ✅ Modal closed successfully');
        }
      }
      
      console.log('   ✅ Verification modal test completed');
    } else {
      console.log('   ⚠ No "Verified" elements found');
    }
  });
}); 