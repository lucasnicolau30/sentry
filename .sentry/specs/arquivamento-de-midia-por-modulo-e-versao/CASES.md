# Arquivamento de mídia por módulo e versão

## Prompt

Novo comando `sentry archive <modulo> --version <x.y.z> [--specs a,b,c]`. `.sentry/storage/<modulo>-<versao>/` guarda a seleção curada que vira evidência do
módulo (versionado no git, nunca tocado pelo `clear`, deleção manual). O `sentry.toml`
ganha a chave `output_dir` em `[e2e]` apontando onde o Playwright escreve, e é de lá
que o `archive` lê a evidência. O `archive` executa a suíte e2e do módulo na hora (não empacota o
que sobrou), recusa quando o veredito é reprovado, e sobrescreve quando a versão já
existe. A composição do módulo é declarada uma única vez, na versão 1.0.0, com `--specs`,
e gravada em `[modules]` no `sentry.toml`; da 1.0.1 em diante o comando lê essa lista e
recusa `--specs`. A primeira versão de um módulo é sempre 1.0.0. A pasta arquivada recebe
um `README.md` autossuficiente (módulo, versão, data, commit, veredito, specs, cobertura,
limitações e tabela caso para arquivo de mídia) e a pasta `media/`, sem cópia do relatório.

Decisão do Lucas (2026-10-02): o pool `.sentry/media/` deixou de existir. O Sentry não copia
mais a saída do Playwright para uma pasta intermediária: o `archive` executa a suíte na hora
e busca cada print e vídeo direto na pasta de saída (`output_dir`), porque evidência de
rodadas antigas nunca serviu para nada.

## Campos

- **versao_do_modulo**: texto — a versão informada em `--version`, que nomeia a
  pasta arquivada.
- **composicao_do_modulo**: texto — a lista de specs que compõem o módulo,
  declarada em `--specs` e gravada em `[modules]` do `sentry.toml`.
- **veredito_da_execucao**: booleano — se a suíte e2e do módulo aprovou.
- **saida_do_playwright**: booleano — os artefatos que o Playwright gravou na pasta `output_dir`
  declarada em `[e2e]`.
- **filtro_de_midia**: texto — o tipo de mídia pedido em `--image`/`--video`;
  sem nenhuma das duas, tudo que existir é arquivado.

## Caso: primeira versao de um modulo declara a composicao

- **Requisito:** "A composição do módulo é declarada uma única vez, na versão
  1.0.0, com `--specs`, e gravada em `[modules]` no `sentry.toml`"
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** crítica
- **Classe:** composicao_do_modulo/valido
- **Dado:** um `sentry.toml` sem o módulo declarado
- **Quando:** o comando resolve as specs da versão 1.0.0 com `--specs`
- **Então:** as specs informadas são devolvidas e gravadas em `[modules]`
- **Entrada:** `composicao_do_modulo = cadastro-de-usuario,login`

## Caso: versao seguinte le a composicao congelada

- **Requisito:** "Da 1.0.1 em diante o comando lê essa lista" — é o que torna
  duas versões do mesmo módulo comparáveis entre si
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** crítica
- **Classe:** versao_do_modulo/valido
- **Dado:** um módulo já declarado em `[modules]`
- **Quando:** o comando resolve as specs da versão 1.0.1 sem `--specs`
- **Então:** a lista gravada no `sentry.toml` é devolvida
- **Entrada:** `versao_do_modulo = 1.0.1`

## Caso: composicao ja declarada recusa nova lista de specs

- **Requisito:** "Da 1.0.1 em diante o comando recusa `--specs`" — uma lista
  diferente entre versões esconderia perda de evidência atrás de digitação
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** alta
- **Classe:** composicao_do_modulo/caracteres-especiais
- **Dado:** um módulo já declarado em `[modules]`
- **Quando:** o comando recebe `--specs` numa versão seguinte
- **Então:** o comando recusa, dizendo que a composição está congelada e que a
  mudança se faz editando o `sentry.toml`

## Caso: modulo novo so nasce na versao inicial

