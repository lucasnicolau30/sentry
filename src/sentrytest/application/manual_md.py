"""O Markdown do manual: uma seção por módulo, em `.sentry/manual/secoes/<modulo>.md`.

É o que faz do manual um documento vivo. Os passos vêm do roteiro do `training` e o Sentry os
reescreve a cada `sentry manual <modulo>`; o resto (introdução, avisos, cartões) é de quem escreve
o manual, à mão ou pelo agente, e nunca é tocado. Só entra o que está listado em `AJUDA_DO_FORMATO`;
qualquer outra coisa vira parágrafo.
"""
import re
from dataclasses import dataclass, field
from pathlib import Path

from . import training

PASTA_DAS_SECOES = Path(".sentry") / "manual" / "secoes"
TIPOS_DE_AVISO = {"info": "info", "note": "info", "sucesso": "sucesso", "success": "sucesso",
                  "atencao": "atencao", "atenção": "atencao", "warning": "atencao"}
ABRE_PASSOS, ABRE_CARTOES, FECHA = ":::passos", ":::cartoes", ":::"

_FRONT_MATTER = "---"
_COMENTARIO = re.compile(r"\s*<!--.*-->\s*$")
_PASSO = re.compile(r"(\d+)\.\s+(\S.*)")
_AVISO = re.compile(r">\s*\[!(\w+)\]\s*(.*)")

MODELO = """---
modulo: {modulo}
ordem: {ordem}
---
# {titulo}

<!-- Escreva aqui a introdução da seção: o que o módulo faz e para quem. -->
<!-- Aviso: "> [!INFO] Título" (ou SUCESSO, ATENCAO), com o texto nas linhas seguintes, também começando por ">". -->
<!-- Cartões lado a lado: um bloco ":::cartoes" com "### Título" e o texto de cada um, fechado por ":::". -->
<!-- Negrito: **assim**. O bloco ":::passos" é do Sentry: "sentry manual {modulo}" o reescreve a partir do roteiro. -->

{passos}
"""


@dataclass
class Passo:
    titulo: str
    fala: str


@dataclass
class Secao:
    modulo: str
    titulo: str
    ordem: int | None = None
    # cada bloco é uma tupla: ("paragrafo", texto), ("subtitulo", texto), ("aviso", tipo, titulo, texto),
    # ("cartoes", [(titulo, texto), ...]) ou ("passos", [Passo, ...])
    blocos: list = field(default_factory=list)


def caminho_da_secao(root: Path, modulo: str) -> Path:
    return root / PASTA_DAS_SECOES / f"{training.validar_modulo(modulo)}.md"


def _erro(origem: str, linha: int, mensagem: str) -> ValueError:
    return ValueError(f"{origem}:{linha}: {mensagem}")


def _front_matter(linhas: list[str], origem: str) -> tuple[dict, int]:
    """Lê o bloco `---` do topo: `chave: valor`, uma por linha. Devolve os dados e onde o corpo começa."""
    if not linhas or linhas[0].strip() != _FRONT_MATTER:
        raise _erro(origem, 1, 'a seção começa com um bloco "---" com a chave modulo')
    dados = {}
    for n, linha in enumerate(linhas[1:], start=2):
        if linha.strip() == _FRONT_MATTER:
            return dados, n
        if not linha.strip():
            continue
        chave, separador, valor = linha.partition(":")
        if not separador or not chave.strip():
            raise _erro(origem, n, f'esperava "chave: valor", achei "{linha.strip()}"')
        dados[chave.strip()] = valor.strip()
    raise _erro(origem, len(linhas), 'o bloco "---" do topo não foi fechado')


