"""Arquivo visual por rota.

`sentry archive` ganha um segundo modo: em vez de empacotar evidência de uma
suíte já escrita, ele fotografa rotas declaradas em `[modules.<nome>]` --
mesmo que o módulo nunca tenha sido testado pelo Sentry. Login (quando
`login = true`) é feito uma vez, com seletores declarados em
`[archive.login]` e credenciais só em variável de ambiente. Specs opcionais
dentro do próprio módulo certificam o resultado; sem elas, o README avisa que
é registro visual, não certificação.
"""
import json
from pathlib import Path

import pytest

from sentrytest.application import archive as archive_module
from sentrytest.application.archive import (
    is_route_module, module_requires_login, module_route_specs, module_routes,
    render_readme_rotas, resolve_credentials, resolve_login, storage_path,
    write_archive_rotas)
from sentrytest.init_project import initialize_project


def manifesto(rotas=("/login", "/usuarios")):
    return {"rotas": [
        {"rota": rota, "slug": rota.strip("/").replace("/", "-") or "raiz",
         "arquivos": ["desktop.png", "mobile.png"]}
        for rota in rotas
    ], "erro": None}


def payload_aprovado():
    return {"data": {"id": "r1", "commit": "a94b1fb00000aa",
                     "timestamp": "2026-09-22T10:30:45+00:00",
                     "verdict": {"status": "aprovado"}}}


# cenario: modulo declarado por rotas fotografa cada rota numa pasta propria
def test_modulo_declarado_por_rotas_fotografa_cada_rota_numa_pasta_propria(tmp_path: Path, monkeypatch):
    modulo_config = {"rotas": ["/login", "/usuarios"]}
    chamadas = {}

    def fake_capture_routes(root, routes, *, login, destino, base_url, gravar_video, node_bin="node"):
        chamadas["routes"] = routes
        for rota in routes:
            slug = rota.strip("/").replace("/", "-") or "raiz"
            (destino / slug).mkdir(parents=True, exist_ok=True)
            (destino / slug / "desktop.png").write_bytes(b"png")
            (destino / slug / "mobile.png").write_bytes(b"png")
        return manifesto(routes)

    monkeypatch.setattr(archive_module, "capture_routes", fake_capture_routes)
    destino, houve_falha = write_archive_rotas(tmp_path, "usuarios", "1.0.0", modulo_config, {})

    assert houve_falha is False
    assert chamadas["routes"] == ["/login", "/usuarios"]
    assert (destino / "login").is_dir()
    assert (destino / "usuarios").is_dir()
    assert (destino / "README.md").exists()


# cenario: cada rota fotografada gera print em desktop e mobile
def test_cada_rota_fotografada_gera_print_em_desktop_e_mobile(tmp_path: Path, monkeypatch):
    modulo_config = {"rotas": ["/login"]}

    def fake_capture_routes(root, routes, *, login, destino, base_url, gravar_video, node_bin="node"):
        (destino / "login").mkdir(parents=True, exist_ok=True)
        (destino / "login" / "desktop.png").write_bytes(b"png")
        (destino / "login" / "mobile.png").write_bytes(b"png")
        return manifesto(["/login"])

    monkeypatch.setattr(archive_module, "capture_routes", fake_capture_routes)
    destino, _ = write_archive_rotas(tmp_path, "acesso", "1.0.0", modulo_config, {})

    assert (destino / "login" / "desktop.png").exists()
    assert (destino / "login" / "mobile.png").exists()


# cenario: modulo sem specs e registro visual sem certificacao
def test_modulo_sem_specs_e_registro_visual_sem_certificacao(tmp_path: Path, monkeypatch):
    modulo_config = {"rotas": ["/usuarios"]}
    monkeypatch.setattr(archive_module, "capture_routes",
                        lambda *a, **k: manifesto(["/usuarios"]))
    destino, _ = write_archive_rotas(tmp_path, "usuarios", "1.0.0", modulo_config, {})

    readme = (destino / "README.md").read_text(encoding="utf-8")
    assert "sem certificação" in readme
    assert "registro visual" in readme


