"""A pasta da skill `sentry-cases` é declarada pelo usuário; `.claude/skills` é só o padrão."""
from __future__ import annotations

import tomllib
from pathlib import Path

import pytest

from sentrytest import cli
from sentrytest.adapters.local_tools import is_generated_artifact
from sentrytest.init_project import initialize_project

AGENTES = ".agentes/skills"


def _skill(raiz: Path, pasta: str) -> Path:
    return raiz / pasta / "sentry-cases" / "SKILL.md"


def _toml(raiz: Path, corpo: str) -> None:
    (raiz / "sentry.toml").write_text('[project]\nname = "demo"\n\n' + corpo, encoding="utf-8")


def _todas_as_skills(raiz: Path) -> list[Path]:
    return sorted(raiz.rglob("SKILL.md"))


# cenario: sem declaracao a skill vai para a pasta padrao
def test_sem_declaracao_a_skill_vai_para_a_pasta_padrao(tmp_path: Path) -> None:
    initialize_project(tmp_path)
    assert _skill(tmp_path, ".claude/skills").is_file()
    assert _todas_as_skills(tmp_path) == [_skill(tmp_path, ".claude/skills")]


# cenario: pasta declarada no sentry toml recebe a skill e a padrao nao e criada
def test_pasta_declarada_no_sentry_toml_recebe_a_skill_e_a_padrao_nao_e_criada(tmp_path: Path) -> None:
    _toml(tmp_path, f'[init]\nskills_dirs = ["{AGENTES}"]\n')
    initialize_project(tmp_path)
    assert _skill(tmp_path, AGENTES).is_file()
    assert not (tmp_path / ".claude").exists()


# cenario: lista vazia nao grava skill e mantem o guia universal
def test_lista_vazia_nao_grava_skill_e_mantem_o_guia_universal(tmp_path: Path) -> None:
    _toml(tmp_path, "[init]" + chr(10) + "skills_dirs = []" + chr(10))
    initialize_project(tmp_path)
    assert _todas_as_skills(tmp_path) == []
    assert (tmp_path / "AGENT-SENTRY.md").is_file()


# cenario: varias pastas declaradas recebem a mesma skill
def test_varias_pastas_declaradas_recebem_a_mesma_skill(tmp_path: Path) -> None:
    _toml(tmp_path, f'[init]\nskills_dirs = [".claude/skills", "{AGENTES}"]\n')
    primeira = initialize_project(tmp_path)
    assert _skill(tmp_path, ".claude/skills").read_text(encoding="utf-8") == _skill(tmp_path, AGENTES).read_text(encoding="utf-8")
    assert any(item.replace("\\", "/") == f"{AGENTES}/sentry-cases/SKILL.md" for item in primeira)
    assert initialize_project(tmp_path) == []  # a segunda execução não regrava nada


