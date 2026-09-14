from __future__ import annotations
import re
import unicodedata
from pathlib import Path
from ..ports.inputs import SpecScenario

# O marcador nao ancora num comentario de linguagem especifica: `// cenario:`,
# `-- cenario:`, `# cenario:` e `* cenario:` casam igual, entao o vinculo declarado
# ja e' agnostico de linguagem.
#
# Ancora no inicio da linha, apos o abre-comentario: o marcador e' uma linha de
# comentario, nao texto solto. Sem a ancora, um teste que *escreve* um marcador
# noutro arquivo -- `write_text("# cenario: x\n", encoding="utf-8")` -- ou que o monta
# num template -- `f"# cenario: {nome}\n"` -- devolvia `x\n", encoding="utf-8")` e
# `{nome}\n` como nomes de cenario. Passava despercebido enquanto o marcador so servia
# para associar teste (nome impossivel nao casa com nada) e virou ruido assim que
# marcador sem caso correspondente passou a ser achado.
_MARKER = re.compile(r"^[ \t]*(?://|--|\#|\*|/\*)[ \t]*(?:scenario|cenario)\s*[:=][ \t]*([^\n]+)",
                     re.IGNORECASE | re.MULTILINE)

# Como cada stack declara um teste. Aplicado por extensao, nao a todos os
# arquivos: um `test("...")` solto em codigo Python nao deve virar nome de teste.
_PY = (re.compile(r"\bdef\s+(test_[A-Za-z0-9_]+)"),)
# Em JS/TS o nome do teste e' a string descritiva, nao um identificador -- o que
# aproxima ainda mais do nome do caso escrito em prosa no CASES.md.
_JS = (
    re.compile(r"\b(?:it|test)\s*\(\s*[\"'`]([^\"'`]+)[\"'`]"),
    re.compile(r"\bfunction\s+(test[A-Za-z0-9_]*)\s*\("),
)
_GO = (re.compile(r"\bfunc\s+(Test[A-Za-z0-9_]*)\s*\("),)
# Kotlin aceita nome entre crases com espacos: fun `rejeita slug vazio`()
_JVM = (re.compile(
    r"@Test\b[^\n]*\n(?:\s*@[^\n]*\n)*\s*(?:public\s+|private\s+|protected\s+|internal\s+)?"
    r"(?:suspend\s+)?(?:void|fun)\s+`?([A-Za-z0-9_ ]+?)`?\s*\("),)
_DOTNET = (re.compile(
    r"\[(?:Fact|Test|TestMethod|Theory)\][^\n]*\n(?:\s*\[[^\n]*\]\n)*\s*"
    r"(?:public\s+|private\s+|protected\s+)?(?:async\s+)?(?:void|Task)\s+([A-Za-z0-9_]+)\s*\("),)
_RUBY = (
    re.compile(r"\b(?:it|specify)\s+[\"']([^\"']+)[\"']"),
    re.compile(r"\bdef\s+(test_[A-Za-z0-9_]+)"),
)
_PHP = (re.compile(r"\bfunction\s+(test[A-Za-z0-9_]*)\s*\("),)
_RUST = (re.compile(r"#\[(?:tokio::)?test\][^\n]*\n\s*(?:async\s+)?fn\s+([A-Za-z0-9_]+)\s*\("),)

TEST_DEFINITIONS = {
    ".py": _PY,
    ".js": _JS, ".jsx": _JS, ".ts": _JS, ".tsx": _JS, ".mjs": _JS, ".cjs": _JS,
    ".go": _GO,
    ".java": _JVM, ".kt": _JVM, ".kts": _JVM,
    ".cs": _DOTNET,
    ".rb": _RUBY,
    ".php": _PHP,
    ".rs": _RUST,
}

# Onde procurar testes. Projeto com teste ao lado do codigo (src/foo.test.ts)
# declara [tests] paths no sentry.toml -- preferimos exigir a declaracao a
# varrer o repositorio inteiro adivinhando o que e' teste.
DEFAULT_TEST_PATHS = ("tests", "test", "spec", "__tests__")
_VENDOR = {"node_modules", ".git", "__pycache__", "vendor", "target", "dist", "build", ".venv", ".tox"}

