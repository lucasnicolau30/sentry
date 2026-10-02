"""`sentry promo`: o vídeo promocional do projeto, gerado pela skill brag.

O brag é uma skill de agente, não um binário; o Sentry aciona por subprocess o agente
que o usuário declarou em `[video] agente` no `sentry.toml`. Sem declaração o agente é
o `claude` (`claude -p`), e só nesse caso o Sentry sabe onde procurar e como instalar o
brag. Faltou o agente, a skill ou o `ffmpeg`, ou o agente falhou: erro claro, sem
fallback silencioso -- um vídeo "gerado" por um caminho que o usuário não pediu
esconderia que o brag não rodou.
"""
import json
import shutil
import subprocess
from pathlib import Path
from typing import NamedTuple

IDIOMAS = ("pt", "en")
IDIOMA_PADRAO = "pt"
SAIDA_DO_BRAG = "brag-output"
PASTA_DE_MIDIA = Path(".sentry") / "video"
TEMPO_MAXIMO = 1800
TEMPO_DA_INSTALACAO = 300

# O agente padrão, `claude -p`, não tem quem aprove permissão: sem esta lista o brag
# pararia no primeiro `npx hyperframes`. Lista de ferramentas, não bypass geral. No
# Windows o `claude` roda comandos pela ferramenta PowerShell, não pela Bash: liberar só
# a Bash deixava o brag sem poder rodar node, npx e ffmpeg. Vale só para o padrão.
FERRAMENTAS = "Bash,PowerShell,Read,Write,Edit,Glob,Grep,Skill"

AGENTE_PADRAO = "claude"
MARCADOR_DO_PEDIDO = "{prompt}"
ONDE_DECLARAR = "[video] agente"
EXEMPLO_DE_AGENTE = 'agente = ["meu-agente", "--rodar", "{prompt}"]'
INSTALAR_BRAG = "/plugin marketplace add latent-spaces/brag  e depois  /plugin install brag@brag"
INSTALAR_FFMPEG = "https://ffmpeg.org/download.html"

PROMPTS = {
    "pt": ("/brag Gere o vídeo promocional deste projeto em português do Brasil: todo texto na "
           "tela e na copy em PT-BR. Salve o .mp4 final em brag-output/."),
    "en": ("/brag Generate the promo video for this project in English: all on-screen text and "
           "copy in English. Save the final .mp4 in brag-output/."),
}


class Agente(NamedTuple):
    """O comando que aciona o brag. `comando` ainda traz `{prompt}` no lugar do pedido."""
    comando: list[str]
    nome: str
    padrao: bool


def agente_declarado(config: dict) -> list | None:
    """O `[video] agente` do `sentry.toml`, como foi escrito; None quando não há declaração."""
    video = config.get("video")
    return video.get("agente") if isinstance(video, dict) else None


def validar_agente(agente) -> list[str] | None:
    """O comando declarado, ou None (usa o padrão). Um comando sem `{prompt}` rodaria sem
    receber o pedido do brag, então é recusado em vez de gastar uma rodada à toa."""
    if agente is None:
        return None
    valido = (isinstance(agente, list) and agente
              and all(isinstance(parte, str) and parte.strip() for parte in agente)
              and any(MARCADOR_DO_PEDIDO in parte for parte in agente))
    if not valido:
        raise ValueError(f"{ONDE_DECLARAR} deve ser uma lista de textos com o comando do agente, e um deles "
                         f"deve conter {MARCADOR_DO_PEDIDO} no lugar do pedido; exemplo: {EXEMPLO_DE_AGENTE}")
    return list(agente)


def validar_idioma(idioma: str) -> str:
    if idioma not in IDIOMAS:
        raise ValueError(f"idioma desconhecido: {idioma!r}; use um de: {', '.join(IDIOMAS)}")
    return idioma


def _plugin_brag_instalado(home: Path) -> bool:
    """O `claude` registra os plugins em `installed_plugins.json`; a pasta de cache
    sobrevive à desinstalação, então olhar o disco acharia um brag que já saiu."""
    registro = home / ".claude" / "plugins" / "installed_plugins.json"
    try:
        plugins = json.loads(registro.read_text(encoding="utf-8")).get("plugins", {})
    except (OSError, ValueError, AttributeError):
        return False
    return any(nome.split("@")[0] == "brag" and instalacoes for nome, instalacoes in plugins.items())


