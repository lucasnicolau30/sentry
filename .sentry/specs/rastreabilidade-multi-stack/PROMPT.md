Rastreabilidade (`build_traceability`) fora de Python: reconhecer definição de teste em
oito stacks (TS, Go, Java, Kotlin, C#, Ruby, PHP, Rust), aceitar o marcador `// cenario:`
(comentário de qualquer linguagem, não só `#`), permitir declarar `test_paths` quando o
projeto não usa a pasta `tests/` convencional, não deixar um arquivo de teste com bytes
inválidos derrubar a varredura dos demais, e nunca varrer `node_modules`/vendor em busca
de teste. E o casamento de marcador contra caso: sem normalizar acento um marcador correto
ficava preso em "não coberto"; e a associação por semelhança de nome de função tinha um
limiar frouxo demais, produzindo vínculo falso quando palavras genéricas (`sem`, `nada`,
`declarado`) somavam similaridade sem relação real de conteúdo.
