# caminho relativo declarado executa em qualquer grafia

No Windows, caminho relativo com barra normal nao executa. .venv/Scripts/python.exe -m pytest e reconhecido mas o CreateProcess nao resolve. Testei as quatro variantes: so relativo+/ quebra. O codigo normaliza barra invertida para barra normal para reconhecer (local_tools.py:230) mas passa args[0] cru para executar (:241).
