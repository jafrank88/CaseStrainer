// ***********************************************
// This example support/e2e.js is processed and
// loaded automatically before your test files.
// ***********************************************

// Import commands.js using ES2015 syntax:
import './commands';

// Alternatively you can use CommonJS syntax:
// require('./commands')


// Custom error messages for common assertions
chai.Assertion.addMethod('withinViewport', function () {
  const $el = this._obj;
  const windowHeight = Cypress.config('viewportHeight');
  const windowWidth = Cypress.config('viewportWidth');
  const rect = $el[0].getBoundingClientRect();

  this.assert(
    rect.top >= 0 &&
    rect.left >= 0 &&
    rect.bottom <= windowHeight &&
    rect.right <= windowWidth,
    'expected #{this} to be within the viewport',
    'expected #{this} to not be within the viewport',
    this._obj
  );
});

// Global before hook to run before all tests
before(() => {
  // Add any global setup here
  cy.log('Running global test setup');
});

// Global beforeEach hook to run before each test
beforeEach(() => {
  // Add any test setup here
  cy.log(`Starting test: ${Cypress.currentTest.title}`);
});

// Global afterEach hook to run after each test
afterEach(() => {
  // Add any test cleanup here
  cy.log(`Finished test: ${Cypress.currentTest.title}`);
});

// Global after hook to run after all tests
after(() => {
  // Add any global cleanup here
  cy.log('All tests completed');
});
