"""Arquivamento de mídia por módulo e versão.

Dois diretórios com naturezas opostas. `.sentry/media/` é o pool bruto: enche
sozinho a cada execução e2e, fica fora do Git e o `sentry clear` poda. Já
`.sentry/storage/<modulo>-<versao>/` é a seleção curada: só existe porque alguém
rodou `sentry archive` de propósito, é versionada, e nem o `clear` a toca --
deletar é decisão manual de quem arquivou.

O arquivo precisa se sustentar sozinho: o relatório da execução é substituído na
próxima e a cópia por run é podada, então apontar para eles daria link quebrado
em seis meses. Por isso o `README.md` gerado carrega veredito, cobertura e
limitações junto da tabela de mídia, em vez de referenciar o relatório.
"""
from __future__ import annotations

import shutil
from pathlib import Path

from .formatting import format_instant

PRIMEIRA_VERSAO = "1.0.0"
MEDIA_DIR = ("media",)
STORAGE_DIR = ("storage",)


def media_path(root: Path) -> Path:
    return root.joinpath(".sentry", *MEDIA_DIR)


def storage_path(root: Path) -> Path:
    return root.joinpath(".sentry", *STORAGE_DIR)


def collect_media(root: Path, output_dir: str | None) -> tuple[Path, ...]:
    """Recolhe para `.sentry/media/` o que a suíte e2e acabou de gravar.

    O Playwright limpa o próprio diretório de saída a cada execução; sem copiar,
    a evidência de uma execução some na seguinte e não haveria o que promover.
    Sem `output_dir` declarado não há de onde recolher, e isso não é erro: o
    projeto simplesmente não pediu arquivamento de mídia.
    """
    if not output_dir:
        return ()
    origem = root / output_dir
    if not origem.is_dir():
        return ()
    destino = media_path(root)
    destino.mkdir(parents=True, exist_ok=True)
    recolhidos = []
    for arquivo in sorted(origem.rglob("*")):
        if not arquivo.is_file():
            continue
        alvo = destino / arquivo.relative_to(origem)
        alvo.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(arquivo, alvo)
        recolhidos.append(alvo)
    return tuple(recolhidos)


def declared_modules(config: dict) -> dict[str, list[str]]:
    return {name: list(specs) for name, specs in (config.get("modules") or {}).items()}


def resolve_specs(config: dict, module: str, version: str, specs: list[str] | None) -> list[str]:
    """As specs que compõem o módulo, declaradas uma única vez na 1.0.0.

    Congelar a composição é o que torna duas versões do mesmo módulo
    comparáveis: se a 1.0.1 tem menos evidência que a 1.0.0, foi o código que
    mudou, não a lista que alguém digitou diferente.
    """
    declarados = declared_modules(config)
    if module not in declarados:
        if version != PRIMEIRA_VERSAO:
            raise ValueError(
                f"módulo {module} ainda não existe: a primeira versão é sempre {PRIMEIRA_VERSAO}, "
                f"não {version}")
        if not specs:
            raise ValueError(
                f"módulo {module} ainda não existe: declare as specs que o compõem com "
                f"--specs na versão {PRIMEIRA_VERSAO}")
        return list(specs)
    if specs:
        raise ValueError(
            f"a composição de {module} já foi declarada na {PRIMEIRA_VERSAO} e está congelada; "
            f"para mudá-la, edite [modules] no sentry.toml")
    return declarados[module]


def record_module(root: Path, module: str, specs: list[str]) -> None:
    """Grava a composição em `[modules]` do sentry.toml.

    Escrita por acréscimo, sem reescrever o arquivo: o `sentry.toml` é do
    usuário, e reserializá-lo apagaria comentários e ordem que ele escolheu.
    """
    caminho = root / "sentry.toml"
    lista = ", ".join(f'"{spec}"' for spec in specs)
    linha = f'{module} = [{lista}]\n'
    texto = caminho.read_text(encoding="utf-8") if caminho.exists() else ""
    if "[modules]" in texto:
        corpo = texto.replace("[modules]\n", f"[modules]\n{linha}", 1)
    else:
        corpo = texto + ("" if texto.endswith("\n") or not texto else "\n") + f"\n[modules]\n{linha}"
    caminho.write_text(corpo, encoding="utf-8")


