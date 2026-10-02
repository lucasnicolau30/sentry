# docs: card de comandos lista todos os comandos

## Prompt

Na página de documentação, a frase "Referência completa de init, new, check, run, report, history, archive, promo, training e clear" não lista todos os comandos da CLI: faltam review, watch, status e context.

Decisões do Lucas: o card "Comandos e Habilidades" passa a citar todos os comandos da CLI, cada um
destacado em branco como os demais, na mesma ordem da faixa de comandos da página. A fonte da verdade é a
própria CLI (`build_parser()`), não uma lista copiada à mão.

## Campos

- **comando**: booleano — se cada subcomando da CLI aparece, destacado, na frase de referência do card, em português e em inglês.

## Caso: a frase de referencia cita todos os comandos da cli

- **Requisito:** "nem todos os comandos estão em branco" — a frase do card deve citar todos os comandos da CLI
- **Camada:** backend
- **Tipo:** contrato
- **Prioridade:** média
- **Classe:** comando/valido
- **Dado:** a frase "Referência completa de ..." (e "Full reference for ...") do card Comandos e Habilidades
- **Quando:** os comandos destacados na frase são lidos e comparados com os subcomandos da CLI
- **Então:** a frase cita todos os subcomandos da CLI, sem faltar nenhum e sem sobrar um que não exista, em português e em inglês
- **Entrada:** `comando = todos os subcomandos de build_parser()`

## Classes não aplicáveis

- **comando/vazio**: a CLI sempre tem subcomandos; a ausência de qualquer um já é pega pelo teste de consistência dos documentos.
