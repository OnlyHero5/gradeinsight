from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from typing import Any

TWO_DECIMAL = Decimal("0.01")


def to_decimal(value: Any) -> Decimal | None:
    if value is None:
        return None
    if isinstance(value, Decimal):
        return value
    if isinstance(value, (int, float)):
        return Decimal(str(value))

    text = str(value).strip()
    if text == "":
        return None

    try:
        return Decimal(text)
    except Exception:
        return None


def to_int(value: Any) -> int | None:
    decimal_value = to_decimal(value)
    if decimal_value is None:
        return None

    try:
        return int(decimal_value)
    except Exception:
        return None


def quantize_two(value: Decimal) -> Decimal:
    return value.quantize(TWO_DECIMAL, rounding=ROUND_HALF_UP)
