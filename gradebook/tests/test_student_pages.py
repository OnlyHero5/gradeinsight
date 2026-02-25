from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone

from gradebook.models import Exam, ExamScore, Student
from worklists.models import Task, TaskAssignment


@pytest.mark.django_db
def test_student_list_page_shows_exam_and_task_summary(client) -> None:
    user_model = get_user_model()
    user_model.objects.create_user(username="teacher-list", password="p")
    assert client.login(username="teacher-list", password="p")

    student_a = Student.objects.create(
        name="Student A",
        external_id="5001",
        admission_ticket="5001",
        custom_exam_id="5001",
        class_name="八年级7班",
    )
    student_b = Student.objects.create(
        name="Student B",
        external_id="5002",
        admission_ticket="5002",
        custom_exam_id="5002",
        class_name="八年级7班",
    )
    exam_1 = Exam.objects.create(name="E1", source_sha256="a" * 64)
    exam_2 = Exam.objects.create(name="E2", source_sha256="b" * 64)

    ExamScore.objects.create(
        exam=exam_1,
        student=student_a,
        total_score=Decimal("78"),
        rank_in_class=12,
    )
    ExamScore.objects.create(
        exam=exam_2,
        student=student_a,
        total_score=Decimal("89"),
        rank_in_class=5,
    )
    ExamScore.objects.create(
        exam=exam_1,
        student=student_b,
        total_score=Decimal("66"),
        rank_in_class=21,
    )

    task_1 = Task.objects.create(exam=exam_1, name="补做阅读", question_key="51", rule_json={})
    task_2 = Task.objects.create(exam=exam_2, name="补做听力", question_key="31", rule_json={})
    TaskAssignment.objects.create(task=task_1, student=student_a, submitted_at=None)
    TaskAssignment.objects.create(task=task_2, student=student_a, submitted_at=timezone.now())
    TaskAssignment.objects.create(task=task_1, student=student_b, submitted_at=None)

    response = client.get(reverse("student_list"))

    assert response.status_code == 200
    html = response.content.decode("utf-8")
    assert "学生档案" in html
    assert "Student A" in html
    assert "Student B" in html

    by_id = {row["student"].id: row for row in response.context["student_rows"]}
    assert by_id[student_a.id]["exam_count"] == 2
    assert by_id[student_a.id]["pending_task_count"] == 1
    assert by_id[student_a.id]["completed_task_count"] == 1
    assert by_id[student_b.id]["pending_task_count"] == 1


@pytest.mark.django_db
def test_student_detail_page_shows_task_completion_blocks(client) -> None:
    user_model = get_user_model()
    user_model.objects.create_user(username="teacher-detail", password="p")
    assert client.login(username="teacher-detail", password="p")

    student = Student.objects.create(
        name="Student Task",
        external_id="6001",
        admission_ticket="6001",
        custom_exam_id="6001",
        class_name="八年级7班",
    )
    exam = Exam.objects.create(name="Final", source_sha256="c" * 64)
    ExamScore.objects.create(
        exam=exam,
        student=student,
        total_score=Decimal("82"),
        rank_in_class=9,
    )

    task_pending = Task.objects.create(exam=exam, name="语法订正", question_key="41", rule_json={})
    task_done = Task.objects.create(exam=exam, name="作文重写", question_key="56", rule_json={})
    TaskAssignment.objects.create(task=task_pending, student=student, submitted_at=None)
    TaskAssignment.objects.create(
        task=task_done,
        student=student,
        submitted_at=timezone.now() - timedelta(hours=3),
    )

    response = client.get(reverse("student_detail", kwargs={"student_id": student.id}))

    assert response.status_code == 200
    html = response.content.decode("utf-8")
    assert "任务完成情况" in html
    assert "未完成任务" in html
    assert "已完成任务" in html
    assert "语法订正" in html
    assert "作文重写" in html

    summary = response.context["task_summary"]
    assert summary["pending"] == 1
    assert summary["completed"] == 1
