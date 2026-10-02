import { test, expect } from "@playwright/test";
import { execFile, execFileSync } from "node:child_process";
import fs from "node:fs";
import http from "node:http";
import os from "node:os";
import path from "node:path";
import { promisify } from "node:util";

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

// cenario: captura espera as animacoes e fotografa a pagina ja revelada
for (const arquivo of ["desktop.png", "mobile.png"]) {
  test(`captura espera as animações e fotografa a página já revelada (${arquivo})`, async ({ page }) => {
    // /docs?tab=setup é longa e cada seção só aparece quando entra na janela:
    // sem o disparo das animações, o meio da página sai preto.
    const { outDir, manifesto } = rodarCaptura({ routes: ["/docs?tab=setup"], login: null, video: false });
    try {
      expect(manifesto.rotas[0].erro).toBeUndefined();
      const png = fs.readFileSync(path.join(outDir, "docs-tab-setup", arquivo)).toString("base64");
      await page.goto("about:blank");
      const claros = await page.evaluate(async (dados) => {
        const imagem = new Image();
        imagem.src = `data:image/png;base64,${dados}`;
        await imagem.decode();
        const tela = document.createElement("canvas");
        tela.width = imagem.width;
        tela.height = imagem.height;
        const contexto = tela.getContext("2d")!;
        contexto.drawImage(imagem, 0, 0);
        // A faixa do meio: bem abaixo da primeira tela e acima do rodapé.
        const topo = Math.floor(imagem.height * 0.35);
        const altura = Math.floor(imagem.height * 0.3);
        const pixels = contexto.getImageData(0, topo, imagem.width, altura).data;
        let total = 0;
        for (let i = 0; i < pixels.length; i += 4) {
          if (pixels[i] + pixels[i + 1] + pixels[i + 2] > 150) total += 1;
        }
        return total;
      }, png);
      expect(claros).toBeGreaterThan(500);
    } finally {
      fs.rmSync(outDir, { recursive: true, force: true });
    }
  });
}

// cenario: captura espera as animacoes e fotografa a pagina ja revelada
test("captura espera o texto digitado letra a letra terminar", async ({ page }) => {
  // Uma barra que cresce 5% a cada 150 ms e só chega à borda direita aos 3 s: a
  // animação é de JavaScript, invisível para `document.getAnimations()`. Tirada cedo,
  // a borda direita sai preta.
  const html = `<body style="margin:0;background:#000"><div id="b" style="height:200px;width:0;background:#fff"></div>
    <script>let w=0;const t=setInterval(()=>{w+=5;document.getElementById("b").style.width=w+"%";if(w>=100)clearInterval(t)},150)</script></body>`;
  const servidor = http.createServer((_, resposta) => {
    resposta.setHeader("content-type", "text/html");
    resposta.end(html);
  });
  await new Promise<void>((resolver) => servidor.listen(0, "127.0.0.1", resolver));
  const porta = (servidor.address() as { port: number }).port;
  // Assíncrono de propósito: o `execFileSync` das outras capturas bloquearia este processo,
  // que é quem serve a página, e o navegador nunca receberia resposta.
  const outDir = fs.mkdtempSync(path.join(os.tmpdir(), "sentry-capture-"));
  const configPath = path.join(outDir, "config.json");
  fs.writeFileSync(configPath, JSON.stringify({
    baseURL: `http://127.0.0.1:${porta}`, outDir, routes: ["/"], login: null, video: false,
  }));
  let manifesto;
  try {
    const { stdout } = await promisify(execFile)("node", [SCRIPT_PATH, configPath], { encoding: "utf-8" });
    manifesto = JSON.parse(stdout);
  } finally {
    servidor.close();
  }
  try {
    expect(manifesto.rotas[0].erro).toBeUndefined();
    const png = fs.readFileSync(path.join(outDir, "raiz", "desktop.png")).toString("base64");
    await page.goto("about:blank");
    const brilho = await page.evaluate(async (dados) => {
      const imagem = new Image();
      imagem.src = `data:image/png;base64,${dados}`;
      await imagem.decode();
      const tela = document.createElement("canvas");
      tela.width = imagem.width;
      tela.height = imagem.height;
      const contexto = tela.getContext("2d")!;
      contexto.drawImage(imagem, 0, 0);
      const [r, g, b] = contexto.getImageData(imagem.width - 5, 100, 1, 1).data;
      return r + g + b;
    }, png);
    expect(brilho).toBeGreaterThan(600);
  } finally {
    fs.rmSync(outDir, { recursive: true, force: true });
  }
});
