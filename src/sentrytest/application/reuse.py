"""Reuso de evidência entre execuções: o modo instantâneo e o cache por hash.

Duas alavancas de tempo, uma regra só: evidência reaproveitada nunca pode se
apresentar como medida agora. Por isso toda função daqui devolve, junto do dado
reusado, a procedência (`run_id` e `timestamp`) da execução de onde ele veio — é
o que permite ao relatório acusar a idade, em vez de deixar um número velho
passar por medição nova. Reusar sem dizer transformaria evidência velha em
afirmação nova, que é a mesma armadilha do relatório que envelhece sem avisar.

A terceira alavanca óbvia — rodar só os testes que a análise de impacto marca —
foi medida e descartada: cortar 60% da suíte economizou 0,9 s, porque os testes
lentos *são* os impactados (sobem processos de verdade, e é isso que os torna
caros e relevantes ao mesmo tempo). O que sobra é não reexecutar quando nada
mudou, e não executar teste nenhum no loop de digitação.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

from ..ports.inputs import GitChange, TestExecution
from .traceability import DEFAULT_TEST_PATHS, collect_test_files

# O modo é consequência de executar ou não a suíte, e é o que decide o que o
# relatório pode afirmar sobre cobertura.
COMPLETE = "completo"
INSTANT = "instantâneo"

COVERAGE_UNAVAILABLE = "sem execução completa anterior: não há cobertura a reaproveitar"


def _configuration(payload: dict) -> dict:
    return (payload.get("data") or {}).get("configuration") or {}


def provenance(payload: dict) -> dict:
    """De qual execução veio o dado reusado, e de quando ela é.

    O instante importa tanto quanto o identificador: sem ele o leitor não
    distingue evidência de cinco minutos atrás de evidência de cinco dias atrás,
    e as duas sustentam decisões muito diferentes.
    """
    data = payload.get("data") or {}
    return {"run_id": data.get("id"), "timestamp": data.get("timestamp")}


def _executed_the_suite(payload: dict) -> bool:
    """A execução registrada rodou a suíte de verdade?

    Três recusas, e cada uma evita reusar uma não-medição:

    - sem `run_tests` nunca houve suíte, só a estrutura da mudança;
    - com `from_cache` a execução é ela mesma um reuso, e apontar para ela
      esconderia atrás de um intermediário a execução que de fato mediu —
      a procedência tem de nomear a origem, não o último elo da corrente;
    - com erro de infraestrutura o processo até subiu, mas nada foi contado, e
      reusar isso seria reusar a ausência de evidência como se fosse evidência.
    """
    configuration = _configuration(payload)
    if not configuration.get("run_tests") or configuration.get("from_cache"):
        return False
    execution = configuration.get("test_execution") or {}
    return bool(execution) and not execution.get("infrastructure_error")


def last_executed_run(runs: list[dict]) -> dict | None:
    """A execução mais recente que rodou a suíte, ou None se nunca houve uma.

    `load_runs` devolve em ordem de inserção, então a mais recente que serve é a
    última da lista a passar no critério.
    """
    for payload in reversed(list(runs)):
        if _executed_the_suite(payload):
            return payload
    return None


def reused_coverage(runs: list[dict]) -> dict:
    """O bloco `coverage` do modo instantâneo, sempre marcado com a origem.

    Sem execução anterior o bloco continua existindo, com `reused_from` nulo e
    número nenhum: chave omitida deixaria o leitor sem saber se o Sentry não
    mediu ou se não olhou — a mesma distinção entre "não coberto" e "não
    verificado" que o resto do produto faz questão de manter.
    """
    payload = last_executed_run(runs)
    if payload is None:
        return {"global_percent": None, "changed_percent": None, "files": {},
                "error": COVERAGE_UNAVAILABLE, "executed_lines": {}, "measured_lines": {},
                "reused_from": None}
    coverage = _configuration(payload).get("coverage") or {}
    # As linhas vêm junto dos percentuais: é delas que sai o recorte de "o que ainda não
    # tem evidência", e entregar o número sem as linhas daria ao consumidor um total sem
    # nenhum lugar onde agir. Elas envelhecem exatamente como o percentual, e a mesma
    # marca de procedência serve para as duas coisas.
    return {"global_percent": coverage.get("global_percent"),
            "changed_percent": coverage.get("changed_percent"),
            "files": coverage.get("files") or {},
            "error": coverage.get("error"),
            "executed_lines": coverage.get("executed_lines") or {},
            "measured_lines": coverage.get("measured_lines") or {},
            "reused_from": provenance(payload)}


def _content_digest(path: Path) -> str:
    """Resumo do conteúdo do arquivo, em bytes.

    Bytes e não texto: o hash não decide nada sobre codificação, e um arquivo
    binário ou com byte inválido não pode derrubar a análise. Arquivo ilegível
    (apagado pela mudança, típico do status `D`) tem resumo próprio — ele volta a
    diferir assim que o arquivo reaparecer.
    """
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return "ausente"


def _label(root: Path, path: Path) -> str:
    """O arquivo pelo caminho relativo à raiz. Absoluto amarraria o hash ao
    diretório em que o projeto está: mover a pasta invalidaria um cache que
    descreve exatamente o mesmo conteúdo."""
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def input_fingerprint(root: Path, change: GitChange,
                      test_paths: tuple[str, ...] = DEFAULT_TEST_PATHS,
                      spec_paths: tuple[Path, ...] = ()) -> str:
    """A impressão do que decide se a execução completa anterior ainda serve.

    Três entradas, e nada além delas: o diff, os arquivos de teste e as specs.
    Mudou qualquer uma, a execução anterior deixou de descrever esta situação —
    ou o código é outro, ou o que se cobra dele é outro.

    O diff entra pelo conteúdo dos arquivos que ele lista, não pelo texto do
    `git diff`. Dois motivos: o texto bruto carrega os artefatos que o próprio
    Sentry escreve — neste repositório `.sentry/reports/latest.md` é versionado e
    muda de identificador a cada execução, o que faria o hash nunca repetir e o
    cache nunca acertar —, enquanto `statuses` já vem filtrado desses artefatos;
    e o conteúdo é mais preciso que as faixas de linha, que não distinguem duas
    edições diferentes na mesma linha.

    Revisão e base entram junto: com a mesma árvore mas outro commit, a evidência
    anterior fala de outro ponto da história, e é o commit que o relatório carimba.
    """
    digest = hashlib.sha256()
    digest.update(f"revisao:{change.revision}\nbase:{change.reference}\n".encode())
    for name, status in sorted((change.statuses or {}).items()):
        digest.update(f"diff:{name}:{status}:{_content_digest(root / name)}\n".encode())
    for path in sorted(collect_test_files(root, test_paths)):
        digest.update(f"teste:{_label(root, path)}:{_content_digest(path)}\n".encode())
    for path in sorted(spec_paths):
        digest.update(f"spec:{_label(root, path)}:{_content_digest(path)}\n".encode())
    return digest.hexdigest()


def cached_run(runs: list[dict], fingerprint: str, change: GitChange) -> dict | None:
    """A execução completa que ainda descreve esta entrada, ou None para rodar a suíte.

    Sem diff legível não há acerto possível. Fora de um repositório Git o Sentry
    não enxerga qual arquivo de código mudou, e o hash passaria a depender só de
    testes e specs: editar o código não invalidaria nada e o veredito falaria de
    um código que ninguém leu. Repetir a suíte é caro; afirmar sobre código não
    visto é pior.

    Sem execução anterior o cache simplesmente não acerta — inventar acerto onde
    não há evidência a reusar seria o contrário do que este produto faz.
    """
    if change.error or not change.revision:
        return None
    for payload in reversed(list(runs)):
        if _executed_the_suite(payload) and _configuration(payload).get("input_hash") == fingerprint:
            return payload
    return None


def cached_execution(payload: dict) -> TestExecution:
    """A contagem da execução reaproveitada, no formato que o adapter devolveria.

    As regras julgam `TestExecution`, não dicionário: reconstruir aqui é o que
    faz o veredito do acerto de cache sair idêntico ao da execução original, em
    vez de depender de um caminho paralelo de avaliação.
    """
    execution = _configuration(payload).get("test_execution") or {}
    return TestExecution(execution.get("command", ""), passed=execution.get("passed", 0),
                         failed=execution.get("failed", 0), skipped=execution.get("skipped", 0),
                         not_run=execution.get("not_run", 0), output=execution.get("output", ""),
                         infrastructure_error=execution.get("infrastructure_error"),
                         status=execution.get("status"),
                         duration_seconds=execution.get("duration_seconds", 0.0))
