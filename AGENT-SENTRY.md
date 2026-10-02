# Sentry — guia para agentes de IA

O Sentry mede se a implementação corresponde à intenção declarada. Ele não gera
código nem testes: quem declara intenção e quem escreve código e testes é você
(o agente) ou o usuário; o Sentry só mede.

Funciona com todos os agentes de IA que consigam rodar comandos de shell.

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

6. Rode `sentry review --spec <slug>` — ele encadeia `check`, `run` com testes e o
   relatório, num comando só. Os passos separados (`sentry check <slug>` →
   `sentry run --spec <slug> --run-tests`) continuam valendo quando você quiser
   parar entre eles. Para analisar todas as specs de uma vez, use `--spec all`.

   Sem spec nenhuma, `sentry review` ainda mede o que não depende dela: cobertura
   do alterado, caminhos de erro descobertos, testes falhando e testes impactados.
   As dimensões que dependem de intenção declarada saem `não aplicável` dizendo
   isso — nunca `coberta`. A spec é o teto do produto, não o piso.

7. Leia o relatório atual — `sentry report`, ou o `.sentry/reports/latest-<data>.md`
   gravado pela execução: os achados vêm primeiro, ordenados por severidade;
   evidência bruta (arquivos alterados, saída do pytest) vem depois.

## O loop

O fluxo acima acontece uma vez por funcionalidade. O que se repete dezenas de
vezes por tarefa é este loop, e ele é desenhado para que o passo mais frequente
seja o mais barato:

- **Ao pegar a tarefa** — `sentry new "<nome>" --prompt "<pedido>" --json` e você
  preenche o `CASES.md`. É o passo que custa token, e ele acontece uma vez.
- **Ao salvar** — deixe `sentry watch` rodando e não rode mais nada. Ele reavalia
  sozinho no modo instantâneo: nenhuma suíte executada, nenhum token gasto.
- **Ao salvar um teste** — o próprio watch escala para o modo completo, porque é
  executando que a mudança no teste vira evidência. Se o diff, os arquivos de
  teste e as specs não mudaram desde a última execução completa, a resposta volta
  do cache — e o relatório diz que voltou, e de quando é a evidência.
- **Quando houver lacuna** — rode `sentry context --json` e trabalhe **só sobre o
  que ele devolver**. Reler o código inteiro para descobrir o que falta é gastar
  contexto com o que o Sentry já mediu.
- **Antes de commitar** — `sentry review`: o veredito completo antes de o commit
  existir. É um hook local de desenvolvimento, não um portão remoto.
- **Periodicamente** — `sentry status`: a aplicação inteira, não só o diff. Todo
  arquivo de código é tratado como alterado, sempre com a suíte completa e nunca
  com o cache — é a medição autoritativa, não o loop rápido. Aponta arquivos com
  zero cobertura e marcadores órfãos em qualquer lugar do projeto, mesmo fora do
  que esta tarefa tocou.

Duas regras amarram o loop:

1. **O passo mais frequente é o mais barato.** Se avaliar ao salvar custasse a
   suíte inteira, ninguém deixaria o watch ligado — e a avaliação voltaria a ser
   cerimônia em vez de hábito.
2. **O LLM só é chamado onde a máquina não conclui.** O Sentry tria de forma
   determinística por zero token; você entra onde ele aponta lacuna, não onde ele
   já tem evidência.

### O que `sentry context --json` devolve

Um payload denso, e só do que não tem evidência:

- `summary`: veredito, número de achados e `tests_executed`;
- `uncovered_lines`: por arquivo, as faixas de linha alteradas que nenhum teste
  executou;
- `uncovered_error_paths`: `raise`/`throw` em linha alterada que nenhum teste
  executou;
- `failing_tests`: os nomes dos testes falhos, como a suíte os nomeou;
- `scenarios_without_tests`: casos declarados sem teste associado;
- `missing_equivalence_classes`: as classes que o catálogo cobra e nenhum caso
  cobre;
- `orphan_markers`: marcador `cenario:` que não corresponde a caso nenhum;
- `limitations`: o que o Sentry não pôde medir, dito em voz alta.

Toda chave sempre existe, vazia quando não há nada: chave ausente seria ambígua
entre "nada a fazer" e "o Sentry não olhou". Por isso `summary.tests_executed`
falso com `uncovered_lines` vazio significa que ninguém mediu — não que nada
ficou descoberto.

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

## Outros comandos

- `sentry init [--install] [--skills-dir PASTA]` — prepara o projeto (uma vez só; `sentry new`
  já chama isso implicitamente). Idempotente. A skill `sentry-cases` vai para a(s) pasta(s)
  de `[init] skills_dirs` no `sentry.toml` (padrão `.claude/skills`); `--skills-dir` escolhe
  outra e a registra lá.
- `sentry report` — reexibe o último relatório sem rodar nada de novo.
- `sentry history` — lista execuções e compara as duas últimas: cobertura,
  testes, achados novos, resolvidos e persistentes.
- `sentry clear [--keep-last N] [--yes]` — poda execuções e relatórios antigos.
  Sem `--yes` só mostra o que sairia. Nunca toca em `.sentry/specs/`, em
  `.sentry/storage/` nem em `.sentry/video/`.
