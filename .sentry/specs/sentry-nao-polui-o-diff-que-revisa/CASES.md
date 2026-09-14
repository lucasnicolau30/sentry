# Sentry não polui o diff que revisa

## Prompt

Ele polui o diff que revisa — "Arquivos alterados: 3" incluiu .gitignore (que ele alterou) e sentry.toml (que ele criou). is_generated_artifact exclui .sentry/ e as skills, mas não esses dois.

## Campos

- **arquivo**: texto — o caminho do arquivo alterado, como o Git o reporta. Só
  `sentry.toml` e `.gitignore` na raiz do projeto estão em questão.
- **origem_da_alteracao**: texto — quem escreveu as linhas alteradas: o `sentry init` ou
  o usuário. É isso, e não o nome do arquivo, que decide se a alteração é do usuário.

## Caso: sentry.toml intocado desde o init fica fora do diff

- **Requisito:** "'Arquivos alterados: 3' incluiu ... sentry.toml (que ele criou)"
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** crítica
- **Classe:** origem_da_alteracao/valido
- **Dado:** um projeto onde o `sentry init` acabou de criar o `sentry.toml` e ninguém o editou
- **Quando:** o Sentry monta o contexto da mudança
- **Então:** o arquivo não aparece entre os arquivos alterados
- **Entrada:** `arquivo = "sentry.toml"`, `origem_da_alteracao = "init"`

## Caso: sentry.toml editado pelo usuario volta ao diff

- **Requisito:** o Sentry cria o arquivo, mas quem o edita depois é o usuário — e essa
  edição é mudança dele, que precisa ser revisada
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** crítica
- **Classe:** origem_da_alteracao/valido
- **Dado:** um `sentry.toml` cujo conteúdo difere do que o `init` escreveria
- **Quando:** o Sentry monta o contexto da mudança
- **Então:** o arquivo aparece entre os arquivos alterados
- **Entrada:** `arquivo = "sentry.toml"`, `origem_da_alteracao = "usuario"`

## Caso: gitignore so com as entradas do Sentry fica fora do diff

- **Requisito:** "'Arquivos alterados: 3' incluiu .gitignore (que ele alterou)"
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** alta
- **Classe:** arquivo/valido
- **Dado:** um `.gitignore` cujas únicas linhas alteradas são as que o `init` acrescenta
- **Quando:** o Sentry monta o contexto da mudança
- **Então:** o arquivo não aparece entre os arquivos alterados
- **Entrada:** `arquivo = ".gitignore"`, `origem_da_alteracao = "init"`

## Caso: gitignore com linha do usuario na mesma mudanca entra no diff

- **Requisito:** a exclusão é da alteração do Sentry, não do arquivo; uma linha do usuário
  no mesmo arquivo não pode ser escondida junto
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** alta
- **Classe:** origem_da_alteracao/valido
- **Dado:** um `.gitignore` com as entradas do `init` e também uma linha escrita pelo usuário
- **Quando:** o Sentry monta o contexto da mudança
- **Então:** o arquivo aparece entre os arquivos alterados
- **Entrada:** `arquivo = ".gitignore"`, `origem_da_alteracao = "usuario"`

## Caso: arquivo de nome parecido nao e excluido

- **Requisito:** a exclusão vale para os dois arquivos que o `init` escreve na raiz, não
  para qualquer caminho que os contenha no nome
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** média
- **Classe:** arquivo/caracteres-especiais
- **Dado:** arquivos como `sentry.toml.bak`, `pacote/sentry.toml` e `docs/.gitignore`
- **Quando:** o Sentry decide o que é artefato gerado
- **Então:** nenhum deles é excluído do diff
- **Entrada:** `arquivo = "pacote/sentry.toml"`

## Caso: exclusao nao depende de leitura possivel do arquivo

- **Requisito:** decidir por conteúdo não pode derrubar a análise quando o arquivo não
  puder ser lido
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** média
- **Classe:** arquivo/vazio
- **Dado:** um `sentry.toml` que não pode ser lido (ausente ou ilegível) no momento da análise
- **Quando:** o Sentry decide o que é artefato gerado
- **Então:** o arquivo é tratado como mudança do usuário e permanece no diff, sem exceção
- **Entrada:** `arquivo = "sentry.toml"`, `origem_da_alteracao = ""`

## Classes não aplicáveis

- **arquivo/tamanho-maximo-excedido**: o comprimento do caminho é limite do sistema de
  arquivos; um caminho longo demais simplesmente não é um dos dois nomes em questão.
- **origem_da_alteracao/vazio**: verificada no caso de arquivo ilegível, onde a origem não
  pode ser determinada.
- **origem_da_alteracao/tamanho-maximo-excedido**: a origem não é texto digitado, e sim o
  resultado de uma comparação; não tem comprimento a limitar.
- **origem_da_alteracao/caracteres-especiais**: idem — a comparação é entre o conteúdo
  atual e o que o `init` escreveria, e o conteúdo do arquivo é o campo `arquivo`, não este.