def _ler_passos(linhas: list[tuple[int, str]], origem: str, abre: int) -> list[Passo]:
    passos = []
    for n, linha in linhas:
        if not linha.strip():
            continue
        achado = _PASSO.fullmatch(linha.rstrip())
        if achado:
            passos.append(Passo(achado.group(2).strip(), ""))
        elif linha.startswith((" ", "\t")) and passos:
            passos[-1].fala = f"{passos[-1].fala} {linha.strip()}".strip()
        else:
            raise _erro(origem, n, f'no bloco :::passos esperava "1. Título" e a fala recuada, achei "{linha.strip()}"')
    if not passos:
        raise _erro(origem, abre, "o bloco :::passos está vazio")
    return passos


def _ler_cartoes(linhas: list[tuple[int, str]], origem: str, abre: int) -> list[tuple[str, str]]:
    cartoes = []
    for n, linha in linhas:
        if linha.startswith("### "):
            cartoes.append([linha[4:].strip(), []])
        elif linha.strip():
            if not cartoes:
                raise _erro(origem, n, 'no bloco :::cartoes cada cartão começa com "### Título"')
            cartoes[-1][1].append(linha.strip())
    if not cartoes:
        raise _erro(origem, abre, "o bloco :::cartoes está vazio")
    return [(titulo, " ".join(texto)) for titulo, texto in cartoes]


def _ler_aviso(linhas: list[tuple[int, str]], origem: str) -> tuple:
    n, primeira = linhas[0]
    achado = _AVISO.fullmatch(primeira.strip())
    if not achado or achado.group(1).lower() not in TIPOS_DE_AVISO:
        raise _erro(origem, n, 'o aviso começa com "> [!INFO] Título" (ou SUCESSO, ATENCAO)')
    texto = " ".join(linha.lstrip(">").strip() for _, linha in linhas[1:] if linha.lstrip(">").strip())
    return ("aviso", TIPOS_DE_AVISO[achado.group(1).lower()], achado.group(2).strip(), texto)


def ler_secao(texto: str, origem: str = "secao.md") -> Secao:
    """O Markdown de uma seção em blocos; erro com `arquivo:linha` para o que não se entende."""
    linhas = texto.replace("\r\n", "\n").split("\n")
    dados, inicio = _front_matter(linhas, origem)
    if not dados.get("modulo"):
        raise _erro(origem, 1, "falta a chave modulo no bloco do topo")
    ordem = None
    if dados.get("ordem"):
        if not dados["ordem"].isdigit():
            raise _erro(origem, 1, f'ordem precisa ser um número inteiro, achei "{dados["ordem"]}"')
        ordem = int(dados["ordem"])
    secao, paragrafo, titulo = Secao(modulo=dados["modulo"], titulo="", ordem=ordem), [], False

    def fechar_paragrafo():
        if paragrafo:
            secao.blocos.append(("paragrafo", " ".join(paragrafo)))
            paragrafo.clear()

    n = inicio
    while n < len(linhas):
        linha, n = linhas[n], n + 1
        if _COMENTARIO.fullmatch(linha):
            continue
        if linha.strip() in (ABRE_PASSOS, ABRE_CARTOES):
            fechar_paragrafo()
            abre, miolo = n, []
            while n < len(linhas) and linhas[n].strip() not in (FECHA, ABRE_PASSOS, ABRE_CARTOES):
                miolo.append((n + 1, linhas[n]))
                n += 1
            if n == len(linhas) or linhas[n].strip() != FECHA:      # acabou o arquivo ou começou outro bloco
                raise _erro(origem, n, f"o bloco {linha.strip()} não foi fechado com {FECHA}")
            n += 1
            if linha.strip() == ABRE_PASSOS:
                secao.blocos.append(("passos", _ler_passos(miolo, origem, abre)))
            else:
                secao.blocos.append(("cartoes", _ler_cartoes(miolo, origem, abre)))
        elif linha.startswith(":::"):
            raise _erro(origem, n, f'bloco desconhecido "{linha.strip()}": os blocos são {ABRE_PASSOS} e {ABRE_CARTOES}')
        elif linha.startswith(">"):
            fechar_paragrafo()
            citacao = [(n, linha)]
            while n < len(linhas) and linhas[n].startswith(">"):
                citacao.append((n + 1, linhas[n]))
                n += 1
            secao.blocos.append(_ler_aviso(citacao, origem))
        elif linha.startswith("# "):
            fechar_paragrafo()
            if titulo:
                raise _erro(origem, n, 'só um título ("# ") por seção')
            secao.titulo, titulo = linha[2:].strip(), True
        elif linha.startswith("## "):
            fechar_paragrafo()
            secao.blocos.append(("subtitulo", linha[3:].strip()))
        elif linha.strip():
            paragrafo.append(linha.strip())
        else:
            fechar_paragrafo()
    fechar_paragrafo()
    if not secao.titulo:
        raise _erro(origem, inicio + 1, 'falta o título da seção ("# Título")')
    return secao


