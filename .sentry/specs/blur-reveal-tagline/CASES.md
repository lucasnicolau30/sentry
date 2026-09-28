# Tagline do Hero com efeito BlurReveal (spell-ui)

## Prompt

Adicionar o componente BlurReveal do spell-ui (via pnpm dlx shadcn@latest add
@spell/blur-reveal) ao frontend, exibindo o texto 'A disciplina entre o commit e a
confianca' com efeito de blur reveal. Decisao registrada com o usuario: rodar
`pnpm dlx shadcn@latest init` primeiro (cria components.json, alias `@/` e o
utilitario `cn()`) e so entao `add @spell/blur-reveal`, em vez de reimplementar o
efeito manualmente.

## Campos

- **tagline**: texto — conteúdo fixo (`t("A disciplina entre", "The discipline between")` /
  `t("o commit e a confiança", "commit and confidence")` de `Hero.tsx`), não é input do
  usuário; substitui o `<h1>` atual mantendo o texto e o `t()` de i18n (pt/en).
- **layout**: responsivo — o texto deve permanecer legível nos breakpoints já usados em
  `Hero.tsx` (`sm:text-5xl`).
- **motion**: acessibilidade — o efeito de blur reveal não pode impedir a leitura do
  texto para quem usa `prefers-reduced-motion` nem para leitores de tela.

## Caso: hero exibe a tagline em PT com efeito blur reveal

- **Requisito:** o texto `t()` em português aparece dentro do `BlurReveal` no lugar do `<h1>` atual
- **Camada:** frontend
- **Tipo:** e2e
- **Prioridade:** alta
- **Classe:** tagline/valido
- **Dado:** a landing page carregada com idioma pt
- **Quando:** o Hero é renderizado
- **Então:** o texto "A disciplina entre o commit e a confiança" fica visível, dentro do componente BlurReveal, preservando a quebra de linha atual

## Caso: hero exibe a tagline em EN com efeito blur reveal

- **Requisito:** o texto `t()` em inglês aparece dentro do `BlurReveal` quando o idioma é trocado
- **Camada:** frontend
- **Tipo:** e2e
- **Prioridade:** alta
- **Classe:** tagline/valido
- **Dado:** a landing page carregada com idioma en
- **Quando:** o Hero é renderizado
- **Então:** o texto "The discipline between commit and confidence" fica visível, dentro do componente BlurReveal

## Caso: tagline permanece legível em mobile

- **Requisito:** o BlurReveal não quebra o layout responsivo existente do Hero
- **Camada:** frontend
- **Tipo:** e2e
- **Prioridade:** média
- **Classe:** layout/mobile
- **Dado:** viewport mobile (375px)
- **Quando:** o Hero é renderizado
- **Então:** o texto não estoura o container nem sobrepõe outros elementos

## Caso: tagline permanece legível em tablet

- **Requisito:** o BlurReveal não quebra o layout responsivo existente do Hero
- **Camada:** frontend
- **Tipo:** e2e
- **Prioridade:** média
- **Classe:** layout/tablet
- **Dado:** viewport tablet (768px)
- **Quando:** o Hero é renderizado
- **Então:** o texto não estoura o container nem sobrepõe outros elementos

## Caso: tagline permanece legível em desktop

- **Requisito:** o BlurReveal não quebra o layout responsivo existente do Hero
- **Camada:** frontend
- **Tipo:** e2e
- **Prioridade:** média
- **Classe:** layout/desktop
- **Dado:** viewport desktop (1280px)
- **Quando:** o Hero é renderizado
- **Então:** o texto não estoura o container nem sobrepõe outros elementos

## Caso: texto acessível independentemente da animação

- **Requisito:** o efeito de blur reveal não esconde o conteúdo de quem usa `prefers-reduced-motion` ou leitor de tela
- **Camada:** frontend
- **Tipo:** e2e
- **Prioridade:** alta
- **Classe:** motion/contraste
- **Dado:** `prefers-reduced-motion: reduce` ativo no navegador
- **Quando:** o Hero é renderizado
- **Então:** o texto da tagline está presente no DOM e legível (sem depender da animação já ter concluído) e o contraste contra o fundo `--bg` permanece igual ao `<h1>` atual

## Classes não aplicáveis

- **tagline/vazio**: campo é conteúdo fixo do código-fonte, não input de usuário — não há estado "vazio" a testar
- **tagline/tamanho-maximo-excedido**: texto é constante definida no código, não sofre truncamento dinâmico
- **tagline/caracteres-especiais**: texto fixo já validado no código-fonte (acento "ç" tratado como texto normal, não input arbitrário)
- **motion/foco-visivel**: BlurReveal envolve um `<h1>` estático, não introduz elemento focável
- **motion/navegacao-teclado**: idem — nenhum controle interativo é adicionado
- **motion/rotulo-associado**: não há input/controle de formulário associado a este componente