# cenario: modulo com specs roda a suite e carimba veredito
def test_modulo_com_specs_roda_a_suite_e_carimba_veredito(tmp_path: Path, monkeypatch):
    modulo_config = {"rotas": ["/usuarios"], "specs": ["cadastro-de-usuario"]}
    monkeypatch.setattr(archive_module, "capture_routes",
                        lambda *a, **k: manifesto(["/usuarios"]))
    destino, _ = write_archive_rotas(tmp_path, "usuarios", "1.0.0", modulo_config, {},
                                     payload=payload_aprovado())

    readme = (destino / "README.md").read_text(encoding="utf-8")
    assert "Veredito: Aprovado" in readme
    assert "sem certificação" not in readme


# cenario: modulo com specs e reprovado nao arquiva nada
def test_modulo_com_specs_e_reprovado_nao_arquiva_nada(tmp_path: Path, monkeypatch, capsys):
    from sentrytest import cli
    monkeypatch.chdir(tmp_path)
    initialize_project(tmp_path)
    (tmp_path / "sentry.toml").write_text(
        '[project]\nname = "demo"\n\n[modules.usuarios]\nrotas = ["/usuarios"]\nspecs = ["cadastro-de-usuario"]\n',
        encoding="utf-8")

    class RunFalso:
        id = "r1"
        verdict = type("V", (), {"status": type("S", (), {"value": "reprovado"})()})()
        infrastructure_errors = ()

    monkeypatch.setattr(cli, "analyze", lambda *a, **k: RunFalso())
    monkeypatch.setattr(cli, "to_json", lambda run: json.dumps(
        {"data": {"id": "r1", "verdict": {"status": "reprovado"}}}))
    codigo = cli.main(["archive", "usuarios", "--version", "1.0.0"])

    assert codigo == 2
    assert "nada foi arquivado" in capsys.readouterr().out
    assert not (storage_path(tmp_path) / "usuarios-1.0.0").exists()


# cenario: modulo com login true autentica antes de fotografar
def test_modulo_com_login_true_autentica_antes_de_fotografar(tmp_path: Path, monkeypatch):
    modulo_config = {"rotas": ["/usuarios"], "login": True}
    config = {"archive": {"login": {"rota": "/login", "usuario": "#email",
                                    "senha": "#senha", "enviar": "button[type=submit]"}}}
    monkeypatch.setenv("SENTRY_LOGIN_USUARIO", "dev@example.com")
    monkeypatch.setenv("SENTRY_LOGIN_SENHA", "segredo123")
    recebido = {}

    def fake_capture_routes(root, routes, *, login, destino, base_url, gravar_video, node_bin="node"):
        recebido["login"] = login
        return manifesto(["/usuarios"])

    monkeypatch.setattr(archive_module, "capture_routes", fake_capture_routes)
    write_archive_rotas(tmp_path, "usuarios", "1.0.0", modulo_config, config)

    assert recebido["login"] == config["archive"]["login"]


# cenario: modulo sem login true nao tenta autenticar
def test_modulo_sem_login_true_nao_tenta_autenticar(tmp_path: Path, monkeypatch):
    modulo_config = {"rotas": ["/usuarios"]}
    recebido = {}

    def fake_capture_routes(root, routes, *, login, destino, base_url, gravar_video, node_bin="node"):
        recebido["login"] = login
        return manifesto(["/usuarios"])

    monkeypatch.setattr(archive_module, "capture_routes", fake_capture_routes)
    write_archive_rotas(tmp_path, "usuarios", "1.0.0", modulo_config, {})

    assert recebido["login"] is None


# cenario: login true sem configuracao de login declarada e recusado
def test_login_true_sem_configuracao_de_login_declarada_e_recusado(tmp_path: Path):
    modulo_config = {"rotas": ["/usuarios"], "login": True}
    with pytest.raises(ValueError) as erro:
        write_archive_rotas(tmp_path, "usuarios", "1.0.0", modulo_config, {})
    assert "[archive.login]" in str(erro.value)
    assert not (storage_path(tmp_path) / "usuarios-1.0.0").exists()


