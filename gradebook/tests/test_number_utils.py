from __future__ import annotations

import pytest

from gradebook.services.number_utils import question_key_sort_key


@pytest.mark.parametrize(
    "key, expected",
    [
        ("1", (1, 0)),
        ("3", (3, 0)),
        ("10", (10, 0)),
        ("56(1)", (56, 1)),
        ("56(2)", (56, 2)),
        ("100(3)", (100, 3)),
        ("abc", (0, 0)),
    ],
)
def test_question_key_sort_key(key, expected):
    assert question_key_sort_key(key) == expected


def test_natural_sort_order():
    keys = ["1", "10", "2", "3(1)", "3(2)", "3", "20"]
    result = sorted(keys, key=question_key_sort_key)
    assert result == ["1", "2", "3", "3(1)", "3(2)", "10", "20"]
