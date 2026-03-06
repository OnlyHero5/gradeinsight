from __future__ import annotations

from pathlib import Path

from gradebook.services.xls_parser import parse_exam_xls

DATASET_DIR = Path("测试数据集")


def test_parse_exam_xls_extracts_question_keys_and_rows() -> None:
    data = (
        DATASET_DIR
        / "2025-2026学年度第一学期期末考试【八年级】-英语-八7班-单科成绩单.xls"
    ).read_bytes()

    parsed = parse_exam_xls(data)

    assert parsed.student_count == 42
    assert parsed.excluded_from_stats_count == 0
    assert parsed.mismatched_id_count == 0
    assert "51" in parsed.question_keys
    assert "51(3)" in parsed.question_keys
    assert parsed.identity_key
    assert parsed.identity_label

    first = parsed.rows[0]
    assert first.name == "王煜宸"
    assert first.external_id == "59635260"
    assert first.total_score is not None


def test_parse_xls_and_xlsx_final_exam_share_identity_key() -> None:
    from gradebook.services.excel_parser import parse_exam_excel

    xlsx_path = DATASET_DIR / "2025-2026学年度第一学期期末考试【八年级】(英语)-八年级7班.xlsx"
    xls_path = DATASET_DIR / "2025-2026学年度第一学期期末考试【八年级】-英语-八7班-单科成绩单.xls"

    xlsx_parsed = parse_exam_excel(xlsx_path.read_bytes(), source_filename=xlsx_path.name)
    xls_parsed = parse_exam_excel(xls_path.read_bytes(), source_filename=xls_path.name)

    assert xlsx_parsed.identity_key == xls_parsed.identity_key
