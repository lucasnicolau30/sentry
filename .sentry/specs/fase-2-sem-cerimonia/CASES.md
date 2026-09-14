# Fase 2 — usar sem cerimônia

## Prompt

Fase 2: usar sem cerimonia. (a) Modo sem spec: rodar o run sem CASES.md deixa de levantar
excecao e produz o relatorio de evidencia -- cobertura do alterado, caminhos de erro
descobertos, testes falhando, testes impactados -- com as regras que dependem de spec
simplesmente nao disparando. Pedir --spec all ou um slug que nao existe continua sendo
erro, porque ai o pedido e explicito e a realidade nao corresponde. (b) Dimensoes honestas
no modo sem spec: requisitos e APIs saem como nao aplicavel com a justificativa de que
nenhuma intencao foi declarada nesta analise, nunca como coberta; a dimensao de excecoes
continua sendo medida, porque nao depende de spec. (c) Marcador orfao vira achado: um
marcador de cenario que aponta para caso inexistente e reportado; hoje ele some e o caso
renomeado cai para nao coberto sem explicacao, um gerador silencioso de falso negativo.
Sem spec declarada nenhum marcador pode ser considerado orfao. (d) Um comando so: sentry
review encadeia check, run, report e codigo de saida, e precisa funcionar num repositorio
qualquer, sem .sentry e sem sentry.toml.

## Campos

- **argumento_spec**: texto — o que a chamada do `run` pede: nada (deixa o Sentry
  escolher), um slug, ou `all`. É ele que separa "não havia spec" de "pedi uma spec que
  não existe".
- **marcador_cenario**: texto — o nome que um `// cenario:` num arquivo de teste aponta.
  A questão é quando esse nome não corresponde a caso nenhum da spec.
- **arquivo_do_marcador**: texto — onde o marcador está e se a mudança em análise
  escreveu aquela linha. É isso que separa vínculo recém-quebrado de dívida antiga.

## Caso: run sem spec produz relatorio em vez de excecao

- **Requisito:** "rodar o run sem CASES.md deixa de levantar excecao e produz o relatorio
  de evidencia"
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** crítica
- **Classe:** argumento_spec/vazio
- **Dado:** um projeto sem nenhum CASES.md e uma chamada sem `--spec`
- **Quando:** a análise roda
- **Então:** devolve uma execução com veredito, sem levantar exceção
- **Entrada:** `argumento_spec = ""`

## Caso: run --spec all sem nenhuma spec continua sendo erro

- **Requisito:** "Pedir --spec all ... continua sendo erro, porque ai o pedido e explicito
  e a realidade nao corresponde"
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** crítica
- **Classe:** argumento_spec/valido
- **Dado:** um projeto sem nenhum CASES.md
- **Quando:** a análise é pedida com `--spec all`
- **Então:** levanta erro de configuração, e o comando sai com o código de infraestrutura
- **Entrada:** `argumento_spec = "all"`

## Caso: run com slug inexistente continua sendo erro

- **Requisito:** "ou um slug que nao existe continua sendo erro"
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** alta
- **Classe:** argumento_spec/caracteres-especiais
- **Dado:** um projeto onde o slug pedido não existe em `.sentry/specs`
- **Quando:** a spec é resolvida
- **Então:** levanta erro dizendo qual caminho era esperado
- **Entrada:** `argumento_spec = "spec-que-nao-existe"`

## Caso: modo sem spec mede cobertura do alterado e testes impactados

- **Requisito:** "produz o relatorio de evidencia -- cobertura do alterado, caminhos de
  erro descobertos, testes falhando, testes impactados"
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** alta
- **Dado:** um projeto sem spec, com suíte e cobertura disponíveis
- **Quando:** a análise roda com execução de testes
- **Então:** o relatório traz cobertura do alterado, contagem de testes e testes
  impactados, como traria com spec
- **Entrada:** `argumento_spec = ""`

## Caso: regras que dependem de spec nao disparam sem spec