# cenario: login true sem credenciais em variavel de ambiente e recusado
def test_login_true_sem_credenciais_em_variavel_de_ambiente_e_recusado(tmp_path: Path, monkeypatch):
    modulo_config = {"rotas": ["/usuarios"], "login": True}
    config = {"archive": {"login": {"rota": "/login", "usuario": "#email",
                                    "senha": "#senha", "enviar": "button[type=submit]"}}}
    monkeypatch.delenv("SENTRY_LOGIN_USUARIO", raising=False)
    monkeypatch.delenv("SENTRY_LOGIN_SENHA", raising=False)
    with pytest.raises(ValueError) as erro:
        write_archive_rotas(tmp_path, "usuarios", "1.0.0", modulo_config, config)
    assert "SENTRY_LOGIN_USUARIO" in str(erro.value)
    assert "SENTRY_LOGIN_SENHA" in str(erro.value)


# cenario: credenciais de login nunca sao gravadas no toml
def test_credenciais_de_login_nunca_sao_gravadas_no_toml(tmp_path: Path, monkeypatch):
    modulo_config = {"rotas": ["/usuarios"], "login": True}
    config = {"archive": {"login": {"rota": "/login", "usuario": "#email",
                                    "senha": "#senha", "enviar": "button[type=submit]"}}}
    monkeypatch.setenv("SENTRY_LOGIN_USUARIO", "dev@example.com")
    monkeypatch.setenv("SENTRY_LOGIN_SENHA", "segredo-super-secreto")
    (tmp_path / "sentry.toml").write_text('[project]\nname = "demo"\n', encoding="utf-8")

    monkeypatch.setattr(archive_module, "capture_routes",
                        lambda *a, **k: manifesto(["/usuarios"]))
    destino, _ = write_archive_rotas(tmp_path, "usuarios", "1.0.0", modulo_config, config)

    assert "segredo-super-secreto" not in (tmp_path / "sentry.toml").read_text(encoding="utf-8")
    assert "segredo-super-secreto" not in (destino / "README.md").read_text(encoding="utf-8")


# cenario: rota que falha vira ressalva sem derrubar o arquivo
def test_rota_que_falha_vira_ressalva_sem_derrubar_o_arquivo(tmp_path: Path, monkeypatch, capsys):
    from sentrytest import cli
    monkeypatch.chdir(tmp_path)
    initialize_project(tmp_path)
    (tmp_path / "sentry.toml").write_text(
        '[project]\nname = "demo"\n\n[modules.usuarios]\nrotas = ["/usuarios", "/rota-que-nao-existe"]\n',
        encoding="utf-8")

    def fake_capture_routes(root, routes, *, login, destino, base_url, gravar_video, node_bin="node"):
        (destino / "usuarios").mkdir(parents=True, exist_ok=True)
        (destino / "usuarios" / "desktop.png").write_bytes(b"png")
        (destino / "usuarios" / "mobile.png").write_bytes(b"png")
        return {"rotas": [
            {"rota": "/usuarios", "slug": "usuarios", "arquivos": ["desktop.png", "mobile.png"]},
            {"rota": "/rota-que-nao-existe", "slug": "rota-que-nao-existe", "arquivos": [],
             "erro": "net::ERR_ABORTED"},
        ], "erro": None}

    monkeypatch.setattr(archive_module, "capture_routes", fake_capture_routes)
    codigo = cli.main(["archive", "usuarios", "--version", "1.0.0"])

    assert codigo == 1
    saida = capsys.readouterr().out
    assert "ressalvas" in saida
    destino = storage_path(tmp_path) / "usuarios-1.0.0"
    assert (destino / "usuarios" / "desktop.png").exists()
    readme = (destino / "README.md").read_text(encoding="utf-8")
    assert "falhou" in readme


# cenario: modulo declarado por lista de specs continua como antes
def test_modulo_declarado_por_lista_de_specs_continua_como_antes():
    assert is_route_module(["cadastro-de-usuario", "login"]) is False
    assert is_route_module({"rotas": ["/usuarios"]}) is True
    assert is_route_module(None) is False
