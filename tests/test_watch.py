"""O watch: o passo que mais se repete precisa ser o mais barato.

O laço é testado com `iterations` e um `sleep` falso — depender de tempo de parede
tornaria o teste lento e intermitente, que é o oposto do que o watch existe para ser.
"""
from __future__ import annotations

from pathlib import Path

from sentrytest.application.watch import (
    COMPLETO, INSTANTANEO, changed, is_test_file, mode_for, snapshot, watch,
)

# cenario: watch no arquivo de codigo roda o modo instantaneo
def test_salvar_codigo_escolhe_o_modo_instantaneo():
    """Executar a suíte a cada tecla devolveria a fricção que o watch existe para tirar."""
    assert mode_for("src/sentrytest/cli.py") == INSTANTANEO
    assert mode_for(Path("src") / "app.py") == INSTANTANEO

# cenario: watch no arquivo de teste escala para o modo completo
def test_salvar_teste_escala_para_o_modo_completo():
    """Salvar um teste é justamente quando a mudança vira evidência, e evidência só
    sai executando."""
    assert mode_for(Path("tests") / "test_cli.py") == COMPLETO
    assert mode_for("spec/app_spec.rb") == COMPLETO

def test_extensao_de_teste_fora_do_caminho_declarado_nao_escala():
    """Só a extensão não basta: num projeto com testes ao lado do código, `src/app.py`
    e `src/app.test.ts` têm o mesmo peso para o disco e significados opostos."""
    assert is_test_file("src/app.py") is False
    assert mode_for("src/app.py") == INSTANTANEO
    assert mode_for("src/app.test.ts", test_paths=("src",)) == COMPLETO

def test_markdown_nunca_e_arquivo_de_teste():
    assert is_test_file("tests/README.md") is False
    assert mode_for("tests/README.md") == INSTANTANEO

def _projeto(root: Path) -> None:
    (root / "tests").mkdir()
    (root / "src").mkdir()
    (root / "src" / "app.py").write_text("x = 1\n", encoding="utf-8")
    (root / "tests" / "test_app.py").write_text("def test_x():\n    assert True\n", encoding="utf-8")

def test_snapshot_ignora_o_que_o_proprio_sentry_escreve(tmp_path: Path):
    """Sem isto a análise gravaria em `.sentry/` e acordaria a si mesma num laço."""
    _projeto(tmp_path)
    relatorios = tmp_path / ".sentry" / "reports"
    relatorios.mkdir(parents=True)
    (relatorios / "latest.md").write_text("# relatorio\n", encoding="utf-8")
    (tmp_path / "__pycache__").mkdir()
    (tmp_path / "__pycache__" / "app.cpython-312.pyc").write_bytes(b"\x00")

    visto = snapshot(tmp_path)
    assert set(visto) == {"src/app.py", "tests/test_app.py"}

def test_snapshot_acompanha_a_spec_que_e_intencao_declarada(tmp_path: Path):
    """A spec mora sob `.sentry/`, território de artefato gerado — mas ela não é
    gerada, é declarada. Editar um CASES.md muda o que o Sentry vai cobrar."""
    _projeto(tmp_path)
    spec = tmp_path / ".sentry" / "specs" / "demo"
    spec.mkdir(parents=True)
    (spec / "CASES.md").write_text("# Demo\n", encoding="utf-8")
    assert ".sentry/specs/demo/CASES.md" in snapshot(tmp_path)

def test_snapshot_ignora_arquivo_removido_entre_o_rglob_e_o_stat(tmp_path: Path, monkeypatch):
    """A corrida entre listar e medir é real num diretório sendo editado: o
    arquivo já não existe quando o stat chega, e isto não pode derrubar o
    watch — só deve desaparecer do instantâneo, como uma remoção normal."""
    _projeto(tmp_path)
    alvo = tmp_path / "src" / "app.py"
    original = Path.stat

    def stat_instavel(self, *args, **kwargs):
        if self == alvo:
            raise OSError("removido")
        return original(self, *args, **kwargs)

    monkeypatch.setattr(Path, "stat", stat_instavel)
    visto = snapshot(tmp_path)
    assert "src/app.py" not in visto
    assert "tests/test_app.py" in visto


def test_changed_detecta_escrita_criacao_e_remocao():
    antes = {"a.py": (1, 10), "b.py": (2, 20)}
    depois = {"a.py": (9, 10), "c.py": (3, 30)}
    assert changed(antes, depois) == ["a.py", "b.py", "c.py"]

def test_changed_detecta_reescrita_de_mesmo_tamanho_no_mesmo_instante():
    """Trocar um caractere por outro nao muda o tamanho, e um editor rapido pode
    gravar dentro do mesmo tick: e' o caso que o `st_mtime` float perdia."""
    assert changed({"a.py": (1_000_000_001, 6)}, {"a.py": (1_000_000_002, 6)}) == ["a.py"]

def test_watch_chama_o_callback_uma_vez_por_salvamento(tmp_path: Path):
    _projeto(tmp_path)
    chamadas = []
    voltas = {"n": 0}

    def sleep_falso(_):
        # Escreve entre uma volta e outra: simula o salvamento sem tempo de parede.
        # O conteudo novo tem tamanho diferente de proposito -- reescrever com o
        # mesmo numero de bytes dentro do mesmo tick do sistema de arquivos deixaria
        # o teste dependente da resolucao de mtime da maquina, e intermitente.
        voltas["n"] += 1
        if voltas["n"] == 2:
            (tmp_path / "src" / "app.py").write_text("x = 2  # editado\n", encoding="utf-8")

    watch(tmp_path, lambda arquivos, modo: chamadas.append((arquivos, modo)),
          iterations=3, sleep=sleep_falso)
    assert chamadas == [(["src/app.py"], INSTANTANEO)]

def test_watch_escala_quando_o_lote_inclui_um_teste(tmp_path: Path):
    """Basta um teste no lote para que só a execução responda o que mudou."""
    _projeto(tmp_path)
    chamadas = []

    def sleep_falso(_):
        (tmp_path / "src" / "app.py").write_text("x = 3  # editado\n", encoding="utf-8")
        (tmp_path / "tests" / "test_app.py").write_text(
            "def test_y():\n    assert True  # editado\n", encoding="utf-8")

    watch(tmp_path, lambda arquivos, modo: chamadas.append(modo), iterations=1, sleep=sleep_falso)
    assert chamadas == [COMPLETO]

def test_watch_nao_chama_o_callback_quando_nada_muda(tmp_path: Path):
    """Reavaliar sem mudança gastaria o orçamento que o modo instantâneo existe para
    preservar, e encheria o terminal de veredito repetido."""
    _projeto(tmp_path)
    chamadas = []
    watch(tmp_path, lambda arquivos, modo: chamadas.append(modo), iterations=3, sleep=lambda _: None)
    assert chamadas == []