def brag_instalado(root: Path, home: Path) -> bool:
    """Só para o agente padrão: a skill pode viver no projeto, na conta ou num plugin instalado."""
    if (root / ".claude" / "skills" / "brag" / "SKILL.md").is_file():
        return True
    if (home / ".claude" / "skills" / "brag" / "SKILL.md").is_file():
        return True
    return _plugin_brag_instalado(home)


def _detalhe(resultado) -> str:
    return (resultado.stderr or resultado.stdout or "").strip()[-400:]


def instalar_brag(claude: str, *, run=None, avisar=print) -> None:
    """Instala o brag pelo gerenciador de plugins do `claude`, o agente padrão.

    O marketplace já existir não é erro: quem instalou o brag antes e o removeu
    só precisa do segundo passo.
    """
    run = run or subprocess.run
    avisar("A skill brag não está instalada; instalando com `claude plugin`...")
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


def checar_dependencias(root: Path, *, agente=None, which=None, home: Path | None = None, run=None,
                        avisar=print) -> Agente:
    """Devolve o agente a acionar; levanta ValueError dizendo o que falta.

    `agente` é o `[video] agente` do `sentry.toml`. Com ele declarado, o Sentry só exige o
    executável e o `ffmpeg`: não sabe onde aquele agente guarda skills, então não procura
    nem instala o brag. Sem ele, vale o `claude`, e aí a skill brag é procurada e, se faltar,
    instalada pelo Sentry. O agente e o `ffmpeg` são checados antes, para não instalar plugin
    numa máquina que não conseguiria renderizar.
    """
    declarado = validar_agente(agente)
    # Resolvidos na chamada, não na definição: quem simula `which`/`run` troca o módulo.
    which = which or shutil.which
    home = home if home is not None else Path.home()
    nome = declarado[0] if declarado else AGENTE_PADRAO
    executavel = which(nome)
    if not executavel:
        raise ValueError(f"falta o agente (`{nome}` não está no PATH); instale-o ou declare outro em "
                         f"{ONDE_DECLARAR} no sentry.toml")
    if not which("ffmpeg"):
        raise ValueError(f"falta o `ffmpeg` (o brag renderiza com ele); instale em {INSTALAR_FFMPEG}")
    if declarado:
        return Agente([executavel, *declarado[1:]], nome, padrao=False)
    if not brag_instalado(root, home):
        instalar_brag(executavel, run=run, avisar=avisar)
        if not brag_instalado(root, home):
            raise ValueError("o brag foi instalado, mas a skill não apareceu para o agente; "
                             f"instale à mão com: {INSTALAR_BRAG}")
    comando = [executavel, "-p", MARCADOR_DO_PEDIDO, "--allowedTools", FERRAMENTAS]
    # A música e os efeitos do brag vivem na pasta de plugins, fora do projeto.
    plugins = home / ".claude" / "plugins"
    if plugins.is_dir():
        comando += ["--add-dir", str(plugins)]
    return Agente(comando, nome, padrao=True)


def _pedido_ao_agente(agente: Agente, prompt: str) -> str:
    """A barra `/brag` é do `claude`; os outros agentes recebem a skill pelo nome."""
    if not agente.padrao and prompt.startswith("/brag "):
        return "Use a skill brag. " + prompt[len("/brag "):]
    return prompt


def _estado_dos_videos(root: Path) -> dict[Path, int]:
    """Os .mp4 de `brag-output/` e de `brag-output-<data>/`: o brag grava numa pasta com
    data quando `brag-output/` já existe, para não sobrescrever a rodada anterior."""
    return {v: v.stat().st_mtime_ns for pasta in root.glob(f"{SAIDA_DO_BRAG}*") if pasta.is_dir()
            for v in pasta.glob("*.mp4")}


