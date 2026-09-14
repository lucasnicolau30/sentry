# todas as hunks do arquivo sao analisadas

So a ultima hunk de cada arquivo e analisada - local_tools.py:62, sobrescreve em vez de acumular. Fiz 2 hunks com raise (linhas 50 e 370); ele reportou apenas users/serializers.py:370. O caminho de erro do validate_telefone ficou invisivel.
