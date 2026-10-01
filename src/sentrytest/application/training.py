"""`sentry training`: o vídeo de treinamento de um módulo, do roteiro ao .mp4.

O roteiro é declarativo (`.sentry/training/<modulo>.json`): ações são dados,
nunca código, para que o Sentry valide e revise o roteiro no diff sem executar
nada de ninguém. O Playwright do Python grava os passos com o tempo de cada
um -- dentro do pacote, para funcionar em qualquer projeto, sem depender de
Node nem de um `frontend/` -- e o brag (via `claude -p`, como no `promo`)
monta o vídeo com as legendas.
"""
import json
import re
import shutil
import time
import urllib.error
import urllib.request
from pathlib import Path

try:
    from playwright.sync_api import Error as PlaywrightError, sync_playwright
except ImportError:  # sem o pacote: `checar_dependencias_training` explica o que fazer
    PlaywrightError = Exception
    sync_playwright = None

from .promo import PASTA_DE_MIDIA, SAIDA_DO_BRAG, acionar_brag, checar_dependencias, validar_idioma

PASTA_DE_ROTEIROS = Path(".sentry") / "training"
ACOES = ("ir", "digitar", "clicar", "apontar")
TAMANHO_MAXIMO_DO_MODULO = 64
VIEWPORT = {"width": 1920, "height": 1080}
MS_POR_PALAVRA = 380
MINIMO_POR_PASSO_MS = 2500
TEMPO_DO_SELETOR_MS = 10000
INSTALAR_PLAYWRIGHT = "pip install playwright && playwright install chromium"
_NOME_DE_MODULO = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")

IDIOMA_NO_PROMPT = {"pt": "português do Brasil (PT-BR)", "en": "English"}


def validar_modulo(modulo: str) -> str:
    """O nome vira nome de arquivo: separadores de caminho deixariam `../` ler fora da pasta."""
    if len(modulo) > TAMANHO_MAXIMO_DO_MODULO:
        raise ValueError(f"nome de módulo longo demais ({len(modulo)} caracteres); "
                         f"o máximo é {TAMANHO_MAXIMO_DO_MODULO}")
    if not _NOME_DE_MODULO.fullmatch(modulo) or ".." in modulo:
        raise ValueError(f"nome de módulo inválido: {modulo!r}; use letras, números, '.', '_' e '-'")
    return modulo


def caminho_do_roteiro(root: Path, modulo: str) -> Path:
    return root / PASTA_DE_ROTEIROS / f"{validar_modulo(modulo)}.json"


def _texto(valor) -> bool:
    return isinstance(valor, str) and bool(valor.strip())


def validar_roteiro(dados) -> list[str]:
    """Os erros do roteiro, cada um dizendo em que passo e em que campo."""
    if not isinstance(dados, dict):
        return ["o roteiro deve ser um objeto JSON"]
    erros = []
    base = dados.get("base")
    if not _texto(base) or not re.match(r"https?://", base):
        erros.append("campo 'base' ausente ou sem http(s)://")
    if not _texto(dados.get("titulo")):
        erros.append("campo 'titulo' ausente ou vazio")
    passos = dados.get("passos")
    if not isinstance(passos, list) or not passos:
        erros.append("campo 'passos' ausente ou vazio")
        return erros
    for n, passo in enumerate(passos, start=1):
        if not isinstance(passo, dict):
            erros.append(f"passo {n}: deve ser um objeto")
            continue
        for campo in ("titulo", "fala"):
            if not _texto(passo.get(campo)):
                erros.append(f"passo {n}: campo '{campo}' ausente ou vazio")
        erros.extend(_validar_acao(n, passo.get("acao")))
    return erros


def _validar_acao(n: int, acao) -> list[str]:
    if not isinstance(acao, dict):
        return [f"passo {n}: campo 'acao' ausente ou não é um objeto"]
    nomes = [chave for chave in acao if chave != "valor"]
    if len(nomes) != 1:
        return [f"passo {n}: 'acao' deve ter exatamente uma das ações: {', '.join(ACOES)}"]
    nome = nomes[0]
    if nome not in ACOES:
        return [f"passo {n}: ação desconhecida '{nome}'; use uma de: {', '.join(ACOES)}"]
    if not _texto(acao[nome]):
        return [f"passo {n}: a ação '{nome}' tem {'caminho' if nome == 'ir' else 'seletor'} vazio"]
    if nome == "digitar" and not isinstance(acao.get("valor"), str):
        return [f"passo {n}: a ação 'digitar' precisa de 'valor'"]
    return []


