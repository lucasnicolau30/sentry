# interpretador declarado e respeitado

O interpretador declarado e descartado - local_tools.py:157. Declarei .venv/Scripts/python.exe -m pytest, arquivo que nao existe, e ele rodou o Python global sem avisar. Regressao do commit novo: antes essa grafia caia no caminho generico e rodava como declarado. Mata o uso em qualquer projeto com venv.
