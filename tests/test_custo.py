from sentrytest.application.reporting import markdown_report

def payload(**configuration):
    """Payload minimo de uma analise concluida. Cada teste acrescenta so' o campo
    da Fase 3 que ele cobra, para que a falha aponte o campo e nao o cenario inteiro."""
    return {'data': {
        'id': 'r1', 'project': 'demo', 'verdict': {'status': 'aprovado'},
        'timestamp': '2026-09-10T12:00:00+00:00', 'findings': [],
        'configuration': {'execution_mode': 'completo', **configuration},
    }}

def bloco_de_custo(report: str) -> str:
    assert '## Custo' in report
    return report.split('## Custo', 1)[1]

# cenario: relatorio traz o bloco de custo com zero token gasto
def test_bloco_de_custo_declara_zero_token_gasto():
    """Zero token e' a afirmacao central do produto: o Sentry cabe no loop porque
    nao disputa o orcamento de contexto com o agente. Se o numero some do relatorio,
    o argumento vira slide -- e' o proprio artefato que tem que emiti-lo."""
    custo = bloco_de_custo(markdown_report(payload()))
    assert 'Tokens gastos pelo Sentry: **zero**' in custo
    assert 'Nenhum modelo é chamado' in custo

# cenario: bloco de custo mede o tamanho do que o relatorio resumiu
def test_bloco_de_custo_mede_o_diff_resumido_e_o_proprio_relatorio():
    """Diff de tamanho conhecido: 8.000 caracteres sao 2.000 tokens a 4 por token.
    Conferir o numero exato e' o que separa 'o bloco existe' de 'o bloco mede'."""
    report = markdown_report(payload(
        git_change={'files': ['a.py'], 'diff_bytes': 8200, 'diff_chars': 8000}))
    custo = bloco_de_custo(report)
    assert 'Diff resumido: 8.200 bytes ≈ 2.000 tokens' in custo
    assert 'Este relatório:' in custo and 'medido sem este bloco de custo' in custo
    assert '× menor que o diff cru' in custo
    # A estimativa vai declarada como estimativa: numero de token sem tokenizer que
    # nao se anuncia aproximado seria lido como contagem.
    assert 'caracteres por token, sem tokenizer real' in custo

# cenario: bloco de custo mede o tamanho do que o relatorio resumiu
def test_tamanho_declarado_e_o_do_relatorio_sem_o_bloco_de_custo():
    """O relatorio se mede a si mesmo, entao o numero so' pode ser o do texto que
    existia antes do bloco. Cobrar a igualdade exata e' o que impede a versao
    conveniente do teste -- afirmar um tamanho proximo, mas falso."""
    report = markdown_report(payload(git_change={'files': ['a.py'], 'diff_bytes': 8200}))
    # `antes` e' literalmente o relatorio que teria sido entregue sem o bloco --
    # a linha em branco que separa as secoes ja fecha o texto anterior.
    antes, _, _ = report.partition('\n## Custo')
    declarado = len(antes.encode('utf-8'))
    assert f'Este relatório: {declarado:,}'.replace(',', '.') in report

# cenario: bloco de custo mede o tamanho do que o relatorio resumiu
def test_texto_do_diff_quando_presente_e_medido_na_fonte():
    """O caminho principal sao os dois inteiros -- persistir 62 KB de diff por
    execucao para imprimir duas linhas sairia mais caro que o bloco economiza. Mas
    quando o texto esta a mao, medi-lo dispensa confiar em numero de terceiros."""
    custo = bloco_de_custo(markdown_report(payload(
        git_change={'files': ['a.py'], 'diff': 'x' * 8000})))
    assert 'Diff resumido: 8.000 bytes ≈ 2.000 tokens' in custo

