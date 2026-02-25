from __future__ import annotations

from django.contrib import admin

from worklists.models import Task, TaskAssignment


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("name", "exam", "question_key", "created_at")
    search_fields = ("name", "question_key")


@admin.register(TaskAssignment)
class TaskAssignmentAdmin(admin.ModelAdmin):
    list_display = ("task", "student", "submitted_at")
    list_filter = ("submitted_at",)
