from __future__ import annotations

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from gradebook.models import Exam, Student
from worklists.models import Task, TaskAssignment


@pytest.mark.django_db
def test_toggle_submission_marks_submitted(client) -> None:
    user_model = get_user_model()
    user_model.objects.create_user(username="t", password="p")
    assert client.login(username="t", password="p")

    student = Student.objects.create(
        name="A",
        external_id="1001",
        admission_ticket="1001",
        custom_exam_id="1001",
    )
    exam = Exam.objects.create(name="E", source_sha256="z" * 64)
    task = Task.objects.create(exam=exam, name="T", question_key="51", rule_json={})
    assignment = TaskAssignment.objects.create(task=task, student=student, submitted_at=None)

    response = client.post(
        reverse(
            "assignment_toggle",
            kwargs={"task_id": task.id, "assignment_id": assignment.id},
        )
    )

    assert response.status_code == 200
    assignment.refresh_from_db()
    assert assignment.submitted_at is not None