- **Requisito:** "com as regras que dependem de spec simplesmente nao disparando"
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** crítica
- **Dado:** uma análise sem nenhuma intenção declarada
- **Quando:** as regras são avaliadas
- **Então:** nenhum achado de cenário sem teste, requisito sem cenário, classe de
  equivalência ausente ou CASES.md inválido é emitido
- **Entrada:** `argumento_spec = ""`

## Caso: dimensao de requisitos sai nao aplicavel sem intencao declarada

- **Requisito:** "requisitos e APIs saem como nao aplicavel com a justificativa de que
  nenhuma intencao foi declarada nesta analise, nunca como coberta"
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** alta
- **Dado:** uma análise sem spec
- **Quando:** as dimensões são avaliadas
- **Então:** a dimensão de requisitos sai `não aplicável` e a justificativa diz que
  nenhuma intenção foi declarada nesta análise
- **Entrada:** `argumento_spec = ""`

## Caso: dimensao de APIs sai nao aplicavel sem intencao declarada

- **Requisito:** "requisitos e APIs saem como nao aplicavel ... nunca como coberta"
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** alta
- **Dado:** uma análise sem spec
- **Quando:** as dimensões são avaliadas
- **Então:** a dimensão de APIs sai `não aplicável` com a mesma justificativa de intenção
  ausente, e nunca `coberta`
- **Entrada:** `argumento_spec = ""`

## Caso: dimensao de excecoes continua medida sem spec

- **Requisito:** "a dimensao de excecoes continua sendo medida, porque nao depende de spec"
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** alta
- **Dado:** uma análise sem spec, com caminhos de erro nas linhas alteradas
- **Quando:** as dimensões são avaliadas
- **Então:** a dimensão de exceções reporta o que mediu, sem cair em `não aplicável` por
  falta de spec
- **Entrada:** `argumento_spec = ""`

## Caso: marcador que aponta para caso inexistente vira achado

- **Requisito:** "um marcador de cenario que aponta para caso inexistente e reportado;
  hoje ele some e o caso renomeado cai para nao coberto sem explicacao"
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** alta
- **Classe:** marcador_cenario/caracteres-especiais
- **Dado:** uma spec com casos declarados e um teste **alterado nesta mudança**, marcado
  com um nome que não é o de nenhum deles
- **Quando:** a rastreabilidade é montada e as regras avaliadas
- **Então:** um achado nomeia o marcador órfão e o arquivo onde ele está
- **Entrada:** `marcador_cenario = "caso que foi renomeado"`, `arquivo_do_marcador = "alterado"`

## Caso: marcador orfao em linha nao alterada nao vira achado

- **Requisito:** o Sentry julga a mudança; marcador já órfão antes de alguém encostar no
  código é dívida pré-existente, e acusá-la em toda análise afoga o achado útil
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** alta
- **Classe:** arquivo_do_marcador/valido
- **Dado:** um marcador órfão numa linha que esta mudança não tocou, ainda que o arquivo
  tenha sido alterado por outro motivo
- **Quando:** a rastreabilidade é montada
- **Então:** nenhum achado é emitido para ele
- **Entrada:** `arquivo_do_marcador = "linha intocada"`

## Caso: marcador escrito dentro de literal de string nao vira cenario

- **Requisito:** o extrator levava o resto da linha de código como nome de cenário quando
  um teste *escrevia* ou montava um marcador — inofensivo enquanto o marcador só associava
  teste, virou ruído quando marcador sem caso passou a ser achado
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** alta
- **Classe:** arquivo_do_marcador/caracteres-especiais
- **Dado:** um arquivo de teste que escreve `# cenario: x` dentro de uma string, ou que o
  monta num template como `f"# cenario: {nome}"`
- **Quando:** os marcadores são extraídos
- **Então:** nenhum dos dois vira marcador — o marcador é uma linha de comentário, e só
  conta quando o comentário abre a linha
- **Entrada:** `arquivo_do_marcador = "tests/test_fixture.py"`

## Caso: marcador que casa com caso declarado nao vira achado