_EXTENSOES_IMAGEM = {".png", ".jpg", ".jpeg", ".webp"}
_EXTENSOES_VIDEO = {".webm", ".mp4", ".mov"}


def _rotulo(nome_do_arquivo: str) -> str | None:
    """"print", "vídeo", ou `None` para o que não é mídia de exibição.

    O JUnit do Playwright anexa trace.zip junto de print e vídeo -- o trace é
    debug (replay passo a passo), não evidência visual para README de
    treinamento, e classificá-lo como "vídeo" por não ser imagem inventaria um
    vídeo que não existe sempre que só o trace foi produzido.
    """
    extensao = Path(nome_do_arquivo).suffix.lower()
    if extensao in _EXTENSOES_IMAGEM:
        return "print"
    if extensao in _EXTENSOES_VIDEO:
        return "vídeo"
    return None


def _media_nome(caminho: str) -> str:
    """Nome único do arquivo na pasta `media/` arquivada.

    O Playwright nomeia o print/vídeo igual em todo teste (`test-finished-1.png`
    para quem passou); usar só esse nome faria o arquivo de um teste sobrescrever
    o de outro na cópia, e a tabela linkaria o mesmo print errado em toda linha.
    Prefixar pela pasta do teste (que o Playwright já torna única por título)
    resolve a colisão sem precisar reorganizar a pasta `media/` em subpastas.
    """
    partes = Path(caminho).parts
    return f"{partes[-2]}-{partes[-1]}" if len(partes) >= 2 else Path(caminho).name


def _media_evidences(case: dict, *, incluir_imagem: bool = True, incluir_video: bool = True) -> list[str]:
    """Evidências de Playwright do caso que são mídia de exibição (print/vídeo),
    filtradas pelo tipo pedido em `--image`/`--video`.

    Trace nunca entra, com flag ou sem. Sem nenhuma das duas flags, print e
    vídeo são promovidos (comportamento de sempre); com uma ou ambas, só o(s)
    tipo(s) pedido(s) entra(m) na tabela e na pasta arquivada.
    """
    caminhos = [evidence.get("path") for evidence in case.get("evidences", [])
                if evidence.get("source") == "playwright" and evidence.get("path")]
    aceita = {"print": incluir_imagem, "vídeo": incluir_video}
    return [caminho for caminho in caminhos if aceita.get(_rotulo(Path(caminho).name))]


