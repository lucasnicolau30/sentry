Duas garantias do `sentry init` sem spec formal: (1) ele instala `AGENT-SENTRY.md` na
raiz do projeto (diferente da skill, que fica em `.claude/skills/` e só o Claude Code lê
— este arquivo é pra qualquer agente de IA capaz de rodar comandos de shell), mencionando
`sentry new` como próximo passo; (2) o banco `.sentry/sentry.db` sai do `init` já no
schema atual, com a tabela `runs` pronta (sem isso, `sentry history` antes de qualquer
`run` tocaria numa tabela inexistente), e um banco de versão anterior é migrado pra versão
atual sem perder dados existentes de outras tabelas.
