import { test, expect } from "@playwright/test";

// cenario: a box dos videos aparece depois de zero chamada de IA
test("a box dos vídeos aparece depois de zero chamada de IA", async ({ page }) => {
  await page.setViewportSize({ width: 1280, height: 900 });
  await page.goto("/");
  const titulos = await page.locator(".glow-card h3").allTextContents();
  expect(titulos.slice(-2)).toEqual(["Zero chamada de IA no veredito", "Vídeos prontos pelo próprio Sentry"]);
  const box = page.locator(".glow-card", { hasText: "Vídeos prontos pelo próprio Sentry" });
  await expect(box).toContainText("sentry training");
  await expect(box).toContainText("sentry promo");
  await expect(box).toContainText("gastam tokens");
  await expect(box).toContainText("peça ao agente");
  await expect(box).toContainText("só o veredito certifica");
});

// cenario: com seis boxes o grid fica em tres fileiras de duas colunas
test("com seis boxes o grid fica em três fileiras de duas colunas", async ({ page }) => {
  await page.setViewportSize({ width: 1280, height: 900 });
  await page.goto("/");
  await expect(page.locator(".glow-card")).toHaveCount(6);
  // espera as animações de entrada assentarem antes de medir
  await page.waitForTimeout(1500);
  // posições absolutas na página, para a rolagem não mudar as medidas
  const caixas = await page.locator(".glow-card").evaluateAll((els) =>
    els.map((el) => {
      const r = el.getBoundingClientRect();
      return { x: r.left, y: r.top + window.scrollY, width: r.width };
    })
  );
  const larguras = caixas.map((c) => c.width);
  expect(Math.max(...larguras) - Math.min(...larguras)).toBeLessThanOrEqual(2);
  expect(new Set(caixas.map((c) => Math.round(c.x))).size).toBe(2);
  expect(new Set(caixas.map((c) => Math.round(c.y))).size).toBe(3);
});

// cenario: em celular as boxes ficam em uma coluna
test("em celular as boxes ficam em uma coluna", async ({ page }) => {
  await page.setViewportSize({ width: 375, height: 800 });
  await page.goto("/");
  const cards = page.locator(".glow-card");
  await expect(cards).toHaveCount(6);
  await page.waitForTimeout(1500);
  const xs = new Set<number>();
  for (let i = 0; i < 6; i++) {
    await cards.nth(i).scrollIntoViewIfNeeded();
    xs.add(Math.round((await cards.nth(i).boundingBox())!.x));
  }
  expect(xs.size).toBe(1);
  const larguraDaPagina = await page.evaluate(() => document.documentElement.scrollWidth);
  expect(larguraDaPagina).toBeLessThanOrEqual(375);
});

// cenario: no ingles a box e o video promocional ficam em ingles
test("no inglês a box e o vídeo promocional ficam em inglês", async ({ page }) => {
  await page.setViewportSize({ width: 1280, height: 900 });
  await page.goto("/");
  await page.getByRole("button", { name: "Toggle language" }).click();
  const box = page.locator(".glow-card", { hasText: "Videos made by Sentry itself" });
  await expect(box).toBeVisible();
  await expect(box).toContainText("records the module's script");
  await expect(box).toContainText("spend tokens");
  await expect(box).toContainText("ask the agent");
  await expect(box).toContainText("only the verdict certifies");
  const video = page.locator("#video video");
  await expect(video).toHaveAttribute("poster", "/video/poster-en.jpg");
  await expect(video.locator("source")).toHaveAttribute("src", "/video/sentry-en.mp4");
  await expect(page.locator("#video").getByRole("heading", { name: /promo video/i })).toBeVisible();
});
