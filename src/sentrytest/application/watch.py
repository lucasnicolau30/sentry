"""Reavaliar ao salvar: o que transforma o Sentry de evento em estado.

Enquanto o veredito só existia quando alguém digitava o comando, a avaliação competia
com o desenvolvimento por atenção em vez de fazer parte dele. Aqui ela passa a
acontecer sozinha, e o passo que mais se repete — salvar um arquivo — é o mais barato.

Polling de mtime, sem biblioteca de watch: o pacote não tem dependência de runtime
nenhuma, e exigir uma para o comando que deveria ser o mais leve do produto trocaria
fricção de digitação por fricção de instalação.
"""
from __future__ import annotations

import time
from pathlib import Path

from ..adapters.local_tools import is_generated_artifact
from .traceability import DEFAULT_TEST_PATHS, TEST_DEFINITIONS

COMPLETO = "completo"
INSTANTANEO = "instantâneo"

# Diretórios que nunca carregam código do projeto. Varrê-los a cada meio segundo
# custaria mais que a análise que o watch existe para baratear.
_IGNORED = {".git", "node_modules", "__pycache__", ".venv", ".tox", "vendor",
            "target", "dist", "build", ".pytest_cache", ".mypy_cache"}

# A spec mora sob `.sentry/`, que é território de artefato gerado — mas ela não é
# gerada, é declarada. Editar um `CASES.md` muda o que o Sentry vai cobrar, então
# precisa acordar o watch como qualquer outro arquivo de origem.
_SPECS = ".sentry/specs/"


def _relative(path: str | Path) -> str:
    return str(path).replace("\\", "/")


def is_test_file(path: str | Path, test_paths: tuple[str, ...] = DEFAULT_TEST_PATHS) -> bool:
    """Arquivo de teste é o que tem extensão reconhecida **e** mora num dos caminhos
    declarados em `[tests] paths`. Só a extensão não basta: num projeto com testes ao
    lado do código, `src/app.py` e `src/app.test.ts` têm o mesmo peso para o disco e
    significados opostos para a suíte."""
    candidate = Path(path)
    if candidate.suffix.lower() not in TEST_DEFINITIONS:
        return False
    normalized = _relative(candidate)
    return any(declared in candidate.parts or normalized.startswith(declared.rstrip("/") + "/")
               for declared in test_paths)


def mode_for(path: str | Path, test_paths: tuple[str, ...] = DEFAULT_TEST_PATHS) -> str:
    """O modo que o arquivo salvo merece.

    Salvar código é o meio da frase: o loop de digitação precisa de resposta em menos de
    um segundo, e executar a suíte a cada tecla devolveria a fricção que o watch existe
    para tirar. Salvar um **teste** é outra coisa — é justamente aí que a mudança vira
    evidência, e evidência só sai executando.
    """
    return COMPLETO if is_test_file(path, test_paths) else INSTANTANEO


def _interessa(relative: str) -> bool:
    if relative.startswith(_SPECS):
        return relative.endswith(".md")
    if is_generated_artifact(relative):
        # Sem isto a análise gravaria em `.sentry/` e acordaria a si mesma num laço.
        return False
    return Path(relative).suffix.lower() in TEST_DEFINITIONS


def snapshot(root: Path, test_paths: tuple[str, ...] = DEFAULT_TEST_PATHS) -> dict[str, tuple[int, int]]:
    """Assinatura de cada arquivo que interessa: `(mtime em nanossegundos, tamanho)`.

    `st_mtime_ns` e não `st_mtime`: o segundo é float e, com o valor de época atual,
    já gastou a mantissa em segundos — duas escritas próximas colapsam no mesmo número
    e o salvamento passa despercebido. O tamanho entra junto porque um watch
    intermitente é pior que um watch lento: quem salva e não vê veredito volta a
    desconfiar da ferramenta, que é o hábito que este comando existe para construir.

    Não hasheamos conteúdo: ler todo o projeto a cada meio segundo custaria mais que a
    análise instantânea que o watch dispara.
    """
    found: dict[str, tuple[int, int]] = {}
    for path in root.rglob("*"):
        if any(part in _IGNORED for part in path.parts):
            continue
        relative = _relative(path.relative_to(root))
        if not _interessa(relative):
            continue
        try:
            info = path.stat()
        except OSError:
            # Arquivo removido entre o rglob e o stat: some do instantâneo seguinte,
            # que é exatamente como uma remoção deve aparecer.
            continue
        found[relative] = (info.st_mtime_ns, info.st_size)
    return found


def changed(previous: dict[str, tuple[int, int]], current: dict[str, tuple[int, int]]) -> list[str]:
    """O que mudou entre dois instantâneos: escrito, criado ou removido."""
    names = set(previous) | set(current)
    return sorted(name for name in names if previous.get(name) != current.get(name))


def watch(root: Path, on_change, *, interval: float = 0.4, iterations: int | None = None,
          test_paths: tuple[str, ...] = DEFAULT_TEST_PATHS, sleep=time.sleep) -> None:
    """Chama `on_change(arquivos, modo)` a cada salvamento.

    `iterations` limita quantas voltas dar — é o que torna o laço testável sem depender
    de tempo de parede. `None` roda até o usuário interromper.

    Quando um salvamento toca vários arquivos de uma vez, o modo mais caro vence: basta
    um teste no lote para que só a execução responda o que mudou.
    """
    previous = snapshot(root, test_paths)
    volta = 0
    while iterations is None or volta < iterations:
        volta += 1
        sleep(interval)
        current = snapshot(root, test_paths)
        alterados = changed(previous, current)
        previous = current
        if not alterados:
            continue
        modo = COMPLETO if any(is_test_file(name, test_paths) for name in alterados) else INSTANTANEO
        on_change(alterados, modo)
