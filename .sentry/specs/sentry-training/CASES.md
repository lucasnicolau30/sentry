# Sentry training

## Prompt

Novo comando `sentry training` que lê um roteiro declarado por módulo, grava os fluxos com
Playwright e monta o vídeo de treinamento com legendas usando a skill brag por baixo dos
panos (`claude -p '/brag ...'`), salvando em `.sentry/video/` (PT por padrão, `--lang en`
opcional).

Decisões do Lucas: o roteiro é declarativo em `.sentry/training/<modulo>.json` (versionado),
com `base`, `titulo` e `passos`; cada passo tem `titulo`, `fala` e `acao`, e as ações são
dados (`ir`, `digitar`, `clicar`, `apontar`), nunca código. A gravação é própria do
`training` (não reaproveita o `archive --video`), com marcação de tempo por passo para as
legendas. A gravação usa o Playwright do Python, dentro do pacote do Sentry, para funcionar em
qualquer projeto (sem depender de `frontend/` nem de Node). Faltando `claude` ou `ffmpeg`, ou com falha do
`claude -p` ou do app, o comando para com erro claro e código diferente de zero, sem fallback
silencioso. Se falta só a skill brag, o Sentry a instala como o `promo` faz. Se falta o Playwright
(o pacote Python ou o navegador Chromium), o Sentry também instala, com o mesmo Python que o
executa (`python -m pip install playwright` e `python -m playwright install chromium`), avisando
antes que o Chromium pesa cerca de 150 MB; se a instalação falha, para com erro claro e mostra os
comandos manuais. `--lang en` roda o brag outra vez em inglês. O vídeo vai para `.sentry/video/`; o `check`
também valida o roteiro.

## Campos

- **modulo**: texto — o nome do módulo; localiza `.sentry/training/<modulo>.json`.
- **roteiro**: arquivo — o JSON do roteiro, com `base`, `titulo` e `passos`.
- **passo**: roteiro — um item de `passos` com `titulo`, `fala` e `acao`.
- **acao**: roteiro — o que o passo faz na tela: `ir`, `digitar`, `clicar` ou `apontar`.
- **idioma**: idioma — o valor de `--lang`; `pt` por padrão, `en` opcional.
- **app_na_base**: booleano — se a URL `base` do roteiro responde.
- **dependencias**: booleano — se `claude` e `ffmpeg` estão disponíveis; o Playwright do
  Python (pacote e Chromium) e a skill brag são instalados pelo Sentry quando faltam.

## Caso: roteiro valido e aceito

- **Requisito:** "lê um roteiro declarado por módulo"
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** crítica
- **Classe:** roteiro/valido
- **Dado:** `.sentry/training/cadastro.json` com `base`, `titulo` e passos completos
- **Quando:** o roteiro é carregado e validado
- **Então:** os passos são devolvidos na ordem declarada, sem erros
- **Entrada:** `modulo = cadastro`

## Caso: modulo com nome simples localiza o roteiro

- **Requisito:** "lê um roteiro declarado por módulo" — o nome do módulo localiza
  `.sentry/training/<modulo>.json`
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** alta
- **Classe:** modulo/valido
- **Dado:** `.sentry/training/login-de-usuario.json` existente
- **Quando:** o comando resolve o caminho do roteiro de `login-de-usuario`
- **Então:** o caminho devolvido é `.sentry/training/login-de-usuario.json`
- **Entrada:** `modulo = login-de-usuario`

## Caso: modulo com separador de caminho e recusado

- **Requisito:** o nome do módulo vira nome de arquivo; `../` ou `/` permitiria ler fora de
  `.sentry/training/`
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** crítica
- **Classe:** modulo/caracteres-especiais
- **Dado:** um arquivo JSON existente fora de `.sentry/training/`
- **Quando:** o usuário roda `sentry training ../../segredo`
- **Então:** o comando recusa o nome, sai com código diferente de zero e não lê o arquivo
- **Entrada:** `modulo = ../../segredo`

## Caso: modulo com nome longo demais e recusado

- **Requisito:** o nome do módulo vira nome de arquivo e de vídeo; nomes enormes estouram o
  limite do sistema de arquivos
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** baixa
- **Classe:** modulo/tamanho-maximo-excedido
- **Dado:** um nome de módulo com 300 caracteres
- **Quando:** o usuário roda `sentry training` com esse nome
- **Então:** o comando recusa com mensagem clara em vez de falhar com erro do sistema
- **Entrada:** `modulo = a repetido 300 vezes`

