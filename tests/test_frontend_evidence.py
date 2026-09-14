"""Evidência de execução do Playwright: trace e screenshot anexados por cenário.

Nunca cobertura de linha -- não existe para o frontend. O vínculo é o marcador
`// cenario:` que precede o `test()`/`it()`, cruzado com o título que o
relatório JUnit do Playwright publica por teste.
"""
from __future__ import annotations

from pathlib import Path

from sentrytest.application.frontend_evidence import evidence_by_case, junit_attachments, marker_titles

JUNIT = """<testsuites tests="2" failures="0">
<testsuite name="home.spec.ts" tests="2">
<testcase name="mostra o titulo" classname="home.spec.ts" time="0.7">
<system-out><![CDATA[
[[ATTACHMENT|test-results/home-mostra-o-titulo/test-finished-1.png]]

[[ATTACHMENT|test-results/home-mostra-o-titulo/trace.zip]]
]]></system-out>
</testcase>
<testcase name="abre o menu" classname="home.spec.ts" time="0.5">
</testcase>
</testsuite>
</testsuites>"""

SPEC_TS = """import { test, expect } from "@playwright/test";

// cenario: landing mostra o titulo
test("mostra o titulo", async ({ page }) => {
  await page.goto("/");
});

test("abre o menu sem marcador", async ({ page }) => {
  await page.goto("/");
});
"""


def _write(tmp_path: Path, name: str, content: str) -> Path:
    path = tmp_path / name
    path.write_text(content, encoding="utf-8")
    return path


# cenario: marcador cenario em arquivo ts vincula caso ao teste playwright
def test_marcador_cenario_em_arquivo_ts_vincula_caso_ao_teste_playwright(tmp_path: Path):
    spec = _write(tmp_path, "home.spec.ts", SPEC_TS)
    titles = marker_titles([spec])
    assert titles == {"landing mostra o titulo": "mostra o titulo"}


def test_marcador_sem_test_nas_linhas_seguintes_nao_e_associado(tmp_path: Path):
    spec = _write(tmp_path, "solto.spec.ts", "// cenario: sem teste correspondente\n\n\n\ntest(\"outro\", () => {});\n")
    assert marker_titles([spec]) == {}


def test_junit_attachments_le_anexos_do_system_out(tmp_path: Path):
    report = _write(tmp_path, "junit.xml", JUNIT)
    attachments = junit_attachments(report)
    assert attachments["mostra o titulo"] == (
        "test-results/home-mostra-o-titulo/test-finished-1.png",
        "test-results/home-mostra-o-titulo/trace.zip",
    )
    assert "abre o menu" not in attachments


# cenario: sem relatorio junit a evidencia sai vazia sem inventar caminho
def test_sem_relatorio_junit_a_evidencia_sai_vazia_sem_inventar_caminho(tmp_path: Path):
    assert junit_attachments(tmp_path / "nao-existe.xml") == {}


def test_junit_corrompido_a_evidencia_sai_vazia_sem_lancar_excecao(tmp_path: Path):
    report = _write(tmp_path, "quebrado.xml", "<testsuites><testcase sem fechar")
    assert junit_attachments(report) == {}


def test_arquivo_ilegivel_e_ignorado_sem_derrubar_a_busca(tmp_path: Path):
    ilegivel = tmp_path / "binario.spec.ts"
    ilegivel.write_bytes(b"\xff\xfe\x00\x01\x02")
    assert marker_titles([ilegivel]) == {}


# cenario: evidencia de trace e screenshot e anexada ao caso quando o teste passou
def test_evidencia_de_trace_e_screenshot_e_anexada_ao_caso_quando_o_teste_passou(tmp_path: Path):
    spec = _write(tmp_path, "home.spec.ts", SPEC_TS)
    report = _write(tmp_path, "junit.xml", JUNIT)
    evidencia = evidence_by_case(report, [spec])
    assert evidencia == {"landing mostra o titulo": (
        "test-results/home-mostra-o-titulo/test-finished-1.png",
        "test-results/home-mostra-o-titulo/trace.zip",
    )}
