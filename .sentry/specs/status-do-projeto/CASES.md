# Sentry status — mapa da aplicação inteira

## Prompt

sentry status: comando que mede a aplicacao inteira como se tudo estivesse alterado, em
vez de so o diff. Reaproveita analyze() com um GitChange sintetico (whole_tree) que trata
todo arquivo de codigo-fonte rastreado como alterado (linhas 1..N inteiras), com --spec
all forcado, run_tests sempre True, e sem usar o cache local (medicao autoritativa). O
relatorio reusa markdown_report mas troca os rotulos de diff por rotulos de projeto
inteiro e acrescenta uma secao nova listando arquivos com 0% de cobertura (sem nenhum
teste alcancando), tirada do coverage.files ja existente. Marcador orfao passa a ser
detectado no projeto inteiro (nao so no diff), efeito colateral desejado desse modo.

## Campos

- **escopo_da_analise**: texto — `projeto_inteiro` (`sentry status`, todo arquivo de
  código tratado como alterado) ou `diff` (`sentry run`/`review`, o comportamento atual
  contra HEAD/base). Decide se a cobertura "alterada" repete a global e se marcador
  órfão é detectado fora do diff.
- **cobertura_do_arquivo**: decimal — percentual de cobertura de um arquivo individual,
  usado para decidir se ele entra na seção "arquivos sem nenhum teste alcançando".
- **fonte_da_medicao**: texto — `execucao_agora`, sempre. `sentry status` existe para
  ser a medição autoritativa do projeto inteiro; um resultado vindo do cache seria uma
  segunda maneira de responder a mesma pergunta.

## Caso: status reporta cobertura alterada igual a cobertura global

- **Requisito:** "GitChange sintetico ... que trata todo arquivo de codigo-fonte
  rastreado como alterado"
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** crítica
- **Classe:** escopo_da_analise/valido
- **Dado:** um projeto com cobertura medida e `sentry status`
- **Quando:** o relatório de status é gerado
- **Então:** a cobertura "alterada" reportada é igual à cobertura global, porque todo
  arquivo de código foi tratado como alterado
- **Entrada:** `escopo_da_analise = "projeto_inteiro"`

## Caso: sentry run comum nao trata a cobertura alterada como a global

- **Requisito:** contraste que prova que `status` não substituiu o comportamento normal
  de `run`/`review` — só some quando o escopo é o projeto inteiro
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** média
- **Classe:** escopo_da_analise/vazio
- **Dado:** um projeto com uma mudança pequena e cobertura global maior que a do diff
- **Quando:** `sentry run` mede o diff normal contra HEAD
- **Então:** a cobertura alterada reportada continua diferente da global
- **Entrada:** `escopo_da_analise = "diff"`

## Caso: arquivo com 0% de cobertura entra na secao de arquivos sem teste alcancando

- **Requisito:** "acrescenta uma secao nova listando arquivos com 0% de cobertura (sem
  nenhum teste alcancando)"
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** crítica
- **Classe:** cobertura_do_arquivo/vazio
- **Dado:** um `sentry status` cujo relatório de cobertura traz um arquivo com 0%
- **Quando:** o relatório de status é gerado
- **Então:** o arquivo aparece na seção "arquivos sem nenhum teste alcançando"
- **Entrada:** `cobertura_do_arquivo = 0.0`

## Caso: arquivo com cobertura maior que zero nao entra na secao

- **Requisito:** a seção existe para apontar ausência total de evidência, não para
  listar todo arquivo com cobertura imperfeita
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** alta
- **Classe:** cobertura_do_arquivo/valido
- **Dado:** um arquivo com 42% de cobertura no mesmo relatório
- **Quando:** o relatório de status é gerado
- **Então:** o arquivo não aparece na seção "arquivos sem nenhum teste alcançando"
- **Entrada:** `cobertura_do_arquivo = 42.0`

## Caso: marcador orfao em arquivo nao tocado aparece no status

- **Requisito:** "Marcador orfao passa a ser detectado no projeto inteiro (nao so no
  diff), efeito colateral desejado desse modo"
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** alta
- **Classe:** escopo_da_analise/valido
- **Dado:** um marcador `// cenario:` órfão num arquivo de teste sem nenhuma mudança
  recente
- **Quando:** `sentry status` roda
- **Então:** o achado de marcador órfão aparece para aquele arquivo
- **Entrada:** `escopo_da_analise = "projeto_inteiro"`

## Caso: mesmo marcador orfao nao aparece num sentry run comum

- **Requisito:** contraste que isola o efeito colateral ao modo `status` — `run`/`review`
  continuam escopados ao diff
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** média
- **Classe:** escopo_da_analise/vazio
- **Dado:** o mesmo marcador órfão, sem nenhum diff tocando aquele arquivo
- **Quando:** `sentry run` roda normalmente contra HEAD
- **Então:** nenhum achado de marcador órfão aparece para aquele arquivo
- **Entrada:** `escopo_da_analise = "diff"`

## Caso: status nunca reaproveita execucao do cache

- **Requisito:** "sem usar o cache local (medicao autoritativa)"
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** crítica
- **Classe:** fonte_da_medicao/valido
- **Dado:** uma execução completa recente cujo hash de entrada bateria com o cache de
  `sentry run`
- **Quando:** `sentry status` roda em seguida
- **Então:** a suíte é executada de novo, sem voltar do cache
- **Entrada:** `fonte_da_medicao = "execucao_agora"`

## Caso: fora de repositorio git status sai como erro de infraestrutura

- **Requisito:** o mesmo tratamento que `run`/`review` já dão à ausência de repositório
  Git — sem isso `status` inventaria "0 arquivos alterados" como se fosse um projeto
  vazio
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** crítica
- **Classe:** escopo_da_analise/caracteres-especiais
- **Dado:** um diretório que não é repositório Git
- **Quando:** `sentry status` roda
- **Então:** a execução registra erro de infraestrutura, sem inventar cobertura nem
  veredito
- **Entrada:** `escopo_da_analise = "projeto_inteiro"`

## Caso: status --json inclui o payload gravado pelo relatorio

- **Requisito:** paridade com os outros comandos que emitem `--json` (`new`, `context`)
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** média
- **Classe:** fonte_da_medicao/valido
- **Dado:** um `sentry status --json` concluído
- **Quando:** a saída é lida
- **Então:** o JSON traz o mesmo `Run` que o relatório em Markdown descreve
- **Entrada:** `fonte_da_medicao = "execucao_agora"`

## Classes não aplicáveis

- **escopo_da_analise/tamanho-maximo-excedido**: o campo é um de dois valores fechados
  decididos por qual comando chamou `analyze()`, não texto digitado com comprimento a
  limitar.
- **cobertura_do_arquivo/nao-numerico**: vem sempre do parser de cobertura
  (coverage.py/lcov/Cobertura) como número calculado, nunca como texto do usuário.
- **cobertura_do_arquivo/negativo**: percentual de cobertura é uma proporção de linhas
  executadas sobre linhas medidas — nunca negativo por construção.
- **cobertura_do_arquivo/casas-excedentes**: não há regra de formatação de entrada aqui;
  é um float bruto devolvido pelo parser, sem validação de casas decimais.
- **fonte_da_medicao/vazio**: `sentry status` sempre mede agora; não existe um terceiro
  estado a testar além de "mediu agora".
- **fonte_da_medicao/tamanho-maximo-excedido**: idem `escopo_da_analise` — valor fixo
  escolhido pelo código, não texto digitado.
- **fonte_da_medicao/caracteres-especiais**: idem — não é entrada de usuário.
