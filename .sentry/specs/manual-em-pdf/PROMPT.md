# manual-em-pdf

Comando sentry manual <modulo> [--lang pt|en]: lê o roteiro .sentry/training/<modulo>.json e gera um manual em PDF só de texto (fpdf2), sem vídeo, sem imagem e sem agente. Traz 'Antes de começar' com os dados que o usuário precisa (um por passo digitar, com o rótulo lido do próprio input na página: label, aria-label, placeholder) e o passo a passo com título e fala. Saída em .sentry/manual/<modulo>-<idioma>.pdf.
