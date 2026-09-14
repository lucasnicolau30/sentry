`sentry clear` poda execuções e relatórios antigos com segurança: sem `--yes`, só mostra o
que sairia (apagar histórico é irreversível, o padrão precisa mostrar o escopo antes de
destruir); com `--yes`, remove os arquivos de execução (`.sentry/runs/*.json`,
`.sentry/reports/*.md`, `.sentry/reports/*.json`) e as linhas da tabela `runs`, mas nunca
toca em `.sentry/specs/` (intenção declarada pelo usuário, não evidência gerada);
`--keep-last N` preserva as N execuções mais recentes; e sem nenhum histórico, o comando
não inventa trabalho nem erro, só avisa que não há nada a remover.
