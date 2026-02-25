from __future__ import annotations

from django.db import models

from gradebook.models import Exam, Student


class Task(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name="tasks")
    name = models.CharField(max_length=255)
    question_key = models.CharField(max_length=32, blank=True)
    rule_json = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.name


class TaskAssignment(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="assignments")
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="task_assignments")
    submitted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["task", "student"], name="uniq_task_student"),
        ]
        indexes = [
            models.Index(fields=["task", "submitted_at"]),
        ]

    @property
    def is_submitted(self) -> bool:
        return self.submitted_at is not None