## Caso: modulo sem roteiro e recusado

- **Requisito:** "lê um roteiro declarado por módulo" — sem roteiro não há o que gravar
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** alta
- **Classe:** roteiro/inexistente
- **Dado:** nenhum arquivo em `.sentry/training/` para o módulo
- **Quando:** o usuário roda `sentry training inexistente`
- **Então:** o comando diz qual arquivo esperava, sai com código diferente de zero e não
  abre navegador
- **Entrada:** `modulo = inexistente`

## Caso: roteiro com json invalido aponta o erro

- **Requisito:** o roteiro é versionado e editado à mão; JSON quebrado precisa de erro
  legível
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** alta
- **Classe:** roteiro/json-invalido
- **Dado:** um roteiro com vírgula faltando
- **Quando:** o roteiro é carregado
- **Então:** o erro cita o arquivo, a linha e a coluna, e o comando sai com código diferente
  de zero
- **Entrada:** `roteiro = {"passos": [ {"titulo": "a" "fala": "b"} ]}`

## Caso: passo sem fala e recusado

- **Requisito:** cada passo tem `titulo`, `fala` e `acao`; a fala vira a legenda
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** alta
- **Classe:** passo/campo-obrigatorio-ausente
- **Dado:** um roteiro cujo terceiro passo não tem `fala`
- **Quando:** o roteiro é validado
- **Então:** o erro cita o número do passo e o campo ausente, e nada é gravado
- **Entrada:** `passo = {"titulo": "Ler o erro", "acao": {"apontar": "#erro"}}`

## Caso: acao desconhecida e recusada

- **Requisito:** "as ações são dados (`ir`, `digitar`, `clicar`, `apontar`), nunca código"
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** alta
- **Classe:** acao/desconhecida
- **Dado:** um passo com a ação `executar`
- **Quando:** o roteiro é validado
- **Então:** o erro lista as ações aceitas e o comando sai com código diferente de zero
- **Entrada:** `acao = {"executar": "alert(1)"}`

## Caso: acao com seletor vazio e recusada

- **Requisito:** `digitar`, `clicar` e `apontar` precisam de um seletor para existir
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** média
- **Classe:** acao/seletor-vazio
- **Dado:** um passo `{"clicar": ""}`
- **Quando:** o roteiro é validado
- **Então:** o erro cita o passo e informa que o seletor está vazio
- **Entrada:** `acao = {"clicar": ""}`

## Caso: training grava os passos no navegador e marca o tempo de cada um

- **Requisito:** "grava os fluxos com Playwright" e "marcação de tempo por passo para as
  legendas"
- **Camada:** integração
- **Tipo:** e2e
- **Prioridade:** crítica
- **Classe:** acao/valida
- **Dado:** uma página local simples e um roteiro com `ir`, `digitar`, `clicar` e `apontar`
- **Quando:** o `training` executa o roteiro
- **Então:** um `.webm` é gravado e há um tempo de início e de fim para cada passo, em ordem
  crescente
- **Entrada:** `acao = {"ir": "/cadastro"}`

## Caso: training para quando o app da base nao responde

- **Requisito:** "ou do app, o comando para com erro claro e código diferente de zero"
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** crítica
- **Classe:** app_na_base/fora-do-ar
- **Dado:** um roteiro cuja `base` aponta para uma porta sem servidor
- **Quando:** o usuário roda `sentry training cadastro`
- **Então:** o comando diz que a `base` não respondeu, sai com código diferente de zero e
  não chama o `claude`
- **Entrada:** `app_na_base = falso`

## Caso: training para quando falta uma dependencia

- **Requisito:** "Faltando `claude` ou `ffmpeg`, o comando para com erro
  claro e código diferente de zero, sem fallback silencioso"
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** crítica
- **Classe:** dependencias/ausente
- **Dado:** um ambiente sem uma das duas dependências
- **Quando:** o usuário roda `sentry training cadastro`
- **Então:** o comando nomeia a dependência que falta e como instalá-la, sai com código
  diferente de zero e não grava nada
- **Entrada:** `dependencias = falso`

## Caso: training instala o brag quando ele esta ausente

- **Requisito:** "Se falta só a skill brag, o Sentry a instala como o `promo` faz"
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** alta
- **Classe:** dependencias/brag-ausente
- **Dado:** `claude`, `ffmpeg` e Playwright disponíveis e nenhuma skill brag instalada
- **Quando:** o usuário roda `sentry training cadastro`
- **Então:** o Sentry instala o brag pelo Claude Code antes de chamar o `claude -p` e gera o
  vídeo
