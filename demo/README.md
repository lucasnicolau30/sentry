# Demo Cadastro

App pequeno para ter um alvo real do `sentry training` e do `sentry manual`: login, CRUD de empresas e
CRUD de usuários, cada usuário ligado a uma empresa. Só biblioteca padrão do Python, banco SQLite em
`demo/demo.db` (criado na primeira execução e ignorado pelo Git).

```bash
python demo/app.py          # http://127.0.0.1:8800  (admin@demo.com / admin123)
sentry manual demo-usuarios # .sentry/manual/demo-usuarios-pt.pdf
sentry manual demo-empresas # .sentry/manual/demo-empresas-pt.pdf
```

Os roteiros estão em `.sentry/training/demo-usuarios.json` e `.sentry/training/demo-empresas.json`.
O manual lê do próprio app o nome (`application-name`), a cor (`theme-color`) e a logo (o ícone da
página), então o PDF sai com o cabeçalho e as cores do Demo Cadastro: branco e verde.

`DEMO_PORT` troca a porta; se trocar, ajuste o `base` dos roteiros.
