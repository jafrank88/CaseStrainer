// ***********************************************
// This example commands.js shows you how to
// create various custom commands and overwrite
// existing commands.
//
// For more comprehensive examples of custom
// commands please read more here:
// https://on.cypress.io/custom-commands
// ***********************************************
//
//
// -- This is a parent command --
// Cypress.Commands.add('login', (email, password) => { ... })
//
//
// -- This is a child command --
// Cypress.Commands.add('drag', { prevSubject: 'element'}, (subject, options) => { ... })
//
//
// -- This is a dual command --
// Cypress.Commands.add('dismiss', { prevSubject: 'optional'}, (subject, options) => { ... })
//
//
// -- This will overwrite an existing command --
// Cypress.Commands.overwrite('visit', (originalFn, url, options) => { ... })

// Custom command for consistent logging
Cypress.Commands.add('logStep', (message) => {
  const timestamp = new Date().toISOString();
  cy.log(`[${timestamp}] ${message}`);
});

// Custom command to log in if needed
Cypress.Commands.add('login', (username, password) => {
  cy.session([username, password], () => {
    cy.request({
      method: 'POST',
      url: '/api/login',
      body: { username, password },
    }).then(({ body }) => {
      window.localStorage.setItem('authToken', body.token)
    })
  })
})

// Command to check if an element is visible and not covered
Cypress.Commands.add('isVisible', { prevSubject: true }, (subject) => {
  cy.wrap(subject).should('be.visible')
  cy.wrap(subject).should(($el) => {
    const rect = $el[0].getBoundingClientRect()
    const centerX = rect.left + rect.width / 2
    const centerY = rect.top + rect.height / 2
    const elementAtPoint = document.elementFromPoint(centerX, centerY)
    expect($el[0].contains(elementAtPoint)).to.be.true
  })
  return cy.wrap(subject)
})
