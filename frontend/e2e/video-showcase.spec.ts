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
  await expect(video).not.toHaveAttribute("autoplay", /.*/);
  await expect(video).toHaveAttribute("preload", "metadata");
  const barra = page.locator("#video").getByRole("group", { name: /controles do vídeo/i });
  await expect(barra.getByRole("slider", { name: /progresso do vídeo/i })).toBeVisible();
  await expect(barra.getByRole("button", { name: /silenciar/i })).toBeVisible();
  await expect(barra.getByRole("button", { name: /tela cheia/i })).toBeVisible();
  await expect(barra.getByText(/0:00 \/ /)).toBeVisible();
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

// cenario: o player sobe ao passar o mouse como os terminais
test("o player sobe ao passar o mouse como os terminais", async ({ page }) => {
  await page.setViewportSize({ width: 1280, height: 800 });
  await page.goto("/");
  const moldura = page.locator("#video video").locator("xpath=..");
  await moldura.scrollIntoViewIfNeeded();
  const topo = async () => (await moldura.boundingBox())!.y;
  // espera a animação de entrada da seção assentar antes de medir a posição
  await page.waitForTimeout(800);
  const parado = await topo();
  await moldura.hover();
  await expect.poll(topo).toBeLessThan(parado);
  // sem borda brilhante: o hover é só o deslocamento, como no TerminalWindow
  await expect(page.locator("#video .glow-card")).toHaveCount(0);
  await page.mouse.move(0, 0);
  await expect.poll(topo).toBe(parado);
});

// cenario: o play do centro e verde com icone branco e alterna com o pause
test("o play do centro é verde com ícone branco e alterna com o pause", async ({ page }) => {
  await page.setViewportSize({ width: 1280, height: 800 });
  await page.goto("/");
  const video = page.locator("#video video");
  const botao = page.locator("#video").getByRole("button", { name: /assistir ao vídeo promocional/i });
  const disco = botao.locator("span").first();
  await expect(botao).toBeVisible();
  await expect(disco).toHaveCSS("background-color", "rgb(57, 255, 20)");
  await expect(disco).toHaveCSS("color", "rgb(255, 255, 255)");

  // o ícone fica no centro do círculo, sem desvio
  const centro = async (el: typeof disco) => {
    const c = (await el.boundingBox())!;
    return { x: c.x + c.width / 2, y: c.y + c.height / 2 };
  };
  const centroDisco = await centro(disco);
  const centroPlay = await centro(disco.locator("svg").first());
  expect(Math.abs(centroPlay.x - centroDisco.x)).toBeLessThanOrEqual(1);
  expect(Math.abs(centroPlay.y - centroDisco.y)).toBeLessThanOrEqual(1);

  await botao.click();
  await expect.poll(() => video.evaluate((v: HTMLVideoElement) => v.paused)).toBe(false);

  // tocando, o mesmo botão vira o de pausar: aparece logo após o clique e some sozinho
  const pausar = page.locator("#video").getByRole("button", { name: /pausar o vídeo/i });
  const discoPausar = pausar.locator("span").first();
  await expect(discoPausar).toHaveCSS("opacity", "1");
  await expect(discoPausar).toHaveCSS("opacity", "0", { timeout: 6000 });

  // mexer o mouse sobre o vídeo traz o botão de volta, com o ícone branco e centralizado
  const caixa = (await pausar.boundingBox())!;
  await page.mouse.move(caixa.x + caixa.width / 2 + 12, caixa.y + caixa.height / 2 + 12);
  await expect(discoPausar).toHaveCSS("opacity", "1");
  await expect(discoPausar).toHaveCSS("background-color", "rgb(57, 255, 20)");
  await expect(discoPausar).toHaveCSS("color", "rgb(255, 255, 255)");
  const centroPause = await centro(discoPausar.locator("svg").nth(1));
  const centroDiscoPausar = await centro(discoPausar);
  expect(Math.abs(centroPause.x - centroDiscoPausar.x)).toBeLessThanOrEqual(1);
  expect(Math.abs(centroPause.y - centroDiscoPausar.y)).toBeLessThanOrEqual(1);

  await pausar.click();
  await expect.poll(() => video.evaluate((v: HTMLVideoElement) => v.paused)).toBe(true);
  await expect(botao).toBeVisible();
  await expect(disco).toHaveCSS("opacity", "1");
});

// cenario: os icones ficam verdes no hover e o volume e uma barra vertical
const FUNDO_TRANSLUCIDO = /(\/|,) 0\.1\)$/;

test("os ícones ficam verdes no hover e o volume é uma barra vertical", async ({ page }) => {
  await page.setViewportSize({ width: 1280, height: 800 });
  await page.goto("/");
  const barra = page.locator("#video").getByRole("group", { name: /controles do vídeo/i });
  await barra.scrollIntoViewIfNeeded();
  // espera a animação de entrada da seção assentar: o botão não pode se mexer sob o mouse
  await page.waitForTimeout(800);
  const som = barra.getByRole("button", { name: /silenciar/i });
  const telaCheia = barra.getByRole("button", { name: /tela cheia/i });

  // sem o mouse em cima, o ícone é branco e o botão não tem fundo
  await expect(som).toHaveCSS("color", "rgb(255, 255, 255)");
  await expect(som).toHaveCSS("background-color", "rgba(0, 0, 0, 0)");

  // com o mouse, só o ícone vira verde e o botão ganha o fundo escuro translúcido
  await som.hover();
  await expect(som).toHaveCSS("color", "rgb(57, 255, 20)");
  await expect(som).toHaveCSS("background-color", FUNDO_TRANSLUCIDO);
  await telaCheia.hover();
  await expect(telaCheia).toHaveCSS("color", "rgb(57, 255, 20)");
  await expect(telaCheia).toHaveCSS("background-color", FUNDO_TRANSLUCIDO);

  // o volume aparece como uma barra vertical, exatamente em cima do botão de som
  const volume = barra.getByRole("slider", { name: /^volume$/i });
  const trilho = barra.locator("[data-volume-vertical]");
  await expect(trilho).toBeVisible();
  const caixaSom = (await som.boundingBox())!;
  const caixaTrilho = (await trilho.boundingBox())!;
  const caixaBarra = (await volume.boundingBox())!;
  expect(caixaTrilho.height).toBeGreaterThan(caixaTrilho.width * 2);
  expect(caixaBarra.height).toBeGreaterThan(caixaBarra.width * 2);
  expect(caixaTrilho.y + caixaTrilho.height).toBeLessThanOrEqual(caixaSom.y + 1);
  const meio = (c: { x: number; width: number }) => c.x + c.width / 2;
  expect(Math.abs(meio(caixaTrilho) - meio(caixaSom))).toBeLessThanOrEqual(1);
  expect(Math.abs(meio(caixaBarra) - meio(caixaSom))).toBeLessThanOrEqual(1);

  // silenciar liga e desliga o som
  const video = page.locator("#video video");
  await som.click();
  await expect.poll(() => video.evaluate((v: HTMLVideoElement) => v.muted)).toBe(true);
  await expect(barra.getByRole("button", { name: /ativar o som/i })).toBeVisible();
  await barra.getByRole("button", { name: /ativar o som/i }).click();
  await expect.poll(() => video.evaluate((v: HTMLVideoElement) => v.muted)).toBe(false);
});

