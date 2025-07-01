const { defineConfig, devices } = require('@playwright/test');

module.exports = defineConfig({
  // Test directory - updated for new structure
  testDir: '../e2e',
  
  // Timeout settings
  timeout: 60000,
  expect: {
    timeout: 10000
  },
  
  // Global test settings
  fullyParallel: false, // Run tests sequentially for user journey testing
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 1,
  workers: 1, // Single worker for consistent user journey testing
  
  // Reporter configuration - updated paths
  reporter: [
    ['html', { outputFolder: '../../data/test-results/html-report' }],
    ['json', { outputFile: '../../data/test-results/test-results.json' }],
    ['list'],
    ['junit', { outputFile: '../../data/test-results/junit.xml' }]
  ],
  
  // Global test configuration
  use: {
    // Base URL for tests
    baseURL: 'http://localhost:5173',
    
    // Browser settings
    headless: process.env.CI ? true : false,
    viewport: { width: 1440, height: 900 },
    
    // Screenshots and videos - updated paths
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    trace: 'retain-on-failure',
    
    // Timeouts
    actionTimeout: 15000,
    navigationTimeout: 30000,
    
    // Ignore HTTPS errors for development
    ignoreHTTPSErrors: true,
    
    // Color scheme
    colorScheme: 'light',
    
    // Locale
    locale: 'en-US',
    timezoneId: 'America/New_York'
  },

  // Project configurations for different browsers and scenarios
  projects: [
    {
      name: 'chromium-desktop',
      use: { 
        ...devices['Desktop Chrome'],
        viewport: { width: 1440, height: 900 }
      },
    },
    {
      name: 'webkit-desktop',
      use: { 
        ...devices['Desktop Safari'],
        viewport: { width: 1440, height: 900 }
      },
    },
    {
      name: 'firefox-desktop',
      use: { 
        ...devices['Desktop Firefox'],
        viewport: { width: 1440, height: 900 }
      },
    },
    {
      name: 'mobile-chrome',
      use: { 
        ...devices['Pixel 5'],
      },
    },
    {
      name: 'mobile-safari',
      use: { 
        ...devices['iPhone 12'],
      },
    },
    {
      name: 'tablet-chrome',
      use: { 
        ...devices['iPad Pro'],
      },
    }
  ],

  // Development server configuration
  webServer: [
    {
      command: 'cd ../../ui && npm run dev',
      port: 5173,
      reuseExistingServer: !process.env.CI,
      timeout: 30000
    },
    {
      command: 'cd ../../ && python backend_api.py',
      port: 8000,
      reuseExistingServer: !process.env.CI,
      timeout: 30000
    }
  ],

  // Output directory for test artifacts - updated path
  outputDir: '../../data/test-results/artifacts',
  
  // Global setup and teardown - updated paths
  globalSetup: require.resolve('../global-setup.js'),
  globalTeardown: require.resolve('../global-teardown.js'),
}); 