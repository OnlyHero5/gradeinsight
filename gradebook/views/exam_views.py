from __future__ import annotations

import json
from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render

from gradebook.models import Exam, ExamQuestionStat, ExamScore
from gradebook.services.exam_analytics import build_exam_insight_pack
from gradebook.services.number_utils import question_key_sort_key
from gradebook.services.stats_queries import exam_basic_summary, score_histogram


@login_required
def exam_list(request):
    exams = Exam.objects.all().order_by("-exam_date", "-imported_at")
    return render(request, "gradebook/exam_list.html", {"exams": exams})


@login_required
def exam_detail(request, exam_id: int):
    exam = get_object_or_404(Exam, id=exam_id)
    summary = exam_basic_summary(exam)
    histogram = score_histogram(exam)
    insight_pack = build_exam_insight_pack(exam)

    top_scores = (
        ExamScore.objects.filter(exam=exam)
        .select_related("student")
        .exclude(total_score__isnull=True)
        .order_by("-total_score")[:12]
    )
    question_stats = sorted(
        ExamQuestionStat.objects.filter(exam=exam),
        key=lambda s: question_key_sort_key(s.question_key),
    )

    context = {
        "exam": exam,
        "summary": summary,
        "histogram_json": json.dumps(histogram, ensure_ascii=False),
        "score_bands_json": json.dumps(insight_pack["score_bands"], ensure_ascii=False),
        "question_focus_json": json.dumps(insight_pack["question_focus"], ensure_ascii=False, default=_json_encoder),
        "components_json": json.dumps(insight_pack["components"], ensure_ascii=False, default=_json_encoder),
        "top_scores": top_scores,
        "question_stats": question_stats,
        "insight_pack": insight_pack,
        "no_exam_date": exam.exam_date is None,
    }
    return render(request, "gradebook/exam_detail.html", context)


def _json_encoder(value):
    if isinstance(value, Decimal):
        return float(value)
    return value
