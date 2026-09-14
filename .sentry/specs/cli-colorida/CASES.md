# CLI colorida

## Prompt

Deixar a saida do terminal da CLI mais bonita: cores ANSI no veredito (aprovado=verde,
aprovado com ressalvas=amarelo, reprovado=vermelho, inconclusivo=cinza/ciano), na
severidade dos achados (critica/alta=vermelho, media=amarelo, baixa=cinza), em sentry
check ([erro]=vermelho, [classe ausente]=amarelo, linha final de sucesso=verde) e em
sentry init (presente=verde, ausente=vermelho nas dependencias). Zero dependencia de
runtime nova -- codigos ANSI crus, sem colorama nem rich, seguindo o mesmo principio do
watch (pacote sem dependencia de runtime). Cor so aparece quando o stdout e um terminal
interativo (isatty), respeitando NO_COLOR (desliga sempre) e FORCE_COLOR (liga sempre,
mesmo sem tty -- para pipes que ainda querem cor, como less -R). O relatorio salvo em
disco (.sentry/reports/latest.md, e o retornado por --json) nunca pode conter codigo
ANSI -- a cor e' so' para o que vai para o terminal, nunca para o que e' persistido ou
parseado por maquina.

## Campos

- **suporte_a_cor**: texto — decide se a saída pode carregar código ANSI: `tty`
  (stdout interativo), `sem-tty` (redirecionado/pipe), `no-color` (variável
  `NO_COLOR` declarada) ou `force-color` (variável `FORCE_COLOR` declarada).
- **veredito_colorido**: texto — a cor aplicada ao veredito, uma das quatro:
  `verde` (aprovado), `amarelo` (aprovado com ressalvas), `vermelho` (reprovado),
  `cinza` (inconclusivo).
- **severidade_colorida**: texto — a cor aplicada ao rótulo de severidade de um
  achado: `vermelho` (crítica/alta), `amarelo` (média), `cinza` (baixa).

## Caso: cor desabilitada fora de terminal interativo

- **Requisito:** "Cor so aparece quando o stdout e um terminal interativo (isatty)"
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** crítica
- **Classe:** suporte_a_cor/vazio
- **Dado:** um stdout que não é um terminal interativo (`isatty()` falso), sem
  `NO_COLOR` nem `FORCE_COLOR` declaradas
- **Quando:** o texto é colorido
- **Então:** nenhum código ANSI aparece na saída
- **Entrada:** `suporte_a_cor = "sem-tty"`

## Caso: NO_COLOR desabilita mesmo em terminal interativo

- **Requisito:** "respeitando NO_COLOR (desliga sempre)"
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** crítica
- **Classe:** suporte_a_cor/valido
- **Dado:** um stdout interativo (`isatty()` verdadeiro) com `NO_COLOR` declarada
- **Quando:** o texto é colorido
- **Então:** nenhum código ANSI aparece na saída
- **Entrada:** `suporte_a_cor = "no-color"`

## Caso: FORCE_COLOR habilita mesmo sem terminal interativo

- **Requisito:** "FORCE_COLOR (liga sempre, mesmo sem tty -- para pipes que ainda
  querem cor, como less -R)"
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** alta
- **Classe:** suporte_a_cor/valido
- **Dado:** um stdout não interativo com `FORCE_COLOR` declarada
- **Quando:** o texto é colorido
- **Então:** o código ANSI aparece na saída
- **Entrada:** `suporte_a_cor = "force-color"`

## Caso: veredito aprovado sai verde

- **Requisito:** "aprovado=verde"
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** alta
- **Classe:** veredito_colorido/valido
- **Dado:** um veredito `aprovado`, com cor habilitada
- **Quando:** a linha do veredito é montada para o terminal
- **Então:** o texto do veredito é envolvido pelo código de cor verde
- **Entrada:** `veredito_colorido = "verde"`

## Caso: veredito aprovado com ressalvas sai amarelo

- **Requisito:** "aprovado com ressalvas=amarelo"
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** alta
- **Classe:** veredito_colorido/valido
- **Dado:** um veredito `aprovado com ressalvas`, com cor habilitada
- **Quando:** a linha do veredito é montada para o terminal
- **Então:** o texto do veredito é envolvido pelo código de cor amarelo
- **Entrada:** `veredito_colorido = "amarelo"`

