# Arquivo visual por rota

## Prompt

O archive vira um versionador do estado visual da aplicação, não só evidência de teste.
Um módulo declarado em sentry.toml como [modules.<nome>] com rotas = [...] é fotografado
abrindo cada rota com Playwright (print da página inteira em desktop e mobile, vídeo da
navegação opcional), um módulo por pasta em .sentry/storage/<modulo>-<versao>/, mesmo que
o módulo nunca tenha sido testado pelo Sentry. Módulos com login = true fazem o login
declarado em [archive.login] (rota, seletores de usuário, senha e botão; credenciais em
SENTRY_LOGIN_USUARIO e SENTRY_LOGIN_SENHA, nunca no toml) antes de fotografar. Se o módulo
tiver specs, a suíte roda e o README carimba o veredito (reprovado não arquiva); sem
specs, o README diz que é registro visual sem certificação. Módulos antigos declarados
como lista de specs continuam como antes. Estado que a URL não alcança (dados no banco,
modal aberto por clique) fica para depois.

## Campos

- **rotas_do_modulo**: texto — a lista de rotas declaradas em `[modules.<nome>]`
  que o comando fotografa, uma por vez, cada uma numa pasta própria dentro do
  módulo arquivado.
- **login_do_modulo**: booleano — se o módulo exige sessão antes de fotografar,
  lido de `login = true` em `[modules.<nome>]`.
- **configuracao_de_login**: texto — a declaração em `[archive.login]` (rota,
  seletor de usuário, seletor de senha, seletor do botão de envio) usada para
  autenticar antes de fotografar módulos com `login = true`.
- **credenciais_de_login**: texto — usuário e senha lidos de
  `SENTRY_LOGIN_USUARIO`/`SENTRY_LOGIN_SENHA`, nunca do `sentry.toml`.
- **certificacao_do_modulo**: booleano — se o módulo tem specs associadas
  (composição antiga por `--specs`/`[modules]`) e portanto roda a suíte e
  carimba veredito, em vez de ser só registro visual.
- **resultado_da_captura**: booleano — se alguma rota do módulo falhou ao ser
  fotografada (rota inexistente, servidor fora do ar); as demais rotas
  continuam sendo fotografadas mesmo assim.

## Caso: modulo declarado por rotas fotografa cada rota numa pasta propria

- **Requisito:** "Um módulo declarado em sentry.toml como [modules.<nome>] com
  rotas = [...] é fotografado abrindo cada rota com Playwright... um módulo
  por pasta"
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** crítica
- **Classe:** rotas_do_modulo/valido
- **Dado:** um módulo declarado com `rotas = ["/login", "/usuarios"]` e sem
  `login`
- **Quando:** `sentry archive` roda para esse módulo
- **Então:** existe uma subpasta de mídia por rota (`login/`, `usuarios/`)
  dentro de `.sentry/storage/<modulo>-<versao>/`, cada uma com o print da
  rota correspondente
- **Entrada:** `rotas_do_modulo = /login,/usuarios`

## Caso: cada rota fotografada gera print em desktop e mobile

- **Requisito:** "print da página inteira em desktop e mobile"
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** alta
- **Classe:** rotas_do_modulo/valido
- **Dado:** um módulo declarado com uma única rota
- **Quando:** a rota é fotografada
- **Então:** a pasta da rota recebe dois prints, um em viewport desktop e
  outro em viewport mobile, nomeados de forma a distinguir os dois

## Caso: modulo sem specs e registro visual sem certificacao

- **Requisito:** "sem specs, o README diz que é registro visual sem
  certificação... mesmo que o módulo nunca tenha sido testado pelo Sentry"
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** crítica
- **Classe:** certificacao_do_modulo/ausente
- **Dado:** um módulo declarado só com `rotas`, sem specs associadas
- **Quando:** `sentry archive` roda para esse módulo
- **Então:** nenhuma suíte é executada, nenhum veredito é exigido, e o
  README diz explicitamente que é um registro visual sem certificação

## Caso: modulo com specs roda a suite e carimba veredito

