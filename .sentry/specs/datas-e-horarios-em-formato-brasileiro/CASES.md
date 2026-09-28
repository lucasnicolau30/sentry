# Datas e horários no formato brasileiro

## Prompt

Timestamps exibidos ao usuário (cabeçalho do relatório, nota de cache reaproveitado,
`sentry history`) passam a sair no formato brasileiro `DD/MM/AAAA HH:MM:SS` com o fuso
declarado, ex.: `22/09/2026 07:30:45 (UTC-3)`, convertido para o horário local da
máquina. O armazenamento continua em ISO/UTC no modelo e no JSON. Microssegundos somem
da exibição mas permanecem no JSON. Ids de run não são formatados, só timestamps. Um
timestamp ausente ou fora do padrão ISO nunca quebra o comando: sai como está ou como
"indisponível". Fuso com minutos quebrados (ex.: Índia, UTC+5:30) sai por extenso, não
truncado.

## Campos

- **instante**: data — o timestamp gravado em ISO/UTC, convertido para o
  horário local da máquina na exibição.
- **fuso_horario**: texto — o offset UTC declarado junto do instante
  formatado, derivado do próprio horário local da máquina.
- **identificador_de_run**: texto — o UUID da run, que nunca passa pelo
  helper de formatação de data.
- **cache_reaproveitado**: booleano — se a nota de reaproveitamento de cache
  também usa o helper de formatação de instante.

## Caso: instante do cabecalho sai em formato brasileiro com fuso

- **Requisito:** "Formato: DD/MM/AAAA HH:MM:SS com o fuso declarado — ex.:
  22/09/2026 07:30:45 (UTC-3)"
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** crítica
- **Classe:** instante/valida
- **Dado:** um timestamp ISO/UTC com microssegundos
- **Quando:** o relatório em markdown é gerado
- **Então:** a linha "Analisado em:" traz o instante no formato brasileiro com
  o fuso entre parênteses, sem a data ISO original

## Caso: microssegundos somem da exibicao e ficam no armazenamento

- **Requisito:** "Microssegundos: somem da exibição (`19:52:57.634585` →
  `19:52:57`), permanecem no JSON"
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** alta
- **Classe:** instante/valida
- **Dado:** um timestamp ISO/UTC com microssegundos
- **Quando:** o instante é formatado para exibição e o payload é serializado
  em JSON
- **Então:** os microssegundos não aparecem no texto exibido, mas continuam
  presentes no JSON

## Caso: nota de cache reaproveitado tambem sai formatada

- **Requisito:** "Helper compartilhado: a formatação vira um único helper
  usado por `application/reporting.py` e `cli.py`"
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** alta
- **Classe:** cache_reaproveitado/presente
- **Dado:** um relatório reaproveitado de uma execução anterior
- **Quando:** o relatório em markdown é gerado
- **Então:** a nota de cache reaproveitado cita a execução anterior com o
  instante já no formato brasileiro, nas duas linhas de cobertura reusada,
  sem o ISO original

## Caso: history lista execucoes com a data formatada

- **Requisito:** "São 3 pontos no código do report (mais o `history`)"
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** alta
- **Classe:** instante/valida
- **Dado:** uma run persistida no banco com timestamp ISO/UTC
- **Quando:** `sentry history` é executado
- **Então:** a listagem traz o instante no formato brasileiro, sem o ISO
  original

## Caso: instante ausente nao quebra a formatacao

- **Requisito:** "Valores legados e ausentes: o helper precisa aguentar sem
  quebrar (...) os fallbacks que já existem hoje (`None`)"
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** alta
- **Classe:** instante/vazio
- **Dado:** um timestamp ausente (`None`)
- **Quando:** o instante é formatado
- **Então:** o resultado é "indisponível", e o relatório traz "Analisado em:
  indisponivel" sem quebrar

## Caso: timestamp gravado fora do padrao nao quebra a formatacao

- **Requisito:** "Valores legados: o helper precisa aguentar sem quebrar os
  timestamps ISO já gravados nas runs antigas"
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** média
- **Classe:** instante/formato-invalido
- **Dado:** um valor que não é um timestamp ISO válido
- **Quando:** o instante é formatado
- **Então:** o valor original é devolvido sem alteração e sem exceção

## Caso: identificador de run continua sem formatacao

- **Requisito:** "Ids não são formatados: a linha `- Run: <uuid>` (...) fica
  como está. Só timestamps ganham formato BR"
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** média
- **Classe:** identificador_de_run/valido
- **Dado:** um relatório com um `run_id` UUID
- **Quando:** o relatório em markdown é gerado
- **Então:** a linha "Run:" traz o UUID intocado

## Caso: fuso com minutos quebrados sai declarado por extenso

- **Requisito:** "Fuso: (...) declarado junto porque o report é evidência
  auditável"
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** média
- **Classe:** fuso_horario/valido
- **Dado:** um instante com fuso de minutos quebrados (UTC+5:30) e outro com
  fuso de hora cheia (UTC-3)
- **Quando:** o rótulo do fuso é derivado do instante
- **Então:** o de minutos quebrados sai por extenso (`UTC+5:30`), e o de hora
  cheia sai sem minutos (`UTC-3`)

## Classes não aplicáveis

- **instante/inexistente**: o instante vem sempre do timestamp que o próprio
  Sentry grava (ISO válido) ou de dado legado; não há entrada de usuário
  digitando uma data de calendário inválida.
- **instante/limite-inferior**: não há intervalo mínimo aceito — qualquer
  instante passado é formatado.
- **instante/limite-superior**: não há intervalo máximo aceito — não existe
  regra de "data futura demais" para este campo.
- **fuso_horario/vazio**: o fuso é sempre derivado do horário local da
  máquina no momento da exibição, nunca digitado por usuário.
- **fuso_horario/tamanho-maximo-excedido**: mesma razão acima — não é texto
  livre com limite de tamanho.
- **fuso_horario/caracteres-especiais**: mesma razão acima — não é entrada de
  usuário.
- **identificador_de_run/vazio**: o `run_id` é gerado internamente
  (`uuid.uuid4()`), nunca chega vazio a este ponto.
- **identificador_de_run/tamanho-maximo-excedido**: UUID tem tamanho fixo,
  não é texto livre.
- **identificador_de_run/caracteres-especiais**: mesma razão acima — não é
  entrada de usuário.
