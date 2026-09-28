# relatorio carrega data e hora no nome

O arquivo .sentry/reports/latest.md passa a se chamar latest-<id>.md, onde <id> e a data e hora da execucao no formato YYYYMMDD-HHMMSS derivado do timestamp da run em horario local da maquina. Continua sendo um arquivo so: a cada execucao o latest-* anterior sai e o novo entra com o nome atualizado, nunca acumula. As copias permanentes {run_id}.md e {run_id}.json seguem iguais, e o run_id continua sendo UUID. Os pontos que hoje abrem o arquivo por nome fixo (sentry report e sentry clear) passam a localiza-lo pelo padrao latest-*.md.
