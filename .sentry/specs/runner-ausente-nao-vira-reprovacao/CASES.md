# Runner ausente não vira reprovação

## Prompt

pytest ausente → reprovado em vez de inconclusivo — local_tools.py:86. Output foi literalmente No module named 'pytest', mas ele fabricou failed=1, deixou infrastructure_error=None, gerou achado test-failing crítica e saiu exit 2. É exatamente o caso que o design dele diz existir para evitar — e é a primeira execução de qualquer um, já que o próprio init avisou "pytest=ausente".

## Campos

- **codigo_saida**: inteiro — o código de saída do processo da suíte. Só 0 e 1
  são veredito de qualidade no pytest; o resto descreve ambiente ou configuração.
- **resumo_da_suite**: texto — a evidência de execução na saída do processo
  (`N passed`, `N failed`, `N skipped`) ou no relatório JUnit. Vazio significa que
  nenhum teste foi contabilizado, logo não há prova de que a suíte rodou.

## Caso: runner ausente sai como inconclusivo e nao como reprovacao

- **Requisito:** "pytest ausente → reprovado em vez de inconclusivo"; a saída foi
  literalmente `No module named 'pytest'`
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** crítica
- **Classe:** resumo_da_suite/vazio
- **Dado:** um projeto que declara `pytest` mas não tem o pacote instalado
- **Quando:** o Sentry executa a suíte e o processo termina com código 1 sem contabilizar teste algum
- **Então:** a execução sai como não executada, com erro de infraestrutura, e nenhuma
  reprovação é contada
- **Entrada:** `codigo_saida = 1`, `resumo_da_suite = ""`

## Caso: reprovacao real continua sendo reprovacao

- **Requisito:** o conserto não pode transformar falha de teste em inconclusivo
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** crítica
- **Classe:** resumo_da_suite/valido
- **Dado:** uma suíte pytest cujo resumo reporta testes contabilizados e uma falha
- **Quando:** o Sentry executa a suíte e o processo termina com código 1
- **Então:** a execução sai como reprovada, sem erro de infraestrutura, com a contagem do resumo
- **Entrada:** `codigo_saida = 1`, `resumo_da_suite = "1 failed, 2 passed"`

## Caso: suite aprovada permanece coberta

- **Requisito:** o caminho feliz não muda
- **Camada:** integração
- **Tipo:** integração
- **Prioridade:** alta
- **Classe:** codigo_saida/zero
- **Dado:** uma suíte pytest que passa inteira
- **Quando:** o Sentry executa a suíte
- **Então:** a execução sai como coberta, sem erro de infraestrutura e sem reprovação fabricada
- **Entrada:** `codigo_saida = 0`, `resumo_da_suite = "3 passed"`

## Caso: falha sem contagem no resumo ainda conta como reprovacao

- **Requisito:** só a ausência de qualquer teste contabilizado é inconclusiva; com
  prova de execução, saída não-zero continua sendo veredito de qualidade
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** alta
- **Classe:** codigo_saida/valido
- **Dado:** uma suíte que contabilizou testes mas cujo resumo não traz `N failed`
  (erro em teardown, por exemplo)
- **Quando:** o Sentry classifica a execução
- **Então:** a execução sai como reprovada, com pelo menos uma reprovação contada
- **Entrada:** `codigo_saida = 1`, `resumo_da_suite = "2 passed"`

## Caso: processo morto por sinal e inconclusivo

- **Requisito:** ambiente que derruba o processo não é qualidade do código
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** média
- **Classe:** codigo_saida/negativo
- **Dado:** uma suíte encerrada por sinal do sistema operacional, sem contabilizar teste
- **Quando:** o Sentry classifica a execução
- **Então:** a execução sai como não executada, com erro de infraestrutura
- **Entrada:** `codigo_saida = -9`, `resumo_da_suite = ""`

## Caso: saida longa e truncada sem perder o resumo

- **Requisito:** a evidência guardada é o fim da saída, onde o resumo do pytest fica
- **Camada:** backend
- **Tipo:** unitário
- **Prioridade:** baixa
- **Classe:** resumo_da_suite/tamanho-maximo-excedido
- **Dado:** uma suíte cuja saída excede o limite de evidência guardada
- **Quando:** o Sentry registra a execução
- **Então:** a evidência é truncada mas mantém o resumo final, e a contagem vem dele
- **Entrada:** `resumo_da_suite = "<80000 caracteres> 1 failed, 1 passed"`

## Classes não aplicáveis

- **codigo_saida/vazio**: o código de saída sempre existe quando o processo termina; a
  ausência de processo é o caminho de `OSError`, já coberto por outra spec.
- **codigo_saida/nao-numerico**: vem do sistema operacional como inteiro, nunca como texto.
- **codigo_saida/limite-superior**: qualquer código fora da tabela do pytest já cai na
  regra geral de "sem teste contabilizado"; não há limite superior próprio a verificar.
- **resumo_da_suite/caracteres-especiais**: a saída é lida com `errors="replace"` e o
  resumo é casado por expressão regular numérica; nenhum caractere muda a classificação.
