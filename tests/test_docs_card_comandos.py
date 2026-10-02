"""A frase de referência do card "Comandos e Habilidades" cita todos os comandos da CLI."""
from __future__ import annotations

import argparse
import re
from pathlib import Path

import pytest

from sentrytest.cli import build_parser

DOCS_PAGE = Path(__file__).resolve().parent.parent / "frontend" / "src" / "components" / "DocsPage.tsx"


def _subcomandos(parser: argparse.ArgumentParser | None = None) -> list[str]:
    parser = parser or build_parser()
    grupos = parser._subparsers._group_actions if parser._subparsers is not None else []
    acoes = [acao for acao in grupos if isinstance(acao, argparse._SubParsersAction)]
    if not acoes:
        raise AssertionError("nenhum subparser encontrado em build_parser()")
    return list(acoes[0].choices)


def _comandos_da_frase(abertura: str) -> list[str]:
    """Os nomes destacados (`text-[var(--text-h)]`) na frase que começa em `abertura`, até o ponto final."""
    texto = DOCS_PAGE.read_text(encoding="utf-8").replace("\r\n", "\n")
    inicio = texto.index(abertura)
    fim = texto.index("</>", inicio)
    trecho = texto[inicio:fim]
    return re.findall(r'<span className="text-\[var\(--text-h\)\]">([a-z]+)</span>', trecho)


@pytest.mark.parametrize("abertura", ["Referência completa de", "Full reference for"])
# cenario: a frase de referencia cita todos os comandos da cli
def test_a_frase_de_referencia_cita_todos_os_comandos_da_cli(abertura: str):
    citados = _comandos_da_frase(abertura)
    esperados = _subcomandos()
    assert sorted(citados) == sorted(esperados), (
        f"faltam: {sorted(set(esperados) - set(citados))}; sobram: {sorted(set(citados) - set(esperados))}")
    assert len(citados) == len(set(citados)), "algum comando aparece duas vezes"


def test_subcomandos_sem_subparser_e_erro_de_uso_e_nao_lista_vazia():
    """Caminho defensivo, sem cenário declarado: uma lista vazia se leria como "a CLI não tem
    comando nenhum", que esconderia o defeito em vez de acusá-lo."""
    with pytest.raises(AssertionError):
        _subcomandos(argparse.ArgumentParser())
