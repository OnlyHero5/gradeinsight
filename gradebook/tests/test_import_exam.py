from __future__ import annotations

from pathlib import Path

import pytest

from gradebook.models import ExamQuestionStat, ExamScore, Student
from gradebook.services.import_exam import import_exam_from_excel_bytes, import_exam_from_xlsx_bytes

DATASET_DIR = Path("测试数据集")


@pytest.mark.django_db
def test_import_creates_exam_and_question_stats() -> None:
    data = (
        DATASET_DIR
        / "2025-2026学年度第一学期期末考试【八年级】(英语)-八年级7班.xlsx"
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
    data = (
        DATASET_DIR
        / "2025-2026学年度第一学期期末考试【八年级】-英语-八7班-单科成绩单.xls"
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


@pytest.mark.django_db
def test_import_total_only_xlsx_creates_exam_without_question_stats() -> None:
    path = DATASET_DIR / "（必）八年级英语模拟1(英语)-八年级7班(1).xlsx"

    exam = import_exam_from_excel_bytes(
        path.read_bytes(),
        exam_name="英语模拟1",
        exam_date=None,
        source_filename=path.name,
    )

    assert exam.participants_n == 44
    assert exam.excluded_n >= 1
    assert ExamQuestionStat.objects.filter(exam=exam).count() == 0
    assert ExamScore.objects.filter(exam=exam).count() == 44


@pytest.mark.django_db
def test_import_total_only_xlsx_merges_student_by_name_when_ids_missing() -> None:
    detail_path = DATASET_DIR / "2025-2026学年度第一学期期末考试【八年级】(英语)-八年级7班.xlsx"
    total_only_path = DATASET_DIR / "（必）2025年秋学期八年级英语模拟卷2(英语)-八年级7班.xlsx"

    detail_exam = import_exam_from_excel_bytes(
        detail_path.read_bytes(),
        exam_name="英语期末",
        exam_date=None,
        source_filename=detail_path.name,
    )

    assert detail_exam.participants_n == 44
    student_count_before = Student.objects.count()

    total_only_exam = import_exam_from_excel_bytes(
        total_only_path.read_bytes(),
        exam_name="英语模拟2",
        exam_date=None,
        source_filename=total_only_path.name,
    )

    assert total_only_exam.participants_n == 44
    assert Student.objects.count() == student_count_before
    student = Student.objects.get(name="曹庭玮")
    assert ExamScore.objects.filter(student=student).count() == 2
