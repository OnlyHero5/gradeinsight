from __future__ import annotations

from pathlib import Path

from gradebook.services.xls_parser import parse_exam_xls


def test_parse_exam_xls_extracts_question_keys_and_rows() -> None:
    data = Path(
        "2025-2026学年度第一学期期末考试【八年级】-英语-八7班-单科成绩单.xls"
    ).read_bytes()

    parsed = parse_exam_xls(data)

    assert parsed.student_count == 42
    assert parsed.excluded_from_stats_count == 0
    assert parsed.mismatched_id_count == 0
    assert "51" in parsed.question_keys
    assert "51(3)" in parsed.question_keys

    first = parsed.rows[0]
    assert first.name == "王煜宸"
    assert first.external_id == "59635260"
    assert first.total_score is not None
