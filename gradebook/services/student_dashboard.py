from __future__ import annotations

from collections import defaultdict
from decimal import Decimal
from typing import Iterable

from gradebook.models import ExamScore, Student
from gradebook.services.number_utils import quantize_two
from worklists.models import TaskAssignment


def build_student_overview_rows() -> list[dict]:
    students = list(Student.objects.all().order_by("external_id"))
    if not students:
        return []

    student_ids = [item.id for item in students]
    scores = list(
        ExamScore.objects.filter(student_id__in=student_ids)
        .select_related("exam")
        .order_by("student_id")
    )
    assignments = list(
        TaskAssignment.objects.filter(student_id__in=student_ids)
        .select_related("task", "task__exam")
        .order_by("-task__created_at", "-id")
    )

    score_map = _group_by_student(scores)
    assignment_map = _group_by_student(assignments)
    rows: list[dict] = []

    for student in students:
        student_scores = sorted(score_map[student.id], key=_score_sort_key)
        latest_score = student_scores[-1] if student_scores else None
        valid_scores = _valid_total_scores(student_scores)
        student_assignments = assignment_map[student.id]
        completed_count = len([item for item in student_assignments if item.is_submitted])
        pending_count = len(student_assignments) - completed_count

        rows.append(
            {
                "student": student,
                "exam_count": len(student_scores),
                "latest_score": latest_score,
                "avg_total_score": _mean_or_none(valid_scores),
                "pending_task_count": pending_count,
                "completed_task_count": completed_count,
                "all_task_count": len(student_assignments),
            }
        )

    return rows


def build_student_task_snapshot(student: Student) -> dict:
    assignments = list(
        TaskAssignment.objects.filter(student=student)
        .select_related("task", "task__exam")
        .order_by("-task__created_at", "-id")
    )
    pending = [item for item in assignments if not item.is_submitted]
    completed = [item for item in assignments if item.is_submitted]

    return {
        "all_tasks": assignments,
        "pending_tasks": pending,
        "completed_tasks": completed,
        "task_summary": {
            "all": len(assignments),
            "pending": len(pending),
            "completed": len(completed),
        },
    }


def _group_by_student(rows: Iterable) -> defaultdict[int, list]:
    grouped: defaultdict[int, list] = defaultdict(list)
    for row in rows:
        grouped[row.student_id].append(row)
    return grouped


def _valid_total_scores(score_rows: list[ExamScore]) -> list[Decimal]:
    values = []
    for row in score_rows:
        if row.excluded_from_stats or row.total_score is None:
            continue
        values.append(row.total_score)
    return values


def _mean_or_none(values: list[Decimal]) -> Decimal | None:
    if not values:
        return None
    return quantize_two(sum(values) / len(values))


def _score_sort_key(item: ExamScore):
    if item.exam.exam_date is not None:
        return (item.exam.exam_date, item.exam.imported_at)
    return (item.exam.imported_at.date(), item.exam.imported_at)
