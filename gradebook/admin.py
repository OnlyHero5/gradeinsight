from __future__ import annotations

from django.contrib import admin

from gradebook.models import Exam, ExamImport, ExamQuestionScore, ExamQuestionStat, ExamScore, Student


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ("name", "external_id", "class_name", "updated_at")
    search_fields = ("name", "external_id", "admission_ticket", "custom_exam_id")


@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ("name", "exam_date", "participants_n", "excluded_n", "imported_at")
    search_fields = ("name", "source_filename", "source_sha256")


@admin.register(ExamScore)
class ExamScoreAdmin(admin.ModelAdmin):
    list_display = ("exam", "student", "total_score", "excluded_from_stats")
    list_filter = ("excluded_from_stats",)


@admin.register(ExamQuestionScore)
class ExamQuestionScoreAdmin(admin.ModelAdmin):
    list_display = ("exam", "student", "question_key", "score_value")
    search_fields = ("question_key",)


@admin.register(ExamQuestionStat)
class ExamQuestionStatAdmin(admin.ModelAdmin):
    list_display = ("exam", "question_key", "mean_score", "median_score", "sample_n")
    search_fields = ("question_key",)


@admin.register(ExamImport)
class ExamImportAdmin(admin.ModelAdmin):
    list_display = ("id", "source_filename", "exam_name", "status", "created_at")
    list_filter = ("status",)