def render_readme(module: str, version: str, payload: dict, specs: list[str],
                  linhas_de_media: list[tuple[str, str]], *,
                  incluir_imagem: bool = True, incluir_video: bool = True) -> str:
    data = payload.get("data") or {}
    configuration = data.get("configuration") or {}
    coverage = configuration.get("coverage") or {}
    verdict = (data.get("verdict") or {}).get("status", "inconclusivo")
    global_percent = coverage.get("global_percent")
    cobertura = f"{global_percent:.2f}%".replace(".", ",") if global_percent is not None else "indisponível"
    reused = coverage.get("reused_from") or {}
    if reused:
        cobertura += f" — medida em {format_instant(reused.get('timestamp'))}, não nesta execução"
    commit = data.get("commit")
    linhas = [
        f"# Módulo {module} — v{version}",
        "",
        f"- Arquivado em: {format_instant(data.get('timestamp'))}",
        f"- Commit: {commit[:12] if commit else 'indisponível'}",
        f"- Veredito: {verdict.capitalize()}",
        f"- Specs: {', '.join(specs)}",
        f"- Cobertura global: {cobertura}",
        "",
        "## Evidência por caso",
        "",
        "| Caso | Status | Mídia |",
        "|---|---|---|",
    ]
    for case in data.get("test_cases", []):
        evidencias_do_caso = {_media_nome(path) for path in
                              _media_evidences(case, incluir_imagem=incluir_imagem, incluir_video=incluir_video)}
        midias = [f"[{_rotulo(nome)}](media/{nome})" for nome, _ in linhas_de_media if nome in evidencias_do_caso]
        if not midias:
            continue
        nome_do_caso = case.get("name") or case.get("id", "")
        linhas.append(f"| {nome_do_caso} | {case.get('status', '?')} | {', '.join(midias)} |")
    linhas += [
        "",
        "## Limitações",
        "",
        "- Caso de camada frontend não recebe cobertura de linha: o status vem de "
        "evidência de execução, não de número.",
    ]
    if reused:
        linhas.append("- Cobertura global reaproveitada da última execução completa; esta "
                      "rodou apenas a suíte e2e.")
    if not linhas_de_media:
        linhas.append("- Nenhuma mídia foi produzida: o módulo não tem caso de camada frontend "
                      "com evidência de execução do Playwright.")
    elif not incluir_imagem or not incluir_video:
        excluido = "prints" if not incluir_imagem else "vídeos"
        todas = [caminho for case in data.get("test_cases", []) for caminho in _media_evidences(case)]
        if any(_rotulo(Path(caminho).name) == ("print" if not incluir_imagem else "vídeo") for caminho in todas):
            linhas.append(f"- {excluido.capitalize()} existem mas ficaram de fora: "
                          f"a execução pediu só {'vídeo' if not incluir_imagem else 'print'} "
                          f"(`--{'video' if not incluir_imagem else 'image'}`).")
    return "\n".join(linhas) + "\n"


def write_archive(root: Path, module: str, version: str, payload: dict, specs: list[str], *,
                  incluir_imagem: bool = True, incluir_video: bool = True) -> Path:
    """Escreve `.sentry/storage/<modulo>-<versao>/` com a mídia e o README.

    Sobrescreve a pasta quando a versão já existe: rearquivar é dizer que a
    evidência de agora é a que vale para aquela versão. `incluir_imagem` e
    `incluir_video` vêm de `--image`/`--video` de `sentry archive`: sem nenhuma
    das duas, tudo que existir é promovido.
    """
    destino = storage_path(root) / f"{module}-{version}"
    if destino.exists():
        shutil.rmtree(destino)
    pasta_de_media = destino / "media"
    pasta_de_media.mkdir(parents=True, exist_ok=True)
    linhas_de_media: list[tuple[str, str]] = []
    for case in (payload.get("data") or {}).get("test_cases", []):
        for caminho in _media_evidences(case, incluir_imagem=incluir_imagem, incluir_video=incluir_video):
            origem = root / caminho
            if not origem.is_file():
                # O anexo do JUnit vem relativo a pasta do proprio junit.xml (ex.:
                # `..\test-results\<pasta-do-teste>\arquivo.png`), nao a raiz do
                # projeto -- so' o nome do arquivo colide entre testes diferentes
                # (varios "test-finished-1.png"), entao o pool local precisa ser
                # buscado pela dupla <pasta-do-teste>/<arquivo>, nao so' o nome.
                partes = Path(caminho).parts
                origem = media_path(root).joinpath(*partes[-2:]) if len(partes) >= 2 \
                    else media_path(root) / Path(caminho).name
            if not origem.is_file():
                continue
            nome_unico = _media_nome(caminho)
            shutil.copy2(origem, pasta_de_media / nome_unico)
            linhas_de_media.append((nome_unico, caminho))
    (destino / "README.md").write_text(
        render_readme(module, version, payload, specs, linhas_de_media,
                      incluir_imagem=incluir_imagem, incluir_video=incluir_video),
        encoding="utf-8")
    return destino