def listar_secoes(root: Path) -> list[Secao]:
    """Todas as seções do manual, na ordem: primeiro as com `ordem`, depois as outras pelo nome do módulo."""
    pasta = root / PASTA_DAS_SECOES
    secoes = [ler_secao(arquivo.read_text(encoding="utf-8"), arquivo.relative_to(root).as_posix())
              for arquivo in sorted(pasta.glob("*.md"))] if pasta.is_dir() else []
    return sorted(secoes, key=lambda s: (s.ordem is None, s.ordem or 0, s.modulo))


def _bloco_de_passos(roteiro: dict) -> str:
    """O bloco `:::passos` do roteiro, sem os passos marcados com `"manual": false` (preparo que só o
    vídeo precisa, como entrar no sistema), numerados de novo."""
    def linha(texto: str) -> str:
        return " ".join(str(texto).split())

    passos = [passo for passo in roteiro["passos"] if passo.get("manual", True)]
    if not passos:
        raise ValueError('todos os passos do roteiro têm "manual": false; o manual precisa de pelo menos um')
    corpo = [f"{n}. {linha(passo['titulo'])}\n   {linha(passo['fala'])}" for n, passo in enumerate(passos, 1)]
    return "\n".join([ABRE_PASSOS, *corpo, FECHA])


def com_passos(texto: str, roteiro: dict) -> str:
    """O Markdown com o bloco `:::passos` trocado pelo do roteiro; sem o bloco, ele vai para o fim."""
    novo = _bloco_de_passos(roteiro)
    linhas = texto.replace("\r\n", "\n").rstrip("\n").split("\n")
    abre = next((n for n, linha in enumerate(linhas) if linha.strip() == ABRE_PASSOS), None)
    if abre is None:
        return "\n".join(linhas) + "\n\n" + novo + "\n"
    fecha = next((n for n in range(abre + 1, len(linhas)) if linhas[n].strip() == FECHA), None)
    if fecha is None:
        raise ValueError(f"o bloco {ABRE_PASSOS} não foi fechado com {FECHA}")
    return "\n".join(linhas[:abre] + novo.split("\n") + linhas[fecha + 1:]) + "\n"


def sincronizar(root: Path, modulo: str) -> tuple[Path, bool]:
    """Cria a seção do módulo, ou atualiza só os passos dela a partir do roteiro. Devolve o arquivo e
    se ele foi criado agora."""
    roteiro = training.carregar_roteiro(root, modulo)
    arquivo = caminho_da_secao(root, modulo)
    criada = not arquivo.exists()
    if criada:
        ordens = [s.ordem for s in listar_secoes(root) if s.ordem is not None]
        texto = MODELO.format(modulo=modulo, ordem=max(ordens, default=0) + 1, titulo=roteiro["titulo"],
                              passos=_bloco_de_passos(roteiro))
    else:
        texto = com_passos(arquivo.read_text(encoding="utf-8"), roteiro)
        ler_secao(texto, arquivo.relative_to(root).as_posix())            # o que sai precisa continuar válido
    arquivo.parent.mkdir(parents=True, exist_ok=True)
    arquivo.write_text(texto, encoding="utf-8", newline="\n")
    return arquivo, criada
