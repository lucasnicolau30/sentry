"""Catálogo de classes de equivalência exigidas por tipo de campo.

O catálogo não gera casos: ele cobra os casos que o agente deixou de declarar.
A comparação é puramente determinística, sem inferência sobre texto livre.
"""
from __future__ import annotations

import unicodedata

FIELD_CLASSES: dict[str, tuple[str, ...]] = {
    "cpf": ("vazio", "letras", "tamanho-menor", "tamanho-maior", "digito-verificador-invalido", "valido-formatado", "valido-limpo"),
    "cnpj": ("vazio", "letras", "tamanho-menor", "tamanho-maior", "digito-verificador-invalido", "valido-formatado", "valido-limpo"),
    "email": ("vazio", "sem-arroba", "sem-dominio", "espacos", "valido"),
    "senha": ("vazio", "curta", "sem-numero", "sem-especial", "valida"),
    "data": ("vazio", "formato-invalido", "inexistente", "limite-inferior", "limite-superior", "valida"),
    "telefone": ("vazio", "letras", "tamanho-menor", "tamanho-maior", "valido"),
    "cep": ("vazio", "letras", "tamanho-invalido", "inexistente", "valido"),
    "inteiro": ("vazio", "nao-numerico", "negativo", "zero", "limite-superior", "valido"),
    "decimal": ("vazio", "nao-numerico", "negativo", "casas-excedentes", "valido"),
    "texto": ("vazio", "tamanho-maximo-excedido", "caracteres-especiais", "valido"),
    "rota": ("com-permissao", "sem-permissao", "nao-autenticado", "token-expirado"),
}


def _normalize(text: str) -> str:
    stripped = unicodedata.normalize("NFKD", text.strip().casefold())
    return "".join(char for char in stripped if not unicodedata.combining(char))


def merge_catalog(extra: dict | None) -> dict[str, tuple[str, ...]]:
    """Combina o catálogo padrão com tipos declarados em sentry.toml."""
    catalog = {key: value for key, value in FIELD_CLASSES.items()}
    for name, classes in (extra or {}).items():
        if isinstance(classes, (list, tuple)) and classes:
            catalog[_normalize(str(name))] = tuple(str(item) for item in classes)
    return catalog


def required_classes(field_type: str, catalog: dict[str, tuple[str, ...]] | None = None) -> tuple[str, ...]:
    return (catalog or FIELD_CLASSES).get(_normalize(field_type), ())


def missing_classes(fields, cases, catalog: dict[str, tuple[str, ...]] | None = None, not_applicable=()) -> tuple[dict, ...]:
    """Classes exigidas pelo catálogo que nenhum caso declarado cobre.

    `fields` são FieldSpec e `cases` são CaseSpec, ambos vindos de case_specs.
    Campos de tipo desconhecido são ignorados: o catálogo nunca inventa exigência.
    `not_applicable` (NotApplicableClass) marca classe/campo como dispensado com
    justificativa — não gera achado, mas também não conta como testado.
    """
    covered: dict[str, set[str]] = {}
    for case in cases:
        raw = getattr(case, "equivalence_class", None)
        if not raw or "/" not in raw:
            continue
        field_name, class_name = raw.split("/", 1)
        covered.setdefault(_normalize(field_name), set()).add(_normalize(class_name))

    justified = {(_normalize(item.field), _normalize(item.class_name)) for item in not_applicable}

    findings = []
    for field in fields:
        expected = required_classes(field.type, catalog)
        if not expected:
            continue
        seen = covered.get(_normalize(field.name), set())
        for class_name in expected:
            key_class = _normalize(class_name)
            if key_class in seen or (_normalize(field.name), key_class) in justified:
                continue
            findings.append({"field": field.name, "type": field.type, "class": class_name})
    return tuple(findings)


def unknown_field_types(fields, catalog: dict[str, tuple[str, ...]] | None = None) -> tuple[str, ...]:
    """Tipos declarados que o catálogo não conhece — viram limitação, não achado."""
    active = catalog or FIELD_CLASSES
    return tuple(sorted({field.type for field in fields if _normalize(field.type) not in active}))
