from __future__ import annotations

from pathlib import Path

from gradebook.services.xlsx_parser import parse_exam_xlsx


def test_parse_exam_xlsx_extracts_question_keys_and_quality_hints() -> None:
    data = Path(
        "2025-2026学年度第一学期期末考试【八年级】(英语)-八年级7班.xlsx"
    ).read_bytes()

    parsed = parse_exam_xlsx(data)

    assert "51" in parsed.question_keys
    assert "51(3)" in parsed.question_keys
    assert parsed.student_count == 44
    assert parsed.excluded_from_stats_count >= 1
    assert parsed.mismatched_id_count >= 1
