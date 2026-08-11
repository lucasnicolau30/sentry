# Sentry — guia para agentes de IA

O Sentry mede se a implementação corresponde à intenção declarada. Ele não gera
código nem testes: quem declara intenção e quem escreve código e testes é você
(o agente) ou o usuário; o Sentry só mede.

Funciona com qualquer agente de IA que consiga rodar comandos de shell — não é
específico do Claude Code.

## Divisão de responsabilidade

- Você declara intenção: escreve o `CASES.md`.
- O Sentry mede a realidade: decide status, teste associado, evidência e veredito.

Nunca escreva `status` ou `coberto` no `CASES.md` — isso é conclusão do Sentry,
não sua.

## Fluxo

1. `sentry new "<nome>" --prompt "<pedido>" --json`
   Cria `.sentry/specs/<slug>/{PROMPT.md,CASES.md}` e devolve, no mesmo comando:
   - `template`: o esqueleto do `CASES.md` a preencher;
   - `layers`, `test_types`, `priorities`: os únicos valores aceitos;
   - `field_classes`: as classes de equivalência cobradas por tipo de campo;
   - `specDir`: onde o arquivo foi criado.

2. **Pergunte antes de escrever.** Resolva com quem pediu a funcionalidade toda
   ambiguidade que mude um caso. Não invente requisito.

3. Preencha o `CASES.md`: um `## Caso:` por comportamento verificável, com
   `Requisito`, `Camada`, `Tipo`, `Prioridade`, `Dado`, `Quando`, `Então`.
   `- **Classe:** <campo>/<classe>` liga o caso a uma classe de equivalência do
   catálogo — é por aqui que o Sentry sabe o que ainda falta declarar.

4. Rode `sentry check <slug>`. Corrija cada `[erro]` e `[classe ausente]` até a
   saída fechar limpa.

5. **Ligue cada caso ao teste real.** Escreva, na linha acima da função de
   teste, um comentário `# cenario: <nome exato do caso>`:

   ```python
   # cenario: rejeita slug que escapa da pasta de specs
   def test_select_spec_rejects_slug_escaping_specs_dir(tmp_path):
       ...
   ```

   O marcador funciona em qualquer linguagem, com qualquer comentário
   (`// cenario:`, `-- cenario:`), e tolera diferença de acento. Sem ele o
   vínculo cai no palpite de reserva por semelhança de nome, que falha quando o
   caso está em português e o teste em inglês.

   A extração de nomes de teste reconhece `.py`, `.js`/`.ts`, `.go`, `.java`,
   `.kt`, `.cs`, `.rb`, `.php` e `.rs`, em `tests/`, `test/`, `spec/` e
   `__tests__/`. Teste ao lado do código exige declarar `[tests] paths`.

6. Rode `sentry check <slug>` → `sentry run --spec <slug> --run-tests`. Para
   analisar todas as specs de uma vez, use `--spec all`.

7. Leia `.sentry/reports/latest.md`: os achados vêm primeiro, ordenados por
   severidade; evidência bruta (arquivos alterados, saída do pytest) vem depois.

## Fora de Python

Um projeto de outra stack declara sua suíte e seu relatório de cobertura; o
Sentry executa e lê, sem depender de pytest:

```toml
[test]
command = "npx jest"
junit_xml = "reports/junit.xml"

[coverage]
path = "coverage/lcov.info"

[tests]
paths = ["src"]          # só se os testes não ficam em tests/
```

Cobertura aceita `lcov`, `cobertura` XML e o JSON do coverage.py, detectados
pelo conteúdo. Caminhos de erro são detectados por AST em Python e por padrão
sintático nas demais stacks — a diferença aparece como limitação no relatório.

## Python: prefira pytest à suíte do unittest

O Sentry embrulha o comando em `coverage run` e coleta a contagem via
`--junitxml` **quando reconhece o pytest** — nas três grafias equivalentes:
`pytest`, `python -m pytest` e o executável do venv (`.venv/bin/pytest`).

Qualquer outro comando é executado exatamente como declarado, sem instrumentação
e sem flag injetada. Isso inclui `python -m unittest`: ele roda, mas o Sentry não
tem de onde tirar contagem nem cobertura, e o veredito sai `não executado` —
ausência de evidência, não reprovação. Para medir uma suíte `unittest`, declare o
relatório que ela gera:

```toml
[test]
command = "python -m unittest discover"
junit_xml = "reports/junit.xml"   # gerado por unittest-xml-reporting, p.ex.
```

Em Django, rode a suíte por pytest em vez de `manage.py test` — é o que dá
cobertura medida sem configuração extra:

```toml
[test]
command = "python -m pytest"   # com pytest-django instalado
```

Com `DJANGO_SETTINGS_MODULE` no `pytest.ini`/`pyproject.toml`, ou inline
(`python -m pytest --ds=myproject.settings`). O `manage.py test` cai no caminho
genérico: roda, mas não mede.

## Limites

- Só verifica backend (`Camada: backend | integração`); frontend é recusado de
  propósito — sem adaptador que o verifique, um caso ali ficaria eternamente
  `não coberto`.
- Sem `--run-tests` não há cobertura: o veredito tende a `inconclusivo`, nunca
  a `aprovado` por ausência de evidência.
- Não edite nada dentro de `.sentry/reports/` ou `.sentry/runs/`: são evidências
  de auditoria.
