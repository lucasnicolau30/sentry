from __future__ import annotations
import ast
import re
from pathlib import Path
from .traceability import DEFAULT_TEST_PATHS, collect_test_files

SOURCE_EXTENSIONS = {".py", ".js", ".jsx", ".ts", ".tsx", ".java", ".kt", ".kts", ".cs", ".go", ".rs", ".php"}
TEST_PATTERNS = ("test_", ".test.", ".spec.", "_test.", "_spec.")
# Diretorios que existem no caminho mas nao no nome importavel: `src/pkg/mod.py`
# e importado como `pkg.mod`. Sem descartar o prefixo, nenhum teste de projeto com
# layout src/ -- a convencao Python padrao -- casa com o que mudou.
SOURCE_ROOTS = ("src", "lib", "app")

def _module_names(path: str) -> set[str]:
    file = Path(path)
    parts = file.with_suffix("").as_posix().split("/")
    names = {".".join(parts), file.stem}
    if len(parts) > 1 and parts[0] in SOURCE_ROOTS:
        names.add(".".join(parts[1:]))
    return names

def _imports(path: Path) -> set[str]:
    text = path.read_text(encoding="utf-8")
    if path.suffix == ".py":
        tree = ast.parse(text)
        values = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                values.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                values.add(node.module)
        return values
    values = set(re.findall(r"(?:from|import|use)\s+['\"]?([A-Za-z0-9_./-]+)", text))
    values.update(re.findall(r"require\(\s*['\"]([^'\"]+)['\"]\s*\)", text))
    values.update(re.findall(r"(?:package|namespace)\s+([A-Za-z0-9_.]+)", text))
    return values

def _is_test(path: Path) -> bool:
    name = path.name.lower()
    return name.startswith("test_") or any(pattern in name for pattern in TEST_PATTERNS[1:])

def _path_segments(value: str) -> set[str]:
    return {segment for segment in re.split(r"[./]", value) if segment}

def _related(module: str, imported: str) -> bool:
    if "/" in module or "/" in imported:
        return bool(_path_segments(module) & _path_segments(imported))
    return module == imported or imported.startswith(module + ".") or module.startswith(imported + ".")

def select_impacted_tests(root: Path, changed_files: tuple[str, ...], executed: bool = False,
                          test_paths: tuple[str, ...] = DEFAULT_TEST_PATHS) -> dict:
    changed_sources = [name for name in changed_files if Path(name).suffix.lower() in SOURCE_EXTENSIONS]
    changed_modules = set().union(*(_module_names(name) for name in changed_sources)) if changed_sources else set()
    impacted = []
    unrelated = []
    limitations = []
    # Mesma coleta da matriz de casos, e' o que impede o relatorio de se
    # contradizer: varrendo um `tests/` fixo, o impacto declarava "nenhum arquivo
    # de teste encontrado" no mesmo relatorio em que a matriz associava um teste
    # que o projeto guarda ao lado do codigo, via [tests] paths.
    found = collect_test_files(root, test_paths)
    for path in found:
        if not _is_test(path):
            continue
        try:
            imports = _imports(path)
            related = any(_related(module, imported) for module in changed_modules for imported in imports)
            item = {"path": str(path.relative_to(root)), "related": related, "executed": executed}
            (impacted if related else unrelated).append(item)
        except (OSError, SyntaxError) as error:
            limitations.append(f"{path.relative_to(root)}: {error}")
    if changed_files and not changed_sources:
        limitations.append("arquivos alterados nao possuem extensao suportada")
    elif changed_sources and not found:
        # Nomear onde se procurou transforma um zero mudo em algo acionavel: ou o
        # projeto guarda os testes noutro lugar, ou a declaracao esta errada.
        limitations.append(f"nenhum arquivo de teste encontrado em: {', '.join(test_paths) or '(nenhum caminho declarado)'}")
    return {"impacted": impacted, "unrelated": unrelated, "limitations": limitations}
