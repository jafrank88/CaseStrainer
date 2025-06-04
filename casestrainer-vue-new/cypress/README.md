# CaseStrainer End-to-End Tests

This directory contains end-to-end (E2E) tests for the CaseStrainer application using [Cypress](https://www.cypress.io/).

## Prerequisites

- Node.js (v14 or later)
- npm (v6 or later)
- CaseStrainer development server running on `http://localhost:5173`

## Installation

1. Install dependencies:
   ```bash
   npm install
   ```

2. Install Cypress (if not already installed):
   ```bash
   npm install cypress --save-dev
   ```

## Running Tests

### Development Mode

1. Start the development server:
   ```bash
   npm run dev
   ```

2. In a separate terminal, open the Cypress Test Runner:
   ```bash
   npx cypress open
   ```

3. Click on a test file to run it in the interactive test runner.

### Headless Mode

Run all tests in headless mode:
```bash
npx cypress run
```

Run a specific test file:
```bash
npx cypress run --spec "cypress/e2e/home.cy.js"
```

## Test Structure

- `cypress/e2e/` - Contains all test files
  - `home.cy.js` - Tests for the home page
  - `citation.cy.js` - Tests for citation validation
- `cypress/fixtures/` - Contains test data
  - `validCitation.json` - Example of a valid citation response
  - `invalidCitation.json` - Example of an invalid citation response
- `cypress/support/` - Support files
  - `e2e.js` - Runs before every test file
  - `commands.js` - Custom Cypress commands

## Writing Tests

### Best Practices

1. **Descriptive Test Names**: Use descriptive test names that explain what is being tested.
2. **Isolation**: Each test should be independent and not rely on the state of other tests.
3. **Selectors**: Use `data-*` attributes to select elements instead of CSS classes.
4. **Assertions**: Make assertions about the state of the application, not just the presence of elements.
5. **Page Objects**: Consider using Page Object Model for complex applications.

### Example Test

```javascript
describe('Citation Validation', () => {
  beforeEach(() => {
    cy.visit('/')
  })

  it('validates a citation successfully', () => {
    const testCitation = '123 U.S. 456'
    
    cy.get('input[type="text"]')
      .clear()
      .type(testCitation)
    
    cy.get('button[type="submit"]')
      .click()
    
    // Assertions...
  })
})
```

## Continuous Integration

To run tests in a CI environment, add this to your CI configuration:

```yaml
- name: Run Cypress tests
  run: |
    npm install
    npm run test:ci
```

## Debugging

- Use `cy.log()` to log messages to the command log.
- Use `cy.pause()` to pause test execution.
- Use `cy.debug()` to pause and inspect the application state.
- Check the Cypress Dashboard for screenshots and videos of test runs.

## Resources

- [Cypress Documentation](https://docs.cypress.io/)
- [Cypress Best Practices](https://docs.cypress.io/guides/references/best-practices)
- [Cypress API Reference](https://docs.cypress.io/api/table-of-contents)
