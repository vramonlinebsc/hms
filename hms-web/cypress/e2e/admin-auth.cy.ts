describe("Admin Authentication", () => {
  it("allows admin to log in and routes to /admin", () => {
    cy.intercept(
      "POST",
      "http://localhost:5000/admin/login"
    ).as("adminLogin")

    cy.visit("/")

    cy.get('[data-testid="login-username"]').type("admin")
    cy.get('[data-testid="login-password"]').type("admin123")
    cy.get('[data-testid="login-submit"]').click()

    cy.wait("@adminLogin")
      .its("response.statusCode")
      .should("eq", 200)

    cy.location("pathname", { timeout: 10000 })
      .should("eq", "/admin")
  })
})