- **Requisito:** "A primeira versão de um módulo é sempre 1.0.0"
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** alta
- **Classe:** versao_do_modulo/tamanho-maximo-excedido
- **Dado:** um `sentry.toml` sem o módulo declarado
- **Quando:** o comando é chamado com uma versão diferente de 1.0.0
- **Então:** o comando recusa, dizendo qual é a primeira versão esperada
- **Entrada:** `versao_do_modulo = 2.0.0`

## Caso: modulo novo sem specs declaradas e recusado

- **Requisito:** sem a composição, não há o que medir nem o que arquivar — o
  comando não adivinha quais specs formam o módulo
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** alta
- **Classe:** composicao_do_modulo/vazio
- **Dado:** um `sentry.toml` sem o módulo declarado
- **Quando:** o comando é chamado na 1.0.0 sem `--specs`
- **Então:** o comando recusa, pedindo a declaração das specs

## Caso: veredito reprovado nao arquiva nada

- **Requisito:** "Recusa quando o veredito é reprovado" — o arquivo afirma que o
  módulo está testado; guardar a gravação de um módulo com teste falhando
  registraria o erro, que não é o propósito
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** crítica
- **Classe:** veredito_da_execucao/ausente
- **Dado:** um módulo cuja execução termina reprovada
- **Quando:** `sentry archive` roda
- **Então:** nada é escrito em `.sentry/storage/` e o comando sai com o código
  do veredito

## Caso: arquivo aprovado grava midia e readme

- **Requisito:** "A pasta arquivada recebe um `README.md` autossuficiente e a
  pasta `media/`, sem cópia do relatório"
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** crítica
- **Classe:** veredito_da_execucao/presente
- **Dado:** uma execução aprovada com evidência de Playwright anexada a um caso
- **Quando:** o arquivo do módulo é escrito
- **Então:** existe `.sentry/storage/<modulo>-<versao>/README.md` com veredito,
  specs e a tabela de casos, e a mídia está em `media/`, sem `relatorio.md`

## Caso: modulo aprovado sem nenhuma midia declara a ausencia

- **Requisito:** o objetivo do `archive` é guardar foto e vídeo para
  treinamento de equipe; um módulo composto só de specs de backend não produz
  mídia nenhuma, e isso precisa ser dito, não silenciado — nada some em
  silêncio é princípio do produto
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** alta
- **Classe:** saida_do_playwright/vazio
- **Dado:** uma execução aprovada sem nenhuma evidência de Playwright anexada
  a nenhum caso
- **Quando:** o arquivo do módulo é escrito
- **Então:** a pasta `media/` fica vazia, a tabela "Evidência por caso" não
  ganha linha nenhuma, e "Limitações" ganha a frase "Nenhuma mídia foi
  produzida: o módulo não tem caso de camada frontend com evidência de
  execução do Playwright."

## Caso: flag image sozinha arquiva so prints

- **Requisito:** "pedindo uma das duas, só aquele tipo entra" — `--image` sem
  `--video` restringe a mídia arquivada a prints, mesmo quando a execução
  também produziu vídeo
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** alta
- **Classe:** filtro_de_midia/valido
- **Dado:** uma execução aprovada com prints e vídeos anexados a casos
- **Quando:** o arquivo é escrito só com `--image`
- **Então:** a pasta `media/` e a tabela só trazem os prints; o vídeo fica de
  fora e "Limitações" declara que ficou de fora por causa da flag
- **Entrada:** `filtro_de_midia = image`

## Caso: flag video sozinha arquiva so videos

- **Requisito:** "`--video` liga a gravação de vídeo do Playwright" — no
  arquivo em si, restringe a mídia arquivada a vídeos, mesmo quando a execução
  também produziu print
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** alta
- **Classe:** filtro_de_midia/valido
- **Dado:** uma execução aprovada com prints e vídeos anexados a casos
- **Quando:** o arquivo é escrito só com `--video`
- **Então:** a pasta `media/` e a tabela só trazem os vídeos; o print fica de
  fora e "Limitações" declara que ficou de fora por causa da flag
- **Entrada:** `filtro_de_midia = video`

## Caso: sem nenhuma flag de midia arquiva tudo que existir

