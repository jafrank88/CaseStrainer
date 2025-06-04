// ***********************************************
// This example commands.js shows you how to
// create various custom commands and overwrite
// existing commands.
//
// For more comprehensive examples of custom
// commands please read more here:
// https://on.cypress.io/custom-commands
// ***********************************************

/**
 * Validates a citation in the CaseStrainer application
 * @param {string} citation - The citation text to validate
 * @example
 * cy.validateCitation('123 U.S. 456')
 */
Cypress.Commands.add('validateCitation', (citation) => {
  // Intercept the API call to validate citations
  cy.intercept('POST', '/casestrainer/api/validate').as('validateCitation')
  
  // Enter the citation and submit the form
  cy.get('input[type="text"]')
    .clear()
    .type(citation)
  
  cy.get('button[type="submit"]')
    .click()
  
  // Wait for the API call to complete
  cy.wait('@validateCitation')
})

// Export any necessary functions if needed
export {}