- **Entrada:** `dependencias = brag-ausente`

## Caso: training instala o playwright quando falta o pacote

- **Requisito:** "Se falta o Playwright [...] o Sentry também instala, com o mesmo Python que o
  executa" — quem nunca instalou o Playwright não precisa saber o comando
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** crítica
- **Classe:** dependencias/playwright-ausente
- **Dado:** `claude` e `ffmpeg` disponíveis e o pacote `playwright` não instalado no Python do
  Sentry
- **Quando:** o usuário roda `sentry training cadastro`
- **Então:** o Sentry avisa, roda `<python do Sentry> -m pip install playwright`, carrega o pacote
  recém-instalado e segue para a gravação
- **Entrada:** `dependencias = playwright-ausente`

## Caso: training instala o chromium quando falta so o navegador

- **Requisito:** "o pacote Python ou o navegador Chromium" — o pacote instalado sem o navegador
  é o erro mais comum e não pode estourar no meio da gravação
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** crítica
- **Classe:** dependencias/navegador-ausente
- **Dado:** o pacote `playwright` instalado e o Chromium ausente
- **Quando:** o usuário roda `sentry training cadastro`
- **Então:** o Sentry avisa que o Chromium pesa cerca de 150 MB, roda
  `<python do Sentry> -m playwright install chromium` e segue para a gravação
- **Entrada:** `dependencias = navegador-ausente`

## Caso: training para quando a instalacao do playwright falha

- **Requisito:** "se a instalação falha, para com erro claro e mostra os comandos manuais"
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** alta
- **Classe:** dependencias/instalacao-playwright-falhou
- **Dado:** o Playwright ausente e uma instalação (pip ou Chromium) que sai com código diferente
  de zero, estoura o tempo ou não executa
- **Quando:** o usuário roda `sentry training cadastro`
- **Então:** o comando mostra o erro da instalação e os comandos manuais
  (`pip install playwright && playwright install chromium`), sai com código diferente de zero e
  não grava nem chama o `claude -p`
- **Entrada:** `dependencias = instalacao-playwright-falhou`

## Caso: training monta o video em portugues por padrao

- **Requisito:** "monta o vídeo de treinamento com legendas usando a skill brag [...] em
  `.sentry/video/`, PT por padrão"
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** crítica
- **Classe:** idioma/pt
- **Dado:** gravação e tempos prontos e um `claude` simulado que deixa o `.mp4`
- **Quando:** o usuário roda `sentry training cadastro` sem `--lang`
- **Então:** o `claude -p` recebe as falas e os tempos dos passos em português e o `.mp4`
  fica em `.sentry/video/`, com o módulo no nome
- **Entrada:** `idioma = pt`

## Caso: training com lang en roda o brag de novo em ingles

- **Requisito:** "`--lang en` roda o brag outra vez em inglês"
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** alta
- **Classe:** idioma/en
- **Dado:** o vídeo em português já gerado
- **Quando:** o usuário roda `sentry training cadastro --lang en`
- **Então:** o `claude -p` é chamado de novo pedindo legendas em inglês e o vídeo em inglês
  é gravado em arquivo distinto, sem sobrescrever o português
- **Entrada:** `idioma = en`

## Caso: training propaga a falha do claude sem deixar video parcial

- **Requisito:** "com falha do `claude -p` [...] o comando para com erro claro e código
  diferente de zero"
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** crítica
- **Classe:** dependencias/claude-falhou
- **Dado:** gravação pronta e um `claude` simulado que sai com código diferente de zero
- **Quando:** o usuário roda `sentry training cadastro`
- **Então:** o comando mostra o erro do `claude`, sai com código diferente de zero e não
  deixa `.mp4` em `.sentry/video/`
- **Entrada:** `dependencias = claude-falhou`

## Caso: check valida os roteiros declarados

- **Requisito:** "o `check` também valida o roteiro" — erro de roteiro aparece antes de
  gastar uma gravação
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** média
- **Classe:** roteiro/invalido-no-check
- **Dado:** um roteiro com passo sem `fala` em `.sentry/training/`
- **Quando:** o usuário roda `sentry check`
- **Então:** o `check` reporta o erro do roteiro com o número do passo
- **Entrada:** `roteiro = passo sem fala`

## Classes não aplicáveis

- **idioma/vazio**: `--lang` sem valor é recusado pelo argparse antes do Sentry agir; o
  default `pt` cobre a ausência da opção.
- **modulo/vazio**: o argumento posicional é obrigatório no argparse.