def _videos_novos(root: Path, antes: dict[Path, int]) -> list[Path]:
    """Os .mp4 que não existiam ou foram reescritos desde `antes`, o mais recente primeiro.

    Compara com o estado anterior em vez de com a hora do relógio: o relógio do
    sistema e o carimbo do arquivo têm granularidades diferentes no Windows, e
    um vídeo gravado no mesmo instante pareceria mais antigo que o início.
    """
    agora = _estado_dos_videos(root)
    return sorted((v for v, mtime in agora.items() if antes.get(v) != mtime),
                  key=lambda v: agora[v], reverse=True)


def _levar_o_resto_do_brag(pasta: Path, alvo: Path) -> None:
    """Move tudo que o brag deixou em `pasta` para `alvo` e remove a pasta, já vazia.

    O que tiver o mesmo nome em `alvo` é substituído: uma rodada nova refaz a composição
    e os textos de divulgação da anterior, em vez de empilhar versões.
    """
    for item in sorted(pasta.iterdir()):
        novo = alvo / item.name
        if novo.is_dir() and not novo.is_symlink():
            shutil.rmtree(novo)
        elif novo.exists() or novo.is_symlink():
            novo.unlink()
        shutil.move(str(item), str(novo))
    pasta.rmdir()


def acionar_brag(root: Path, prompt: str, destino: Path, *, agente: Agente, run=None,
                 saida: Path | None = None) -> Path:
    """Roda o agente com o prompt do brag e leva a saída dele para a pasta de `destino`.

    Com `saida`, o prompt pediu esse caminho exato: um arquivo velho nele é apagado antes
    (é saída nossa, de uma rodada anterior), senão o agente o encontraria pronto e não
    geraria nada novo -- e o Sentry não distinguiria isso de uma falha.

    O vídeo novo é movido para `destino` e o resto da pasta de saída do brag
    (composição, planos, textos de divulgação) vai junto para a mesma pasta; a pasta
    do brag, já vazia, é removida. `brag-output/` não acumula nada no projeto do dev.
    """
    run = run or subprocess.run
    if saida is not None:
        saida.unlink(missing_ok=True)
    antes = _estado_dos_videos(root)
    pedido = _pedido_ao_agente(agente, prompt)
    comando = [parte.replace(MARCADOR_DO_PEDIDO, pedido) for parte in agente.comando]
    try:
        resultado = run(comando,
                        cwd=root, capture_output=True, timeout=TEMPO_MAXIMO,
                        text=True, encoding="utf-8", errors="replace")
    except subprocess.TimeoutExpired:
        raise ValueError(f"o brag passou de {TEMPO_MAXIMO // 60} min sem terminar; nada foi gravado") from None
    except OSError as error:
        raise ValueError(f"não foi possível executar o agente (`{agente.nome}`): {error}") from None
    if resultado.returncode != 0:
        detalhe = (resultado.stderr or resultado.stdout or "").strip()[-600:]
        raise ValueError(f"o agente (`{agente.nome}`) terminou com código {resultado.returncode}"
                         + (f": {detalhe}" if detalhe else ""))
    videos = [saida] if saida is not None and saida.is_file() else _videos_novos(root, antes)
    if not videos:
        # O que o agente disse é a única pista de por que o brag parou (pediu algo, negou uma
        # permissão, desistiu): sem isto o erro seria um beco sem saída.
        resposta = (resultado.stdout or "").strip()[-800:]
        raise ValueError(f"o agente (`{agente.nome}`) terminou, mas não deixou nenhum .mp4 novo em "
                         f"{SAIDA_DO_BRAG}*/; o vídeo não foi gerado"
                         + (f". O agente respondeu: {resposta}" if resposta else ""))
    origem = videos[0]
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.unlink(missing_ok=True)
    shutil.move(str(origem), str(destino))
    _levar_o_resto_do_brag(origem.parent, destino.parent)
    return destino


def gerar_promo(root: Path, idioma: str = IDIOMA_PADRAO, *, agente=None, which=None,
                run=None, home: Path | None = None) -> Path:
    """Roda o brag e guarda o vídeo em `.sentry/video/promo-<idioma>.mp4`, com o resto da saída dele."""
    validar_idioma(idioma)
    agente = checar_dependencias(root, agente=agente, which=which, home=home, run=run)
    destino = root / PASTA_DE_MIDIA / f"promo-{idioma}.mp4"
    return acionar_brag(root, PROMPTS[idioma], destino, agente=agente, run=run)
