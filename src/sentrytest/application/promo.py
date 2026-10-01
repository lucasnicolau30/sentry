"""`sentry promo`: o vídeo promocional do projeto, gerado pela skill brag.

O brag é uma skill do Claude Code, não um binário; o Sentry a aciona por
subprocess com `claude -p`. Faltou `claude`, a skill ou o `ffmpeg`, ou o
`claude` falhou: erro claro, sem fallback silencioso -- um vídeo "gerado" por
um caminho que o usuário não pediu esconderia que o brag não rodou.
"""
import shutil
import subprocess
import time
from pathlib import Path

IDIOMAS = ("pt", "en")
IDIOMA_PADRAO = "pt"
SAIDA_DO_BRAG = "brag-output"
PASTA_DE_MIDIA = Path(".sentry") / "media"
TEMPO_MAXIMO = 1800

# `claude -p` não tem quem aprove permissão: sem esta lista o brag pararia no
# primeiro `npx hyperframes`. Lista de ferramentas, não bypass geral.
FERRAMENTAS = "Bash,Read,Write,Edit,Glob,Grep,Skill"

INSTALAR_CLAUDE = "https://claude.com/claude-code"
INSTALAR_BRAG = "/plugin marketplace add latent-spaces/brag  e depois  /plugin install brag@brag"
INSTALAR_FFMPEG = "https://ffmpeg.org/download.html"

PROMPTS = {
    "pt": ("/brag Gere o vídeo promocional deste projeto em português do Brasil: todo texto na "
           "tela e na copy em PT-BR. Salve o .mp4 final em brag-output/."),
    "en": ("/brag Generate the promo video for this project in English: all on-screen text and "
           "copy in English. Save the final .mp4 in brag-output/."),
}


def validar_idioma(idioma: str) -> str:
    if idioma not in IDIOMAS:
        raise ValueError(f"idioma desconhecido: {idioma!r}; use um de: {', '.join(IDIOMAS)}")
    return idioma


def brag_instalado(root: Path, home: Path) -> bool:
    """A skill pode viver no projeto, na conta ou dentro de um plugin instalado."""
    if (root / ".claude" / "skills" / "brag" / "SKILL.md").is_file():
        return True
    if (home / ".claude" / "skills" / "brag" / "SKILL.md").is_file():
        return True
    plugins = home / ".claude" / "plugins"
    return plugins.is_dir() and any(plugins.glob("**/skills/brag/SKILL.md"))


def checar_dependencias(root: Path, *, which=None, home: Path | None = None) -> str:
    """Devolve o caminho do `claude` ou levanta ValueError dizendo o que falta."""
    # Resolvidos na chamada, não na definição: quem simula `which`/`run` troca o módulo.
    which = which or shutil.which
    home = home if home is not None else Path.home()
    claude = which("claude")
    if not claude:
        raise ValueError(f"falta o Claude Code (`claude` não está no PATH); instale em {INSTALAR_CLAUDE}")
    if not brag_instalado(root, home):
        raise ValueError(f"falta a skill brag no Claude Code; instale com: {INSTALAR_BRAG}")
    if not which("ffmpeg"):
        raise ValueError(f"falta o `ffmpeg` (o brag renderiza com ele); instale em {INSTALAR_FFMPEG}")
    return claude


def _videos_novos(pasta: Path, desde: float) -> list[Path]:
    if not pasta.is_dir():
        return []
    return sorted((v for v in pasta.glob("*.mp4") if v.stat().st_mtime >= desde),
                  key=lambda v: v.stat().st_mtime, reverse=True)


def gerar_promo(root: Path, idioma: str = IDIOMA_PADRAO, *, which=None,
                run=None, home: Path | None = None) -> Path:
    """Roda o brag e copia o vídeo novo para `.sentry/media/promo-<idioma>.mp4`.

    Copia em vez de mover: `brag-output/` já tem vídeos versionados, e mover o
    arquivo apagaria um que o git conhece.
    """
    validar_idioma(idioma)
    claude = checar_dependencias(root, which=which, home=home)
    run = run or subprocess.run
    inicio = time.time()
    try:
        resultado = run([claude, "-p", PROMPTS[idioma], "--allowedTools", FERRAMENTAS],
                        cwd=root, capture_output=True, timeout=TEMPO_MAXIMO,
                        text=True, encoding="utf-8", errors="replace")
    except subprocess.TimeoutExpired:
        raise ValueError(f"o brag passou de {TEMPO_MAXIMO // 60} min sem terminar; nada foi gravado") from None
    except OSError as error:
        raise ValueError(f"não foi possível executar o claude: {error}") from None
    if resultado.returncode != 0:
        detalhe = (resultado.stderr or resultado.stdout or "").strip()[-600:]
        raise ValueError(f"o claude -p terminou com código {resultado.returncode}"
                         + (f": {detalhe}" if detalhe else ""))
    videos = _videos_novos(root / SAIDA_DO_BRAG, inicio)
    if not videos:
        raise ValueError(f"o claude terminou, mas não deixou nenhum .mp4 novo em {SAIDA_DO_BRAG}/; "
                         "o vídeo não foi gerado")
    destino = root / PASTA_DE_MIDIA / f"promo-{idioma}.mp4"
    destino.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(videos[0], destino)
    return destino
