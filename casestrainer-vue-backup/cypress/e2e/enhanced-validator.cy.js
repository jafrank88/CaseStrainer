// Test setup with improved error handling
describe('Enhanced Validator - Text Analysis', { 
  // Increase test timeout to 2 minutes
  defaultCommandTimeout: 120000,
  // Disable video recording
  video: false,
  // Disable screenshots on failure
  screenshotOnRunFailure: false
}, () => {
  before(() => {
    // Run once before all tests
    cy.log('Setting up test environment');
  });

  beforeEach(() => {
    cy.logStep('Starting test setup');
    
    // Clear cookies and local storage before each test
    cy.clearCookies();
    cy.clearLocalStorage();
    
    // Visit the enhanced validator page directly
    cy.visit('/enhanced-validator', {
      onBeforeLoad(win) {
        // Disable service workers that might interfere with tests
        delete win.navigator.__proto__.serviceWorker;
      },
      timeout: 60000
    });

    // Wait for the page to load completely
    cy.get('h2', { timeout: 30000 })
      .should('be.visible')
      .and('contain', 'Enhanced Citation Validator');

    // Set up API intercept with correct prefix
    cy.intercept('POST', '/casestrainer/api/analyze').as('apiRequests');
    
    // Ensure the page is fully interactive
    cy.window().should('have.property', 'app');
    
    // Wait for the tab navigation to be visible and store in alias
    const navTabs = '.nav-tabs';
    cy.get(navTabs, { timeout: 10000 }).should('be.visible');
    
    // Find and click the "Paste Text" tab
    const pasteTabSelector = `${navTabs} .nav-link`;
    const pasteTabText = 'Paste Text';
    cy.get(pasteTabSelector).contains(pasteTabText).as('pasteTab');
    cy.get('@pasteTab').click();
    
    // Wait for the tab to be active
    cy.get(`${pasteTabSelector}.active`).should('contain', pasteTabText);
    
    // Verify the tab is active
    cy.get(`${pasteTabSelector}.active`).should('contain', 'Paste Text');
    
    // Wait for the enhanced text paste container to be visible
    cy.get('.enhanced-text-paste', { timeout: 10000 })
      .should('be.visible')
      .as('textPasteContainer');
      
    // Now check for the textarea inside the container
    cy.get('@textPasteContainer')
      .find('textarea#textInput')
      .should('be.visible')
      .as('textInput');
  });
  
  afterEach(() => {
    // Log test completion
    cy.log('Test completed');
  });
  
  // Helper function to test a single citation
  const testCitation = (citation, expectedText) => {
    cy.logStep(`Testing citation: ${citation}`);
    
    try {
      // Get the text input and verify it's visible and enabled
      const textInput = '@textInput';
      cy.get(textInput, { timeout: 10000 }).as('inputElement');
      cy.get('@inputElement').should('be.visible');
      cy.get('@inputElement').should('be.enabled');
      
      // Clear the input
      cy.get('@textInput').clear();
      
      // Type the citation and verify the value
      cy.get('@textInput').type(citation);
      cy.get('@textInput').should('have.value', citation);
      
      // Click the analyze button
      cy.get('@textPasteContainer').within(() => {
        cy.contains('button', 'Analyze Citations')
          .should('be.visible')
          .and('be.enabled')
          .click();
      });
      
      // Wait for API call to complete with retry logic
      cy.wait('@apiRequests', { timeout: 30000 })
        .then((interception) => {
          expect(interception.response.statusCode).to.be.oneOf([200, 201]);
          return cy.wrap(interception);
        });
      
      // Verify the results are displayed
      cy.get('.results-container', { timeout: 30000 })
        .should('be.visible')
        .and('contain', expectedText || 'Citation Analysis Results');
        
      return cy.wrap(true);
    } catch (error) {
      cy.log('Error in testCitation:', error);
      return cy.wrap(false);
    }
  };

  it('should analyze a legal citation from pasted text', () => {
    const citation = '410 U.S. 113 (1973)';
    testCitation(citation, 'Citation Analysis Results');
  });

  it('should handle multiple citations in pasted text', () => {
    const citations = '410 U.S. 113 (1973)\n505 U.S. 833 (1992)';
    testCitation(citations, 'Citation Analysis Results');
  });

  it('should show appropriate error for invalid citation format', () => {
    const invalidCitation = 'Not a valid citation';
    testCitation(invalidCitation, 'No citations found');
  });

  it('should handle empty input', () => {
    cy.logStep('Testing empty input');
    
    try {
      // Clear the input
      cy.get('@textInput')
        .should('be.visible')
        .clear()
        .should('have.value', '');
      
      // Click the analyze button
      cy.get('@textPasteContainer').within(() => {
        cy.contains('button', 'Analyze Citations')
          .should('be.visible')
          .and('be.enabled')
          .click();
      });
      
      // Check for validation error - try multiple possible selectors
      cy.get('.error-message, .alert-danger, .text-danger, .alert-warning', { timeout: 10000 })
        .first()
        .should('be.visible')
        .and('contain', 'Please enter some text to analyze');
    } catch (error) {
      cy.log('Error in empty input test:', error);
      throw error;
    }
  });
  
  it('should handle large text input', () => {
    // Generate a large text with multiple citations
    const largeText = Array(100).fill('534 F.3d 1290').join('\n');
    
    try {
      // Type the large text into the input
      cy.get('@textInput')
        .should('be.visible')
        .clear()
        .type(largeText)
        .should('have.value', largeText);
      
      // Click the analyze button
      cy.get('@textPasteContainer').within(() => {
        cy.contains('button', 'Analyze Citations')
          .should('be.visible')
          .and('be.enabled')
          .click();
      });
      
      // Wait for API call to complete
      cy.wait('@apiRequests', { timeout: 60000 })
        .then((interception) => {
          expect(interception.response.statusCode).to.be.oneOf([200, 201]);
        });
      
      // Verify the results are displayed
      cy.get('.results-container', { timeout: 30000 })
        .should('be.visible')
        .and('contain', 'Citation Analysis Results');
    } catch (error) {
      cy.log('Error in large text input test:', error);
      throw error;
    }
  });
  
  it('should handle network errors gracefully', () => {
    // Intercept the API call and force an error
    cy.intercept('POST', '/casestrainer/api/analyze', {
      statusCode: 500,
      body: { error: 'Internal Server Error' },
      forceNetworkError: false
    }).as('analyzeRequest');
    
    const citation = '410 U.S. 113';
    
    try {
      // Type the citation into the input
      cy.get('@textInput')
        .should('be.visible')
        .clear()
        .type(citation)
        .should('have.value', citation);
      
      // Click the analyze button
      cy.get('@textPasteContainer').within(() => {
        cy.contains('button', 'Analyze Citations')
          .should('be.visible')
          .and('be.enabled')
          .click();
      });
      
      // Wait for the error response
      cy.wait('@analyzeRequest', { timeout: 30000 });
      
      // Verify error message is shown - check multiple possible selectors
      cy.get('.alert-danger, .error-message, .alert-error', { timeout: 10000 })
        .first()
        .should('be.visible')
        .and('contain', 'error');
    } catch (error) {
      cy.log('Error in network error test:', error);
      throw error;
    }
  });
});
