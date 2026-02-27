from __future__ import annotations

import csv

from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone

from worklists.models import Task, TaskAssignment


@login_required
def task_list(request):
    tasks = Task.objects.select_related("exam").annotate(
        total_count=Count("assignments"),
        submitted_count=Count("assignments", filter=Q(assignments__submitted_at__isnull=False)),
    )
    return render(request, "worklists/task_list.html", {"tasks": tasks})


@login_required
def task_detail(request, task_id: int):
    task = get_object_or_404(Task.objects.select_related("exam"), id=task_id)
    status_filter = request.GET.get("status", "all")

    assignments = TaskAssignment.objects.filter(task=task).select_related("student")
    if status_filter == "submitted":
        assignments = assignments.exclude(submitted_at__isnull=True)
    elif status_filter == "pending":
        assignments = assignments.filter(submitted_at__isnull=True)

    agg = TaskAssignment.objects.filter(task=task).aggregate(
        total=Count("id"),
        submitted=Count("id", filter=Q(submitted_at__isnull=False)),
    )
    counts = {
        "total": agg["total"],
        "submitted": agg["submitted"],
        "pending": agg["total"] - agg["submitted"],
    }

    context = {
        "task": task,
        "assignments": assignments.order_by("student__name"),
        "status_filter": status_filter,
        "counts": counts,
    }
    return render(request, "worklists/task_detail.html", context)


@login_required
def task_export_pending_csv(request, task_id: int):
    task = get_object_or_404(Task, id=task_id)
    rows = (
        TaskAssignment.objects.filter(task=task, submitted_at__isnull=True)
        .select_related("student")
        .order_by("student__name")
    )

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="task_{task.id}_pending.csv"'
    writer = csv.writer(response)
    writer.writerow(["姓名", "学号", "状态"])
    for row in rows:
        writer.writerow([row.student.name, row.student.external_id, "未交"])
    return response


@login_required
def assignment_toggle(request, task_id: int, assignment_id: int):
    assignment = get_object_or_404(TaskAssignment.objects.select_related("student", "task"), id=assignment_id, task_id=task_id)

    assignment.submitted_at = None if assignment.submitted_at else timezone.now()
    assignment.save(update_fields=["submitted_at"])

    return render(
        request,
        "worklists/_assignment_row.html",
        {"assignment": assignment, "task": assignment.task},
    )
