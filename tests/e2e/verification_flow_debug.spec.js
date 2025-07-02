const { test, expect } = require('@playwright/test');

// Test configuration for verification flow debugging
const TEST_CONFIG = {
  BACKEND_URL: 'http://localhost:8000',
  FRONTEND_URL: 'http://localhost:3000',
  SCREENSHOTS_DIR: '../../data/screenshots',
  TIMEOUTS: {
    navigation: 15000,
    api_call: 20000,
    verification: 30000
  }
};

test.describe('Verification Flow Debug - Complete Journey', () => {
  let page;
  let context;
  let requestLog = [];
  let responseLog = [];

  test.beforeAll(async ({ browser }) => {
    // Create browser context with detailed logging
    context = await browser.newContext({
      viewport: { width: 1440, height: 900 },
      storageState: undefined
    });
    page = await context.newPage();

    // Setup comprehensive request/response logging
    page.on('request', request => {
      const logEntry = {
        method: request.method(),
        url: request.url(),
        headers: request.headers(),
        timestamp: new Date().toISOString()
      };
      requestLog.push(logEntry);
      console.log(`→ ${request.method()} ${request.url()}`);
    });

    page.on('response', response => {
      const logEntry = {
        status: response.status(),
        url: response.url(),
        headers: response.headers(),
        timestamp: new Date().toISOString()
      };
      responseLog.push(logEntry);
      console.log(`← ${response.status()} ${response.url()}`);
    });

    // Log console messages from the browser
    page.on('console', msg => {
      console.log(`[BROWSER LOG] ${msg.type()}: ${msg.text()}`);
    });

    // Log page errors
    page.on('pageerror', error => {
      console.error(`[PAGE ERROR] ${error.message}`);
    });
  });

  test.afterAll(async () => {
    // Save logs for debugging
    console.log('\n=== REQUEST LOG ===');
    console.log(JSON.stringify(requestLog, null, 2));
    console.log('\n=== RESPONSE LOG ===');
    console.log(JSON.stringify(responseLog, null, 2));
    await context.close();
  });

  test('Complete Verification Flow - From Setup to Verified User Debugging', async () => {
    console.log('🔍 Starting complete verification flow debugging...');

    // Step 1: Initial load and screenshot
    console.log('\n📸 Step 1: Loading initial application...');
    await page.goto(TEST_CONFIG.FRONTEND_URL);
    await page.waitForLoadState('networkidle');
    await page.screenshot({ 
      path: `${TEST_CONFIG.SCREENSHOTS_DIR}/01-initial-load.png`,
      fullPage: true 
    });

    // Step 2: Check current state and navigate accordingly
    console.log('\n📸 Step 2: Analyzing current state...');
    
    // Check what screen we're on
    const setupButton = page.locator('text=Setup Spotify Integration');
    const useExistingButton = page.locator('text=Use Existing Setup');
    const welcomeBackText = page.locator('text=Welcome Back');
    const loginButtons = page.locator('button:has-text("Login")');

    const isSetupScreen = await setupButton.isVisible().catch(() => false);
    const isWelcomeScreen = await welcomeBackText.isVisible().catch(() => false);
    
    await page.screenshot({ 
      path: `${TEST_CONFIG.SCREENSHOTS_DIR}/02-current-state.png`,
      fullPage: true 
    });

    if (isSetupScreen) {
      console.log('   → Currently on Setup screen, checking for existing setups...');
      
      // Check if "Use Existing Setup" is available
      if (await useExistingButton.isVisible()) {
        console.log('   → Clicking "Use Existing Setup" to get to verified users...');
        await useExistingButton.click();
        await page.waitForTimeout(2000);
        await page.screenshot({ 
          path: `${TEST_CONFIG.SCREENSHOTS_DIR}/03-after-use-existing.png`,
          fullPage: true 
        });
      } else {
        console.log('   → No existing setup available, clicking Setup Spotify Integration...');
        await setupButton.click();
        await page.waitForTimeout(2000);
        await page.screenshot({ 
          path: `${TEST_CONFIG.SCREENSHOTS_DIR}/03-after-setup-click.png`,
          fullPage: true 
        });
      }
    }

    // Step 3: Navigate to the Welcome Back screen with verified users
    console.log('\n📸 Step 3: Getting to Welcome Back screen...');
    
    // Wait for the Welcome Back screen to appear
    await page.waitForSelector('text=Welcome Back', { timeout: TEST_CONFIG.TIMEOUTS.navigation });
    await page.screenshot({ 
      path: `${TEST_CONFIG.SCREENSHOTS_DIR}/04-welcome-back-screen.png`,
      fullPage: true 
    });

    // Step 4: Analyze the verified users
    console.log('\n📸 Step 4: Analyzing verified users...');
    
    const userCards = page.locator('[class*="bg-"], .card, .border').filter({ hasText: 'Login' });
    const userCount = await userCards.count();
    console.log(`   → Found ${userCount} user cards`);

    for (let i = 0; i < userCount; i++) {
      const userCard = userCards.nth(i);
      const userName = await userCard.locator('text=/^[A-Za-z0-9\s]+$/').first().textContent();
      const hasVerified = await userCard.locator('text=Verified').isVisible();
      console.log(`   → User ${i + 1}: ${userName}, Verified: ${hasVerified}`);
    }

    await page.screenshot({ 
      path: `${TEST_CONFIG.SCREENSHOTS_DIR}/05-user-analysis.png`,
      fullPage: true 
    });

    // Step 5: Find and interact with "Verified" text
    console.log('\n📸 Step 5: Testing "Verified" click interaction...');
    
    const verifiedElements = page.locator('text=Verified');
    const verifiedCount = await verifiedElements.count();
    console.log(`   → Found ${verifiedCount} "Verified" elements`);

    if (verifiedCount > 0) {
      // Take screenshot before clicking
      await page.screenshot({ 
        path: `${TEST_CONFIG.SCREENSHOTS_DIR}/06-before-verified-click.png`,
        fullPage: true 
      });

      // Highlight the Verified element we're about to click
      await verifiedElements.first().highlight();
      await page.screenshot({ 
        path: `${TEST_CONFIG.SCREENSHOTS_DIR}/07-verified-highlighted.png`,
        fullPage: true 
      });

      // Get the element's properties before clicking
      const verifiedElement = verifiedElements.first();
      const boundingBox = await verifiedElement.boundingBox();
      const isClickable = await verifiedElement.isEnabled();
      const tagName = await verifiedElement.evaluate(el => el.tagName);
      const className = await verifiedElement.getAttribute('class');
      const role = await verifiedElement.getAttribute('role');

      console.log(`   → Verified element properties:`);
      console.log(`      Tag: ${tagName}`);
      console.log(`      Class: ${className}`);
      console.log(`      Role: ${role}`);
      console.log(`      Clickable: ${isClickable}`);
      console.log(`      Bounding box: ${JSON.stringify(boundingBox)}`);

      // Clear logs to focus on this interaction
      requestLog = [];
      responseLog = [];

      // Click on the "Verified" text
      console.log('   → Clicking on "Verified" text...');
      await verifiedElement.click();
      
      // Wait a moment for any navigation or loading
      await page.waitForTimeout(3000);
      
      // Take screenshot after clicking
      await page.screenshot({ 
        path: `${TEST_CONFIG.SCREENSHOTS_DIR}/08-after-verified-click.png`,
        fullPage: true 
      });

      // Analyze what happened after the click
      const currentUrl = page.url();
      const pageTitle = await page.title();
      const pageContent = await page.content();
      const isBlankPage = pageContent.includes('<body></body>') || pageContent.length < 500;

      console.log(`   → After clicking "Verified":`);
      console.log(`      Current URL: ${currentUrl}`);
      console.log(`      Page title: ${pageTitle}`);
      console.log(`      Is blank page: ${isBlankPage}`);
      console.log(`      Page content length: ${pageContent.length}`);

      // Check for any error messages or dialogs
      const errorMessages = page.locator('text=error, text=Error, [class*="error"]');
      const hasErrors = await errorMessages.count() > 0;
      
      if (hasErrors) {
        console.log('   → Found error messages:');
        for (let i = 0; i < await errorMessages.count(); i++) {
          const errorText = await errorMessages.nth(i).textContent();
          console.log(`      Error ${i + 1}: ${errorText}`);
        }
      }

      // Check for any modals or popups
      const modals = page.locator('[role="dialog"], .modal, [class*="modal"]');
      const hasModals = await modals.count() > 0;
      
      if (hasModals) {
        console.log('   → Found modals/dialogs:');
        await page.screenshot({ 
          path: `${TEST_CONFIG.SCREENSHOTS_DIR}/09-modal-detected.png`,
          fullPage: true 
        });
      }

      // Log any network activity that occurred
      console.log(`   → Network activity during click:`);
      console.log(`      Requests made: ${requestLog.length}`);
      console.log(`      Responses received: ${responseLog.length}`);
      
      if (requestLog.length > 0) {
        requestLog.forEach((req, index) => {
          console.log(`      Request ${index + 1}: ${req.method} ${req.url}`);
        });
      }
      
      if (responseLog.length > 0) {
        responseLog.forEach((res, index) => {
          console.log(`      Response ${index + 1}: ${res.status} ${res.url}`);
        });
      }

    } else {
      console.log('   ⚠ No "Verified" elements found!');
      await page.screenshot({ 
        path: `${TEST_CONFIG.SCREENSHOTS_DIR}/06-no-verified-found.png`,
        fullPage: true 
      });
    }

    // Step 6: Debug the issue by inspecting the DOM
    console.log('\n📸 Step 6: Deep DOM inspection...');
    
    const verifiedLinks = await page.evaluate(() => {
      const elements = document.querySelectorAll('*:contains("Verified")');
      return Array.from(elements).map(el => ({
        tagName: el.tagName,
        className: el.className,
        textContent: el.textContent,
        href: el.href,
        onclick: el.onclick ? el.onclick.toString() : null,
        parentTagName: el.parentElement ? el.parentElement.tagName : null,
        parentClassName: el.parentElement ? el.parentElement.className : null
      }));
    });

    console.log('   → Verified elements in DOM:');
    console.log(JSON.stringify(verifiedLinks, null, 2));

    // Step 7: Try alternative approaches to find clickable elements
    console.log('\n📸 Step 7: Testing alternative interaction methods...');
    
    // Try finding by different selectors
    const possibleSelectors = [
      'a:has-text("Verified")',
      'button:has-text("Verified")',
      '[href*="verified"]',
      '[onclick*="verified"]',
      'text=Verified >> ..',
      '.verified, #verified, [data-verified]'
    ];

    for (const selector of possibleSelectors) {
      try {
        const elements = page.locator(selector);
        const count = await elements.count();
        if (count > 0) {
          console.log(`   → Found ${count} elements with selector: ${selector}`);
          const element = elements.first();
          const href = await element.getAttribute('href');
          const onclick = await element.getAttribute('onclick');
          console.log(`      href: ${href}`);
          console.log(`      onclick: ${onclick}`);
        }
      } catch (error) {
        // Selector might not be valid, skip
      }
    }

    // Final screenshot
    await page.screenshot({ 
      path: `${TEST_CONFIG.SCREENSHOTS_DIR}/10-final-state.png`,
      fullPage: true 
    });

    console.log('\n✅ Verification flow debugging completed!');
    console.log(`📁 Screenshots saved to: ${TEST_CONFIG.SCREENSHOTS_DIR}`);
  });
}); 