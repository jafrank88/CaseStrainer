const { defineConfig } = require('cypress');
const { readFileSync, existsSync } = require('fs');
const { resolve } = require('path');

module.exports = defineConfig({
  e2e: {
    // Base URL for all tests
    baseUrl: 'http://localhost:8080',
    
    // Test settings
    testIsolation: false,
    specPattern: 'cypress/e2e/enhanced-validator.cy.js',
    
    // Timeout settings
    defaultCommandTimeout: 10000,
    pageLoadTimeout: 60000,
    responseTimeout: 30000,
    requestTimeout: 5000,
    taskTimeout: 60000,
    execTimeout: 60000,
    defaultAssertionTimeout: 5000,
    
    // Viewport settings
    viewportWidth: 1280,
    viewportHeight: 800,
    
    // File paths
    supportFile: 'cypress/support/e2e.js',
    fixturesFolder: 'cypress/fixtures',
    downloadsFolder: 'cypress/downloads',
    screenshotsFolder: 'cypress/screenshots',
    videosFolder: 'cypress/videos',
    
    // Screenshot configuration
    screenshotOnRunFailure: true,
    screenshotOptions: {
      capture: 'runner',
      clip: { x: 0, y: 0, width: 1280, height: 800 },
      scale: false,
      disableTimersAndAnimations: true,
      trashAssetsBeforeRuns: true
    },
    
    // Video settings
    video: false,
    videoCompression: 32,
    videoUploadOnPasses: false,
    
    // Browser settings
    chromeWebSecurity: false,
    modifyObstructiveCode: false,
    
    // Performance settings
    numTestsKeptInMemory: 5,
    
    // Retry configuration
    retries: {
      runMode: 2,
      openMode: 0
    },
    retryOnNetworkFailure: true,
    retryOnStatusCodeFailure: true,
    
    // Wait settings
    waitForAnimations: true,
    animationDistanceThreshold: 5,
    
    // Scroll behavior
    scrollBehavior: 'center',
    
    // File watching
    watchForFileChanges: false,
    
    // Experimental features
    experimentalFetchPolyfill: false,
    experimentalSessionAndOrigin: false,
    experimentalRunAllSpecs: false,
    experimentalStudio: false,
    experimentalWebKitSupport: false,
    
    // Environment variables
    env: {
      // API configuration
      apiUrl: 'http://localhost:5000/casestrainer/api',
      
      // Test user credentials
      testUser: {
        username: 'testuser',
        password: 'testpass123'
      },
      
      // API test settings
      api: {
        timeout: 30000,
        retries: 2
      }
    },
    
    // Node event handlers
    setupNodeEvents(on, config) {
      // Log to terminal for better debugging
      on('task', {
        log(message) {
          console.log(message);
          return null;
        },
        table(message) {
          console.table(message);
          return null;
        }
      });

      // Load environment variables from cypress.env.json if it exists
      try {
        const envPath = resolve('cypress.env.json');
        if (existsSync(envPath)) {
          const envData = readFileSync(envPath, 'utf8');
          const env = JSON.parse(envData);
          config.env = { ...config.env, ...env };
        }
      } catch (e) {
        // File doesn't exist or is invalid, ignore
      }

      return config;
    }
  },
  
  // Component testing configuration
  component: {
    devServer: {
      framework: 'vue',
      bundler: 'vite'
    }
  }
});
