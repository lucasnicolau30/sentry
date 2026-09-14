# runner ausente nao vira reprovacao

pytest ausente -> reprovado em vez de inconclusivo - local_tools.py:86. Output foi literalmente No module named 'pytest', mas ele fabricou failed=1, deixou infrastructure_error=None, gerou achado test-failing critica e saiu exit 2. E exatamente o caso que o design dele diz existir para evitar - e e a primeira execucao de qualquer um, ja que o proprio init avisou pytest=ausente.
