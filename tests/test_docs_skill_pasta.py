"""Os documentos dizem que a skill vai para a pasta declarada, sem atribuí-la a uma marca."""
from __future__ import annotations

import re
from pathlib import Path

import pytest

from sentrytest.skills import AGENT_GUIDE

ROOT = Path(__file__).resolve().parent.parent
DOCS_PAGE = ROOT / "frontend" / "src" / "components" / "DocsPage.tsx"


def _plano(trecho: str) -> str:
    """O texto corrido de um trecho JSX, sem marcas, chaves de string nem quebras de linha."""
    return " ".join(re.sub(r"<[^>]+>|\{\" \"\}", " ", trecho).split())


def _pagina() -> str:
    return DOCS_PAGE.read_text(encoding="utf-8").replace("\r\n", "\n")


def _linha_do_comando(texto: str, comando: str) -> str:
    """O trecho que descreve o comando: da linha que o abre até a linha do próximo."""
    linhas = texto.splitlines()
    inicio = next(i for i, linha in enumerate(linhas) if f"sentry {comando}" in linha and linha.lstrip("-| ").startswith("`sentry"))
    fim = next((i for i in range(inicio + 1, len(linhas)) if linhas[i].lstrip("-| ").startswith("`sentry")), len(linhas))
    return " ".join(" ".join(linhas[inicio:fim]).split())


def _documentos() -> dict[str, str]:
    docs = {nome: (ROOT / nome).read_text(encoding="utf-8") for nome in ("README.md", "README.pt.md", "AGENT-SENTRY.md")}
    docs["guia do skills.py"] = AGENT_GUIDE
    return docs


# cenario: os documentos dizem que a skill vai para a pasta declarada e nao e de uma marca
def test_os_readmes_dizem_que_a_skill_vai_para_a_pasta_declarada():
    for nome in ("README.md", "README.pt.md"):
        texto = (ROOT / nome).read_text(encoding="utf-8")
        linha = next(l for l in texto.splitlines() if "sentry-cases" in l and "SKILL.md" in l)
        assert "[init] skills_dirs" in linha and ".claude/skills/" in linha, nome
        assert "Claude Code" not in linha, f"{nome}: a skill ainda é atribuída ao Claude Code"


# cenario: os documentos dizem que a skill vai para a pasta declarada e nao e de uma marca
def test_a_docs_page_diz_que_a_skill_vai_para_a_pasta_declarada_em_pt_e_em_en():
    pagina = _pagina()
    assert "(Claude Code)" not in pagina and "pelo Claude Code" not in pagina and "by Claude Code" not in pagina
    setup = _plano(pagina[pagina.index("function SetupContent("):pagina.index("function WorkflowContent(")])
    assert re.search(r"\(na pasta de \[init\] skills_dirs ?, \.claude/skills por padrão\)", setup)
    assert re.search(r"\(in the folder of \[init\] skills_dirs ?, \.claude/skills by default\)", setup)
    comandos = _plano(pagina[pagina.index("id=\"skill-sentry-cases\""):])
    assert "Gravada pelo sentry init na pasta de [init] skills_dirs" in comandos
    assert "o agente que lê skills dessa pasta a carrega automaticamente" in comandos
    assert "Written by sentry init to the folder of [init] skills_dirs" in comandos
    assert "an agent that reads skills from that folder loads it automatically" in comandos


@pytest.mark.parametrize("nome", ["README.md", "README.pt.md", "AGENT-SENTRY.md", "guia do skills.py"])
# cenario: as descricoes do init trazem a flag skills-dir
def test_as_descricoes_do_init_trazem_a_flag_skills_dir(nome: str):
    descricao = _linha_do_comando(_documentos()[nome], "init")
    assert "--skills-dir" in descricao and "[init] skills_dirs" in descricao, nome


# cenario: as descricoes do init trazem a flag skills-dir
def test_a_docs_page_traz_a_flag_skills_dir_na_entrada_do_init_em_pt_e_em_en():
    pagina = _pagina()
    entradas = re.findall(r'command: "sentry init .*?(?=\n\s+command:|\n\s+icon:|\n\];|\n  \],)', pagina, flags=re.S)
    assert len(entradas) == 2
    pt, en = (_plano(e) for e in entradas)
    assert "[--skills-dir PASTA]" in pt and "Com --skills-dir (repetível), escolhe a pasta da skill e a registra em [init] skills_dirs" in pt
    assert "[--skills-dir DIR]" in en and "With --skills-dir (repeatable), picks the skill folder and records it in [init] skills_dirs" in en


# cenario: o exemplo de sentry toml traz a secao init
def test_o_exemplo_de_sentry_toml_traz_a_secao_init():
    for nome in ("README.md", "README.pt.md"):
        texto = (ROOT / nome).read_text(encoding="utf-8")
        assert re.search(r'\[init\] +# (optional|opcional): .*\.claude/skills\)\nskills_dirs = \[".claude/skills", ".agentes/skills"\]', texto), nome
    pagina = _pagina()
    setup = pagina[pagina.index("function SetupContent("):pagina.index("function WorkflowContent(")]
    bloco = _plano(setup[setup.index('[init]{" "}'):]).replace("{'", "").replace("'}", "")
    assert "opcional: onde a skill sentry-cases é gravada (padrão: .claude/skills)" in bloco
    assert "optional: where the sentry-cases skill is written (default: .claude/skills)" in bloco
    assert 'skills_dirs = [".claude/skills", ".agentes/skills"]' in bloco


# cenario: os readmes apontam o projeto do brag para a pasta de videos
def test_os_readmes_apontam_o_projeto_do_brag_para_a_pasta_de_videos():
    for nome, frase in (("README.md", "the brag project in `.sentry/video/`"), ("README.pt.md", "o projeto do brag em `.sentry/video/`")):
        descricao = _linha_do_comando((ROOT / nome).read_text(encoding="utf-8"), "promo")
        assert frase in descricao, nome
        assert "projeto do brag em `brag-output/`" not in descricao and "brag project in `brag-output/`" not in descricao
