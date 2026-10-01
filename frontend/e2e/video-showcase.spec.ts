import { test, expect } from "@playwright/test";

// cenario: home mostra a area do video com titulo e player
test("home mostra a área do vídeo com título e player", async ({ page }) => {
  await page.setViewportSize({ width: 1280, height: 800 });
  await page.goto("/");
  const area = page.locator("#video");
  await expect(area.getByRole("heading", { name: /veja o sentry em ação/i })).toBeVisible();
  const video = area.locator("video");
  await expect(video).toBeVisible();
  await expect(video.locator("source")).toHaveAttribute("src", "/video/sentry-pt.mp4");
});

// cenario: o video nao toca sozinho e tem controles
test("o vídeo não toca sozinho e tem controles", async ({ page }) => {
  await page.setViewportSize({ width: 1280, height: 800 });
  await page.goto("/");
  const video = page.locator("#video video");
  await expect(video).toHaveAttribute("controls", "");
  await expect(video).not.toHaveAttribute("autoplay", /.*/);
  await expect(video).toHaveAttribute("preload", "metadata");
});

// cenario: o video e o texto trocam com o idioma da pagina
test("o vídeo e o texto trocam com o idioma da página", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("button", { name: "Toggle language" }).click();
  const area = page.locator("#video");
  await expect(area.getByRole("heading", { name: /see sentry in action/i })).toBeVisible();
  await expect(area.locator("video source")).toHaveAttribute("src", "/video/sentry-en.mp4");
});

// cenario: em celular o player cabe na tela
test("em celular o player cabe na tela", async ({ page }) => {
  await page.setViewportSize({ width: 375, height: 700 });
  await page.goto("/");
  const video = page.locator("#video video");
  await video.scrollIntoViewIfNeeded();
  const caixa = await video.boundingBox();
  expect(caixa).not.toBeNull();
  expect(caixa!.x).toBeGreaterThanOrEqual(0);
  expect(caixa!.x + caixa!.width).toBeLessThanOrEqual(375);
  const larguraDaPagina = await page.evaluate(() => document.documentElement.scrollWidth);
  expect(larguraDaPagina).toBeLessThanOrEqual(375);
});
