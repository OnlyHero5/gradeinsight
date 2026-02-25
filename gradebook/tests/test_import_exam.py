from __future__ import annotations

from pathlib import Path

import pytest

from gradebook.models import ExamQuestionStat
from gradebook.services.import_exam import import_exam_from_excel_bytes, import_exam_from_xlsx_bytes


@pytest.mark.django_db
def test_import_creates_exam_and_question_stats() -> None:
    data = Path(
        "2025-2026学年度第一学期期末考试【八年级】(英语)-八年级7班.xlsx"
    ).read_bytes()

    exam = import_exam_from_xlsx_bytes(
        data,
        exam_name="英语期末",
        exam_date=None,
        source_filename="sample.xlsx",
    )

    stat = ExamQuestionStat.objects.get(exam=exam, question_key="51")
    assert stat.sample_n > 0
    assert stat.mean_score is not None


@pytest.mark.django_db
def test_import_xls_creates_exam_and_question_stats() -> None:
    data = Path(
        "2025-2026学年度第一学期期末考试【八年级】-英语-八7班-单科成绩单.xls"
    ).read_bytes()

    exam = import_exam_from_excel_bytes(
        data,
        exam_name="英语期末-xls",
        exam_date=None,
        source_filename="sample.xls",
    )

    stat = ExamQuestionStat.objects.get(exam=exam, question_key="51")
    assert exam.participants_n == 42
    assert stat.sample_n == 42
    assert stat.mean_score is not None
