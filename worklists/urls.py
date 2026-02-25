from __future__ import annotations

from django.urls import path

from worklists.views import (
    assignment_toggle,
    task_detail,
    task_export_pending_csv,
    task_list,
)

urlpatterns = [
    path("tasks/", task_list, name="task_list"),
    path("tasks/<int:task_id>/", task_detail, name="task_detail"),
    path(
        "tasks/<int:task_id>/assignments/<int:assignment_id>/toggle/",
        assignment_toggle,
        name="assignment_toggle",
    ),
    path(
        "tasks/<int:task_id>/export/pending.csv",
        task_export_pending_csv,
        name="task_export_pending_csv",
    ),
]
