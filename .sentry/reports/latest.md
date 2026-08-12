# Sentry Report

- Run: 593a83ae-59a1-416a-87ca-c093de50dc75
- Projeto: sentry
- Veredito: **aprovado** — nenhum achado relevante — pode seguir.

## Achados

- Nenhum achado registrado.

## Contexto

- Arquivos alterados: 2
- Testes impactados: 5
- Testes não relacionados: 14
- Cenários sem teste: 0
- Cobertura global (todo o projeto): 98,27%
- Cobertura alterada (só o código desta mudança): 55,80%
- Testes: 233 passados, 0 falhos, 0 ignorados, 0 nao executados
- Duracao: 34.81 s

## Dimensões de cobertura

| Dimensão | Status | Evidência | Justificativa |
| --- | --- | --- | --- |
| requisitos e regras de negócio | coberta | 6/6 cenários da spec com teste associado | todos os itens têm evidência de cobertura |
| APIs, persistência, transações e integrações | coberta | 4/4 casos de contrato ou integração cobertos | todos os itens têm evidência de cobertura |
| exceções, resiliência e recuperação | não aplicável | nenhum caminho de erro nas linhas alteradas | nada desta dimensão foi declarado ou alterado nesta análise |
| segurança e autorização | não aplicável | nenhum campo do tipo `rota` declarado | nada desta dimensão foi declarado ou alterado nesta análise |

## Matriz de casos

- Total: 6
- Por status: coberto=6

### Backend

- `coberto` **nome puro continua resolvido pelo PATH** (TC-04) — o nome segue intocado, para o sistema operacional resolver no PATH (alta, unitário) — tests\test_execution_evidence.py
- `coberto` **caminho declarado inexistente nomeia onde foi procurado** (TC-05) — o erro de infraestrutura mostra o caminho já resolvido contra a raiz, dizendo (média, unitário) — tests\test_execution_evidence.py

### Integração

- `coberto` **caminho relativo com barra normal executa** (TC-01) — o processo roda, sem erro de infraestrutura (crítica, integração) — tests\test_execution_evidence.py
- `coberto` **as quatro grafias do mesmo executavel sao equivalentes** (TC-02) — as quatro chegam ao mesmo arquivo e produzem o mesmo resultado (crítica, integração) — tests\test_execution_evidence.py
- `coberto` **caminho relativo e resolvido contra a raiz do projeto** (TC-03) — o interpretador do projeto é encontrado e executado (crítica, integração) — tests\test_execution_evidence.py
- `coberto` **suite nao-pytest com caminho relativo tambem e resolvida** (TC-06) — o processo roda, sem erro de infraestrutura (alta, integração) — tests\test_execution_evidence.py

## Limitações

> O Sentry não conseguiu verificar isto — não é aprovação nem reprovação, é ausência de evidência.

- Nenhuma limitação registrada.

## Classes não aplicáveis

> Dispensadas de propósito, com justificativa declarada no CASES.md — não é lacuna do Sentry.

- caminho_do_executavel/vazio — `[test] command` em branco já é verificado na spec
- caminho_do_executavel/tamanho-maximo-excedido — o comprimento do caminho é limite do

## Evidência

### Arquivos alterados

- Comparado com: árvore de trabalho contra `HEAD`

- src/sentrytest/adapters/local_tools.py
- tests/test_execution_evidence.py

### Execução de testes

- Comando: `C:\Users\lucas.ferreira\AppData\Local\Programs\Python\Python312\python.exe -m coverage run -m pytest`
- Saida resumida:
```
n.py ...........                              [ 20%]
tests\test_changed_coverage.py ...............                           [ 27%]
tests\test_cli.py ...........                                            [ 31%]
tests\test_contextual_reporting.py ........                              [ 35%]
tests\test_dimensions.py ...............                                 [ 41%]
tests\test_domain_models.py ...                                          [ 42%]
tests\test_error_paths.py ............                                   [ 48%]
tests\test_execution_evidence.py .........................               [ 58%]
tests\test_git_context.py .....................                          [ 67%]
tests\test_history_cli.py ........                                       [ 71%]
tests\test_impact.py ..............                                      [ 77%]
tests\test_init_project.py ......                                        [ 79%]
tests\test_input_adapters.py .                                           [ 80%]
tests\test_reporting.py ...                                              [ 81%]
tests\test_rules.py ...............                                      [ 87%]
tests\test_toml_config.py .....                                          [ 90%]
tests\test_traceability.py .......................                       [100%]

- generated xml file: C:\Users\LUCAS~1.FER\AppData\Local\Temp\tmpc37hgfgc\junit.xml -
============================ 233 passed in 33.91s =============================

```
