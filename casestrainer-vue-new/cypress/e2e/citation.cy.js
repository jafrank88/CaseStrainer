// Test suite for Citation Validation functionality
describe('Citation Validation', () => {
  // Before each test, visit the home page and set up API mocks
  beforeEach(() => {
    cy.visit('/')
    
    // Mock successful citation validation response
    cy.intercept('POST', '/casestrainer/api/validate', {
      statusCode: 200,
      fixture: 'validCitation.json'
    }).as('validateCitation')
  })

  // Test successful citation validation
  it('validates a citation successfully', () => {
    const testCitation = '123 U.S. 456'
    
    // Enter citation and submit the form
    cy.get('input[type="text"]')
      .clear()
      .type(testCitation)
    
    cy.get('button[type="submit"]')
      .click()
    
    // Wait for the API call to complete
    cy.wait('@validateCitation')
    
    // Check if the results section is displayed
    cy.get('.results-section')
      .should('be.visible')
      .within(() => {
        // Check if the citation is displayed correctly
        cy.get('.citation-text')
          .should('be.visible')
          .and('contain', testCitation)
        
        // Check validation status
        cy.get('.validation-status')
          .should('be.visible')
          .and('contain', 'Valid')
        
        // Check if metadata is displayed
        cy.get('.metadata-section')
          .should('be.visible')
          .within(() => {
            cy.get('.case-name').should('contain', 'Sample Case Name')
            cy.get('.citation-details').should('contain', '123 U.S. 456')
            cy.get('.decision-year').should('contain', '2022')
          })
      })
  })

  // Test handling of invalid citation format
  it('shows an error for invalid citation format', () => {
    // Mock failed validation response
    cy.intercept('POST', '/casestrainer/api/validate', {
      statusCode: 200,
      fixture: 'invalidCitation.json'
    }).as('invalidCitation')
    
    const invalidCitation = 'invalid-citation'
    
    // Enter invalid citation and submit
    cy.get('input[type="text"]')
      .clear()
      .type(invalidCitation)
    
    cy.get('button[type="submit"]')
      .click()
    
    // Wait for the API call to complete
    cy.wait('@invalidCitation')
    
    // Check if error message is displayed
    cy.get('.error-message')
      .should('be.visible')
      .within(() => {
        cy.get('.error-title')
          .should('be.visible')
          .and('contain', 'Validation Error')
        
        cy.get('.error-details')
          .should('be.visible')
          .and('contain', 'Invalid citation format')
      })
  })

  // Test network error handling
  it('handles network errors gracefully', () => {
    // Mock network error
    cy.intercept('POST', '/casestrainer/api/validate', {
      statusCode: 500,
      body: {
        error: 'Internal Server Error',
        message: 'An unexpected error occurred'
      }
    }).as('serverError')
    
    // Submit the form
    cy.get('input[type="text"]')
      .clear()
      .type('123 U.S. 456')
    
    cy.get('button[type="submit"]')
      .click()
    
    // Wait for the API call to complete
    cy.wait('@serverError')
    
    // Check if error message is displayed
    cy.get('.error-message')
      .should('be.visible')
      .and('contain', 'An error occurred while validating the citation')
  })
})
