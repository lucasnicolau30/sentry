# docs: aba de vídeos na documentação

## Prompt

Os vídeos (`sentry promo` e `sentry training`) estão espalhados na documentação: a árvore do `.sentry/` em "Comece aqui", o versionamento em Setup e as entradas dos comandos em "Comandos e Habilidades". Criar uma aba própria, "Vídeos", entre "O fluxo de trabalho" e "Comandos e Habilidades", que reúna o assunto em português e em inglês.

Decisões do Lucas: os vídeos usam o agente e gastam tokens, só quando o usuário pede; a afirmação de "zero IA" vale só para o veredito; o training não certifica nada; para mudar um vídeo basta pedir ao agente; o roteiro do training é dado, nunca código.

## Campos

- **texto_da_aba**: booleano — se o texto da aba "Vídeos" de `DocsPage.tsx`, em cada idioma, traz o conteúdo declarado.

## Caso: a aba de videos entra na navegacao entre o fluxo e os comandos

- **Requisito:** "criassemos uma nova aba para os videos" — posição na navegação
- **Camada:** frontend
- **Tipo:** contrato
- **Prioridade:** alta
- **Classe:** texto_da_aba/valido
- **Dado:** a lista de abas da documentação e os botões de anterior e próximo de cada aba
- **Quando:** a lista e os botões são lidos
- **Então:** "Vídeos" fica entre "O fluxo de trabalho" e "Comandos e Habilidades", e os botões de anterior e próximo das três abas apontam uns para os outros
- **Entrada:** `texto_da_aba = lista de abas e rodapés`

## Caso: a aba explica promo e training e que gastam tokens so quando o usuario pede

- **Requisito:** "ressalva de tokens, só quando você pede" — visão geral, promo e training
- **Camada:** frontend
- **Tipo:** contrato
- **Prioridade:** alta
- **Classe:** texto_da_aba/valido
- **Dado:** o texto da aba "Vídeos"
- **Quando:** é lido em português e em inglês
- **Então:** descreve `sentry promo` e `sentry training`, diz que usam o agente e gastam tokens, só quando o usuário pede, e que não certificam nada, porque só o veredito certifica
- **Entrada:** `texto_da_aba = visão geral, promo e training, pt e en`

## Caso: a aba mostra o formato do roteiro do training

- **Requisito:** o roteiro é dado, nunca código — o usuário precisa ver o formato para poder pedir ao agente que o altere
- **Camada:** frontend
- **Tipo:** contrato
- **Prioridade:** média
- **Classe:** texto_da_aba/valido
- **Dado:** a seção do training da aba "Vídeos"
- **Quando:** é lida
- **Então:** mostra um exemplo de `.sentry/training/<módulo>.json` com `base`, `titulo` e `passos`, cada passo com `titulo`, `fala` e uma `acao`, e cita as quatro ações `ir`, `digitar`, `clicar` e `apontar`
- **Entrada:** `texto_da_aba = exemplo do roteiro`

## Caso: a aba diz onde ficam os videos como versionar e como altera-los

- **Requisito:** "pasta oficial dos vídeos `.sentry/video/`", versionamento e alteração pelo agente
- **Camada:** frontend
- **Tipo:** contrato
- **Prioridade:** média
- **Classe:** texto_da_aba/valido
- **Dado:** as seções de arquivos e de alteração da aba "Vídeos"
- **Quando:** são lidas em português e em inglês
- **Então:** dizem que os vídeos e a saída do brag ficam em `.sentry/video/`, que quem quiser versionar escreve `!.sentry/video/` no `.gitignore` e que, para mudar um vídeo, basta pedir ao agente, sem rodar o comando de novo
- **Entrada:** `texto_da_aba = arquivos e alteração, pt e en`

## Classes não aplicáveis

- **texto_da_aba/vazio**: o texto já existe na página; a ausência de texto é coberta pelos testes de documentação.