- **Requisito:** "Se o módulo tiver specs, a suíte roda e o README carimba o
  veredito (reprovado não arquiva)"
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** crítica
- **Classe:** certificacao_do_modulo/presente
- **Dado:** um módulo declarado com `rotas` e também com specs associadas
- **Quando:** `sentry archive` roda para esse módulo
- **Então:** a suíte e2e das specs roda antes da fotografia, e o README
  carimba o veredito da execução

## Caso: modulo com specs e reprovado nao arquiva nada

- **Requisito:** "reprovado não arquiva" — reafirma para o modo por rotas a
  mesma regra já válida no arquivo por specs
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** crítica
- **Classe:** certificacao_do_modulo/presente
- **Dado:** um módulo declarado com `rotas` e specs cuja execução reprova
- **Quando:** `sentry archive` roda para esse módulo
- **Então:** nada é escrito em `.sentry/storage/` e o comando sai com o
  código do veredito

## Caso: modulo com login true autentica antes de fotografar

- **Requisito:** "Módulos com login = true fazem o login declarado em
  [archive.login]... antes de fotografar"
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** crítica
- **Classe:** login_do_modulo/presente
- **Dado:** um módulo com `login = true` e `[archive.login]` declarado no
  `sentry.toml`, com credenciais válidas nas variáveis de ambiente
- **Quando:** `sentry archive` roda para esse módulo
- **Então:** o Playwright visita a rota de login, preenche os seletores
  declarados, envia o formulário, e só então visita as rotas do módulo
  autenticado

## Caso: modulo sem login true nao tenta autenticar

- **Requisito:** implícito — módulos sem `login = true` continuam
  fotografando rotas públicas sem tentar nenhum fluxo de autenticação
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** alta
- **Classe:** login_do_modulo/ausente
- **Dado:** um módulo declarado por rotas sem `login = true`
- **Quando:** `sentry archive` roda para esse módulo
- **Então:** nenhuma tentativa de login ocorre, e as rotas são visitadas
  diretamente

## Caso: login true sem configuracao de login declarada e recusado

- **Requisito:** "Módulos com login = true fazem o login declarado em
  [archive.login]" — sem a declaração não há como autenticar
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** alta
- **Classe:** configuracao_de_login/ausente
- **Dado:** um módulo com `login = true` mas nenhum `[archive.login]` no
  `sentry.toml`
- **Quando:** `sentry archive` roda para esse módulo
- **Então:** o comando recusa antes de abrir qualquer navegador, dizendo que
  falta `[archive.login]`

## Caso: login true sem credenciais em variavel de ambiente e recusado

- **Requisito:** "credenciais em SENTRY_LOGIN_USUARIO e SENTRY_LOGIN_SENHA,
  nunca no toml" — sem elas no ambiente não há com o que preencher o
  formulário
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** alta
- **Classe:** credenciais_de_login/ausente
- **Dado:** um módulo com `login = true` e `[archive.login]` declarado, mas
  sem `SENTRY_LOGIN_USUARIO`/`SENTRY_LOGIN_SENHA` no ambiente
- **Quando:** `sentry archive` roda para esse módulo
- **Então:** o comando recusa antes de abrir qualquer navegador, dizendo
  quais variáveis de ambiente faltam

## Caso: credenciais de login nunca sao gravadas no toml

- **Requisito:** "nunca no toml"
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** crítica
- **Classe:** credenciais_de_login/valido
- **Dado:** credenciais válidas em `SENTRY_LOGIN_USUARIO`/`SENTRY_LOGIN_SENHA`
- **Quando:** o módulo é arquivado com sucesso
- **Então:** nem o `sentry.toml` nem o README gerado contêm o valor das
  credenciais em texto

## Caso: modulo declarado por lista de specs continua como antes

- **Requisito:** "Módulos antigos declarados como lista de specs continuam
  como antes"
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** crítica
- **Classe:** rotas_do_modulo/ausente
- **Dado:** um módulo já declarado em `[modules]` como lista de specs (forma
  antiga), sem `rotas`
