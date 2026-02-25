from __future__ import annotations

import pytest
from django.contrib.auth import get_user_model
from django.test import Client
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


@pytest.mark.django_db
def test_task_detail_includes_htmx_csrf_bridge(client) -> None:
    user_model = get_user_model()
    user_model.objects.create_user(username="t2", password="p")
    assert client.login(username="t2", password="p")

    student = Student.objects.create(
        name="B",
        external_id="1002",
        admission_ticket="1002",
        custom_exam_id="1002",
    )
    exam = Exam.objects.create(name="E2", source_sha256="x" * 64)
    task = Task.objects.create(exam=exam, name="T2", question_key="52", rule_json={})
    TaskAssignment.objects.create(task=task, student=student, submitted_at=None)

    response = client.get(reverse("task_detail", kwargs={"task_id": task.id}))
    html = response.content.decode("utf-8")

    assert response.status_code == 200
    assert "htmx:configRequest" in html
    assert "X-CSRFToken" in html


@pytest.mark.django_db
def test_toggle_submission_requires_csrf_header_under_csrf_checks() -> None:
    user_model = get_user_model()
    user_model.objects.create_user(username="t3", password="p")

    student = Student.objects.create(
        name="C",
        external_id="1003",
        admission_ticket="1003",
        custom_exam_id="1003",
    )
    exam = Exam.objects.create(name="E3", source_sha256="w" * 64)
    task = Task.objects.create(exam=exam, name="T3", question_key="53", rule_json={})
    assignment = TaskAssignment.objects.create(task=task, student=student, submitted_at=None)

    csrf_client = Client(enforce_csrf_checks=True)
    csrf_client.get(reverse("login"))
    assert csrf_client.login(username="t3", password="p")

    url = reverse("assignment_toggle", kwargs={"task_id": task.id, "assignment_id": assignment.id})

    denied = csrf_client.post(url, HTTP_HX_REQUEST="true")
    assert denied.status_code == 403

    csrf_token = csrf_client.cookies["csrftoken"].value
    success = csrf_client.post(
        url,
        HTTP_HX_REQUEST="true",
        HTTP_X_CSRFTOKEN=csrf_token,
    )
    assert success.status_code == 200
