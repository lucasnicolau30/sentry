# Revisar branch contra base declarada

## Prompt

Não dá para revisar branch contra base — run só tem --spec e --run-tests; analyze chama change() sem referência, então é sempre git diff HEAD. O adapter aceita reference, mas nada expõe. Em PR já commitada o diff sai vazio — o que limita muito o uso em CI.

## Campos

- **base**: texto — a referência Git contra a qual comparar, declarada em `sentry run
  --base <ref>`. Vazio significa o comportamento atual: a árvore de trabalho contra `HEAD`.

## Caso: base declarada revela o que a branch mudou

- **Requisito:** "Em PR já commitada o diff sai vazio — o que limita muito o uso em CI"
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** crítica
- **Classe:** base/valido
- **Dado:** uma branch com commits sobre `main` e a árvore de trabalho limpa
- **Quando:** a análise roda com `--base main`
- **Então:** os arquivos e as linhas commitados na branch aparecem como alterados, em vez
  do diff vazio que `HEAD` produz
- **Entrada:** `base = "main"`

## Caso: sem base declarada o comportamento atual permanece

- **Requisito:** quem roda localmente sobre alterações não commitadas não pode ser afetado
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** crítica
- **Classe:** base/vazio
- **Dado:** uma árvore de trabalho com alterações não commitadas
- **Quando:** a análise roda sem `--base`
- **Então:** o diff é o da árvore contra `HEAD`, como antes
- **Entrada:** `base = ""`

## Caso: base compara a partir do ponto em que a branch divergiu

- **Requisito:** revisar a branch é revisar o que ela mudou, não o que a base andou
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** crítica
- **Classe:** base/valido
- **Dado:** uma branch criada de `main` e uma `main` que recebeu outro commit depois disso
- **Quando:** a análise roda com `--base main`
- **Então:** só as alterações da branch aparecem; o commit que entrou em `main` depois da
  divergência fica de fora
- **Entrada:** `base = "main"`

## Caso: base inexistente vira erro de infraestrutura

- **Requisito:** em CI, um nome de base errado não pode virar diff vazio e aprovação
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** crítica
- **Classe:** base/caracteres-especiais
- **Dado:** uma referência que não existe no repositório, com caracteres que o Git rejeita
- **Quando:** a análise roda com essa base
- **Então:** a execução registra erro de infraestrutura nomeando a referência, e o veredito
  não é aprovado silenciosamente
- **Entrada:** `base = "origin/nao-existe~~"`

## Caso: a base efetivamente usada aparece no relatorio

- **Requisito:** o relatório precisa dizer contra o que comparou, ou não é auditável
- **Camada:** integração
- **Tipo:** contrato
- **Prioridade:** alta
- **Classe:** base/valido
- **Dado:** uma análise rodada com `--base main`
- **Quando:** o relatório é montado
- **Então:** a referência declarada aparece na evidência da execução
- **Entrada:** `base = "main"`

## Classes não aplicáveis

- **base/tamanho-maximo-excedido**: o comprimento de uma referência é limite do Git; uma
  referência longa demais apenas não existe, e cai no caso de base inexistente.