- `sentry archive <modulo> --version X.Y.Z [--specs A,B,C] [--image] [--video]` —
  dois modos, conforme o módulo é declarado em `sentry.toml`.
  - **Por specs** (`[modules] <modulo> = [...]`): executa a suíte e2e do módulo
    e, se aprovada, arquiva a mídia em `.sentry/storage/<modulo>-<versao>/` com
    um `README.md` autossuficiente. Recusa veredito reprovado. A composição do
    módulo é declarada uma única vez, com `--specs`, na versão 1.0.0, e fica
    gravada em `[modules]` do `sentry.toml`.
  - **Por rota** (`[modules.<modulo>] rotas = [...]`): fotografa cada rota
    declarada com Playwright (desktop + mobile, vídeo opcional), uma pasta por
    rota dentro de `.sentry/storage/<modulo>-<versao>/` — mesmo que o módulo
    nunca tenha sido testado. `login = true` mais `[archive.login]` (rota,
    seletor de usuário, senha e botão) faz login uma única vez antes de
    fotografar; credenciais vêm só de `SENTRY_LOGIN_USUARIO`/
    `SENTRY_LOGIN_SENHA`, nunca do `sentry.toml`. Uma lista `specs` opcional
    dentro do próprio `[modules.<modulo>]` roda a suíte e carimba veredito no
    README, igual ao modo por specs; sem ela, o README avisa que é registro
    visual, sem certificação. Uma rota que falha ao carregar (rota errada,
    dev server fora do ar) não derruba as demais — o comando sai com o código
    de ressalva (1) e o README nomeia qual rota falhou.
  - Sem `--image`/`--video`, tudo que for produzido é arquivado; pedindo uma
    das duas, só aquele tipo entra na mídia arquivada, e `--video` liga a
    gravação de vídeo do Playwright para aquela execução (os dois modos
    aceitam essas flags).
- `sentry promo [--lang pt|en]` — gera o vídeo promocional do projeto com a skill
  brag, acionada pelo agente declarado em `[video] agente` no `sentry.toml` (o padrão é o
  Claude, acionado como `claude -p "/brag ..."`). Exige esse agente e o `ffmpeg`; faltando algum,
  ou se o agente falhar ou não deixar um `.mp4` novo em `brag-output/`, para com erro claro e código 3, sem
  fallback silencioso. Grava `.sentry/video/promo-<idioma>.mp4` (movido de
  `brag-output/`, a pasta de trabalho do brag, junto com o resto da saída dele: composição e
  texto de divulgação; o `init` põe `brag-output/` no `.gitignore`). Com o agente padrão, se falta só a skill brag, o Sentry a instala (`claude plugin
  marketplace add latent-spaces/brag` e `claude plugin install brag@brag`) e segue; com agente
  declarado a skill é assunto dele: o Sentry a pede pelo nome e não instala nada.
  `--lang en` roda o brag de novo em inglês; o padrão é português. Roda o agente e gasta tokens, só quando o usuário pede. Para alterar o
  vídeo o usuário não precisa rodar o comando de novo: ele pede ao agente que mude o
  script (o projeto do brag em `.sentry/video/`) até chegar no resultado desejado.
- `sentry training <modulo> [--lang pt|en]` — grava o vídeo de treinamento de um
  módulo. Lê o roteiro declarativo `.sentry/training/<modulo>.json` (versionado):
  `base`, `titulo` e `passos`, cada passo com `titulo`, `fala` e uma `acao` que é
  dado, nunca código (`ir`, `digitar` com `valor`, `clicar` ou `apontar`). Grava
  com o Playwright do Python (já no Sentry), marcando o tempo de cada passo, e a skill brag (pelo
  agente configurado, como no `promo`) monta o vídeo com as legendas em
  `.sentry/video/training-<modulo>-<idioma>.mp4`. Para com erro claro e código 3
  se o nome do módulo for inseguro, o roteiro faltar ou for inválido, o app de
  `base` não responder, ou faltar o agente ou o `ffmpeg`. O que faltar do brag
  e do Playwright o Sentry instala sozinho: o Playwright com o mesmo Python que o
  executa (`python -m pip install playwright` e `python -m playwright install
  chromium`, cerca de 150 MB); se a instalação falhar, para e mostra os comandos
  manuais. O `sentry check` valida todos os roteiros. `--lang en` roda o brag
  de novo em inglês. Roda o agente e gasta tokens, só quando o usuário pede. Para alterar o vídeo o usuário não precisa rodar o comando de
  novo: ele pede ao agente que ajuste o roteiro (`.sentry/training/<modulo>.json`)
  até chegar no resultado desejado. O training não certifica nada: só grava e não dá
  veredito; só o veredito certifica.

## Limites

- Verifica backend (`Camada: backend | integração`) por cobertura de linha real,
  e frontend (`Camada: frontend`) por evidência de execução do Playwright — trace
  e screenshot por caso, nunca cobertura de linha, porque TypeScript não é medido
  por coverage.py/lcov/Cobertura. Declare `[e2e]` em `sentry.toml` para habilitar
  a segunda suíte.
- Sem `--run-tests` a análise roda no modo instantâneo: nenhuma suíte é
  executada, e a cobertura exibida é a da última execução completa, carimbada
  como vinda dela. Sem nenhuma execução completa anterior, a cobertura sai
  indisponível — e o veredito tende a `inconclusivo`, nunca a `aprovado` por
  ausência de evidência.
- Não edite nada dentro de `.sentry/reports/` ou `.sentry/runs/`: são evidências
  de auditoria.