# CamelCase vira palavras separadas antes do casefold: sem isto `TestRejeitaSlug`
# do Go e `rejeitaSlug` do Java virariam um token unico e nunca casariam.
_CAMEL = re.compile(r"(?<=[a-z0-9])(?=[A-Z])")
_TEST_PREFIX = re.compile(r"^test[_\-\s]?", re.IGNORECASE)
_STOPWORDS = {
    # artigos, preposicoes e conectivos
    "o", "a", "os", "as", "de", "da", "do", "das", "dos", "com", "para", "e", "que",
    "um", "uma", "no", "na", "nos", "nas", "the", "of", "with", "for", "and",
    # negacao e quantificadores: aparecem em quase todo nome de teste e nao
    # dizem nada sobre o comportamento. Sem remove-los, "sem X, nada acontece"
    # casa com "sem Y, nada e cobrado" so pela estrutura da frase.
    "sem", "nao", "nada", "todo", "toda", "todos", "todas", "mais", "menos",
    "ja", "so", "apenas", "ainda", "mesmo", "porem", "mas",
    "not", "no", "any", "all", "more", "less", "only", "still", "but",
    # palavras do proprio vocabulario Dado/Quando/Entao
    "dado", "quando", "entao", "given", "when", "then",
}
# 0,6 permitia que 40% do nome divergisse. Como este palpite decide status
# `coberto` -- a afirmacao mais forte do relatorio -- exige containment quase
# total de um dos lados; abaixo disso o caso sai `nao coberto`, que e' honesto.
_OVERLAP_THRESHOLD = 0.75

def _normalize(text: str) -> str:
    """casefold + remove acento: o marcador `# cenario:` e o nome do caso no
    CASES.md precisam casar mesmo se um dos dois foi digitado sem acento — sem
    isto, um marcador correto porem sem acento fica preso em 'nao coberto'."""
    stripped = unicodedata.normalize("NFKD", text.strip().casefold())
    return "".join(char for char in stripped if not unicodedata.combining(char))

def _tokenize(name: str) -> set[str]:
    # A separacao de CamelCase precisa vir antes do casefold, que apagaria a
    # fronteira entre as palavras.
    spaced = _CAMEL.sub(" ", name.replace("_", " "))
    words = re.split(r"[^\w]+", _normalize(spaced))
    return {word for word in words if word and word not in _STOPWORDS}

def _strip_test_prefix(name: str) -> str:
    """`test_rejeita_x`, `TestRejeitaX` e `testRejeitaX` viram todos `rejeita x`.
    O prefixo e' convencao do framework e nao descreve o comportamento."""
    return _TEST_PREFIX.sub("", name, count=1)

def collect_test_files(root: Path, test_paths: tuple[str, ...]) -> list[Path]:
    """Os arquivos de teste do projeto, segundo `[tests] paths`.

    Publica e' compartilhada de proposito: a matriz de casos e a analise de
    impacto precisam partir do mesmo conjunto. Enquanto o impacto varria um
    `tests/` fixo, o mesmo relatorio dizia "nenhum arquivo de teste encontrado"
    e ao mesmo tempo associava um teste que a matriz tinha achado.
    """
    found: set[Path] = set()
    for name in test_paths:
        target = root / name
        # Declarar um arquivo unico e' legitimo -- projeto com um so arquivo de
        # teste, ou recorte deliberado -- e cair fora por nao ser diretorio
        # devolveria de novo um zero silencioso.
        if target.is_file():
            if target.suffix.lower() in TEST_DEFINITIONS:
                found.add(target)
            continue
        if not target.is_dir():
            continue
        for path in target.rglob("*"):
            if path.suffix.lower() not in TEST_DEFINITIONS:
                continue
            if any(part in _VENDOR for part in path.parts):
                continue
            found.add(path)
    return sorted(found)

def _associated_tests(tests: dict[str, list[str]], scenario_name: str, test_functions: dict[str, list[str]]) -> list[str]:
    associated = []
    name = _normalize(scenario_name)
    for key, paths_for_key in tests.items():
        if key == name or key in name or name in key:
            associated.extend(paths_for_key)
    scenario_tokens = _tokenize(scenario_name)
    if scenario_tokens:
        for path, functions in test_functions.items():
            for function in functions:
                function_tokens = _tokenize(_strip_test_prefix(function))
                if not function_tokens:
                    continue
                overlap = len(scenario_tokens & function_tokens) / min(len(scenario_tokens), len(function_tokens))
                if overlap >= _OVERLAP_THRESHOLD:
                    associated.append(path)
                    break
    return sorted(set(associated))

