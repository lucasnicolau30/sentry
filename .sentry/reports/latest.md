# Sentry Report

- Run: 769a7709-62b5-4d44-aecc-262aedca5803
- Projeto: sentry
- Veredito: **aprovado** — nenhum achado relevante — pode seguir.

## Achados

- Nenhum achado registrado.

## Contexto

- Arquivos alterados: 3
- Testes impactados: 5
- Testes não relacionados: 14
- Cenários sem teste: 0
- Cobertura global (todo o projeto): 98,07%
- Cobertura alterada (só o código desta mudança): 41,49%
- Testes: 201 passados, 0 falhos, 0 ignorados, 0 nao executados
- Duracao: 17.71 s

## Dimensões de cobertura

| Dimensão | Status | Evidência | Justificativa |
| --- | --- | --- | --- |
| requisitos e regras de negócio | coberta | 5/5 cenários da spec com teste associado | todos os itens têm evidência de cobertura |
| APIs, persistência, transações e integrações | coberta | 4/4 casos de contrato ou integração cobertos | todos os itens têm evidência de cobertura |
| exceções, resiliência e recuperação | coberta | 1/1 caminhos de erro alterados executados por algum teste | todos os itens têm evidência de cobertura |
| segurança e autorização | não aplicável | nenhum campo do tipo `rota` declarado | nada desta dimensão foi declarado ou alterado nesta análise |

## Matriz de casos

- Total: 5
- Por status: coberto=5

### Backend

- `coberto` **pytest invocado por caminho de executavel e reconhecido** (TC-04) — é reconhecido como pytest e normalizado para `-m pytest` (média, unitário) — tests\test_execution_evidence.py

### Integração

- `coberto` **comando nao-pytest sem junit declarado nao recebe a flag do pytest** (TC-01) — o comando roda exatamente como declarado, sem `--junitxml`, e o erro de (crítica, integração) — tests\test_execution_evidence.py
- `coberto` **suite nao-pytest le o junit declarado sem injetar flag** (TC-02) — a contagem vem do relatório, sem flag injetada e sem cobertura própria (alta, integração) — tests\test_execution_evidence.py
- `coberto` **pytest invocado como modulo e reconhecido** (TC-03) — é reconhecido como pytest, embrulhado em `coverage run` e a cobertura é medida (crítica, integração) — tests\test_execution_evidence.py
- `coberto` **comando vazio vira erro de infraestrutura** (TC-05) — a execução sai como não executada com erro de infraestrutura, sem exceção (alta, integração) — tests\test_execution_evidence.py

## Limitações

> O Sentry não conseguiu verificar isto — não é aprovação nem reprovação, é ausência de evidência.

- Nenhuma limitação registrada.

## Classes não aplicáveis

> Dispensadas de propósito, com justificativa declarada no CASES.md — não é lacuna do Sentry.

- comando/tamanho-maximo-excedido — o comprimento do comando é limite do sistema
- junit_xml/tamanho-maximo-excedido — idem, o caminho é validado pelo sistema de arquivos.
- junit_xml/caracteres-especiais — o caminho é usado como `self.root / junit_xml` sem

## Evidência

### Arquivos alterados

- src/sentrytest/adapters/local_tools.py
- src/sentrytest/skills.py
- tests/test_execution_evidence.py

### Execução de testes

- Comando: `C:\Users\lucas.ferreira\AppData\Local\Programs\Python\Python312\python.exe -m coverage run -m pytest`
- Saida resumida:
```
n.py ...........                              [ 23%]
tests\test_changed_coverage.py ...............                           [ 31%]
tests\test_cli.py ...........                                            [ 36%]
tests\test_contextual_reporting.py ........                              [ 40%]
tests\test_dimensions.py ...........                                     [ 46%]
tests\test_domain_models.py ...                                          [ 47%]
tests\test_error_paths.py ............                                   [ 53%]
tests\test_execution_evidence.py .............                           [ 60%]
tests\test_git_context.py ..........                                     [ 65%]
tests\test_history_cli.py ........                                       [ 69%]
tests\test_impact.py .........                                           [ 73%]
tests\test_init_project.py ......                                        [ 76%]
tests\test_input_adapters.py .                                           [ 77%]
tests\test_reporting.py ...                                              [ 78%]
tests\test_rules.py ...............                                      [ 86%]
tests\test_toml_config.py .....                                          [ 88%]
tests\test_traceability.py .......................                       [100%]

- generated xml file: C:\Users\LUCAS~1.FER\AppData\Local\Temp\tmpizstuwjq\junit.xml -
============================ 201 passed in 16.97s =============================

```
