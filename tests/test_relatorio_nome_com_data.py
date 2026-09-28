"""O relatório atual carrega a data e a hora da execução no nome.

Um nome fixo não diz de quando é a evidência sem abrir o arquivo. Continua sendo
um arquivo só: quem preserva histórico é a cópia permanente por run.
"""
from datetime import datetime, timedelta, timezone
from pathlib import Path

from sentrytest.application.reporting import LATEST_PREFIX, latest_reports, write_reports


def payload(run_id, timestamp):
    return {'data': {'id': run_id, 'project': 'demo', 'timestamp': timestamp,
                     'verdict': {'status': 'aprovado'}, 'findings': []}}


def reports_dir(root: Path) -> Path:
    return root / '.sentry' / 'reports'


def local_iso(year, month, day, hour, minute, second):
    """Instante que, convertido para o fuso local, cai exatamente nesses valores."""
    naive = datetime(year, month, day, hour, minute, second)
    return naive.astimezone().isoformat()


# cenario: nome do relatorio carrega a data e hora da execucao
def test_nome_do_relatorio_carrega_a_data_e_hora_da_execucao(tmp_path: Path):
    write_reports(tmp_path, payload('r1', local_iso(2026, 9, 22, 10, 30, 45)))
    assert (reports_dir(tmp_path) / 'latest-20260922-103045.md').exists()
    assert not (reports_dir(tmp_path) / 'latest.md').exists()


# cenario: id do relatorio sai do horario local e nao do utc gravado
def test_id_do_relatorio_sai_do_horario_local_e_nao_do_utc_gravado(tmp_path: Path):
    # Instante em UTC cuja conversao para o fuso local muda o dia: se o nome
    # saisse do UTC cru, ele apontaria para a data errada de quem le.
    local_moment = datetime(2026, 9, 22, 1, 15, 0).astimezone()
    offset = local_moment.utcoffset() or timedelta(0)
    utc_moment = (local_moment - offset).replace(tzinfo=timezone.utc)
    write_reports(tmp_path, payload('r1', utc_moment.isoformat()))
    assert (reports_dir(tmp_path) / 'latest-20260922-011500.md').exists()


# cenario: relatorio anterior sai quando o novo entra
def test_relatorio_anterior_sai_quando_o_novo_entra(tmp_path: Path):
    write_reports(tmp_path, payload('r1', local_iso(2026, 9, 22, 9, 12, 3)))
    write_reports(tmp_path, payload('r2', local_iso(2026, 9, 22, 10, 30, 45)))
    atuais = latest_reports(reports_dir(tmp_path))
    assert [path.name for path in atuais] == ['latest-20260922-103045.md']


# cenario: primeira execucao grava sem anterior a remover
def test_primeira_execucao_grava_sem_anterior_a_remover(tmp_path: Path):
    assert latest_reports(reports_dir(tmp_path)) == []
    write_reports(tmp_path, payload('r1', local_iso(2026, 9, 22, 10, 30, 45)))
    assert len(latest_reports(reports_dir(tmp_path))) == 1


# cenario: copias permanentes por run continuam gravadas
def test_copias_permanentes_por_run_continuam_gravadas(tmp_path: Path):
    run_id = '7c2e9a04-3b61-4f8d-9e12-5a7c8d3f1b20'
    write_reports(tmp_path, payload(run_id, local_iso(2026, 9, 22, 10, 30, 45)))
    assert (reports_dir(tmp_path) / f'{run_id}.md').exists()
    assert (reports_dir(tmp_path) / f'{run_id}.json').exists()


# cenario: comandos localizam o relatorio pelo padrao do nome
def test_comandos_localizam_o_relatorio_pelo_padrao_do_nome(tmp_path: Path):
    reports = reports_dir(tmp_path)
    write_reports(tmp_path, payload('r1', local_iso(2026, 9, 22, 10, 30, 45)))
    # A copia permanente mora na mesma pasta e nao pode ser confundida com o atual.
    (reports / 'r1.md').write_text('copia', encoding='utf-8')
    encontrados = latest_reports(reports)
    assert len(encontrados) == 1
    assert encontrados[0].name.startswith(LATEST_PREFIX)
    assert '# Sentry Report' in encontrados[0].read_text(encoding='utf-8')


# cenario: relatorio de nome fixo antigo sai na primeira execucao
def test_relatorio_de_nome_fixo_antigo_sai_na_primeira_execucao(tmp_path: Path):
    reports = reports_dir(tmp_path)
    reports.mkdir(parents=True, exist_ok=True)
    (reports / 'latest.md').write_text('veredito de uma versao anterior', encoding='utf-8')
    write_reports(tmp_path, payload('r1', local_iso(2026, 9, 22, 10, 30, 45)))
    assert not (reports / 'latest.md').exists()
    assert (reports / 'latest-20260922-103045.md').exists()


# cenario: relatorio sem instante registrado ainda recebe nome proprio
def test_relatorio_sem_instante_registrado_ainda_recebe_nome_proprio(tmp_path: Path):
    write_reports(tmp_path, payload('r1', None))
    assert (reports_dir(tmp_path) / 'latest-r1.md').exists()