- **Requisito:** o achado é do vínculo quebrado; um marcador que cumpre seu papel não pode
  ser acusado
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** alta
- **Classe:** marcador_cenario/valido
- **Dado:** um teste marcado com o nome de um caso que existe na spec
- **Quando:** a rastreabilidade é montada
- **Então:** nenhum achado de marcador órfão é emitido
- **Entrada:** `marcador_cenario = "soma retorna o total"`

## Caso: arquivo de teste sem marcador nao vira achado

- **Requisito:** o marcador é opcional — a associação por semelhança de nome continua
  valendo, e ausência de marcador não é vínculo quebrado
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** média
- **Classe:** marcador_cenario/vazio
- **Dado:** arquivos de teste sem nenhum `// cenario:`
- **Quando:** a rastreabilidade é montada
- **Então:** nenhum achado de marcador órfão é emitido
- **Entrada:** `marcador_cenario = ""`

## Caso: sem spec declarada nenhum marcador e orfao

- **Requisito:** "Sem spec declarada nenhum marcador pode ser considerado orfao"
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** crítica
- **Dado:** um projeto sem spec, cujos testes têm marcadores de cenário
- **Quando:** a análise roda no modo sem spec
- **Então:** nenhum marcador é reportado como órfão, porque não há matriz com que
  compará-los
- **Entrada:** `argumento_spec = ""`, `marcador_cenario = "qualquer nome"`

## Caso: review encadeia check run e report num comando

- **Requisito:** "sentry review encadeia check, run, report e codigo de saida"
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** crítica
- **Dado:** um projeto com spec válida e suíte que passa
- **Quando:** o usuário roda `sentry review`
- **Então:** a saída traz a validação da spec e o relatório completo, numa só invocação
- **Entrada:** `argumento_spec = ""`

## Caso: review devolve o codigo de saida do veredito

- **Requisito:** "encadeia check, run, report e codigo de saida"
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** alta
- **Dado:** um projeto cuja análise termina em determinado veredito
- **Quando:** o usuário roda `sentry review`
- **Então:** o código de saída é o mesmo que o `run` devolveria para aquele veredito
- **Entrada:** `argumento_spec = ""`

## Caso: review roda em repositorio sem sentry e sem toml

- **Requisito:** "precisa funcionar num repositorio qualquer, sem .sentry e sem
  sentry.toml"
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** crítica
- **Dado:** um repositório sem `.sentry/` e sem `sentry.toml`
- **Quando:** o usuário roda `sentry review`
- **Então:** devolve relatório útil e código de saída, sem exigir preparo nenhum
- **Entrada:** `argumento_spec = ""`

## Caso: review com CASES.md invalido sai reprovado

- **Requisito:** o `check` faz parte da cadeia; spec quebrada precisa aparecer no veredito
  em vez de ser contornada
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** alta
- **Dado:** um projeto cujo CASES.md tem erro estrutural
- **Quando:** o usuário roda `sentry review`
- **Então:** a saída acusa o erro do CASES.md e o código de saída é o de reprovado
- **Entrada:** `argumento_spec = ""`

## Classes não aplicáveis

- **argumento_spec/tamanho-maximo-excedido**: o valor é um slug de diretório, limitado
  pelo sistema de arquivos; um slug longo demais simplesmente não existe em
  `.sentry/specs` e recai no caso de slug inexistente.
- **marcador_cenario/tamanho-maximo-excedido**: o marcador é comparado com o nome do caso
  declarado; comprimento não muda a comparação, e um nome longo que não casa recai no caso
  de marcador órfão.
- **arquivo_do_marcador/vazio**: nenhuma linha de teste alterada é o caso de marcador em
  linha intocada, já coberto — o conjunto vazio é justamente o que faz a regra se calar.
- **arquivo_do_marcador/tamanho-maximo-excedido**: o caminho vem do diff do Git, limitado
  pelo sistema de arquivos; comprimento não participa da decisão, que é pertencer ou não
  ao conjunto de arquivos alterados.
