# manual-em-pdf

Comando sentry manual [<modulo>] [--lang pt|en]: mantém o manual do usuário do projeto, um PDF só (.sentry/manual/manual-<idioma>.pdf) com uma seção por módulo, só texto (fpdf2), sem vídeo, sem imagem e sem agente. Cada módulo é uma seção em Markdown (.sentry/manual/secoes/<modulo>.md): os passos vêm do roteiro do training e são sincronizados a cada execução; a introdução, os avisos e os cartões são escritos à mão (ou pelo agente) e nunca são tocados. O PDF tem capa com sumário, uma seção por página, cabeçalho com logo e nome do app, rodapé e as cores do app.
