"""A traducao do codigo de saida em build verde ou vermelho, no job de auto-analise.

O job "o Sentry se analisa" e' a unica prova publica de que o produto funciona, e ele
ficou verde sem medir nada: as specs nao eram versionadas, o checkout limpo nao achava
matriz de casos, o `run` saia com 3 e a expressao do workflow traduzia 3 em sucesso.

O teste le a expressao real do arquivo e a avalia -- copiar a regra para ca deixaria os
dois divergirem em silencio, que e' exatamente a falha que se esta fechando.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

WORKFLOW = Path(__file__).resolve().parents[1] / '.github' / 'workflows' / 'ci.yml'
_EXPRESSAO = re.compile(r"exit \$\(\( \$\{codigo:-0\} (>|>=|==) (\d+) \? (\d+) : (\d+) \)\)")

def _derruba_o_build(codigo: int) -> bool:
    conteudo = WORKFLOW.read_text(encoding='utf-8')
    encontrado = _EXPRESSAO.search(conteudo)
    assert encontrado, 'expressao de saida do job de auto-analise nao encontrada em ci.yml'
    operador, limite, entao, senao = encontrado.groups()
    comparacoes = {'>': codigo > int(limite), '>=': codigo >= int(limite), '==': codigo == int(limite)}
    return int(entao if comparacoes[operador] else senao) != 0

# cenario: codigo de aprovado mantem o build verde
def test_aprovado_mantem_o_build_verde():
    assert _derruba_o_build(0) is False

# cenario: codigo de ressalva mantem o build verde
def test_ressalva_mantem_o_build_verde():
    """Ressalva e' o limite: ha achado de severidade alta, mas nada critico, e o
    relatorio ja diz o que rever. Derrubar aqui transformaria o job em ruido."""
    assert _derruba_o_build(1) is False

# cenario: codigo de reprovado derruba o build
def test_reprovado_derruba_o_build():
    assert _derruba_o_build(2) is True

# cenario: codigo de inconclusivo derruba o build
def test_inconclusivo_derruba_o_build():
    """Para o job que existe para provar que o produto funciona, "nao consegui medir"
    e' falha, nao aprovacao silenciosa. Era por aqui que o checkout sem spec passava."""
    assert _derruba_o_build(3) is True

@pytest.mark.parametrize('linha', ['.sentry/specs/', '.sentry/specs'])
def test_gitignore_do_proprio_repositorio_nao_exclui_as_specs(linha):
    """Dogfooding: o Sentry so pode se analisar no CI se as proprias specs chegarem
    la. A correcao no `init` nao alcanca o .gitignore ja commitado deste repositorio."""
    gitignore = (WORKFLOW.parents[2] / '.gitignore').read_text(encoding='utf-8').splitlines()
    assert linha not in gitignore
