// cypress.config.js
import { defineConfig } from 'cypress'

export default defineConfig({
  // Project configuration
  projectId: '1p1qnm',
  
  // E2E testing configuration
  e2e: {
    // Base URL for all tests
    baseUrl: 'http://localhost:5173',
    
    // Support file location
    supportFile: 'cypress/support/e2e.js',
    
    // Test file patterns
    specPattern: [
      'cypress/e2e/**/*.cy.{js,jsx,ts,tsx}',
      'cypress/integration/**/*.spec.{js,jsx,ts,tsx}'
    ],
    
    // Viewport settings
    viewportWidth: 1280,
    viewportHeight: 800,
    
    // Default command timeout (ms)
    defaultCommandTimeout: 10000,
    
    // Response timeout (ms)
    responseTimeout: 30000,
    
    // Page load timeout (ms)
    pageLoadTimeout: 60000,
    
    // Request timeout (ms)
    requestTimeout: 15000,
    
    // Folder where screenshots will be saved
    screenshotsFolder: 'cypress/screenshots',
    
    // Folder where videos will be saved
    videosFolder: 'cypress/videos',
    
    // Enable video recording
    video: true,
    
    // Number of times to retry a failing test
    retries: {
      runMode: 2,
      openMode: 0
    },
    
    // Node event listeners
    setupNodeEvents(on, config) {
      // Example: Load environment variables from .env file
      // require('dotenv').config()
      
      // Example: Add custom tasks
      // on('task', {
      //   log(message) {
      //     console.log(message)
      //     return null
      //   }
      // })
      
      // Example: Load environment-specific configuration
      // const env = config.env.configFile || 'development'
      // const envConfig = require(`./cypress/config/${env}.json`)
      // return { ...config, env: { ...config.env, ...envConfig } }
      
      return config
    }
  },
  
  // Component testing configuration (if needed)
  component: {
    devServer: {
      framework: 'vue',
      bundler: 'vite'
    }
  },
  
  // Environment variables that will be available in tests
  env: {
    // API_BASE_URL: 'http://localhost:5000/casestrainer/api',
    // AUTH_USER: 'test@example.com',
    // AUTH_PASS: 'test123',
  },
  
  // Global test configuration
  // These values will be available in all test files via Cypress.config()
  config: {
    // Custom configuration values
    appName: 'CaseStrainer',
    version: '1.0.0',
    
    // API endpoints
    endpoints: {
      validate: '/casestrainer/api/validate',
      // Add other API endpoints as needed
    },
    
    // Test users
    users: {
      admin: {
        email: 'admin@example.com',
        password: 'admin123'
      },
      // Add other test users as needed
    }
  }
})
