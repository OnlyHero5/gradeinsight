from __future__ import annotations

from decimal import Decimal

import pytest

from gradebook.models import Exam, ExamQuestionScore, ExamQuestionStat, ExamScore, Student
from gradebook.services.question_filter import filter_students_by_question_rule


@pytest.fixture
def seeded_exam() -> tuple[Exam, Student, Student]:
    exam = Exam.objects.create(name="E", source_sha256="y" * 64)
    s1 = Student.objects.create(
        name="S1",
        external_id="1001",
        admission_ticket="1001",
        custom_exam_id="1001",
    )
    s2 = Student.objects.create(
        name="S2",
        external_id="1002",
        admission_ticket="1002",
        custom_exam_id="1002",
    )

    ExamScore.objects.create(
        exam=exam,
        student=s1,
        total_score=Decimal("60"),
        excluded_from_stats=False,
    )
    ExamScore.objects.create(
        exam=exam,
        student=s2,
        total_score=Decimal("80"),
        excluded_from_stats=False,
    )

    ExamQuestionScore.objects.create(
        exam=exam,
        student=s1,
        question_key="51",
        score_value=Decimal("1.0"),
    )
    ExamQuestionScore.objects.create(
        exam=exam,
        student=s2,
        question_key="51",
        score_value=Decimal("3.0"),
    )
    ExamQuestionStat.objects.create(
        exam=exam,
        question_key="51",
        mean_score=Decimal("2.0"),
        median_score=Decimal("2.0"),
        sample_n=2,
    )

    return exam, s1, s2


@pytest.mark.django_db
def test_filter_below_mean_returns_expected_students(seeded_exam: tuple[Exam, Student, Student]) -> None:
    exam, s1, s2 = seeded_exam

    result_ids = filter_students_by_question_rule(
        exam_id=exam.id,
        question_key="51",
        rule={"op": "below_mean"},
    )

    assert s1.id in result_ids
    assert s2.id not in result_ids
