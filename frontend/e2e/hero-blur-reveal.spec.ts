import { test, expect } from "@playwright/test";

// cenario: hero exibe a tagline em PT com efeito blur reveal
test("hero exibe a tagline em PT dentro do BlurReveal", async ({ page }) => {
  await page.goto("/");
  const heading = page.getByRole("heading", { name: /seu agente escreveu o código/i });
  await expect(heading).toBeVisible();
  await expect(heading.locator(".sr-only").first()).toHaveText(
    "Seu agente escreveu o código. O Sentry garante que ele testou."
  );
});

// cenario: hero exibe a tagline em EN com efeito blur reveal
test("hero exibe a tagline em EN dentro do BlurReveal ao trocar idioma", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("button", { name: "Toggle language" }).click();
  const heading = page.getByRole("heading", { name: /your agent wrote the code/i });
  await expect(heading).toBeVisible();
  await expect(heading.locator(".sr-only").first()).toHaveText(
    "Your agent wrote the code. Sentry makes sure it's tested."
  );
});

// cenario: tagline permanece legível em mobile
test("tagline não estoura o container em mobile (375px)", async ({ page }) => {
  await page.setViewportSize({ width: 375, height: 700 });
  await page.goto("/");
  const heading = page.getByRole("heading", { name: /seu agente escreveu o código/i });
  const box = await heading.boundingBox();
  expect(box).not.toBeNull();
  expect(box!.width).toBeLessThanOrEqual(375);
});

// cenario: tagline permanece legível em tablet
test("tagline não estoura o container em tablet (768px)", async ({ page }) => {
  await page.setViewportSize({ width: 768, height: 1024 });
  await page.goto("/");
  const heading = page.getByRole("heading", { name: /seu agente escreveu o código/i });
  const box = await heading.boundingBox();
  expect(box).not.toBeNull();
  expect(box!.width).toBeLessThanOrEqual(768);
});

// cenario: tagline permanece legível em desktop
test("tagline não estoura o container em desktop (1280px)", async ({ page }) => {
  await page.setViewportSize({ width: 1280, height: 800 });
  await page.goto("/");
  const heading = page.getByRole("heading", { name: /seu agente escreveu o código/i });
  const box = await heading.boundingBox();
  expect(box).not.toBeNull();
  expect(box!.width).toBeLessThanOrEqual(1280);
});

// cenario: texto acessível independentemente da animação
test("tagline fica no DOM e acessível com prefers-reduced-motion", async ({ page }) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto("/");
  const heading = page.getByRole("heading", { name: /seu agente escreveu o código/i });
  await expect(heading).toBeVisible();
  await expect(heading).toHaveAccessibleName(
    "Seu agente escreveu o código. O Sentry garante que ele testou."
  );
});
