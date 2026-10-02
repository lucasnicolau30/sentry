"""Arquivamento de mídia por módulo e versão.

`storage` só existe porque alguém rodou o comando de propósito: o `archive` executa a suíte
e2e na hora e leva para lá a evidência que o Playwright gravou. Por isso é versionado e
nenhuma poda o alcança. Não há pool intermediário: a evidência é lida da pasta de saída
do Playwright.
"""
import json
from pathlib import Path

import pytest

from sentrytest.application.archive import (
    PRIMEIRA_VERSAO, record_module, resolve_specs, storage_path, write_archive)
from sentrytest.application.reporting import clear_history
from sentrytest.init_project import initialize_project


def payload(verdict='aprovado', casos=()):
    return {'data': {'id': 'r1', 'project': 'demo', 'commit': 'a94b1fb00000aa',
                     'timestamp': '2026-09-22T10:30:45+00:00',
                     'verdict': {'status': verdict}, 'findings': [],
                     'configuration': {'coverage': {'global_percent': 87.4}},
                     'test_cases': list(casos)}}


def caso(nome, status='coberto', midias=()):
    return {'id': f'TC-01-{nome}', 'name': nome, 'status': status,
            'evidences': [{'source': 'playwright', 'path': path} for path in midias]}


# cenario: primeira versao de um modulo declara a composicao
def test_primeira_versao_de_um_modulo_declara_a_composicao(tmp_path: Path):
    specs = resolve_specs({}, 'modulo-usuarios', PRIMEIRA_VERSAO, ['cadastro-de-usuario', 'login'])
    assert specs == ['cadastro-de-usuario', 'login']
    (tmp_path / 'sentry.toml').write_text('[project]\nname = "demo"\n', encoding='utf-8')
    record_module(tmp_path, 'modulo-usuarios', specs)
    gravado = (tmp_path / 'sentry.toml').read_text(encoding='utf-8')
    assert '[modules]' in gravado
    assert 'modulo-usuarios = ["cadastro-de-usuario", "login"]' in gravado


# cenario: versao seguinte le a composicao congelada
def test_versao_seguinte_le_a_composicao_congelada():
    config = {'modules': {'modulo-usuarios': ['cadastro-de-usuario', 'login']}}
    assert resolve_specs(config, 'modulo-usuarios', '1.0.1', []) == ['cadastro-de-usuario', 'login']


# cenario: composicao ja declarada recusa nova lista de specs
def test_composicao_ja_declarada_recusa_nova_lista_de_specs():
    config = {'modules': {'modulo-usuarios': ['login']}}
    with pytest.raises(ValueError) as erro:
        resolve_specs(config, 'modulo-usuarios', '1.0.1', ['login', 'permissoes'])
    assert 'congelada' in str(erro.value) and 'sentry.toml' in str(erro.value)


# cenario: modulo novo so nasce na versao inicial
def test_modulo_novo_so_nasce_na_versao_inicial():
    with pytest.raises(ValueError) as erro:
        resolve_specs({}, 'modulo-usuarios', '2.0.0', ['login'])
    assert PRIMEIRA_VERSAO in str(erro.value)


# cenario: modulo novo sem specs declaradas e recusado
def test_modulo_novo_sem_specs_declaradas_e_recusado():
    with pytest.raises(ValueError) as erro:
        resolve_specs({}, 'modulo-usuarios', PRIMEIRA_VERSAO, [])
    assert '--specs' in str(erro.value)


# cenario: veredito reprovado nao arquiva nada
def test_veredito_reprovado_nao_arquiva_nada(tmp_path: Path, monkeypatch, capsys):
    from sentrytest import cli
    monkeypatch.chdir(tmp_path)
    initialize_project(tmp_path)
    (tmp_path / 'sentry.toml').write_text(
        '[project]\nname = "demo"\n\n[modules]\nmodulo-usuarios = ["login"]\n', encoding='utf-8')

    class RunFalso:
        id = 'r1'
        verdict = type('V', (), {'status': type('S', (), {'value': 'reprovado'})()})()
        infrastructure_errors = ()

    monkeypatch.setattr(cli, 'analyze', lambda *a, **k: RunFalso())
    monkeypatch.setattr(cli, 'to_json', lambda run: json.dumps(payload('reprovado')))
    codigo = cli.main(['archive', 'modulo-usuarios', '--version', '1.0.1'])
    assert codigo == 2
    assert 'nada foi arquivado' in capsys.readouterr().out
    assert not (storage_path(tmp_path) / 'modulo-usuarios-1.0.1').exists()


