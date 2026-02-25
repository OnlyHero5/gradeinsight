from __future__ import annotations

from django.db import models


class Student(models.Model):
    name = models.CharField(max_length=64)
    external_id = models.CharField(max_length=64, unique=True)
    admission_ticket = models.CharField(max_length=64, blank=True)
    custom_exam_id = models.CharField(max_length=64, blank=True)
    class_name = models.CharField(max_length=64, blank=True)
    note = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["external_id"]

    def __str__(self) -> str:
        return f"{self.name}({self.external_id})"


class Exam(models.Model):
    name = models.CharField(max_length=255)
    exam_date = models.DateField(null=True, blank=True)
    imported_at = models.DateTimeField(auto_now_add=True)
    source_filename = models.CharField(max_length=255, blank=True)
    source_sha256 = models.CharField(max_length=64, unique=True)
    participants_n = models.IntegerField(default=0)
    excluded_n = models.IntegerField(default=0)

    class Meta:
        ordering = ["-exam_date", "-imported_at"]

    def __str__(self) -> str:
        return self.name


class ExamScore(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name="scores")
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="exam_scores")
    total_score = models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True)
    total_raw = models.CharField(max_length=255, blank=True)
    objective_score = models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True)
    subjective_score = models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True)
    rank_in_class = models.IntegerField(null=True, blank=True)
    excluded_from_stats = models.BooleanField(default=False)
    exclude_reason = models.CharField(max_length=255, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["exam", "student"], name="uniq_exam_student"),
        ]
        indexes = [
            models.Index(fields=["exam", "excluded_from_stats"]),
        ]


class ExamQuestionScore(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name="question_scores")
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="question_scores")
    question_key = models.CharField(max_length=32)
    score_value = models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["exam", "student", "question_key"],
                name="uniq_exam_student_question",
            ),
        ]
        indexes = [
            models.Index(fields=["exam", "question_key"]),
            models.Index(fields=["exam", "question_key", "score_value"]),
        ]


class ExamQuestionStat(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name="question_stats")
    question_key = models.CharField(max_length=32)
    mean_score = models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True)
    median_score = models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True)
    sample_n = models.IntegerField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["exam", "question_key"], name="uniq_exam_question_stat"),
        ]
        indexes = [models.Index(fields=["exam", "question_key"])]


class ExamImport(models.Model):
    STATUS_STAGED = "staged"
    STATUS_IMPORTED = "imported"
    STATUS_FAILED = "failed"

    STATUS_CHOICES = [
        (STATUS_STAGED, "staged"),
        (STATUS_IMPORTED, "imported"),
        (STATUS_FAILED, "failed"),
    ]

    created_at = models.DateTimeField(auto_now_add=True)
    source_filename = models.CharField(max_length=255, blank=True)
    source_sha256 = models.CharField(max_length=64, unique=True)
    exam_name = models.CharField(max_length=255)
    exam_date = models.DateField(null=True, blank=True)
    preview_json = models.JSONField(default=dict)
    payload = models.BinaryField(default=bytes, blank=True)
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default=STATUS_STAGED)
    error = models.TextField(blank=True)
