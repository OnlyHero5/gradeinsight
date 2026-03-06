from __future__ import annotations

from pathlib import Path

import pytest

from gradebook.services.excel_parser import parse_exam_excel
from gradebook.services.xlsx_parser import parse_exam_xlsx


DATASET_DIR = Path("测试数据集")


def test_parse_exam_xlsx_extracts_question_keys_and_quality_hints() -> None:
    data = (
        DATASET_DIR
        / "2025-2026学年度第一学期期末考试【八年级】(英语)-八年级7班.xlsx"
    ).read_bytes()

    parsed = parse_exam_xlsx(data)

    assert "51" in parsed.question_keys
    assert "51(3)" in parsed.question_keys
    assert parsed.student_count == 44
    assert parsed.excluded_from_stats_count >= 1
    assert parsed.mismatched_id_count >= 1


def test_parse_second_detail_xlsx_dataset_file() -> None:
    path = DATASET_DIR / "期末模拟3.xlsx"

    parsed = parse_exam_excel(path.read_bytes(), source_filename=path.name)

    assert parsed.student_count == 44
    assert len(parsed.question_keys) >= 40
    assert parsed.excluded_from_stats_count >= 1
    assert parsed.mismatched_id_count >= 1


def test_parse_total_only_xlsx_from_summary_sheet() -> None:
    path = DATASET_DIR / "（必）八年级英语模拟1(英语)-八年级7班(1).xlsx"

    parsed = parse_exam_excel(path.read_bytes(), source_filename=path.name)

    assert parsed.student_count == 44
    assert parsed.question_keys == []
    assert parsed.excluded_from_stats_count >= 1
    assert parsed.mismatched_id_count >= 1
    assert parsed.rows[0].name == "曹庭玮"
    assert parsed.rows[0].external_id == "59631020"
    assert parsed.rows[0].rank_in_class is not None


@pytest.mark.parametrize(
    "filename",
    [
        "（必）2025年秋学期八年级英语模拟卷2(英语)-八年级7班.xlsx",
        "（必）八年级英语模拟1(英语)-八年级7班.xlsx",
    ],
)
def test_parse_total_only_xlsx_from_simple_sheet(filename: str) -> None:
    path = DATASET_DIR / filename

    parsed = parse_exam_excel(path.read_bytes(), source_filename=path.name)

    assert parsed.student_count == 44
    assert parsed.question_keys == []
    assert parsed.excluded_from_stats_count >= 1
    assert parsed.mismatched_id_count == 0
    assert parsed.rows[0].name == "曹庭玮"
    assert parsed.rows[0].rank_in_class is None