# cenario: cobertura reusada e declarada como da execucao anterior
def test_cobertura_reusada_se_declara_da_execucao_anterior():
    """O modo instantaneo nao mede cobertura; ele mostra a da ultima execucao
    completa. Sem o carimbo do instante, o numero de ontem se apresenta como
    medicao de agora -- a mesma armadilha do relatorio que envelhece sem avisar."""
    report = markdown_report(payload(
        execution_mode='instantâneo',
        coverage={'global_percent': 82.5, 'changed_percent': 70.0,
                  'reused_from': {'run_id': 'r0', 'timestamp': '2026-09-10T11:00:00+00:00'}}))
    contexto = report.split('## Contexto', 1)[1]
    for linha in [l for l in contexto.splitlines() if 'Cobertura' in l]:
        assert 'medida na execução anterior (2026-09-10T11:00:00+00:00)' in linha
        assert 'não nesta rodada' in linha

# cenario: cobertura reusada e declarada como da execucao anterior
def test_cobertura_medida_agora_nao_ganha_carimbo_de_reuso():
    """A contrapartida: acusar reuso onde houve medicao desta rodada desqualificaria
    evidencia boa, e o usuario aprenderia a ignorar o aviso."""
    report = markdown_report(payload(
        coverage={'global_percent': 82.5, 'changed_percent': 70.0, 'reused_from': None}))
    assert 'execução anterior' not in report

# cenario: execucao vinda do cache e declarada no relatorio
def test_execucao_do_cache_e_acusada_no_cabecalho():
    """Reusar sem dizer transforma evidencia velha em afirmacao nova. O aviso fica
    no cabecalho, junto do veredito, porque e' ali que se decide se o relatorio vale."""
    report = markdown_report(payload(
        from_cache=True, cached_from={'run_id': 'r0', 'timestamp': '2026-09-10T11:00:00+00:00'}))
    cabecalho = report.split('## Achados', 1)[0]
    assert 'reaproveitada do cache' in cabecalho
    assert 'r0' in cabecalho and '2026-09-10T11:00:00+00:00' in cabecalho
    assert 'nada foi executado agora' in cabecalho

# cenario: execucao vinda do cache e declarada no relatorio
def test_execucao_medida_agora_nao_se_diz_do_cache():
    report = markdown_report(payload(from_cache=False, cached_from=None))
    assert 'cache' not in report

# cenario: relatorio traz o bloco de custo com zero token gasto
def test_payload_antigo_sem_os_campos_da_fase_3_continua_rendendo():
    """Relatorio gravado antes da Fase 3 nao tem `from_cache` nem `reused_from`, e
    `sentry history` os re-renderiza. Quebrar ali perderia historico ja auditado."""
    antigo = {'data': {'id': 'r1', 'project': 'demo', 'verdict': {'status': 'aprovado'}, 'findings': []}}
    report = markdown_report(antigo)
    assert 'Tokens gastos pelo Sentry: **zero**' in report
    assert 'cache' not in report and 'execução anterior' not in report

# cenario: bloco de custo mede o tamanho do que o relatorio resumiu
def test_sem_o_tamanho_do_diff_o_bloco_declara_indisponivel_em_vez_de_estimar():
    """Fora de repositorio Git nao ha diff, e relatorio antigo nao gravou o tamanho.
    Deduzir bytes da lista de arquivos daria um numero plausivel e falso -- justamente
    no bloco que existe para provar que aqui se mede."""
    custo = bloco_de_custo(markdown_report(payload(git_change={'files': ['a.py', 'b.py']})))
    assert 'Diff resumido: indisponível' in custo
    assert 'inventar a medição' in custo
    assert '× menor que o diff cru' not in custo
    # O tamanho do proprio relatorio continua medido: ele existe independente do diff.
    assert 'Este relatório:' in custo

# cenario: bloco de custo mede o tamanho do que o relatorio resumiu
def test_diff_menor_que_o_relatorio_nao_e_anunciado_como_ganho():
    """Numero certo com leitura errada continua sendo relatorio errado: '0,4x menor'
    venderia como economia o caso em que nao ha o que resumir."""
    custo = bloco_de_custo(markdown_report(payload(git_change={'files': ['a.py'], 'diff_bytes': 40})))
    assert 'o relatório é maior que o diff' in custo
    assert '× menor que o diff cru' not in custo
