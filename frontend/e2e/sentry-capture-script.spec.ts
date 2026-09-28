import { test, expect } from "@playwright/test";
import { execFileSync } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";

// process.cwd(), não __dirname: o transform de TS do Playwright roda como ESM
// aqui (sem `__dirname` disponível), e o teste sempre executa com cwd em
// frontend/ -- é onde o playwright.config.ts mora e de onde `npx playwright
// test` é invocado.
const SCRIPT_PATH = path.resolve(process.cwd(), "scripts", "sentry-capture.mjs");
const BASE_URL = "http://localhost:5173";

function rodarCaptura(config: Record<string, unknown>) {
  const outDir = fs.mkdtempSync(path.join(os.tmpdir(), "sentry-capture-"));
  const configPath = path.join(outDir, "config.json");
  fs.writeFileSync(configPath, JSON.stringify({ baseURL: BASE_URL, outDir, ...config }));
  const saida = execFileSync("node", [SCRIPT_PATH, configPath], { encoding: "utf-8" });
  return { outDir, manifesto: JSON.parse(saida) };
}

// cenario: script de captura fotografa uma rota real em desktop e mobile
test("script de captura fotografa uma rota real em desktop e mobile", () => {
  const { outDir, manifesto } = rodarCaptura({ routes: ["/"], login: null, video: false });
  try {
    expect(manifesto.erro).toBeNull();
    expect(manifesto.rotas).toHaveLength(1);
    expect(manifesto.rotas[0].erro).toBeUndefined();
    expect(fs.existsSync(path.join(outDir, "raiz", "desktop.png"))).toBe(true);
    expect(fs.existsSync(path.join(outDir, "raiz", "mobile.png"))).toBe(true);
  } finally {
    fs.rmSync(outDir, { recursive: true, force: true });
  }
});

// cenario: servidor inalcancavel produz mensagem amigavel por rota, sem travar a captura
test("servidor inalcançável produz mensagem amigável por rota, sem travar a captura", () => {
  // Porta que ninguém escuta: reproduz o erro real que o Playwright dá quando o
  // dev server não está no ar, sem depender de infraestrutura externa.
  const { outDir, manifesto } = rodarCaptura({
    baseURL: "http://localhost:59999",
    routes: ["/"],
    login: null,
    video: false,
  });
  try {
    expect(manifesto.erro).toBeNull();
    expect(manifesto.rotas).toHaveLength(1);
    expect(manifesto.rotas[0].erro).toMatch(/dev server está rodando/);
  } finally {
    fs.rmSync(outDir, { recursive: true, force: true });
  }
});
