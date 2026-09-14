Detecção de caminhos de erro (`select_error_paths`) fora de Python: reconhecer `throw`,
`panic`, `raise`/`rescue` e assemelhados por padrão sintático ancorado no início da linha,
já que fora de Python não há parser AST na biblioteca padrão -- e declarar essa diferença
de confiabilidade como limitação, não escondê-la atrás da mesma evidência do AST. Palavra
de erro dentro de comentário ou string não pode virar falso caminho de erro. Uma linha
excluída da medição (`# pragma: no cover`) não pode virar achado de "caminho sem teste" --
mas a exclusão é por linha, não contamina as vizinhas nem o arquivo inteiro. E uma extensão
sem padrão declarado (YAML, texto puro) fica fora da análise, sem falso positivo nem
limitação fabricada.
