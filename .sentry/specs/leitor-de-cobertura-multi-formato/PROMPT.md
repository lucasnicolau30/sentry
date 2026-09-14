`CoverageAdapter` reconhece três formatos de cobertura pelo próprio conteúdo (coverage.py
JSON, lcov, Cobertura XML), sem exigir que o projeto declare qual está usando. Precisa
distinguir "formato não reconhecido" de "formato certo porém malformado" (mensagens de
erro diferentes), rejeitar um relatório do formato certo mas sem nenhum registro real (0%
que na verdade é ausência de evidência), relativizar caminho absoluto do lcov contra a
raiz do projeto (preservando o caminho como veio quando cai fora da raiz, como em
monorepo), e não contar duas vezes a mesma linha quando um relatório lcov mesclado repete
`DA:` pra ela. A cobertura do código alterado (`calculate_changed_coverage`) precisa
funcionar igual a partir de um relatório lcov, não só de coverage.py.
