Robustez do `cli.py` em três situações adversas: `sentry check` sem `--spec`, quando o
projeto tem mais de uma spec, precisa recusar com erro explícito e código de saída 2, em
vez de escolher uma arbitrariamente; `stream.reconfigure` (usado pra forçar UTF-8 em
stdout/stderr) pode não existir ou falhar, e isso não pode impedir o resto do comando de
rodar; e `python -m sentrytest.cli` (o jeito de invocar quando o entry point não está no
PATH) precisa se comportar exatamente igual ao comando `sentry` instalado.
