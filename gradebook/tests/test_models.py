from __future__ import annotations

from decimal import Decimal

import pytest
from django.db import IntegrityError

from gradebook.models import Exam, ExamQuestionScore, Student


@pytest.mark.django_db
def test_student_external_id_unique_in_system() -> None:
    Student.objects.create(
        name="A",
        external_id="1001",
        admission_ticket="1001",
        custom_exam_id="1001",
    )

    with pytest.raises(IntegrityError):
        Student.objects.create(
            name="B",
            external_id="1001",
            admission_ticket="1001",
            custom_exam_id="1001",
        )


@pytest.mark.django_db
def test_exam_question_score_unique_per_student_question() -> None:
    student = Student.objects.create(
        name="A",
        external_id="1002",
        admission_ticket="1002",
        custom_exam_id="1002",
    )
    exam = Exam.objects.create(name="E1", source_sha256="a" * 64)
    ExamQuestionScore.objects.create(
        exam=exam,
        student=student,
        question_key="51",
        score_value=Decimal("1.00"),
    )

    with pytest.raises(IntegrityError):
        ExamQuestionScore.objects.create(
            exam=exam,
            student=student,
            question_key="51",
            score_value=Decimal("2.00"),
        )
