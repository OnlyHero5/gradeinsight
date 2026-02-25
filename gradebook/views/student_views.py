from __future__ import annotations

import json

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render

from gradebook.models import ExamScore, Student
from gradebook.services.weakness import build_question_deltas


@login_required
def student_detail(request, student_id: int):
    student = get_object_or_404(Student, id=student_id)
    score_rows = list(ExamScore.objects.filter(student=student).select_related("exam"))
    score_rows.sort(key=_score_sort_key)

    trend_labels = []
    trend_scores = []
    trend_ranks = []
    for row in score_rows:
        label = row.exam.name
        if row.exam.exam_date:
            label = f"{label} ({row.exam.exam_date})"
        trend_labels.append(label)
        trend_scores.append(float(row.total_score) if row.total_score is not None else None)
        trend_ranks.append(row.rank_in_class)

    selected_exam_id = request.GET.get("exam")
    if selected_exam_id is None and score_rows:
        selected_exam_id = str(score_rows[-1].exam_id)

    selected_row = None
    weak_items = []
    good_items = []
    avg_items = []
    show_deltas = False

    if selected_exam_id:
        selected_row = next((item for item in score_rows if str(item.exam_id) == str(selected_exam_id)), None)
        if selected_row:
            show_deltas, deltas = build_question_deltas(selected_row.exam_id, student.id)
            weak_items = [item for item in deltas if item.level == "weak"]
            good_items = [item for item in deltas if item.level == "good"]
            avg_items = [item for item in deltas if item.level == "avg"]

    context = {
        "student": student,
        "score_rows": score_rows,
        "selected_row": selected_row,
        "show_deltas": show_deltas,
        "weak_items": weak_items,
        "good_items": good_items,
        "avg_items": avg_items,
        "trend_labels_json": json.dumps(trend_labels, ensure_ascii=False),
        "trend_scores_json": json.dumps(trend_scores, ensure_ascii=False),
        "trend_ranks_json": json.dumps(trend_ranks, ensure_ascii=False),
    }
    return render(request, "gradebook/student_detail.html", context)


def _score_sort_key(item: ExamScore):
    if item.exam.exam_date is not None:
        return (item.exam.exam_date, item.exam.imported_at)
    return (item.exam.imported_at.date(), item.exam.imported_at)
