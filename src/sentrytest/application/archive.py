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

import json
import os
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from .formatting import format_instant

PRIMEIRA_VERSAO = "1.0.0"
MEDIA_DIR = ("media",)
STORAGE_DIR = ("storage",)

LOGIN_ENV_USUARIO = "SENTRY_LOGIN_USUARIO"
LOGIN_ENV_SENHA = "SENTRY_LOGIN_SENHA"
DEFAULT_BASE_URL = "http://localhost:5173"
CAPTURE_SCRIPT = ("frontend", "scripts", "sentry-capture.mjs")


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


def is_route_module(modulo_config) -> bool:
    """Distingue a forma nova (`[modules.<nome>]` com `rotas`) da antiga (lista
    de specs em `[modules]`) -- as duas convivem no mesmo `sentry.toml`, e um
    módulo antigo não deve ser confundido com um declarado por rota."""
    return isinstance(modulo_config, dict) and "rotas" in modulo_config


def module_routes(modulo_config: dict) -> list[str]:
    return list(modulo_config.get("rotas") or [])


def module_requires_login(modulo_config: dict) -> bool:
    return bool(modulo_config.get("login", False))


def module_route_specs(modulo_config: dict) -> list[str]:
    """Specs opcionais que certificam um módulo por rota. Presentes, o
    `archive` roda a suíte e carimba veredito; ausentes, o módulo é só
    registro visual -- a diferença central do modo por rota."""
    return list(modulo_config.get("specs") or [])


def resolve_login(config: dict) -> dict:
    """`[archive.login]` declarado no `sentry.toml`. Recusa cedo, antes de
    abrir qualquer navegador, quando um módulo com `login = true` não tem a
    declaração completa -- abrir o navegador para descobrir isso depois
    custaria caro e ainda deixaria o erro mais difícil de entender."""
    login = ((config.get("archive") or {}).get("login")) or {}
    faltando = [chave for chave in ("rota", "usuario", "senha", "enviar") if not login.get(chave)]
    if faltando:
        raise ValueError(
            "módulo exige login mas [archive.login] está incompleto ou ausente no sentry.toml "
            f"(faltando: {', '.join(faltando)})")
    return login


def resolve_credentials() -> dict:
    """Só valida que as variáveis existem -- não são gravadas em nenhum
    arquivo; o processo que fotografa as lê direto do próprio ambiente."""
    usuario = os.environ.get(LOGIN_ENV_USUARIO)
    senha = os.environ.get(LOGIN_ENV_SENHA)
    faltando = [nome for nome, valor in ((LOGIN_ENV_USUARIO, usuario), (LOGIN_ENV_SENHA, senha)) if not valor]
    if faltando:
        raise ValueError(
            f"módulo exige login mas faltam variáveis de ambiente: {', '.join(faltando)}")
    return {"usuario": usuario, "senha": senha}


def capture_routes(root: Path, routes: list[str], *, login: dict | None, destino: Path,
                   base_url: str, gravar_video: bool, node_bin: str = "node",
                   timeout_seconds: int = 120) -> dict:
    """Invoca o script Node/Playwright que faz login (se pedido) e fotografa
    cada rota em desktop e mobile, escrevendo direto em `destino/<slug>/`.

    Uma sessão só de navegador para todas as rotas: login acontece uma vez,
    não uma vez por rota. Credenciais nunca entram no JSON de configuração
    que vai para disco -- viajam só pela herança padrão de ambiente do
    subprocess, lidas pelo script de SENTRY_LOGIN_USUARIO/SENTRY_LOGIN_SENHA.
    """
    destino.mkdir(parents=True, exist_ok=True)
    config_path = destino / "_captura.json"
    config_path.write_text(json.dumps({
        "baseURL": base_url,
        "routes": routes,
        "login": login,
        "outDir": str(destino),
        "video": gravar_video,
    }), encoding="utf-8")
    script = root.joinpath(*CAPTURE_SCRIPT)
    try:
        result = subprocess.run(
            [node_bin, str(script), str(config_path)],
            cwd=root / "frontend", capture_output=True, timeout=timeout_seconds,
            encoding="utf-8", errors="replace")
    except (OSError, subprocess.TimeoutExpired) as error:
        raise ValueError(f"não foi possível executar a captura de rotas: {error}") from error
    finally:
        config_path.unlink(missing_ok=True)
    if result.returncode != 0:
        raise ValueError(f"captura de rotas falhou: {(result.stderr or result.stdout).strip()}")
    try:
        manifesto = json.loads(result.stdout)
    except json.JSONDecodeError as error:
        raise ValueError(f"captura de rotas não devolveu JSON válido: {result.stdout[:200]}") from error
    if manifesto.get("erro"):
        raise ValueError(f"captura de rotas falhou: {manifesto['erro']}")
    return manifesto


