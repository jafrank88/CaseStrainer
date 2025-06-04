// Test suite for the CaseStrainer Home Page
describe('CaseStrainer Home Page', () => {
  // Before each test, visit the home page
  beforeEach(() => {
    cy.visit('/')
  })

  // Test that the welcome message is displayed correctly
  it('displays the welcome message', () => {
    // Check if the main heading is visible and contains the expected text
    cy.get('h1')
      .should('be.visible')
      .and('contain', 'Welcome to CaseStrainer')
    
    // Check if the subtitle is visible and contains the expected text
    cy.get('p.lead')
      .should('be.visible')
      .and('contain', 'A powerful tool for validating and analyzing legal citations')
  })

  // Test that the citation validator component is present and functional
  it('displays the citation validator component', () => {
    // Check if the main container exists
    cy.get('.citation-validator')
      .should('exist')
      .and('be.visible')
    
    // Check if the form exists and has the correct elements
    cy.get('form.validator-form')
      .should('exist')
      .within(() => {
        // Check input field
        cy.get('input[type="text"]')
          .should('be.visible')
          .and('have.attr', 'placeholder', 'Enter a legal citation...')
        
        // Check submit button
        cy.get('button[type="submit"]')
          .should('be.visible')
          .and('contain', 'Validate')
      })
  })

  // Test that the key features section is displayed correctly
  it('shows key features section', () => {
    // Check if the features section exists and has a heading
    cy.get('section#features')
      .should('exist')
      .within(() => {
        cy.get('h2')
          .should('be.visible')
          .and('contain', 'Key Features')
        
        // Check if there are feature cards
        cy.get('.feature-card')
          .should('have.length.at.least', 1)
          .each(($card) => {
            // Each card should have an icon, heading, and description
            cy.wrap($card).within(() => {
              cy.get('svg').should('exist')
              cy.get('h3').should('be.visible')
              cy.get('p').should('be.visible')
            })
          })
      })
  })
})