def carregar_roteiro(root: Path, modulo: str) -> dict:
    caminho = caminho_do_roteiro(root, modulo)
    mostrado = caminho.relative_to(root).as_posix()
    if not caminho.is_file():
        raise ValueError(f"roteiro não encontrado: esperava {mostrado}")
    try:
        dados = json.loads(caminho.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ValueError(f"{mostrado}: JSON inválido na linha {error.lineno}, "
                         f"coluna {error.colno}: {error.msg}") from None
    erros = validar_roteiro(dados)
    if erros:
        raise ValueError(f"{mostrado}: " + "; ".join(erros))
    return dados


def validar_roteiros_declarados(root: Path) -> list[str]:
    """Para o `sentry check`: todos os roteiros da pasta, antes de gastar uma gravação."""
    pasta = root / PASTA_DE_ROTEIROS
    erros = []
    for arquivo in sorted(pasta.glob("*.json")) if pasta.is_dir() else []:
        try:
            carregar_roteiro(root, arquivo.stem)
        except ValueError as error:
            erros.append(str(error))
    return erros


def checar_dependencias_training(root: Path, *, which=None, home: Path | None = None, run=None,
                                 avisar=print) -> str:
    """As do `promo` mais o Playwright do Python. Devolve o caminho do `claude`."""
    claude = checar_dependencias(root, which=which, home=home, run=run, avisar=avisar)
    if sync_playwright is None:
        raise ValueError(f"falta o Playwright do Python; instale com: {INSTALAR_PLAYWRIGHT}")
    return claude


def app_responde(base: str, timeout: float = 5) -> None:
    """Qualquer resposta HTTP serve (até 404): o que importa é ter alguém na porta."""
    try:
        urllib.request.urlopen(base, timeout=timeout).close()
    except urllib.error.HTTPError:
        return
    except (urllib.error.URLError, OSError) as error:
        motivo = getattr(error, "reason", error)
        raise ValueError(f"o app em {base} não respondeu ({motivo}); suba o app antes de gravar") from None


# O vídeo do Playwright não desenha o mouse: o cursor e a onda do clique vivem na própria página.
CURSOR_JS = """
(() => {
  const montar = () => {
    if (document.getElementById("__cur")) return;
    const cur = document.createElement("div");
    cur.id = "__cur";
    cur.style.cssText = "position:fixed;left:-50px;top:-50px;z-index:2147483647;pointer-events:none;width:30px;height:30px;transform:translate(-4px,-3px);filter:drop-shadow(0 2px 4px rgba(0,0,0,.6))";
    cur.innerHTML = '<svg width="30" height="30" viewBox="0 0 24 24"><path d="M4 2l15 9-6.5 1.5L9 19z" fill="#39ff14" stroke="#021002" stroke-width="1.6" stroke-linejoin="round"/></svg>';
    document.documentElement.appendChild(cur);
    addEventListener("mousemove", (e) => { cur.style.left = e.clientX + "px"; cur.style.top = e.clientY + "px"; }, true);
    addEventListener("mousedown", (e) => {
      const r = document.createElement("div");
      r.style.cssText = `position:fixed;left:${e.clientX}px;top:${e.clientY}px;width:16px;height:16px;margin:-8px 0 0 -8px;border-radius:50%;border:3px solid #39ff14;z-index:2147483646;pointer-events:none;opacity:.9;transition:transform .55s ease-out,opacity .55s ease-out`;
      document.documentElement.appendChild(r);
      requestAnimationFrame(() => { r.style.transform = "scale(4)"; r.style.opacity = "0"; });
      setTimeout(() => r.remove(), 700);
    }, true);
  };
  if (document.readyState === "loading") addEventListener("DOMContentLoaded", montar); else montar();
})();
"""


def _traduzir_erro(erro: Exception, base: str) -> str:
    bruto = str(erro)
    if re.search(r"ERR_CONNECTION_REFUSED|ECONNREFUSED|net::ERR_", bruto):
        return f"não foi possível conectar em {base}; confirme que o app está no ar"
    if "Executable doesn't exist" in bruto:
        return "falta o navegador do Playwright; rode: playwright install chromium"
    linhas = bruto.strip().splitlines()
    return linhas[0] if linhas else repr(erro)


def _ate_o_elemento(page, seletor: str, timeout_ms: int):
    alvo = page.locator(seletor).first
    alvo.wait_for(state="visible", timeout=timeout_ms)
    caixa = alvo.bounding_box()
    page.mouse.move(caixa["x"] + caixa["width"] / 2, caixa["y"] + caixa["height"] / 2, steps=40)
    return alvo


def _executar(page, acao: dict, base: str, timeout_ms: int) -> None:
    if "ir" in acao:
        page.goto(base.rstrip("/") + "/" + acao["ir"].lstrip("/"), wait_until="networkidle")
    elif "digitar" in acao:
        campo = _ate_o_elemento(page, acao["digitar"], timeout_ms)
        campo.click()
        campo.fill("")
        campo.press_sequentially(acao.get("valor", ""), delay=70)
    elif "clicar" in acao:
        _ate_o_elemento(page, acao["clicar"], timeout_ms).click()
    elif "apontar" in acao:
        _ate_o_elemento(page, acao["apontar"], timeout_ms)


def _executar_passo(page, n: int, passo: dict, base: str, timeout_ms: int) -> None:
    """Executa um passo; a falha diz qual foi, para o autor do roteiro achar a linha."""
    try:
        _executar(page, passo["acao"], base, timeout_ms)
    except PlaywrightError as erro:
        raise ValueError(f"a gravação falhou no passo {n} ({passo['titulo']}): "
                         f"{_traduzir_erro(erro, base)}") from None


def gravar(root: Path, roteiro: dict, destino: Path, *, timeout_ms: int = TEMPO_DO_SELETOR_MS) -> dict:
    """Grava os passos no Playwright; devolve `{webm, duracao, passos:[{n,titulo,fala,inicio,fim}]}`.

    Cada passo dura ao menos o tempo de ler a própria fala; os instantes de
    início e fim são os que o brag usa para posicionar as legendas.
    """
    if sync_playwright is None:
        raise ValueError(f"falta o Playwright do Python; instale com: {INSTALAR_PLAYWRIGHT}")
    base = roteiro["base"]
    bruto = destino / "_bruto"
    shutil.rmtree(bruto, ignore_errors=True)
    destino.mkdir(parents=True, exist_ok=True)
    passos = []
    try:
        with sync_playwright() as playwright:
            navegador = playwright.chromium.launch()
            try:
                contexto = navegador.new_context(viewport=VIEWPORT, record_video_dir=str(bruto),
                                                 record_video_size=VIEWPORT)
                contexto.add_init_script(CURSOR_JS)
                page = contexto.new_page()
                t0 = time.monotonic()
                page.goto(base, wait_until="networkidle")
                page.mouse.move(VIEWPORT["width"] / 2, VIEWPORT["height"] / 2)
                page.wait_for_timeout(1500)
                for n, passo in enumerate(roteiro["passos"], start=1):
                    inicio, inicio_passo = time.monotonic() - t0, time.monotonic()
                    _executar_passo(page, n, passo, base, timeout_ms)
                    minimo = max(MINIMO_POR_PASSO_MS, len(passo["fala"].split()) * MS_POR_PALAVRA) / 1000
                    page.wait_for_timeout(max(0.0, minimo - (time.monotonic() - inicio_passo)) * 1000)
                    passos.append({"n": n, "titulo": passo["titulo"], "fala": passo["fala"],
                                   "inicio": inicio, "fim": time.monotonic() - t0})
                duracao = time.monotonic() - t0 + 1
                page.wait_for_timeout(1000)
                video = page.video
                contexto.close()  # finaliza o webm
                origem = Path(video.path())
            finally:
                navegador.close()
    except PlaywrightError as erro:
        raise ValueError(f"a gravação falhou: {_traduzir_erro(erro, base)}") from None
    webm = destino / "gravacao.webm"
    shutil.move(str(origem), webm)
    shutil.rmtree(bruto, ignore_errors=True)
    return {"webm": str(webm), "duracao": duracao, "passos": passos}


def montar_prompt(roteiro: dict, gravacao: dict, idioma: str, root: Path, saida: Path) -> str:
    webm = Path(gravacao["webm"])
    try:
        webm = webm.relative_to(root)
    except ValueError:
        pass
    passos = [{"n": p["n"], "titulo": p["titulo"], "fala": p["fala"],
               "inicio_s": round(p["inicio"], 2), "fim_s": round(p["fim"], 2)}
              for p in gravacao["passos"]]
    return (f"/brag Monte o vídeo de TREINAMENTO \"{roteiro['titulo']}\" a partir da gravação de tela "
            f"já pronta em {webm.as_posix()} ({gravacao['duracao']:.1f} s, 1920x1080). Use essa "
            "gravação como filmagem principal: não grave de novo nem altere o app. Ponha as legendas "
            "numa faixa própria abaixo do quadro, para não taparem a tela, uma por passo, nos tempos "
            "abaixo (em segundos a partir do início da gravação; 'fala' é o texto da legenda). "
            f"Idioma de todo texto do vídeo: {IDIOMA_NO_PROMPT[idioma]}; traduza as falas se preciso. "
            f"Salve o .mp4 final exatamente em {saida.as_posix()}.\n\nPassos:\n"
            + json.dumps(passos, ensure_ascii=False, indent=2))


def gerar_training(root: Path, modulo: str, idioma: str = "pt", *, which=None, run=None,
                   home: Path | None = None, gravar_fn=None) -> Path:
    """Valida, grava e monta o vídeo em `.sentry/media/training-<modulo>-<idioma>.mp4`.

    Tudo que dá para recusar sem gravar é recusado antes de abrir o navegador,
    e o app é testado antes do `claude`: um brag sem gravação gastaria tokens à toa.
    """
    validar_idioma(idioma)
    roteiro = carregar_roteiro(root, modulo)
    claude = checar_dependencias_training(root, which=which, home=home, run=run)
    app_responde(roteiro["base"])
    pasta = root / PASTA_DE_MIDIA / f"training-{modulo}"
    gravacao = (gravar_fn or gravar)(root, roteiro, pasta)
    destino = root / PASTA_DE_MIDIA / f"training-{modulo}-{idioma}.mp4"
    saida = Path(SAIDA_DO_BRAG) / f"training-{modulo}-{idioma}.mp4"
    return acionar_brag(root, montar_prompt(roteiro, gravacao, idioma, root, saida), destino,
                        claude=claude, run=run, saida=root / saida)
