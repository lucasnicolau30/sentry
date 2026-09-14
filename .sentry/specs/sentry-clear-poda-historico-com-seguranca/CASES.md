# Sentry clear poda histórico com segurança

## Prompt

`sentry clear` poda execuções e relatórios antigos com segurança: sem `--yes`, só mostra o
que sairia (apagar histórico é irreversível, o padrão precisa mostrar o escopo antes de
destruir); com `--yes`, remove os arquivos de execução (`.sentry/runs/*.json`,
`.sentry/reports/*.md`, `.sentry/reports/*.json`) e as linhas da tabela `runs`, mas nunca
toca em `.sentry/specs/` (intenção declarada pelo usuário, não evidência gerada);
`--keep-last N` preserva as N execuções mais recentes; e sem nenhum histórico, o comando
não inventa trabalho nem erro, só avisa que não há nada a remover.

## Campos

- **flag_yes**: booleano — se `--yes` foi passado ao `sentry clear`.
- **historico_existente**: booleano — se existe pelo menos uma execução
  registrada (linha em `runs`, mais os arquivos que ela deixou no disco).
- **manter_ultimas**: inteiro — o valor de `--keep-last`, quantas
  execuções mais recentes devem sobreviver à poda.

## Caso: clear sem confirmacao apenas mostra o que sairia

- **Requisito:** "Apagar historico e' irreversivel: o padrao precisa
  mostrar o escopo antes de destruir, senao um comando digitado por engano
  perde evidencia"
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** crítica
- **Classe:** flag_yes/ausente
- **Dado:** uma execução registrada, com seus quatro arquivos no disco
- **Quando:** `sentry clear` roda sem `--yes`
- **Então:** a saída inclui `"Repita com \`--yes\`"`, e nenhum arquivo é
  removido

## Caso: clear com confirmacao remove execucoes e preserva as specs

- **Requisito:** "Spec e' intencao declarada pelo usuario, nao evidencia
  gerada: podar historico nunca pode apagar o trabalho de quem escreveu os
  casos"
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** crítica
- **Classe:** flag_yes/presente
- **Dado:** uma execução registrada com seus arquivos, e uma spec em
  `.sentry/specs/demo/CASES.md`
- **Quando:** `sentry clear --yes` roda
- **Então:** os quatro arquivos da execução são removidos, a tabela `runs`
  fica vazia, e o `CASES.md` da spec continua existindo

## Caso: keep-last preserva as execucoes mais recentes

- **Requisito:** poda seletiva, não tudo-ou-nada
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** alta
- **Classe:** manter_ultimas/valido
- **Dado:** três execuções registradas (`r1`, `r2`, `r3`, em ordem
  crescente de data) e um `latest.md` apontando pra mais recente
- **Quando:** `sentry clear --keep-last 2 --yes` roda
- **Então:** os arquivos de `r1` são removidos, os de `r2` e `r3`
  permanecem, e `latest.md` continua existindo
- **Entrada:** `manter_ultimas = 2`

## Caso: clear sem historico nao inventa trabalho

- **Requisito:** sem nada a podar, o comando não inventa erro nem faz
  trabalho desnecessário
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** média
- **Classe:** historico_existente/ausente
- **Dado:** um projeto sem nenhuma execução registrada
- **Quando:** `sentry clear --yes` roda
- **Então:** o comando termina com sucesso (código 0) e a saída inclui
  `"Nada a remover"`

## Classes não aplicáveis

- **flag_yes/vazio**: a flag é um booleano do argparse — presente ou
  ausente, sem estado vazio próprio.
- **historico_existente/vazio**: mesma classe de "ausente" acima — já
  coberta pelo caso de "nao inventa trabalho".
- **manter_ultimas/vazio**: sem `--keep-last`, o padrão é remover tudo
  (`--yes` sem a flag), já coberto pelo caso de confirmação simples.
- **manter_ultimas/negativo**: `--keep-last` é um contador de execuções a
  manter; um valor negativo não é uma entrada que o argparse aceitaria
  como inteiro válido de uso normal.
- **manter_ultimas/nao-numerico**: o argparse já recusa um valor
  não-inteiro antes de `clear` executar.
- **manter_ultimas/zero**: `--keep-last 0` tem o mesmo efeito de não manter
  nenhuma execução — equivalente ao caminho já coberto sem `--keep-last`,
  não uma classe distinta a isolar.
- **manter_ultimas/limite-superior**: contador de execuções sem teto
  próprio do Sentry; um valor maior que o histórico existente apenas
  mantém tudo, sem erro a testar.
