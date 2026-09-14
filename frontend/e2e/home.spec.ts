import { test, expect } from "@playwright/test";

// cenario: landing mostra o titulo e os cards de feature
test("mostra o título e os quatro cards de feature", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: /disciplina entre o commit/i })).toBeVisible();
  await expect(page.getByText("Cobertura do que mudou")).toBeVisible();
  await expect(page.getByText("Veredito com contexto")).toBeVisible();
  await expect(page.getByText("Histórico auditável")).toBeVisible();
  await expect(page.getByText("Rastreabilidade caso")).toBeVisible();
});

// cenario: menu mobile abre e fecha ao clicar no hamburguer
test("menu mobile abre e fecha ao clicar no hambúrguer", async ({ page }) => {
  // O locator precisa ficar restrito ao <header>: o rodapé também mostra um
  // link "Docs" (sempre visível fora de /docs), e sem o escopo o locator
  // ficava ambíguo entre os dois, respondendo pelo do rodapé em vez do menu.
  await page.setViewportSize({ width: 390, height: 700 });
  await page.goto("/");
  const header = page.locator("header");
  const menuButton = header.getByRole("button", { name: "Abrir menu" });
  await expect(header.getByRole("link", { name: "Docs" })).toBeHidden();
  await menuButton.click();
  await expect(header.getByRole("link", { name: "Docs" })).toBeVisible();
  await menuButton.click();
  await expect(header.getByRole("link", { name: "Docs" })).toBeHidden();
});
