import { test, expect } from "@playwright/test";

// cenario: landing mostra o titulo e os cards de feature
test("mostra o título e os cinco cards de feature", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: /seu agente escreveu o código/i })).toBeVisible();
  await expect(page.getByText("Cobertura do que mudou")).toBeVisible();
  await expect(page.getByText("Veredito com contexto")).toBeVisible();
  await expect(page.getByText("Histórico auditável")).toBeVisible();
  await expect(page.getByText("Rastreabilidade caso")).toBeVisible();
  await expect(page.getByText("Zero chamada de IA")).toBeVisible();
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

// cenario: menu mobile mostra os itens do dock sem pílula
test("menu mobile mostra os itens do dock sem pílula", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 700 });
  await page.goto("/");
  const header = page.locator("header");
  await header.getByRole("button", { name: "Abrir menu" }).click();
  const menu = header.locator("nav").last();
  await expect(menu.getByRole("button", { name: "Toggle language" })).toBeVisible();
  await expect(menu.getByRole("link", { name: "PyPI" })).toBeVisible();
  await expect(menu.getByRole("link", { name: "GitHub" })).toBeVisible();
  await expect(menu.getByRole("link", { name: "Docs" })).toBeVisible();
  await expect(menu.locator(".glow-btn")).toHaveCount(0);
  await expect(menu.locator("span.w-px")).toHaveCount(3);
});

// cenario: menu mobile troca o idioma pelo item do dock
test("menu mobile troca o idioma pelo item do dock", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 700 });
  await page.goto("/");
  const header = page.locator("header");
  await header.getByRole("button", { name: "Abrir menu" }).click();
  const lang = header.locator("nav").last().getByRole("button", { name: "Toggle language" });
  await expect(lang).toHaveText("PT");
  await lang.click();
  await expect(lang).toHaveText("EN");
});
