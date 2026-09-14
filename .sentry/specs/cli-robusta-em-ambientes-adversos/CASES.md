# CLI robusta em ambientes adversos

## Prompt

Robustez do `cli.py` em três situações adversas: `sentry check` sem `--spec`, quando o
projeto tem mais de uma spec, precisa recusar com erro explícito e código de saída 2, em
vez de escolher uma arbitrariamente; `stream.reconfigure` (usado pra forçar UTF-8 em
stdout/stderr) pode não existir ou falhar, e isso não pode impedir o resto do comando de
rodar; e `python -m sentrytest.cli` (o jeito de invocar quando o entry point não está no
PATH) precisa se comportar exatamente igual ao comando `sentry` instalado.

## Campos

- **quantidade_de_specs**: inteiro — quantas specs existem no projeto
  quando `sentry check` roda sem `--spec` declarado.
- **suporte_a_reconfigure**: booleano — se `sys.stdout`/`sys.stderr` no
  ambiente onde o comando roda tem o método `reconfigure` disponível.
- **forma_de_invocacao**: texto — como o CLI foi chamado (`sentry ...` via
  entry point, ou `python -m sentrytest.cli ...`).

## Caso: check com multiplas specs sem --spec imprime erro e retorna 2

- **Requisito:** sem `--spec`, mais de uma spec no projeto é ambiguidade,
  não escolha implícita
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** alta
- **Classe:** quantidade_de_specs/multiplas
- **Dado:** um projeto com duas specs criadas (`sentry new` duas vezes)
- **Quando:** `sentry check` roda sem `--spec`
- **Então:** a saída contém `"Erro:"` e o comando devolve o código 2
- **Entrada:** `quantidade_de_specs = 2`

## Caso: falha ao reconfigurar stdout/stderr nao impede o comando de rodar

- **Requisito:** "stream.reconfigure pode nao existir (AttributeError) ou
  falhar (OSError): nenhum dos dois pode impedir o resto do comando de
  rodar"
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** média
- **Classe:** suporte_a_reconfigure/ausente
- **Dado:** `sys.stdout`/`sys.stderr` substituídos por um stream sem
  `reconfigure` (`io.StringIO`)
- **Quando:** `main([])` roda
- **Então:** o comando termina normalmente, código de saída 0

## Caso: rodar como modulo (-m) executa o mesmo CLI

- **Requisito:** paridade entre `sentry` (entry point) e
  `python -m sentrytest.cli`
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** média
- **Classe:** forma_de_invocacao/valido
- **Dado:** o comando `python -m sentrytest.cli --version`, executado num
  subprocesso
- **Quando:** o subprocesso termina
- **Então:** o código de saída é 0 e a saída é a mesma versão que
  `__version__`

## Classes não aplicáveis

- **quantidade_de_specs/vazio**: nenhuma spec no projeto já é caminho
  coberto noutro caso (spec ausente vira infraestrutura, não este erro de
  ambiguidade).
- **quantidade_de_specs/tamanho-maximo-excedido**: contagem de diretórios,
  não texto digitado com comprimento a limitar.
- **suporte_a_reconfigure/verdadeiro**: o caminho feliz (stream normal, com
  `reconfigure` funcionando) é o comportamento padrão em todo outro teste
  do CLI, não uma classe de erro a testar aqui.
- **forma_de_invocacao/vazio**: o CLI sempre é invocado de alguma forma;
  não existe "nenhuma forma de invocação" a testar.
- **forma_de_invocacao/tamanho-maximo-excedido**: a forma de invocação é
  um de dois caminhos fixos do código, não texto digitado.
- **forma_de_invocacao/caracteres-especiais**: idem — não é entrada de
  usuário, é decisão de como o processo foi iniciado.
