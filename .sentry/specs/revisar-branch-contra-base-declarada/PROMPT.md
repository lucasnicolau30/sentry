# revisar branch contra base declarada

Nao da para revisar branch contra base - run so tem --spec e --run-tests; analyze chama change() sem referencia, entao e sempre git diff HEAD. O adapter aceita reference, mas nada expoe. Em PR ja commitada o diff sai vazio - o que limita muito o uso em CI.
