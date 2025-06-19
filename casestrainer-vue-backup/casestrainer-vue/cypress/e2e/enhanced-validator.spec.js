/* eslint-disable no-undef */
/* global cy, describe, it, beforeEach, expect */

// Add custom command for better logging
Cypress.Commands.add('logStep', (message) => {
  const timestamp = new Date().toISOString();
  const logMessage = `[${timestamp}] STEP: ${message}`;
  cy.log(logMessage);
  cy.task('log', logMessage);
});

describe('Enhanced Validator - Text Analysis', () => {
  beforeEach(() => {
    // Clear any existing data
    cy.clearLocalStorage();
    cy.clearCookies();
    
    cy.logStep('Starting test setup...');
    
    // Visit the enhanced validator page with retry logic
    const visitWithRetry = (retries = 3) => {
      cy.logStep(`Visiting the enhanced validator page (${4 - retries}/3 attempts)`);
      
      return cy.visit('/casestrainer/enhanced-validator', {
        onBeforeLoad(win) {
          // Disable service worker if it's causing issues
          delete win.navigator.__proto__.serviceWorker;
        },
        timeout: 60000, // Increased timeout to 60 seconds
        retryOnStatusCodeFailure: true,
        retryOnNetworkFailure: true
      }).then(() => {
        // Verify the page loaded correctly
        return cy.get('h2', { timeout: 20000 })
          .should('be.visible')
          .and('contain', 'Enhanced Citation Validator')
          .then(() => {
            cy.logStep('Page loaded successfully');
            return true;
          });
      }).catch((err) => {
        if (retries <= 0) throw err;
        cy.wait(2000); // Wait 2 seconds before retry
        return visitWithRetry(retries - 1);
      });
    };
    
    // Start the visit process
    visitWithRetry();
    
    // Wait for any initial API calls to complete
    cy.intercept('**/api/**').as('apiRequests');
    cy.wait('@apiRequests', { timeout: 10000 }).then((interception) => {
      if (interception) {
        cy.logStep(`Initial API call completed: ${interception.request.url}`);
      }
    });
    
    // Switch to the "Paste Text" tab with better error handling
    cy.logStep('Switching to Paste Text tab');
    cy.contains('button', 'Paste Text', { timeout: 15000 })
      .should('be.visible')
      .and('not.be.disabled')
      .click({ force: true })
      .then(() => {
        cy.logStep('Switched to Paste Text tab');
        // Wait for any tab-specific content to load
        cy.get('textarea#textInput', { timeout: 10000 }).should('be.visible');
      });
  });

  // Helper function to test a single citation
  const testCitation = (citation, expectedCaseName) => {
    cy.logStep(`Testing citation: ${citation}`);
    
    // Clear and type the citation
    cy.get('textarea#textInput')
      .should('be.visible')
      .clear({ force: true })
      .type(citation, { delay: 50 });

    // Click the analyze button
    cy.contains('button', 'Analyze Text', { timeout: 10000 })
      .should('be.visible')
      .and('not.be.disabled')
      .click({ force: true });

    // Wait for analysis to complete
    cy.logStep('Waiting for analysis to complete...');
    cy.get('.analysis-result', { timeout: 30000 })
      .should('be.visible')
      .then(() => {
        cy.logStep('Analysis completed');
      });

    // Verify the case name is displayed
    if (expectedCaseName) {
      cy.get('.case-name')
        .should('be.visible')
        .and('contain', expectedCaseName);
    }
    
    // Take a screenshot for visual verification
    cy.screenshot(`citation-${citation.replace(/[^a-zA-Z0-9]/g, '-')}`, {
      capture: 'viewport'
    });
  };

  it('should analyze a legal citation from pasted text', () => {
    // Test data
    const testCases = [
      { citation: '534 F.3d 1290', caseName: 'United States v. Caraway' },
      { citation: '410 U.S. 113', caseName: 'Roe v. Wade' },
      { citation: '347 U.S. 483', caseName: 'Brown v. Board of Education' }
    ];
    
    cy.logStep('Starting citation analysis tests');
    
    // Test each citation
    testCases.forEach(({ citation, caseName }) => {
      testCitation(citation, caseName);
    });
  });
  
  it('should handle invalid citation format', () => {
    const invalidCitation = 'This is not a valid citation';
    
    cy.logStep('Testing invalid citation format');
    
    // Enter invalid citation
    cy.get('textarea#textInput')
      .clear()
      .type(invalidCitation);
      
    // Click analyze button
    cy.contains('button', 'Analyze Text').click();
    
    // Verify error message is shown
    cy.get('.error-message', { timeout: 10000 })
      .should('be.visible')
      .and('contain', 'No valid citations found');
      
    // Take a screenshot
    cy.screenshot('invalid-citation');
  });
  
  it('should handle empty input', () => {
    cy.logStep('Testing empty input');
    
    // Clear the input
    cy.get('textarea#textInput').clear();
    
    // Click analyze button
    cy.contains('button', 'Analyze Text').click();
    
    // Verify error message
    cy.get('.error-message', { timeout: 5000 })
      .should('be.visible')
      .and('contain', 'Please enter some text to analyze');
  });
  
  it('should handle large text input', () => {
    // Generate a large text with multiple citations
    const largeText = Array(100).fill().map(() => 
      'This is a sample legal text with a citation to 534 F.3d 1290 (2008)'
    ).join('\n\n');
    
    cy.logStep('Testing large text input');
    
    // Enter large text
    cy.get('textarea#textInput')
      .clear()
      .type(largeText, { delay: 0 });
      
    // Click analyze button
    cy.contains('button', 'Analyze Text').click();
    
    // Wait for analysis to complete
    cy.get('.analysis-result', { timeout: 60000 })
      .should('be.visible');
      
    // Verify at least one citation was found
    cy.get('.citation-result')
      .should('have.length.greaterThan', 0);
      
    // Take a screenshot
    cy.screenshot('large-text-analysis');
  });
  
  it('should maintain state between tab switches', () => {
    const testCitation = '410 U.S. 113';
    
    // Enter text in the textarea
    cy.get('textarea#textInput')
      .clear()
      .type(testCitation);
      
    // Switch to another tab and back
    cy.contains('button', 'Upload File').click();
    cy.contains('button', 'Paste Text').click();
    
    // Verify the text is still there
    cy.get('textarea#textInput')
      .should('have.value', testCitation);
  });
  
  it('should display loading state during analysis', () => {
    const testCitation = '347 U.S. 483';
    
    // Stub the API call to simulate a slow response
    cy.intercept('POST', '**/api/analyze', (req) => {
      // Add a delay to the response
      return Cypress.Promise.delay(2000).then(() => {
        req.reply({
          statusCode: 200,
          body: {
            citations: [{
              citation: testCitation,
              caseName: 'Brown v. Board of Education',
              status: 'found',
              details: 'This is a mock response for testing'
            }]
          }
        });
      });
    }).as('analyzeRequest');
    
    // Enter text and click analyze
    cy.get('textarea#textInput')
      .clear()
      .type(testCitation);
      
    cy.contains('button', 'Analyze Text').click();
    
    // Verify loading state is shown
    cy.get('.loading-indicator, [data-testid="loading-indicator"]', { timeout: 10000 })
      .should('be.visible');
      
    // Wait for the request to complete
    cy.wait('@analyzeRequest');
    
    // Verify loading state is hidden
    cy.get('.loading-indicator, [data-testid="loading-indicator"]')
      .should('not.exist');
  });
});