# cenario: arquivo aprovado grava midia e readme
def test_arquivo_aprovado_grava_midia_e_readme(tmp_path: Path):
    video = tmp_path / 'test-results' / 'cadastro-valido.webm'
    video.parent.mkdir(parents=True, exist_ok=True)
    video.write_bytes(b'video')
    dados = payload(casos=[caso('Cadastro com dados validos cria o usuario',
                                midias=['test-results/cadastro-valido.webm'])])
    destino = write_archive(tmp_path, 'modulo-usuarios', '1.0.0', dados, ['cadastro-de-usuario'])

    assert (destino / 'media' / 'test-results-cadastro-valido.webm').exists()
    assert not (destino / 'relatorio.md').exists()
    readme = (destino / 'README.md').read_text(encoding='utf-8')
    assert '# Módulo modulo-usuarios — v1.0.0' in readme
    assert '- Veredito: Aprovado' in readme
    assert '- Specs: cadastro-de-usuario' in readme
    assert '| Cadastro com dados validos cria o usuario | coberto |' in readme
    assert '[vídeo](media/test-results-cadastro-valido.webm)' in readme
    assert 'não recebe cobertura de linha' in readme


# cenario: modulo aprovado sem nenhuma midia declara a ausencia
def test_modulo_aprovado_sem_nenhuma_midia_declara_a_ausencia(tmp_path: Path):
    dados = payload(casos=[caso('CPF invalido bloqueia o cadastro')])
    destino = write_archive(tmp_path, 'modulo-relatorio', '1.0.0', dados, ['cadastro-de-usuario'])

    assert sorted((destino / 'media').iterdir()) == []
    readme = (destino / 'README.md').read_text(encoding='utf-8')
    assert '| CPF invalido bloqueia o cadastro |' not in readme
    assert 'Nenhuma mídia foi produzida' in readme


# cenario: flag image sozinha arquiva so prints
def test_flag_image_sozinha_arquiva_so_prints(tmp_path: Path):
    (tmp_path / 'test-results').mkdir()
    (tmp_path / 'test-results' / 'print.png').write_bytes(b'print')
    (tmp_path / 'test-results' / 'video.webm').write_bytes(b'video')
    dados = payload(casos=[caso('Cadastro com dados validos cria o usuario',
                                midias=['test-results/print.png', 'test-results/video.webm'])])
    destino = write_archive(tmp_path, 'modulo-usuarios', '1.0.0', dados, ['cadastro-de-usuario'],
                            incluir_imagem=True, incluir_video=False)

    arquivados = {path.name for path in (destino / 'media').iterdir()}
    assert arquivados == {'test-results-print.png'}
    readme = (destino / 'README.md').read_text(encoding='utf-8')
    assert '[print](media/test-results-print.png)' in readme
    assert 'test-results-video.webm' not in readme
    assert 'ficaram de fora' in readme


# cenario: flag video sozinha arquiva so videos
def test_flag_video_sozinha_arquiva_so_videos(tmp_path: Path):
    (tmp_path / 'test-results').mkdir()
    (tmp_path / 'test-results' / 'print.png').write_bytes(b'print')
    (tmp_path / 'test-results' / 'video.webm').write_bytes(b'video')
    dados = payload(casos=[caso('Cadastro com dados validos cria o usuario',
                                midias=['test-results/print.png', 'test-results/video.webm'])])
    destino = write_archive(tmp_path, 'modulo-usuarios', '1.0.0', dados, ['cadastro-de-usuario'],
                            incluir_imagem=False, incluir_video=True)

    arquivados = {path.name for path in (destino / 'media').iterdir()}
    assert arquivados == {'test-results-video.webm'}
    readme = (destino / 'README.md').read_text(encoding='utf-8')
    assert '[vídeo](media/test-results-video.webm)' in readme
    assert 'test-results-print.png' not in readme
    assert 'ficaram de fora' in readme


# cenario: sem nenhuma flag de midia arquiva tudo que existir
def test_sem_flag_de_midia_arquiva_tudo(tmp_path: Path):
    (tmp_path / 'test-results').mkdir()
    (tmp_path / 'test-results' / 'print.png').write_bytes(b'print')
    (tmp_path / 'test-results' / 'video.webm').write_bytes(b'video')
    dados = payload(casos=[caso('Cadastro com dados validos cria o usuario',
                                midias=['test-results/print.png', 'test-results/video.webm'])])
    destino = write_archive(tmp_path, 'modulo-usuarios', '1.0.0', dados, ['cadastro-de-usuario'])

    arquivados = {path.name for path in (destino / 'media').iterdir()}
    assert arquivados == {'test-results-print.png', 'test-results-video.webm'}
    readme = (destino / 'README.md').read_text(encoding='utf-8')
    assert '[print](media/test-results-print.png)' in readme
    assert '[vídeo](media/test-results-video.webm)' in readme
    assert 'ficaram de fora' not in readme