- **Quando:** `sentry archive` roda para esse módulo
- **Então:** o comportamento é exatamente o do arquivamento por specs já
  existente, sem passar pela fotografia por rota

## Caso: rota que falha vira ressalva sem derrubar o arquivo

- **Requisito:** implícito — uma rota inexistente ou um servidor fora do ar
  não deveria apagar a evidência das rotas que funcionaram, mas também não é
  honesto sair como se tudo tivesse dado certo
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** alta
- **Classe:** resultado_da_captura/presente
- **Dado:** um módulo com duas rotas, uma delas inexistente
- **Quando:** `sentry archive` roda para esse módulo
- **Então:** a rota que funcionou é fotografada normalmente, a que falhou
  aparece como "falhou" na tabela do README, e o comando sai com o código de
  ressalva (1), não de sucesso pleno

## Caso: captura que nao consegue executar o node vira erro claro

- **Requisito:** "uma rota que falhou não é sucesso: o comando recusa com erro claro em vez de
  arquivar um módulo incompleto ou quebrar com traceback"
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** alta
- **Classe:** resultado_da_captura/presente
- **Dado:** um módulo com rotas e um Node que não executa (binário ausente ou tempo esgotado)
- **Quando:** a captura de rotas roda
- **Então:** o erro diz que não foi possível executar a captura de rotas e nada fica pela metade na pasta (o `_captura.json` temporário some)

## Caso: captura que sai com codigo diferente de zero vira erro claro

- **Requisito:** "uma rota que falhou não é sucesso: o comando recusa com erro claro em vez de
  arquivar um módulo incompleto ou quebrar com traceback"
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** alta
- **Classe:** resultado_da_captura/presente
- **Dado:** um script de captura que termina com código diferente de zero e escreve no stderr
- **Quando:** a captura de rotas roda
- **Então:** o erro diz que a captura falhou e repete a mensagem do script

## Caso: captura que devolve saida que nao e json vira erro claro

- **Requisito:** "uma rota que falhou não é sucesso: o comando recusa com erro claro em vez de
  arquivar um módulo incompleto ou quebrar com traceback"
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** alta
- **Classe:** resultado_da_captura/presente
- **Dado:** um script de captura que termina bem mas imprime texto que não é JSON
- **Quando:** a captura de rotas roda
- **Então:** o erro diz que a captura não devolveu JSON válido e mostra o começo da saída

## Caso: captura que devolve manifesto com erro vira erro claro

- **Requisito:** "uma rota que falhou não é sucesso: o comando recusa com erro claro em vez de
  arquivar um módulo incompleto ou quebrar com traceback"
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** alta
- **Classe:** resultado_da_captura/presente
- **Dado:** um script de captura que devolve um manifesto com o campo `erro` preenchido
- **Quando:** a captura de rotas roda
- **Então:** o erro diz que a captura falhou com o motivo do manifesto

## Caso: modulo com rotas vazia e recusado

- **Requisito:** "uma rota que falhou não é sucesso: o comando recusa com erro claro em vez de
  arquivar um módulo incompleto ou quebrar com traceback"
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** alta
- **Classe:** resultado_da_captura/presente
- **Dado:** um módulo declarado com `rotas = []`
- **Quando:** o arquivo por rotas roda
- **Então:** o erro pede ao menos uma rota em `[modules.<nome>]` e nenhuma pasta é criada

## Caso: archive por rotas sai com infra quando a analise das specs falha

- **Requisito:** "uma rota que falhou não é sucesso: o comando recusa com erro claro em vez de
  arquivar um módulo incompleto ou quebrar com traceback"
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** alta
- **Classe:** resultado_da_captura/presente
- **Dado:** um módulo por rotas com `specs` apontando para uma spec inexistente
- **Quando:** `sentry archive` roda para esse módulo
- **Então:** o comando mostra o erro, sai com o código de infraestrutura e não fotografa nada

## Caso: archive por rotas sai com infra quando a captura falha

