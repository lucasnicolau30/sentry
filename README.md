# Sentry

English · [Português (Brasil)](README.pt-BR.md)

[![Python](https://img.shields.io/badge/Python-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
![pytest](https://img.shields.io/badge/pytest-0A9EDC?style=flat&logo=pytest&logoColor=white)
[![PyPI](https://img.shields.io/pypi/v/sentry-test.svg?style=flat&label=PyPI&color=3775A9&logo=pypi&logoColor=white)](https://pypi.org/project/sentry-test/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat)](LICENSE)

Change-oriented test quality CLI. `sentry` creates the spec folder, validates the case matrix in markdown, runs the suite, reads the diff and the coverage, and issues an auditable verdict — and writes the workflow down for the AI agent that will implement the change.

Markdown is the source of intent: the CLI parses and validates `CASES.md` and `PROMPT.md` — it never writes them. The AI agent does the drafting; Sentry guarantees structure, traceability and a verdict.

> Not to be confused with [getsentry's Sentry](https://sentry.io) (error monitoring). This project is distributed as `sentry-test`.

## The division of responsibility

- **The AI agent declares intent** — writes `CASES.md`: requirement, layer, type, priority, input, expected result.
- **Sentry measures reality** — decides status, associated test, evidence and verdict.

The agent never writes status. Sentry never calls a model. That's what makes the verdict auditable and reproducible.

## Installation

```bash
pip install sentry-test
```

Requires Python 3.11+. Check with `sentry --version` (prints the package version).

If `pytest` or `coverage` are missing, `init` warns you. To install them too:

```bash
sentry init --install
```

## Setup

```bash
cd your-project
sentry init
```

Creates `.sentry/` (specs, runs, reports and database), `sentry.toml`, the `.gitignore` entries, and writes the workflow in two places:

- **`sentry-cases` skill** at `.claude/skills/sentry-cases/SKILL.md` — loaded automatically by Claude Code and by agents that follow this convention.
- **`AGENT-SENTRY.md`** at the project root — the same workflow in plain markdown, without depending on any tool's convention.

For other agents (Cursor, Windsurf, Codex, opencode), point them to `AGENT-SENTRY.md` from the rules file each one already uses — for example, a line in `.cursor/rules` or `AGENTS.md`:

```markdown
To write or review test cases, follow AGENT-SENTRY.md.
```

`init` is idempotent: it doesn't erase history, doesn't overwrite existing configuration, doesn't duplicate structures.

## The workflow

1. `sentry new "customer registration"` — creates `.sentry/specs/customer-registration/` with `PROMPT.md` (request preserved) and a blank `CASES.md`
2. **`sentry-cases`** — your agent asks about anything ambiguous and fills in `CASES.md` following the template
3. `sentry check customer-registration` — is the structure valid? are the catalog's equivalence classes covered?
4. your agent links each case to the real test with the `# scenario: <exact case name>` marker
5. `sentry run --spec customer-registration --run-tests` — runs the suite, reads diff and coverage, applies the rules, persists
6. `sentry report` / `sentry history` — read back and compare between runs

Every step also works without an agent, via the commands below.

## Commands

Exit code `0` on success; see the exit code table further down.

| Command | What it does |
| --- | --- |
| `sentry init [--install]` | Prepares the repository: `.sentry/`, `sentry.toml`, `.gitignore`, agent guide and skills. With `--install`, installs missing dependencies. |
| `sentry new <name> [--prompt "..."] [--json]` | Creates the spec folder with a slug derived from the name. `--json` emits the template, accepted vocabulary and required classes, for the agent to consume. |
| `sentry check [<slug>\|all]` | Validates `CASES.md`: structure, vocabulary and equivalence class coverage. `all` validates every spec together. |
| `sentry run [--spec <slug>\|all] [--run-tests]` | Runs the analysis and persists it. Without `--run-tests` there's no coverage, and the verdict tends toward `inconclusive`. |
| `sentry report` | Shows the latest report (`.sentry/reports/latest.md`). |
| `sentry history` | Lists runs and compares the last two: coverage, tests, new/resolved/persistent findings. |
| `sentry clear [--keep-last N] [--yes]` | Prunes old runs and reports. Without `--yes` it only shows what would be removed — deleting history is irreversible. Never touches `.sentry/specs/`. |

## Exit codes

Four distinguishable states, to separate "poorly tested code" from "my environment broke":

| Code | Meaning |
| --- | --- |
| `0` | approved |
| `1` | approved with caveats |
| `2` | rejected |
| `3` | inconclusive or infrastructure error |

An infrastructure error never produces an approved verdict: a suite that failed to run is different from a suite that failed.

`sentry check` keeps its own semantics: `0` valid structure, `1` structural errors, `2` couldn't resolve the spec.

## Skills

Generated for each configured agent; `AGENT-SENTRY.md` covers the rest.

| Workflow | What the agent does |
| --- | --- |
| `sentry-cases` | Takes the free-text request, creates the spec, **asks before writing** anything ambiguous that would change a case, fills in `CASES.md`, links each case to a test with `# scenario:` and runs `check` until it closes clean. Never writes status. |

## Deterministic rules

Ten rules, with severity configurable per project.

| Rule | Default severity | Triggers when |
| --- | --- | --- |
| `test-failing` | critical | the suite has a failing test |
| `case-spec-invalid` | critical | `CASES.md` has a structural error |
| `changed-code-uncovered` | high | changed code coverage is zero |
| `scenario-without-test` | high | a declared case has no associated test |
| `error-path-without-test` | high | a `raise`/`throw` on a changed line that no test executed |
| `missing-equivalence-class` | high | a class required by the catalog that no case covers |
| `coverage-below-threshold` | high | changed code coverage below the declared threshold |
| `requirement-without-scenario` | medium | a requirement with no matching scenario |
| `coverage-missing` | medium | changed code coverage couldn't be calculated |
| `global-coverage-below-threshold` | medium | global coverage below the declared threshold |

Without a declared threshold, Sentry doesn't invent a minimum. The project decides what's "enough", and the report records the number applied.

## Equivalence class catalog

A fixed table of situations that need a test, **per field type**. It doesn't generate cases: it flags the ones the agent left undeclared.

Known types: `cpf`, `cnpj`, `email`, `senha` (password), `data` (date), `telefone` (phone), `cep` (postal code), `inteiro` (integer), `decimal`, `texto` (text), `rota` (route).

A class that doesn't make sense for a field can be dismissed **with a justification**, instead of becoming an artificial case or an eternal complaint:

```markdown
## Classes não aplicáveis

- **exclude/tamanho-maximo-excedido**: it's a configuration parameter, not a form field
```

The dismissal removes the finding, but it stays recorded in the report — nothing disappears silently.

## Coverage dimensions

Each one reports `covered`, `partial`, `not covered` or `not applicable`, with evidence.

| Dimension | Where the evidence comes from |
| --- | --- |
| requirements and business rules | spec scenarios with an associated test |
| APIs, persistence, transactions and integrations | `contract`/`integration`-type cases and `integration` layer |
| exceptions, resilience and recovery | changed error paths executed by some test |
| security and authorization | `route`-type fields with all access classes covered |

`not applicable` is distinct from `not covered`: a project with no routes isn't penalized on the security dimension.

## Configuration

`sentry.toml` at the root, versionable, with no secrets. Everything beyond what `init` already writes is optional.

```toml
[project]
name = "my-project"

[specs]
path = ".sentry/specs"

[test]                    # any runner that exports JUnit XML
command = "npx jest"
junit_xml = "reports/junit.xml"   # required outside pytest: it's the only source of counts

[tests]                   # where to look for tests
paths = ["tests"]         # default: tests, test, spec, __tests__

[coverage]                # report generated by your own suite
path = "coverage/lcov.info"
format = "lcov"           # optional: detected by content when omitted

[analysis]
run_tests_by_default = false
timeout_seconds = 300
exclude = ["frontend/"]   # directories out of the analysis scope

[policy.thresholds]       # without this, no minimum is enforced
changed_coverage = 85
global_coverage = 90

[policy.severities]       # overrides the severity of any rule
coverage-missing = "high"

[catalog.fields]          # field types from your own domain
matricula = ["empty", "invalid-format", "valid"]

[dimensions]              # axes that don't apply to the project
disabled = []
```

`.sentry/` holds specs, runs, reports and the database. It stays out of Git, with one deliberate exception: `.sentry/reports/latest.md` is versioned, so the verdict shows up in the PR diff without the reviewer having to run Sentry.

History is kept indefinitely, and grows with every run. To prune it:

```bash
sentry clear --keep-last 10        # shows what would be removed
sentry clear --keep-last 10 --yes  # removes it
```

Specs are never removed: they're declared intent, not generated evidence.

## Supported stacks

**Derivation** — from the request to the case matrix — is language-agnostic: `CASES.md` is markdown and the catalog reasons about data type, not code.

**Verification** depends on the exchange format your suite exports, not on the tool:

| Capability | Support |
| --- | --- |
| Suite execution | any command that exports **JUnit XML** — pytest, Jest, Vitest, `go test` (gotestsum), Surefire, `dotnet test`, RSpec, PHPUnit |
| Coverage | **lcov** (nyc, c8, Jest, simplecov), **Cobertura XML** (JaCoCo, coverlet), **coverage.py** (JSON) — detected by content |
| Case↔test traceability | `.py`, `.js`/`.jsx`/`.ts`/`.tsx`, `.go`, `.java`/`.kt`, `.cs`, `.rb`, `.php`, `.rs` — and the `scenario:` marker works in any comment |
| Error paths | via AST in Python; via syntactic pattern (`throw`, `catch`, `panic`, `rescue`, `panic!`) in the rest |
| Impact analysis | 12 source-code extensions |

Error path detection outside Python is less precise than AST, and the report records that difference as a limitation — it never hides it.

In Python, **pytest** is the only runner instrumented automatically: Sentry recognizes it as `pytest`, `python -m pytest`, and the venv's executable, wraps it in `coverage run` and collects the count on its own. In Django, prefer `command = "python -m pytest"` with `pytest-django` over `manage.py test`. Any other command — including `python -m unittest` — runs **exactly as declared**, with no flag injected: to measure it, declare the `junit_xml` your suite generates, otherwise the verdict comes out `not executed` for lack of evidence.

The `frontend` layer is rejected on purpose: without an adapter to verify it, a declared case would stay stuck as `not covered` forever.

## Local-first

No telemetry, no external calls, no code or diff ever sent anywhere. All history stays on the machine.

## Development

```bash
python -m pip install -e .
python -m pytest
```

Sentry analyzes itself: `sentry run --spec all --run-tests` at the root of the
repository matches the cases declared in `.sentry/specs/` against the real
test functions and reports the four dimensions.

## License

MIT