def build_traceability(specs: tuple[SpecScenario, ...], root: Path, behaviors: tuple[str, ...] = (), issue_text_by_behavior: dict[str, str] | None = None, test_paths: tuple[str, ...] = DEFAULT_TEST_PATHS, declared_names: tuple[str, ...] | None = None, changed_test_lines: dict[str, tuple[int, ...]] | None = None) -> dict:
    issue_text_by_behavior = issue_text_by_behavior or {}
    tests: dict[str, list[str]] = {}
    marker_lines: dict[str, list[tuple[str, int]]] = {}
    test_functions: dict[str, list[str]] = {}
    for path in collect_test_files(root, test_paths):
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            # Varremos mais extensoes agora; um arquivo ilegivel no meio do
            # diretorio de testes nao pode derrubar a rastreabilidade inteira.
            continue
        relative = str(path.relative_to(root))
        for match in _MARKER.finditer(text):
            name = match.group(1).strip().strip("'\"")
            tests.setdefault(_normalize(name), []).append(relative)
            # A linha do marcador, para saber se foi esta mudanca que o escreveu.
            marker_lines.setdefault(_normalize(name), []).append(
                (relative, text.count("\n", 0, match.start()) + 1))
        functions = [name for pattern in TEST_DEFINITIONS[path.suffix.lower()] for name in pattern.findall(text)]
        if functions:
            test_functions[relative] = functions
    scenarios = []
    missing = []
    for scenario in specs:
        associated = _associated_tests(tests, scenario.name, test_functions)
        scenarios.append({"name": scenario.name, "tests": associated, "covered": bool(associated)})
        if not associated:
            missing.append(scenario.name)
    # Marcador que nao aponta para caso nenhum. Renomear um caso quebrava o vinculo em
    # silencio: o marcador continuava la, o caso caia para "nao coberto", e o relatorio
    # nao dizia por que -- um gerador de falso negativo sem rastro.
    #
    # A comparacao e' a mesma de `_associated_tests` (igualdade ou containment
    # normalizado), e nao a de tokens: o palpite por sobreposicao existe para associar
    # teste sem marcador, e usa-lo aqui perdoaria justamente o marcador errado.
    #
    # `declared_names` sao os casos declarados no projeto inteiro, nao so os da spec
    # analisada: o mesmo diretorio de testes atende todas as specs, e comparar contra
    # uma fatia acusaria de orfao todo marcador que pertence a outra.
    #
    # Sem spec declarada nao ha matriz com que comparar, e todo marcador viraria orfao.
    known = declared_names if declared_names is not None else tuple(scenario.name for scenario in specs)
    # Restrito ao marcador que esta mudanca escreveu ou editou -- a linha dele esta no
    # diff. O Sentry julga a mudanca: marcador que ja estava orfao antes de alguem
    # encostar no codigo e' divida pre-existente, e pertence ao mapa do projeto, nao ao
    # veredito desta mudanca.
    #
    # Por arquivo alterado nao basta: um repositorio que use `# cenario:` como
    # documentacao em prosa tem dezenas deles por arquivo, e tocar o arquivo por
    # qualquer motivo despejava todos no relatorio. O achado util -- o nome que acabou
    # de ser errado -- se perdia no meio, que e' o mesmo que nao existir.
    changed = {str(Path(name)): set(lines) for name, lines in (changed_test_lines or {}).items()}
    orphan_markers = []
    if known and changed:
        declared = [_normalize(name) for name in known]
        for marker, occurrences in sorted(marker_lines.items()):
            touched = sorted({path for path, line in occurrences if line in changed.get(path, ())})
            if touched and not any(marker == name or marker in name or name in marker for name in declared):
                orphan_markers.append({"marker": marker, "tests": touched})
    requirements_without_scenarios = []
    for behavior in behaviors:
        matched_scenario = any(_normalize(scenario.name) == _normalize(behavior) or _normalize(behavior) in _normalize(scenario.name) for scenario in specs)
        matched_test = bool(_associated_tests(tests, behavior, test_functions))
        if not matched_test and behavior in issue_text_by_behavior:
            matched_test = bool(_associated_tests(tests, issue_text_by_behavior[behavior], test_functions))
        if not matched_scenario and not matched_test:
            requirements_without_scenarios.append(behavior)
    return {"scenarios": scenarios, "scenarios_without_tests": missing, "requirements_without_scenarios": requirements_without_scenarios, "orphan_markers": orphan_markers}
