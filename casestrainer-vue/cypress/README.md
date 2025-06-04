# CaseStrainer E2E Testing with Cypress

This directory contains end-to-end (E2E) tests for the CaseStrainer application using Cypress. These tests ensure that the application works as expected from the user's perspective.

## Prerequisites

- Node.js (v14 or later)
- npm (v7 or later)
- CaseStrainer backend running on port 5000 (http://localhost:5000)
- Vue.js frontend running (if testing against local development server)

## Installation

1. Install dependencies:
   ```bash
   npm install
   ```

2. Install Cypress (if not already installed):
   ```bash
   npm install --save-dev cypress
   ```

## Configuration

Configuration is managed in `cypress.config.js`. Environment variables can be set in `cypress.env.json`.

Default configuration includes:
- Base URL: `http://localhost:5000/casestrainer`
- Viewport: 1280x800
- Timeout settings optimized for API calls
- Automatic retries for failed tests

## Running Tests

### Interactive Mode (Cypress Test Runner)

1. Start the backend server:
   ```bash
   # From the project root
   python src/app_final_vue.py
   ```

2. In a separate terminal, open the Cypress Test Runner:
   ```bash
   npm run test:e2e
   ```

3. Click on the test file you want to run in the Cypress Test Runner.

### Headless Mode (CI/CD)

Run all tests in headless mode:
```bash
npm run test:e2e:headless
```

### Running Specific Tests

Run a specific test file:
```bash
npx cypress run --spec "cypress/e2e/enhanced-validator.spec.js"
```

## Test Structure

- `cypress/e2e/` - Contains all test files
- `cypress/fixtures/` - Contains test data (e.g., mock API responses)
- `cypress/support/` - Custom commands and global configurations
- `cypress/screenshots/` - Screenshots of test failures
- `cypress/videos/` - Video recordings of test runs

## Writing Tests

### Best Practices

1. **Use Custom Commands**: Common actions should be abstracted into custom commands in `cypress/support/commands.js`
2. **Use Fixtures**: Store test data in JSON files under `cypress/fixtures/`
3. **Keep Tests Independent**: Each test should be able to run independently
4. **Add Assertions**: Every test should verify the expected outcome
5. **Use Data Attributes**: Prefer `data-testid` over CSS selectors for better test stability

### Example Test Structure

```javascript
describe('Feature Name', () => {
  beforeEach(() => {
    // Common setup for all tests
    cy.visit('/path-to-page')
  })

  it('should do something', () => {
    // Test steps and assertions
    cy.get('[data-testid="element"]').should('be.visible')
  })
})
```

## API Testing

The test suite includes API tests that interact directly with the backend. These tests verify:
- Endpoint availability
- Request/response formats
- Error handling
- Authentication/authorization (if applicable)

## Debugging

1. Use `cy.log()` to log information to the command log
2. Use `cy.pause()` to pause test execution
3. Use `cy.debug()` to debug the current state
4. Check the browser's developer tools for additional debugging information

## Continuous Integration

For CI/CD, ensure the following environment variables are set:

- `CYPRESS_BASE_URL`: The base URL of the application under test
- `CYPRESS_RECORD_KEY`: Your Cypress record key (if using Cypress Dashboard)

## Resources

- [Cypress Documentation](https://docs.cypress.io/)
- [Cypress Best Practices](https://docs.cypress.io/guides/references/best-practices)
- [Cypress API Reference](https://docs.cypress.io/api/table-of-contents)
- Use `describe()` and `it()` blocks to organize tests
- Use `beforeEach()` for test setup

## Test Data

- Test data can be stored in the `cypress/fixtures` directory
- Use `cy.fixture()` to load test data in your tests

## Best Practices

- Keep tests independent and isolated
- Use meaningful test descriptions
- Use data attributes (`data-*`) to target elements instead of CSS selectors
- Use custom commands for common actions
- Clean up after tests when necessary

## Debugging

- Use `cy.log()` to log messages to the Cypress Command Log
- Use `cy.pause()` to pause test execution
- Use `cy.debug()` to pause and debug at a specific point in your test
- Check the browser console for errors during test execution

## CI/CD Integration

For CI/CD integration, you can use the following command to run tests in headless mode:

```bash
npm run test:e2e:headless
```

This will run all tests in the `cypress/e2e` directory and generate a video and screenshots of test failures.
