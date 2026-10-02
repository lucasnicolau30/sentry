# docs: o bem-vindo da documentação fala dos vídeos

## Prompt

A home já ganhou uma box sobre os vídeos (`sentry training` e `sentry promo`), mas a aba "Comece aqui" da documentação, a que abre com "Bem-vindo à documentação do Sentry", ainda não diz nada deles. Acrescentar o assunto na frase de abertura e em "O que você pode fazer", como foi feito na home.

Decisões do Lucas: os vídeos usam o agente e gastam tokens, só quando o usuário pede (a afirmação de "zero IA" vale só para o veredito); para mudar um vídeo basta pedir ao agente; o vídeo não certifica nada.

## Campos

- **texto_da_aba**: booleano — se o texto da aba "Comece aqui" de `DocsPage.tsx`, em cada idioma, fala dos vídeos.

## Caso: a frase de abertura do bem-vindo fala dos videos

- **Requisito:** "vamos atualizar aqui no bem vindo para adicionar sobre os videos" — frase de abertura
- **Camada:** frontend
- **Tipo:** contrato
- **Prioridade:** média
- **Classe:** texto_da_aba/valido
- **Dado:** a frase que fica abaixo do título "Bem-vindo à documentação do Sentry"
- **Quando:** o texto é lido em português e em inglês
- **Então:** além do ciclo intenção → veredito, a frase cita o vídeo do projeto e o treinamento de um módulo
- **Entrada:** `texto_da_aba = frase de abertura, pt e en`

## Caso: o que voce pode fazer tem um card dos videos que gastam tokens

- **Requisito:** "igual como foi feito com a home" — a box dos vídeos, com a ressalva de tokens
- **Camada:** frontend
- **Tipo:** contrato
- **Prioridade:** média
- **Classe:** texto_da_aba/valido
- **Dado:** a lista de cards de "O que você pode fazer"
- **Quando:** o texto é lido em português e em inglês
- **Então:** há um card com `sentry promo` e `sentry training` que diz que usam o agente e gastam tokens, só quando o usuário pede, e que o veredito não muda
- **Entrada:** `texto_da_aba = card dos vídeos, pt e en`

## Caso: os cards de o que voce pode fazer fecham o grid de tres colunas

- **Requisito:** com o card novo a lista tem nove cards; o último não deve mais ocupar duas colunas e deixar buraco
- **Camada:** frontend
- **Tipo:** contrato
- **Prioridade:** baixa
- **Classe:** texto_da_aba/valido
- **Dado:** a lista de cards de "O que você pode fazer", agora com nove itens
- **Quando:** o grid é montado
- **Então:** nenhum card recebe `lg:col-span-2`, e as três fileiras ficam completas
- **Entrada:** `texto_da_aba = grid de nove cards`

## Classes não aplicáveis

- **texto_da_aba/vazio**: o texto já existe na página; a ausência de texto é coberta pelos testes de documentação.
