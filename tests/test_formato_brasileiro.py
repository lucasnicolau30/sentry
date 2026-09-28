"""Instantes exibidos em formato brasileiro, com o fuso declarado.

O armazenamento segue ISO/UTC: é dado de máquina. A conversão acontece só na
leitura, e um valor que o helper não entende nunca derruba o comando que só
queria exibi-lo.
"""
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from sentrytest.application.formatting import format_instant
from sentrytest.application.reporting import markdown_report
from sentrytest.cli import main

BRASILEIRO = re.compile(r'\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2} \(UTC[+-]\d{1,2}(:\d{2})?\)')


def payload(run_id='r1', timestamp='2026-09-22T10:30:45+00:00', **configuration):
    return {'data': {'id': run_id, 'project': 'demo', 'timestamp': timestamp,
                     'verdict': {'status': 'aprovado'}, 'findings': [],
                     'configuration': configuration}}


# cenario: instante do cabecalho sai em formato brasileiro com fuso
def test_instante_do_cabecalho_sai_em_formato_brasileiro_com_fuso():
    report = markdown_report(payload(timestamp='2026-09-22T10:30:45.634585+00:00'))
    linha = next(line for line in report.splitlines() if line.startswith('- Analisado em:'))
    assert BRASILEIRO.search(linha)
    assert '2026-09-22T10:30:45' not in linha


# cenario: microssegundos somem da exibicao e ficam no armazenamento
def test_microssegundos_somem_da_exibicao_e_ficam_no_armazenamento():
    armazenado = '2026-09-22T10:30:45.634585+00:00'
    exibido = format_instant(armazenado)
    assert '634585' not in exibido
    assert '634585' in json.dumps(payload(timestamp=armazenado))


# cenario: nota de cache reaproveitado tambem sai formatada
def test_nota_de_cache_reaproveitado_tambem_sai_formatada():
    anterior = '2026-09-22T09:12:03+00:00'
    report = markdown_report(payload(
        from_cache=True,
        cached_from={'run_id': 'r0', 'timestamp': anterior},
        coverage={'global_percent': 87.4, 'changed_percent': 91.0,
                  'reused_from': {'run_id': 'r0', 'timestamp': anterior}},
    ))
    formatado = format_instant(anterior)
    assert f'execução r0 de {formatado}' in report
    # A mesma nota alimenta as duas linhas de cobertura reusada.
    assert report.count(f'medida na execução anterior ({formatado})') == 2
    assert anterior not in report


# cenario: history lista execucoes com a data formatada
def test_history_lista_execucoes_com_a_data_formatada(tmp_path: Path, monkeypatch, capsys):
    import sqlite3
    monkeypatch.chdir(tmp_path)
    sentry_dir = tmp_path / '.sentry'
    sentry_dir.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(sentry_dir / 'sentry.db') as conn:
        conn.execute('CREATE TABLE IF NOT EXISTS runs (id TEXT PRIMARY KEY, payload TEXT NOT NULL)')
        conn.execute('INSERT INTO runs VALUES (?,?)',
                     ('r1', json.dumps(payload('r1', '2026-09-22T10:30:45+00:00'))))
    assert main(['history']) == 0
    saida = capsys.readouterr().out
    assert BRASILEIRO.search(saida)
    assert '2026-09-22T10:30:45' not in saida


# cenario: instante ausente nao quebra a formatacao
def test_instante_ausente_nao_quebra_a_formatacao():
    report = markdown_report(payload(timestamp=None))
    assert '- Analisado em: indisponivel' in report
    assert format_instant(None) == 'indisponível'


# cenario: timestamp gravado fora do padrao nao quebra a formatacao
def test_timestamp_gravado_fora_do_padrao_nao_quebra_a_formatacao():
    assert format_instant('quinta-feira passada') == 'quinta-feira passada'
    assert '- Analisado em: quinta-feira passada' in markdown_report(
        payload(timestamp='quinta-feira passada'))


# cenario: identificador de run continua sem formatacao
def test_identificador_de_run_continua_sem_formatacao():
    run_id = '7c2e9a04-3b61-4f8d-9e12-5a7c8d3f1b20'
    report = markdown_report(payload(run_id=run_id))
    assert f'- Run: {run_id}' in report


# cenario: fuso com minutos quebrados sai declarado por extenso
def test_fuso_com_minutos_quebrados_sai_declarado_por_extenso():
    from datetime import timedelta
    from sentrytest.application.formatting import _offset_label

    indiano = datetime(2026, 9, 22, 16, 0, 45, tzinfo=timezone(timedelta(hours=5, minutes=30)))
    assert _offset_label(indiano) == '(UTC+5:30)'
    assert _offset_label(datetime(2026, 9, 22, tzinfo=timezone(timedelta(hours=-3)))) == '(UTC-3)'