## Caso: veredito reprovado sai vermelho

- **Requisito:** "reprovado=vermelho"
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** alta
- **Classe:** veredito_colorido/valido
- **Dado:** um veredito `reprovado`, com cor habilitada
- **Quando:** a linha do veredito é montada para o terminal
- **Então:** o texto do veredito é envolvido pelo código de cor vermelho
- **Entrada:** `veredito_colorido = "vermelho"`

## Caso: veredito inconclusivo sai cinza

- **Requisito:** "inconclusivo=cinza/ciano"
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** média
- **Classe:** veredito_colorido/valido
- **Dado:** um veredito `inconclusivo`, com cor habilitada
- **Quando:** a linha do veredito é montada para o terminal
- **Então:** o texto do veredito é envolvido pelo código de cor cinza
- **Entrada:** `veredito_colorido = "cinza"`

## Caso: achado critico ou alto sai vermelho

- **Requisito:** "na severidade dos achados (critica/alta=vermelho ...)"
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** alta
- **Classe:** severidade_colorida/valido
- **Dado:** um relatório com achados de severidade `crítica` e `alta`, com cor
  habilitada
- **Quando:** o relatório é colorido para o terminal
- **Então:** o rótulo de severidade de cada um é envolvido pelo código de cor
  vermelho
- **Entrada:** `severidade_colorida = "vermelho"`

## Caso: achado de media severidade sai amarelo

- **Requisito:** "media=amarelo"
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** média
- **Classe:** severidade_colorida/valido
- **Dado:** um relatório com um achado de severidade `média`, com cor habilitada
- **Quando:** o relatório é colorido para o terminal
- **Então:** o rótulo de severidade é envolvido pelo código de cor amarelo
- **Entrada:** `severidade_colorida = "amarelo"`

## Caso: relatorio salvo em disco nunca contem codigo ANSI

- **Requisito:** "O relatorio salvo em disco (.sentry/reports/latest.md, ...) nunca
  pode conter codigo ANSI"
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** crítica
- **Classe:** suporte_a_cor/valido
- **Dado:** uma análise concluída, impressa num terminal com cor habilitada
- **Quando:** o relatório é gravado em `.sentry/reports/latest.md`
- **Então:** o conteúdo do arquivo não contém nenhum código de escape ANSI
- **Entrada:** `suporte_a_cor = "tty"`

## Caso: sentry check colore erro de vermelho e sucesso de verde

- **Requisito:** "em sentry check ([erro]=vermelho ..., linha final de sucesso=verde)"
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** alta
- **Classe:** severidade_colorida/valido
- **Dado:** uma spec com erro estrutural e, noutra rodada, uma spec válida, com cor
  habilitada
- **Quando:** `sentry check` roda em cada uma
- **Então:** a linha `[erro]` sai vermelha na primeira, e a linha de sucesso sai
  verde na segunda
- **Entrada:** `severidade_colorida = "vermelho"`

## Caso: sentry init colore dependencia ausente de vermelho e presente de verde

- **Requisito:** "em sentry init (presente=verde, ausente=vermelho nas
  dependencias)"
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** média
- **Classe:** veredito_colorido/vazio
- **Dado:** a checagem de dependências com uma presente e uma ausente, com cor
  habilitada
- **Quando:** `sentry init` imprime a linha de dependências
- **Então:** `presente` sai verde e `ausente` sai vermelho
- **Entrada:** `veredito_colorido = "verde/vermelho"`

## Classes não aplicáveis

- **suporte_a_cor/tamanho-maximo-excedido**: o valor vem de um conjunto fechado de
  quatro estados decididos pelo ambiente, não texto digitado com comprimento a
  limitar.
- **suporte_a_cor/caracteres-especiais**: idem — não é entrada de usuário.
- **veredito_colorido/tamanho-maximo-excedido**: uma de quatro cores fixas do
  domínio, não texto livre.
- **veredito_colorido/caracteres-especiais**: idem.
- **severidade_colorida/vazio**: toda severidade do domínio (`Severity`) mapeia
  para uma cor; não existe achado sem severidade que chegue a este código.
- **severidade_colorida/tamanho-maximo-excedido**: uma de três cores fixas, não
  texto livre.
- **severidade_colorida/caracteres-especiais**: idem.