def render_readme_rotas(module: str, version: str, manifesto: dict, *,
                        certificado: bool, payload: dict | None = None,
                        commit: str | None = None) -> str:
    """README do módulo arquivado por rota. Sem specs (`certificado=False`)
    o veredito vira uma frase que deixa claro que não há certificação --
    do contrário um print sem asserção nenhuma passaria por prova de que o
    módulo funciona, que não é o que ele é."""
    timestamp = (payload or {}).get("data", {}).get("timestamp") if certificado and payload \
        else datetime.now(timezone.utc).isoformat()
    linhas = [
        f"# Módulo {module} — v{version}",
        "",
        f"- Arquivado em: {format_instant(timestamp)}",
        f"- Commit: {commit[:12] if commit else 'indisponível'}",
    ]
    if certificado and payload:
        verdict = (payload.get("data", {}).get("verdict") or {}).get("status", "inconclusivo")
        linhas.append(f"- Veredito: {verdict.capitalize()}")
    else:
        linhas.append("- Veredito: sem certificação — registro visual")
    linhas += ["", "## Rotas fotografadas", "", "| Rota | Desktop | Mobile |", "|---|---|---|"]
    for item in manifesto.get("rotas", []):
        rota = item["rota"]
        slug = item["slug"]
        if item.get("erro"):
            linhas.append(f"| {rota} | falhou: {item['erro']} | — |")
            continue
        arquivos = item.get("arquivos", [])
        desktop = f"[print]({slug}/desktop.png)" if "desktop.png" in arquivos else "—"
        mobile = f"[print]({slug}/mobile.png)" if "mobile.png" in arquivos else "—"
        linhas.append(f"| {rota} | {desktop} | {mobile} |")
    linhas += ["", "## Limitações", ""]
    if not certificado:
        linhas.append("- Módulo sem specs associadas: os prints e vídeos aqui são registro do "
                      "estado visual, não certificação de que o módulo funciona.")
    linhas.append("- Estado que a URL não alcança sozinha (dado específico já salvo no banco, "
                  "modal aberto por interação) não é capturado nesta versão.")
    return "\n".join(linhas) + "\n"


def write_archive_rotas(root: Path, module: str, version: str, modulo_config: dict, config: dict, *,
                        gravar_video: bool = False, node_bin: str = "node",
                        payload: dict | None = None, commit: str | None = None) -> Path:
    """Escreve `.sentry/storage/<modulo>-<versao>/` no modo por rotas: uma
    subpasta por rota fotografada, mais o README. Sobrescreve a pasta quando
    a versão já existe, igual ao modo por specs."""
    routes = module_routes(modulo_config)
    if not routes:
        raise ValueError(
            f"módulo {module} declara 'rotas' vazia; adicione ao menos uma rota em [modules.{module}]")
    login = None
    if module_requires_login(modulo_config):
        login = resolve_login(config)
        resolve_credentials()
    destino = storage_path(root) / f"{module}-{version}"
    if destino.exists():
        shutil.rmtree(destino)
    destino.mkdir(parents=True, exist_ok=True)
    base_url = ((config.get("archive") or {}).get("base_url")) or DEFAULT_BASE_URL
    manifesto = capture_routes(root, routes, login=login, destino=destino, base_url=base_url,
                               gravar_video=gravar_video, node_bin=node_bin)
    specs = module_route_specs(modulo_config)
    readme = render_readme_rotas(module, version, manifesto, certificado=bool(specs),
                                 payload=payload if specs else None, commit=commit)
    (destino / "README.md").write_text(readme, encoding="utf-8")
    return destino


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
