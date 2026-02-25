from __future__ import annotations

from decimal import Decimal

from gradebook.services.weakness import classify_delta


def test_classify_delta() -> None:
    assert classify_delta(Decimal("-0.10")) == "weak"
    assert classify_delta(Decimal("0.10")) == "good"
    assert classify_delta(Decimal("0.00")) == "avg"
