import { test, expect } from "@playwright/test";

test("mostra o título e os quatro cards de feature", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: /disciplina entre o commit/i })).toBeVisible();
  await expect(page.getByText("Cobertura do que mudou")).toBeVisible();
  await expect(page.getByText("Veredito com contexto")).toBeVisible();
  await expect(page.getByText("Histórico auditável")).toBeVisible();
  await expect(page.getByText("Consistência de frontend")).toBeVisible();
});

test("menu mobile abre e fecha ao clicar no hambúrguer", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 700 });
  await page.goto("/");
  const menuButton = page.getByRole("button", { name: "Abrir menu" });
  await expect(page.getByRole("link", { name: "Docs" })).toBeHidden();
  await menuButton.click();
  await expect(page.getByRole("link", { name: "Docs" })).toBeVisible();
  await menuButton.click();
  await expect(page.getByRole("link", { name: "Docs" })).toBeHidden();
});
