from __future__ import annotations

from django.urls import path

from gradebook.views import (
    exam_detail,
    exam_list,
    import_confirm,
    import_upload,
    question_filter,
    student_detail,
)

urlpatterns = [
    path("exams/", exam_list, name="exam_list"),
    path("exams/<int:exam_id>/", exam_detail, name="exam_detail"),
    path("exams/<int:exam_id>/filter/", question_filter, name="question_filter"),
    path("students/<int:student_id>/", student_detail, name="student_detail"),
    path("import/", import_upload, name="import_upload"),
    path("import/<int:import_id>/confirm/", import_confirm, name="import_confirm"),
]
