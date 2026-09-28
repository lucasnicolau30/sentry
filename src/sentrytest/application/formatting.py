"""Formatação de instantes para leitura humana.

O timestamp é gravado em ISO/UTC (`domain.models`): dado de máquina, ordenável e
sem ambiguidade de fuso. Aqui ele vira leitura -- convertido para o horário local
e escrito em formato brasileiro, com o fuso declarado, porque o relatório é
evidência auditável e um instante sem fuso é ambíguo para quem lê de outro lugar.

Único lugar que formata: o relatório em markdown e a listagem do `history` leem
daqui, senão as duas superfícies divergiriam com o tempo.
"""
from __future__ import annotations

from datetime import datetime, timedelta


def _offset_label(moment: datetime) -> str:
    """`(UTC-3)` para fuso de hora cheia, `(UTC+5:30)` quando há minutos."""
    offset = moment.utcoffset() or timedelta(0)
    total_minutes = int(offset.total_seconds() // 60)
    sign = "-" if total_minutes < 0 else "+"
    hours, minutes = divmod(abs(total_minutes), 60)
    return f"(UTC{sign}{hours}:{minutes:02d})" if minutes else f"(UTC{sign}{hours})"


def _parse(value: str) -> datetime | None:
    try:
        return datetime.fromisoformat(value)
    except (TypeError, ValueError):
        return None


def format_instant(value, fallback: str = "indisponível") -> str:
    """ISO armazenado -> `22/09/2026 07:30:45 (UTC-3)` no horário local.

    Valor ausente vira `fallback`; valor que não é ISO volta como está. Execução
    antiga no histórico não pode derrubar o comando que só queria exibi-la.
    """
    if not value:
        return fallback
    moment = _parse(value) if isinstance(value, str) else None
    if moment is None:
        return str(value)
    local = moment.astimezone()
    return f"{local:%d/%m/%Y %H:%M:%S} {_offset_label(local)}"


def report_slug(value) -> str | None:
    """ISO armazenado -> `20260922-103045`, o id que nomeia o relatório.

    Mesma conversão para horário local do `format_instant`: o nome do arquivo e o
    instante impresso dentro dele precisam falar do mesmo relógio.
    """
    if not value:
        return None
    moment = _parse(value) if isinstance(value, str) else None
    if moment is None:
        return None
    return f"{moment.astimezone():%Y%m%d-%H%M%S}"