- **Requisito:** "uma rota que falhou não é sucesso: o comando recusa com erro claro em vez de
  arquivar um módulo incompleto ou quebrar com traceback"
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** alta
- **Classe:** resultado_da_captura/presente
- **Dado:** um módulo por rotas cuja captura levanta erro
- **Quando:** `sentry archive` roda para esse módulo
- **Então:** o comando mostra o erro e sai com o código de infraestrutura, sem declarar sucesso

## Caso: captura espera as animacoes e fotografa a pagina ja revelada

- **Requisito:** "espere as animações e tire os prints" — o print mostra a página no estado final, não no meio da entrada nem com o conteúdo abaixo da primeira tela ainda escondido
- **Camada:** frontend
- **Tipo:** integração
- **Prioridade:** alta
- **Classe:** rotas_do_modulo/valido
- **Dado:** uma rota longa cujo conteúdo abaixo da primeira tela só aparece quando entra na janela (animação de entrada por rolagem, que se desfaz quando sai dela)
- **Quando:** a rota é fotografada em desktop e em mobile
- **Então:** o print de página inteira mostra o conteúdo de baixo, depois que as animações terminam (inclusive texto digitado letra a letra, que o Sentry espera até a página parar de mudar), e não uma faixa em branco; o que o Sentry faz para isso (tratar todo elemento observado como visível) é dito no README do módulo
- **Entrada:** `rotas_do_modulo = /docs?tab=setup`

## Caso: readme do modulo avisa que as animacoes de entrada foram disparadas

- **Requisito:** a evidência não deve fingir ser o que um visitante vê no primeiro instante da página
- **Camada:** integração
- **Tipo:** unitário
- **Prioridade:** média
- **Classe:** rotas_do_modulo/valido
- **Dado:** um módulo declarado por rotas, com ou sem specs
- **Quando:** o README do módulo arquivado é escrito
- **Então:** a seção Limitações diz que as animações de entrada por rolagem são disparadas todas antes do print, então a página aparece já revelada
- **Entrada:** `rotas_do_modulo = /usuarios`

## Classes não aplicáveis

- **rotas_do_modulo/caracteres-especiais**: rota é texto livre que vira nome
  de pasta sanitizado; não há formato de rota cobrado além de existir.
- **rotas_do_modulo/tamanho-maximo-excedido**: não há limite de quantidade de
  rotas por módulo.
- **rotas_do_modulo/vazio**: coberta pelo caso de "módulo declarado por lista
  de specs continua como antes" — `rotas` ausente não é erro, é o formato
  antigo de módulo, sem fotografia por rota.
- **login_do_modulo/vazio**: é um booleano com padrão `false`; não tem estado
  vazio próprio.
- **configuracao_de_login/valido**: coberta pelo caso de autenticação bem
  sucedida acima — não há classe própria de equivalência além de
  presente/ausente para uma declaração de seletores.
- **configuracao_de_login/vazio**: mesma razão de `ausente` acima — `[archive.login]`
  não declarado e declarado em branco recebem o mesmo tratamento (recusa
  antes de abrir o navegador).
- **configuracao_de_login/tamanho-maximo-excedido**: os valores são seletores
  CSS/rota fixos escritos por quem configura o projeto, não input de usuário
  final; não há limite de tamanho cobrado.
- **configuracao_de_login/caracteres-especiais**: seletor CSS é, por
  natureza, feito de caracteres especiais (`#`, `.`, `[`, `]`); não há
  formato a recusar aqui.
- **credenciais_de_login/vazio**: mesma razão de `ausente` acima — variável
  de ambiente ausente e variável vazia recebem o mesmo tratamento (recusa
  antes de abrir o navegador).
- **credenciais_de_login/tamanho-maximo-excedido**: a credencial é opaca ao
  Sentry — só é repassada ao formulário de login, nunca validada quanto a
  tamanho.
- **credenciais_de_login/caracteres-especiais**: mesma razão acima — a
  credencial é opaca ao Sentry, que não interpreta seu conteúdo.
- **certificacao_do_modulo/vazio**: é um booleano derivado de o módulo ter ou
  não specs associadas, sem estado vazio próprio.