- **Requisito:** "Sem nenhuma das duas, tudo que existir é arquivado" —
  comportamento de sempre, preservado para quem não usa as flags novas
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** crítica
- **Classe:** filtro_de_midia/vazio
- **Dado:** uma execução aprovada com prints e vídeos anexados a casos
- **Quando:** o arquivo é escrito sem `--image` nem `--video`
- **Então:** a pasta `media/` e a tabela trazem prints e vídeos, sem nenhuma
  nota de exclusão em "Limitações"

## Caso: midia com caminho relativo ao junit e encontrada na pasta de saida do playwright

- **Requisito:** o anexo que o Playwright grava no JUnit é relativo à pasta do
  próprio `junit.xml` (ex.: `..\test-results\<pasta-do-teste>\arquivo.png`),
  não à raiz do projeto — resolver contra a raiz erra sempre, e cair pro nome
  puro do arquivo colide quando dois testes produzem "test-finished-1.png"
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** crítica
- **Classe:** saida_do_playwright/valido
- **Dado:** uma evidência cujo caminho começa com `..\` e não existe relativo à
  raiz, mas cujo arquivo está na pasta de saída do Playwright (`output_dir`), em
  `<pasta-do-teste>/`
- **Quando:** o arquivo do módulo é escrito com `output_dir` declarado
- **Então:** o arquivo é encontrado pela dupla pasta-do-teste/nome-do-arquivo e
  entra na mídia arquivada

## Caso: rearquivar a mesma versao sobrescreve a pasta

- **Requisito:** "Sobrescreve quando a versão já existe" — rearquivar é dizer
  que a evidência de agora é a que vale para aquela versão
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** média
- **Classe:** versao_do_modulo/valido
- **Dado:** uma pasta de versão já arquivada, com um arquivo antigo dentro
- **Quando:** o arquivo da mesma versão é escrito de novo
- **Então:** a pasta contém apenas o conteúdo da execução nova

## Caso: clear poda execucoes e relatorios e preserva o arquivado e os videos

- **Requisito:** "`.sentry/storage/` nunca é tocado" — a evidência arquivada só existe porque alguém a criou de
  propósito; o mesmo vale para os vídeos de `.sentry/video/`, que são entregas pedidas pelo dev
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** crítica
- **Classe:** saida_do_playwright/valido
- **Dado:** um relatório atual, um vídeo em `.sentry/video/` e um módulo arquivado em storage
- **Quando:** `sentry clear --yes` roda
- **Então:** o relatório é removido, e o vídeo e a pasta arquivada continuam intactos

## Caso: init mantem o storage versionado e ignora so a pasta de videos

- **Requisito:** mídia arquivada é a evidência versionada do módulo — é o motivo de ela existir; os vídeos de
  `promo` e `training` ficam fora do Git por padrão
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** alta
- **Classe:** saida_do_playwright/nao-numerico
- **Dado:** um projeto recém-inicializado
- **Quando:** o `.gitignore` escrito pelo `init` é lido
- **Então:** `.sentry/video/` está excluído, `.sentry/media/` não aparece e `.sentry/storage/` não aparece

## Caso: modulo aponta para spec inexistente e recusado

- **Requisito:** a composição nomeia specs; uma que não existe não pode virar
  arquivo silenciosamente com menos evidência do que foi declarado
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** alta
- **Classe:** composicao_do_modulo/tamanho-maximo-excedido
- **Dado:** um módulo cuja composição nomeia uma spec que não existe em disco
- **Quando:** a análise do módulo é pedida
- **Então:** o erro nomeia a spec que faltou

## Classes não aplicáveis

- **versao_do_modulo/vazio**: `--version` é obrigatório no argparse, que recusa
  a chamada antes do comando executar.
- **versao_do_modulo/caracteres-especiais**: a versão é texto livre que nomeia
  uma pasta; não há formato cobrado além de existir.
- **composicao_do_modulo/tamanho-maximo-excedido**: reaproveitada acima para a
  spec inexistente — não há limite de quantidade de specs por módulo.
- **veredito_da_execucao/vazio**: é um booleano derivado do veredito da
  execução — aprovado ou não, sem estado vazio próprio.
- **filtro_de_midia/tamanho-maximo-excedido**: `--image`/`--video` são flags
  booleanas do argparse (`store_true`), sem valor digitado — não há tamanho a
  estourar.
- **filtro_de_midia/caracteres-especiais**: mesma razão acima; não existe
  texto livre para ter caractere especial.