# cenario: midia com caminho relativo ao junit e encontrada na pasta de saida do playwright
def test_midia_com_caminho_relativo_ao_junit_e_encontrada_na_pasta_de_saida_do_playwright(tmp_path: Path):
    pasta_do_teste = tmp_path / 'frontend' / 'test-results' / 'hero-blur-reveal-hero-exib-26b64'
    pasta_do_teste.mkdir(parents=True)
    (pasta_do_teste / 'test-finished-1.png').write_bytes(b'print')
    dados = payload(casos=[caso('Cadastro com dados validos cria o usuario',
                                midias=[r'..\test-results\hero-blur-reveal-hero-exib-26b64\test-finished-1.png'])])
    destino = write_archive(tmp_path, 'modulo-usuarios', '1.0.0', dados, ['cadastro-de-usuario'],
                            output_dir='frontend/test-results')

    assert (destino / 'media' / 'hero-blur-reveal-hero-exib-26b64-test-finished-1.png').exists()
    readme = (destino / 'README.md').read_text(encoding='utf-8')
    assert '[print](media/hero-blur-reveal-hero-exib-26b64-test-finished-1.png)' in readme


def test_midia_que_nao_resolve_e_sem_output_dir_fica_de_fora_sem_quebrar(tmp_path: Path):
    """Caminho defensivo, sem cenário declarado: sem `output_dir` não há onde buscar um
    caminho relativo ao JUnit; a mídia fica de fora e o arquivamento segue, em vez de quebrar."""
    dados = payload(casos=[caso('Cadastro', midias=[r'..\test-results\algum-teste\test-finished-1.png'])])
    destino = write_archive(tmp_path, 'modulo-usuarios', '1.0.0', dados, ['cadastro-de-usuario'])
    assert sorted((destino / 'media').iterdir()) == []


# cenario: rearquivar a mesma versao sobrescreve a pasta
def test_rearquivar_a_mesma_versao_sobrescreve_a_pasta(tmp_path: Path):
    antigo = storage_path(tmp_path) / 'modulo-usuarios-1.0.0' / 'media' / 'sobra.webm'
    antigo.parent.mkdir(parents=True, exist_ok=True)
    antigo.write_bytes(b'execucao antiga')
    destino = write_archive(tmp_path, 'modulo-usuarios', '1.0.0', payload(), ['login'])
    assert not antigo.exists()
    assert sorted(path.name for path in destino.iterdir()) == ['README.md', 'media']


# cenario: clear poda execucoes e relatorios e preserva o arquivado e os videos
def test_clear_poda_execucoes_e_relatorios_e_preserva_o_arquivado_e_os_videos(tmp_path: Path):
    relatorio = tmp_path / '.sentry' / 'reports' / 'latest-20260101-100000.md'
    relatorio.parent.mkdir(parents=True, exist_ok=True)
    relatorio.write_text('# relatorio', encoding='utf-8')
    video = tmp_path / '.sentry' / 'video' / 'promo-pt.mp4'
    video.parent.mkdir(parents=True, exist_ok=True)
    video.write_bytes(b'video')
    arquivado = write_archive(tmp_path, 'modulo-usuarios', '1.0.0', payload(), ['login'])

    clear_history(tmp_path, keep_last=0, apply=True)
    assert not relatorio.exists()
    assert video.exists()
    assert (arquivado / 'README.md').exists()


# cenario: init mantem o storage versionado e ignora so a pasta de videos
def test_init_mantem_o_storage_versionado_e_ignora_so_a_pasta_de_videos(tmp_path: Path):
    initialize_project(tmp_path)
    gitignore = (tmp_path / '.gitignore').read_text(encoding='utf-8')
    assert '.sentry/video/' in gitignore
    assert '.sentry/media/' not in gitignore
    assert '.sentry/storage' not in gitignore


# cenario: modulo aponta para spec inexistente e recusado
def test_modulo_aponta_para_spec_inexistente_e_recusado(tmp_path: Path, monkeypatch, capsys):
    from sentrytest import cli
    from sentrytest.application.analyze import analyze
    initialize_project(tmp_path)
    with pytest.raises(FileNotFoundError) as erro:
        analyze(tmp_path, ['spec-que-nao-existe'], run_tests=False)
    assert 'spec-que-nao-existe' in str(erro.value)

    # Pela CLI o mesmo erro vira saida de infraestrutura, nao rastreamento cru:
    # "nao consegui medir" e' diferente de "medi e reprovei".
    monkeypatch.chdir(tmp_path)
    (tmp_path / 'sentry.toml').write_text(
        '[project]\nname = "demo"\n\n[modules]\nmodulo-usuarios = ["spec-que-nao-existe"]\n',
        encoding='utf-8')
    assert cli.main(['archive', 'modulo-usuarios', '--version', '1.0.1']) == 3
    assert 'spec-que-nao-existe' in capsys.readouterr().out
