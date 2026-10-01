"""`sentry promo`: o vídeo promocional do projeto, gerado pela skill brag.

O brag é uma skill do Claude Code, não um binário; o Sentry a aciona por
subprocess com `claude -p`. Faltou `claude`, a skill ou o `ffmpeg`, ou o
`claude` falhou: erro claro, sem fallback silencioso -- um vídeo "gerado" por
um caminho que o usuário não pediu esconderia que o brag não rodou.
"""
import shutil
import subprocess
from pathlib import Path

IDIOMAS = ("pt", "en")
IDIOMA_PADRAO = "pt"
SAIDA_DO_BRAG = "brag-output"
PASTA_DE_MIDIA = Path(".sentry") / "media"
TEMPO_MAXIMO = 1800
TEMPO_DA_INSTALACAO = 300

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


def _detalhe(resultado) -> str:
    return (resultado.stderr or resultado.stdout or "").strip()[-400:]


def instalar_brag(claude: str, *, run=None, avisar=print) -> None:
    """Instala o brag pelo gerenciador de plugins do próprio Claude Code.

    O marketplace já existir não é erro: quem instalou o brag antes e o removeu
    só precisa do segundo passo.
    """
    run = run or subprocess.run
    avisar("A skill brag não está instalada; instalando pelo Claude Code...")
    for argumentos in (("marketplace", "add", "latent-spaces/brag"), ("install", "brag@brag")):
        comando = [claude, "plugin", *argumentos]
        try:
            resultado = run(comando, capture_output=True, timeout=TEMPO_DA_INSTALACAO,
                            text=True, encoding="utf-8", errors="replace")
        except (OSError, subprocess.TimeoutExpired) as error:
            raise ValueError(f"não foi possível instalar o brag ({' '.join(comando[1:])}): {error}; "
                             f"instale à mão com: {INSTALAR_BRAG}") from None
        ja_existe = "already" in _detalhe(resultado).lower()
        if resultado.returncode != 0 and not ja_existe:
            raise ValueError(f"a instalação do brag falhou ({' '.join(comando[1:])}): {_detalhe(resultado)}; "
                             f"instale à mão com: {INSTALAR_BRAG}")


def checar_dependencias(root: Path, *, which=None, home: Path | None = None, run=None,
                        avisar=print) -> str:
    """Devolve o caminho do `claude`; levanta ValueError dizendo o que falta.

    Só a skill brag é instalada pelo Sentry. `claude` e `ffmpeg` são checados
    antes, para não instalar plugin numa máquina que não conseguiria renderizar.
    """
    # Resolvidos na chamada, não na definição: quem simula `which`/`run` troca o módulo.
    which = which or shutil.which
    home = home if home is not None else Path.home()
    claude = which("claude")
    if not claude:
        raise ValueError(f"falta o Claude Code (`claude` não está no PATH); instale em {INSTALAR_CLAUDE}")
    if not which("ffmpeg"):
        raise ValueError(f"falta o `ffmpeg` (o brag renderiza com ele); instale em {INSTALAR_FFMPEG}")
    if not brag_instalado(root, home):
        instalar_brag(claude, run=run, avisar=avisar)
        if not brag_instalado(root, home):
            raise ValueError("o brag foi instalado, mas a skill não apareceu no Claude Code; "
                             f"instale à mão com: {INSTALAR_BRAG}")
    return claude


def _estado_dos_videos(pasta: Path) -> dict[Path, int]:
    return {v: v.stat().st_mtime_ns for v in pasta.glob("*.mp4")} if pasta.is_dir() else {}


def _videos_novos(pasta: Path, antes: dict[Path, int]) -> list[Path]:
    """Os .mp4 que não existiam ou foram reescritos desde `antes`, o mais recente primeiro.

    Compara com o estado anterior em vez de com a hora do relógio: o relógio do
    sistema e o carimbo do arquivo têm granularidades diferentes no Windows, e
    um vídeo gravado no mesmo instante pareceria mais antigo que o início.
    """
    agora = _estado_dos_videos(pasta)
    return sorted((v for v, mtime in agora.items() if antes.get(v) != mtime),
                  key=lambda v: agora[v], reverse=True)


def acionar_brag(root: Path, prompt: str, destino: Path, *, claude: str, run=None) -> Path:
    """Roda `claude -p` com o prompt do brag e copia o vídeo novo para `destino`.

    Copia em vez de mover: `brag-output/` já tem vídeos versionados, e mover o
    arquivo apagaria um que o git conhece.
    """
    run = run or subprocess.run
    antes = _estado_dos_videos(root / SAIDA_DO_BRAG)
    try:
        resultado = run([claude, "-p", prompt, "--allowedTools", FERRAMENTAS],
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
    videos = _videos_novos(root / SAIDA_DO_BRAG, antes)
    if not videos:
        raise ValueError(f"o claude terminou, mas não deixou nenhum .mp4 novo em {SAIDA_DO_BRAG}/; "
                         "o vídeo não foi gerado")
    destino.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(videos[0], destino)
    return destino


def gerar_promo(root: Path, idioma: str = IDIOMA_PADRAO, *, which=None,
                run=None, home: Path | None = None) -> Path:
    """Roda o brag e guarda o vídeo em `.sentry/media/promo-<idioma>.mp4`."""
    validar_idioma(idioma)
    claude = checar_dependencias(root, which=which, home=home, run=run)
    destino = root / PASTA_DE_MIDIA / f"promo-{idioma}.mp4"
    return acionar_brag(root, PROMPTS[idioma], destino, claude=claude, run=run)
