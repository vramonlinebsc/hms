describe("Admin auth", () => {
  it("logs in as admin and validates session", () => {
    cy.visit("http://localhost:5173/login")

    // Vuetify text fields render input inside wrappers
    cy.contains("Username")
      .parent()
      .find("input")
      .type("admin")

    cy.contains("Password")
      .parent()
      .find("input")
      .type("admin123")

    cy.contains("button", "Login").click()

    // Allow routing + async auth
    cy.location("pathname", { timeout: 10000 }).should("include", "admin")
  })
})