# cenario: a flag skills-dir grava a escolha no sentry toml
def test_a_flag_skills_dir_grava_a_escolha_no_sentry_toml(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    cli.main(["init", "--skills-dir", AGENTES])
    declarado = tomllib.loads((tmp_path / "sentry.toml").read_text(encoding="utf-8"))
    assert declarado["init"]["skills_dirs"] == [AGENTES]
    assert _skill(tmp_path, AGENTES).is_file()
    assert not (tmp_path / ".claude").exists()
    # sem a flag, a escolha continua valendo: o init (que o `sentry run` também roda) não recria o padrão
    cli.main(["init"])
    assert not (tmp_path / ".claude").exists()
    assert tomllib.loads((tmp_path / "sentry.toml").read_text(encoding="utf-8"))["init"]["skills_dirs"] == [AGENTES]


def test_a_flag_aceita_mais_de_uma_pasta(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    cli.main(["init", "--skills-dir", ".claude/skills", "--skills-dir", AGENTES])
    assert _skill(tmp_path, ".claude/skills").is_file() and _skill(tmp_path, AGENTES).is_file()
    assert tomllib.loads((tmp_path / "sentry.toml").read_text(encoding="utf-8"))["init"]["skills_dirs"] == [".claude/skills", AGENTES]


def test_a_flag_repetida_com_a_mesma_escolha_do_toml_e_aceita(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    cli.main(["init", "--skills-dir", AGENTES])
    antes = (tmp_path / "sentry.toml").read_text(encoding="utf-8")
    assert cli.main(["init", "--skills-dir", AGENTES]) in (cli.EXIT_OK, cli.EXIT_INFRA)  # INFRA só se faltar pytest/coverage
    assert (tmp_path / "sentry.toml").read_text(encoding="utf-8") == antes


# cenario: a flag e recusada quando o sentry toml ja declara outras pastas
def test_a_flag_e_recusada_quando_o_sentry_toml_ja_declara_outras_pastas(tmp_path: Path, monkeypatch, capsys) -> None:
    monkeypatch.chdir(tmp_path)
    _toml(tmp_path, '[init]\nskills_dirs = [".claude/skills"]\n')
    antes = (tmp_path / "sentry.toml").read_text(encoding="utf-8")
    assert cli.main(["init", "--skills-dir", AGENTES]) == cli.EXIT_INFRA
    assert "[init] skills_dirs" in capsys.readouterr().out
    assert (tmp_path / "sentry.toml").read_text(encoding="utf-8") == antes
    assert _todas_as_skills(tmp_path) == []


def test_a_flag_e_recusada_quando_o_sentry_toml_ja_tem_uma_secao_init(tmp_path: Path, monkeypatch, capsys) -> None:
    """Acrescentar `[init]` de novo deixaria o TOML inválido; o usuário edita a seção que já existe."""
    monkeypatch.chdir(tmp_path)
    _toml(tmp_path, "[init]\n")
    assert cli.main(["init", "--skills-dir", AGENTES]) == cli.EXIT_INFRA
    assert "[init]" in capsys.readouterr().out
    assert _todas_as_skills(tmp_path) == []


@pytest.mark.parametrize("declaracao", [
    '["/absoluta"]', '["../fora"]', '["a/../../fora"]', '[""]', '"texto"', '[1]', '["C:/absoluta"]',
])
# cenario: pasta insegura e recusada antes de gravar qualquer coisa
def test_pasta_insegura_e_recusada_antes_de_gravar_qualquer_coisa(tmp_path: Path, monkeypatch, capsys, declaracao: str) -> None:
    monkeypatch.chdir(tmp_path)
    _toml(tmp_path, f"[init]\nskills_dirs = {declaracao}\n")
    assert cli.main(["init"]) == cli.EXIT_INFRA
    assert "skills_dirs" in capsys.readouterr().out
    assert _todas_as_skills(tmp_path) == []
    assert not (tmp_path.parent / "fora").exists() and not (tmp_path / ".sentry").exists()


@pytest.mark.parametrize("pasta", ["/absoluta", "../fora", "", "C:/absoluta"])
def test_a_flag_tambem_recusa_pasta_insegura(tmp_path: Path, monkeypatch, capsys, pasta: str) -> None:
    monkeypatch.chdir(tmp_path)
    assert cli.main(["init", "--skills-dir", pasta]) == cli.EXIT_INFRA
    assert "skills_dirs" in capsys.readouterr().out
    assert _todas_as_skills(tmp_path) == [] and not (tmp_path / "sentry.toml").exists()


# cenario: skill em pasta declarada fica fora do diff como arquivo gerado
def test_skill_em_pasta_declarada_fica_fora_do_diff_como_arquivo_gerado() -> None:
    assert is_generated_artifact(f"{AGENTES}/sentry-cases/SKILL.md")
    assert is_generated_artifact(AGENTES.replace("/", "\\") + "\\sentry-cases\\SKILL.md")
    assert is_generated_artifact(".claude/skills/sentry-cases/SKILL.md")
    # a skill do usuário, na mesma pasta, não é do Sentry e continua aparecendo
    assert not is_generated_artifact(f"{AGENTES}/minha-skill/SKILL.md")


# cenario: o checklist do init mostra o caminho da skill sem citar uma marca
def test_o_checklist_do_init_mostra_o_caminho_da_skill_sem_citar_uma_marca(tmp_path: Path, monkeypatch, capsys) -> None:
    monkeypatch.chdir(tmp_path)
    _toml(tmp_path, f'[init]\nskills_dirs = [".claude/skills", "{AGENTES}"]\n')
    cli.main(["init"])
    linha = next(l for l in capsys.readouterr().out.splitlines() if "Instalando skill" in l)
    assert ".claude/skills/sentry-cases/SKILL.md" in linha and f"{AGENTES}/sentry-cases/SKILL.md" in linha
    assert "Claude —" not in linha and "skill Claude" not in linha
    cli.main(["init"])
    saida = capsys.readouterr().out
    assert "Instalando skill" not in saida
    assert any(l.rstrip().endswith("Skill") for l in saida.splitlines())
