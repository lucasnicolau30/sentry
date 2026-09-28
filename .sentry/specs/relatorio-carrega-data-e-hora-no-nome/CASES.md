# Relatório carrega data e hora no nome

## Prompt

O arquivo `.sentry/reports/latest.md` passa a se chamar `latest-<id>.md`, onde `<id>` é a
data e hora da execução no formato `YYYYMMDD-HHMMSS` derivado do timestamp da run em
horário local da máquina. Continua sendo um arquivo só: a cada execução o `latest-*`
anterior sai e o novo entra com o nome atualizado, nunca acumula. As cópias permanentes
`{run_id}.md` e `{run_id}.json` seguem iguais, e o `run_id` continua sendo UUID. Os pontos
que hoje abrem o arquivo por nome fixo (`sentry report` e `sentry clear`) passam a
localizá-lo pelo padrão `latest-*.md`.

## Campos

- **id_de_data_e_hora**: data — o identificador `YYYYMMDD-HHMMSS` que nomeia o
  relatório, derivado do timestamp da execução convertido para o horário local
  da máquina.
- **relatorio_anterior**: booleano — se já existe um `latest-*.md` na pasta de
  relatórios antes da execução gravar o dela.
- **copias_permanentes**: booleano — os arquivos `{run_id}.md` e
  `{run_id}.json`, nomeados pelo UUID da execução, que preservam o histórico.
- **leitura_por_padrao**: booleano — se os comandos que hoje abrem o relatório
  por nome fixo o localizam pelo padrão `latest-*.md`.

## Caso: nome do relatorio carrega a data e hora da execucao

- **Requisito:** "O nome do arquivo passa a carregar a data e hora da execução
  em `YYYYMMDD-HHMMSS`" — é o nome que identifica a execução sem precisar abrir
  o arquivo
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** crítica
- **Classe:** id_de_data_e_hora/valida
- **Dado:** uma execução cujo timestamp corresponde a 22/09/2026 às 10:30:45 no
  horário local
- **Quando:** os relatórios são gravados
- **Então:** existe `.sentry/reports/latest-20260922-103045.md`, e não existe
  mais nenhum `latest.md` de nome fixo
- **Entrada:** `id_de_data_e_hora = 20260922-103045`

## Caso: id do relatorio sai do horario local e nao do utc gravado

- **Requisito:** "O id é derivado do timestamp da run, no horário local da
  máquina" — um id em UTC ao lado de um instante convertido mostraria dois
  horários diferentes para a mesma execução
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** alta
- **Classe:** id_de_data_e_hora/limite-inferior
- **Dado:** uma execução com timestamp gravado em UTC cuja conversão para o
  horário local cai no dia anterior
- **Quando:** o id do relatório é derivado desse timestamp
- **Então:** o id reflete a data e a hora locais, não as de UTC

## Caso: relatorio anterior sai quando o novo entra

- **Requisito:** "Continua sendo um arquivo só: a cada execução o `latest-*`
  anterior sai e o novo entra" — acumular um relatório por execução encheria o
  diretório e o repositório, que não é o comportamento de hoje
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** crítica
- **Classe:** relatorio_anterior/presente
- **Dado:** um `latest-20260922-091203.md` de uma execução anterior na pasta
- **Quando:** uma execução nova grava seu relatório
- **Então:** a pasta tem exatamente um arquivo `latest-*.md`, o da execução
  nova, e o anterior não existe mais

## Caso: primeira execucao grava sem anterior a remover

- **Requisito:** sem relatório anterior, gravar o primeiro não é erro nem
  trabalho extra
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** média
- **Classe:** relatorio_anterior/ausente
- **Dado:** uma pasta de relatórios sem nenhum `latest-*.md`
- **Quando:** a primeira execução grava seu relatório
- **Então:** o arquivo com o id da execução é criado e o comando termina com
  sucesso

## Caso: copias permanentes por run continuam gravadas

- **Requisito:** "As cópias permanentes `{run_id}.md` e `{run_id}.json` seguem
  iguais, e o `run_id` continua sendo UUID" — são elas que preservam o
  histórico, já que o `latest-*` é substituído a cada execução
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** alta
- **Classe:** copias_permanentes/presente
- **Dado:** uma execução registrada com seu UUID
- **Quando:** os relatórios são gravados
- **Então:** `{run_id}.md` e `{run_id}.json` existem com o UUID no nome, ao lado
  do `latest-<id>.md`

## Caso: comandos localizam o relatorio pelo padrao do nome

- **Requisito:** "Os pontos que hoje abrem o arquivo por nome fixo (`sentry
  report` e `sentry clear`) passam a localizá-lo pelo padrão `latest-*.md`" —
  sem isso, os dois procurariam um caminho que não existe mais
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** crítica
- **Classe:** leitura_por_padrao/presente
- **Dado:** um relatório gravado como `latest-20260922-103045.md`
- **Quando:** `sentry report` roda
- **Então:** o conteúdo desse relatório é exibido, sem erro de arquivo
  inexistente

## Caso: relatorio sem instante registrado ainda recebe nome proprio

- **Requisito:** sem instante de onde derivar o id, o relatório ainda precisa de
  um nome que o identifique — um nome montado sobre um valor ausente não
  localizaria nem distinguiria nada
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** média
- **Classe:** id_de_data_e_hora/vazio
- **Dado:** um payload de execução sem timestamp registrado
- **Quando:** os relatórios são gravados
- **Então:** o relatório atual é nomeado pelo identificador da execução, sem
  exceção levantada

## Caso: relatorio de nome fixo antigo sai na primeira execucao

- **Requisito:** quem vem de uma versão anterior tem um `latest.md` de nome fixo
  no repositório; deixado para trás ele seguiria versionado, afirmando um
  veredito antigo que nenhuma execução atualiza mais
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** alta
- **Classe:** relatorio_anterior/presente
- **Dado:** uma pasta de relatórios com o `latest.md` de nome fixo de uma versão
  anterior
- **Quando:** uma execução grava seu relatório
- **Então:** o `latest.md` não existe mais, e no lugar dele está o relatório
  nomeado pela data e hora da execução

## Classes não aplicáveis

- **id_de_data_e_hora/formato-invalido**: a data não é digitada por ninguém; ela
  vem do relógio da máquina já como objeto de data.
- **id_de_data_e_hora/inexistente**: mesma razão — não há entrada de usuário que
  possa nomear um dia que não existe no calendário.
- **id_de_data_e_hora/limite-superior**: o id não tem teto declarado; qualquer
  instante futuro produz um nome válido, sem regra de limite a verificar.
- **relatorio_anterior/vazio**: é um booleano derivado da existência do arquivo
  em disco — presente ou ausente, sem estado vazio próprio.
- **copias_permanentes/ausente**: as cópias são sempre gravadas junto com o
  relatório; não existe caminho em que a execução termine sem elas.
- **copias_permanentes/vazio**: mesma razão do booleano acima.
- **leitura_por_padrao/ausente**: a busca por padrão substitui o nome fixo; não
  resta caminho que ainda procure `latest.md`.
- **leitura_por_padrao/vazio**: mesma razão do booleano acima.
