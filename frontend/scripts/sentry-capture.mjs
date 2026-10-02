// Captura de mídia por rota para `sentry archive` no modo por rotas.
//
// Recebe, como único argumento, o caminho de um JSON de configuração (rotas,
// login opcional, pasta de saída, se grava vídeo). Abre UMA sessão de
// navegador: faz login uma única vez quando pedido e então visita cada rota
// na mesma sessão, fotografando em desktop e mobile. Credenciais nunca
// entram nesse JSON -- viajam só pelo ambiente do processo (herdado do
// Python que o lançou), lidas daqui direto de SENTRY_LOGIN_USUARIO/
// SENTRY_LOGIN_SENHA, para nunca serem gravadas em disco em texto plano.
import { chromium } from "@playwright/test";
import fs from "node:fs";
import path from "node:path";

const VIEWPORTS = {
  desktop: { width: 1280, height: 800 },
  mobile: { width: 390, height: 844 },
};

function slugDeRota(rota) {
  if (rota === "/") return "raiz";
  // Rota pode trazer query string (ex.: "/docs?tab=setup" -- uma aba real de
  // navegação, não estado de clique). "?" é proibido em nome de pasta no
  // Windows, então "/", "?", "=" e "&" viram o mesmo separador "-".
  const limpo = rota
    .replace(/^\/+/, "")
    .replace(/[/?=&]+/g, "-")
    .replace(/^-+|-+$/g, "");
  return limpo || "raiz";
}

// Espera as animações de entrada (BlurReveal e afins) terminarem antes do
// print -- sem isso, a rota é fotografada no meio da revelação e sai
// borrada. Ignora animação com `iterations: Infinity` (ex.: o cursor
// piscando do terminal) -- essa nunca termina, e esperar por ela travaria
// a captura até o timeout em toda rota que a tiver na tela.
// O erro cru do Playwright pra um dev server fora do ar ("net::ERR_CONNECTION_REFUSED
// at http://localhost:5173/login") é técnico e não diz o que fazer. Detecta esse
// padrão e troca por uma dica acionável -- as outras falhas passam intactas.
function mensagemAmigavel(erro, baseURL) {
  const texto = String((erro && erro.message) || erro);
  if (/ERR_CONNECTION_REFUSED|ECONNREFUSED|net::ERR_/.test(texto)) {
    return `não foi possível conectar em ${baseURL} -- confirme que o dev server está rodando (ex.: npm run dev)`;
  }
  return texto;
}

async function waitForAnimationsToSettle(page, timeoutMs = 3000) {
  await page.evaluate((timeout) => {
    const finitas = document.getAnimations().filter((animacao) => {
      const timing = animacao.effect && animacao.effect.getTiming ? animacao.effect.getTiming() : {};
      return timing.iterations !== Infinity;
    });
    const assentou = Promise.all(finitas.map((animacao) => animacao.finished.catch(() => {})));
    const limite = new Promise((resolve) => setTimeout(resolve, timeout));
    return Promise.race([assentou, limite]);
  }, timeoutMs);
}

// Animação de entrada por rolagem (`whileInView`, lazy-load) só roda quando o elemento
// entra na janela, e um print de página inteira nunca rola: tudo abaixo da primeira
// tela sairia escondido, e há quem desfaça a entrada quando o elemento sai da janela,
// então rolar até o fim também não resolve. Antes de a página carregar, o observador
// de interseção passa a tratar todo elemento observado como visível: a página aparece
// já revelada, como para quem rolou até o fim. É dito no README do módulo.
const OBSERVADOR_SEMPRE_VISIVEL = () => {
  class ObservadorSempreVisivel {
    constructor(callback) {
      this.callback = callback;
    }
    observe(alvo) {
      const caixa = alvo.getBoundingClientRect();
      setTimeout(() => this.callback([{
        target: alvo, isIntersecting: true, intersectionRatio: 1, time: performance.now(),
        boundingClientRect: caixa, intersectionRect: caixa, rootBounds: null,
      }], this), 0);
    }
    unobserve() {}
    disconnect() {}
    takeRecords() {
      return [];
    }
  }
  window.IntersectionObserver = ObservadorSempreVisivel;
};

