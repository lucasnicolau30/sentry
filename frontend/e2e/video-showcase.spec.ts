import { test, expect } from "@playwright/test";

// cenario: home mostra a area do video com titulo e player
test("home mostra a área do vídeo promocional com título e player", async ({ page }) => {
  await page.setViewportSize({ width: 1280, height: 800 });
  await page.goto("/");
  const area = page.locator("#video");
  await expect(area.getByRole("heading", { name: /vídeo promocional/i })).toBeVisible();
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
  await expect(area.getByRole("heading", { name: /promo video/i })).toBeVisible();
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

// cenario: a area do video e a ultima da home
test("a área do vídeo é a última da home", async ({ page }) => {
  await page.setViewportSize({ width: 1280, height: 800 });
  await page.goto("/");
  await expect(page.locator("main section").last()).toHaveAttribute("id", "video");
});

// cenario: o poster tem um botao grande de assistir que some ao dar play
test("o pôster tem um botão grande de assistir que some ao dar play", async ({ page }) => {
  await page.setViewportSize({ width: 1280, height: 800 });
  await page.goto("/");
  const assistir = page.locator("#video").getByRole("button", { name: /assistir ao vídeo promocional/i });
  await expect(assistir).toBeVisible();
  await assistir.click();
  await expect(assistir).toBeHidden();
});

// cenario: a area mostra a duracao, os idiomas e o comando que gera o video
test("a área mostra a duração, os idiomas e o comando que gera o vídeo", async ({ page }) => {
  await page.setViewportSize({ width: 1280, height: 800 });
  await page.goto("/");
  const area = page.locator("#video");
  await area.scrollIntoViewIfNeeded();
  await expect(area.getByText("1:06 min")).toBeVisible();
  await expect(area.getByText("PT e EN")).toBeVisible();
  await expect(area.getByText("sentry promo")).toBeVisible();
  await expect(area.getByText(/peça ao agente/i)).toBeVisible();
});