// Animações feitas em JavaScript (texto digitado letra a letra, contadores) não aparecem
// em `document.getAnimations()`. Elas se denunciam mexendo no DOM: a página só está
// pronta quando fica um tempo sem mudar. O limite evita esperar para sempre uma página
// que nunca se aquieta (um relógio, por exemplo); animação de CSS que nunca termina
// (um cursor piscando) não mexe no DOM e não atrapalha.
const DOM_QUIETO_MS = 800;
const LIMITE_DA_ESPERA_MS = 10000;

async function aguardarDomQuieto(page) {
  await page.evaluate(({ quieto, limite }) => new Promise((resolve) => {
    let temporizador;
    const observador = new MutationObserver(() => {
      clearTimeout(temporizador);
      temporizador = setTimeout(terminar, quieto);
    });
    function terminar() {
      observador.disconnect();
      clearTimeout(limiteGeral);
      resolve();
    }
    const limiteGeral = setTimeout(terminar, limite);
    observador.observe(document.documentElement, {
      subtree: true, childList: true, attributes: true, characterData: true,
    });
    temporizador = setTimeout(terminar, quieto);
  }), { quieto: DOM_QUIETO_MS, limite: LIMITE_DA_ESPERA_MS });
}

async function revelarPagina(page) {
  await page.evaluate(() => {
    for (const imagem of document.querySelectorAll('img[loading="lazy"]')) imagem.loading = "eager";
  });
  await page.waitForLoadState("networkidle");
  await waitForAnimationsToSettle(page);
  await aguardarDomQuieto(page);
  await waitForAnimationsToSettle(page);
}

async function main() {
  const configPath = process.argv[2];
  const config = JSON.parse(fs.readFileSync(configPath, "utf-8"));
  const { baseURL, routes, login, outDir, video } = config;
  const resultado = { rotas: [], erro: null };

  const browser = await chromium.launch();
  try {
    const videoDir = path.join(outDir, "_video_tmp");
    const context = await browser.newContext({
      viewport: VIEWPORTS.desktop,
      recordVideo: video ? { dir: videoDir } : undefined,
    });
    await context.addInitScript(OBSERVADOR_SEMPRE_VISIVEL);
    const page = await context.newPage();

    if (login) {
      const usuario = process.env.SENTRY_LOGIN_USUARIO;
      const senha = process.env.SENTRY_LOGIN_SENHA;
      await page.goto(new URL(login.rota, baseURL).toString());
      await page.fill(login.usuario, usuario ?? "");
      await page.fill(login.senha, senha ?? "");
      await Promise.all([
        page.waitForLoadState("networkidle"),
        page.click(login.enviar),
      ]);
    }

    for (const rota of routes) {
      const slug = slugDeRota(rota);
      const pasta = path.join(outDir, slug);
      fs.mkdirSync(pasta, { recursive: true });
      const item = { rota, slug, arquivos: [] };
      try {
        await page.setViewportSize(VIEWPORTS.desktop);
        await page.goto(new URL(rota, baseURL).toString());
        await revelarPagina(page);
        await page.screenshot({ path: path.join(pasta, "desktop.png"), fullPage: true });
        item.arquivos.push("desktop.png");

        await page.setViewportSize(VIEWPORTS.mobile);
        await revelarPagina(page);
        await page.screenshot({ path: path.join(pasta, "mobile.png"), fullPage: true });
        item.arquivos.push("mobile.png");
      } catch (erroRota) {
        item.erro = mensagemAmigavel(erroRota, baseURL);
      }
      resultado.rotas.push(item);
    }

    if (video) {
      const videoHandle = page.video();
      await context.close();
      const videoPath = videoHandle ? await videoHandle.path() : null;
      if (videoPath && fs.existsSync(videoPath)) {
        fs.copyFileSync(videoPath, path.join(outDir, "navegacao.webm"));
      }
      fs.rmSync(videoDir, { recursive: true, force: true });
    } else {
      await context.close();
    }
  } catch (erro) {
    resultado.erro = mensagemAmigavel(erro, baseURL);
  } finally {
    await browser.close();
  }
  process.stdout.write(JSON.stringify(resultado));
}

main();
