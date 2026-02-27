from __future__ import annotations

from collections import defaultdict
from decimal import Decimal
from statistics import median

from gradebook.models import Exam, ExamQuestionScore, ExamQuestionStat, ExamScore
from gradebook.services.number_utils import quantize_two


def rebuild_question_stats(exam: Exam) -> None:
    eligible_student_ids = list(
        ExamScore.objects.filter(exam=exam, excluded_from_stats=False).values_list("student_id", flat=True)
    )
    if not eligible_student_ids:
        return

    question_scores = defaultdict(list)
    rows = ExamQuestionScore.objects.filter(
        exam=exam,
        student_id__in=eligible_student_ids,
        score_value__isnull=False,
    ).values_list("question_key", "score_value")

    for question_key, score_value in rows:
        if score_value is None:
            continue
        question_scores[question_key].append(score_value)

    ExamQuestionStat.objects.filter(exam=exam).delete()

    stats = []
    for question_key, values in question_scores.items():
        count = len(values)
        mean_score = quantize_two(sum(values) / count)
        median_score = quantize_two(Decimal(str(median(values))))
        stats.append(
            ExamQuestionStat(
                exam=exam,
                question_key=question_key,
                mean_score=mean_score,
                median_score=median_score,
                sample_n=count,
            )
        )

    ExamQuestionStat.objects.bulk_create(stats)


def exam_basic_summary(exam: Exam) -> dict[str, Decimal | int | None]:
    score_values = list(
        ExamScore.objects.filter(exam=exam, excluded_from_stats=False)
        .exclude(total_score__isnull=True)
        .values_list("total_score", flat=True)
    )

    if not score_values:
        return {
            "participant_count": 0,
            "mean": None,
            "median": None,
            "max": None,
            "min": None,
        }

    decimals = list(score_values)
    ordered = sorted(decimals)
    count = len(ordered)
    mean_value = quantize_two(sum(ordered) / count)
    median_value = quantize_two(Decimal(str(median(ordered))))

    return {
        "participant_count": count,
        "mean": mean_value,
        "median": median_value,
        "max": ordered[-1],
        "min": ordered[0],
    }


def score_histogram(exam: Exam, step: int = 10) -> list[dict[str, int | str]]:
    values = list(
        ExamScore.objects.filter(exam=exam, excluded_from_stats=False)
        .exclude(total_score__isnull=True)
        .values_list("total_score", flat=True)
    )

    if not values:
        return []

    bins: dict[tuple[int, int], int] = defaultdict(int)
    for value in values:
        score = int(value)
        left = (score // step) * step
        right = left + step
        bins[(left, right)] += 1

    histogram = []
    for left, right in sorted(bins):
        histogram.append({"label": f"{left}-{right}", "count": bins[(left, right)]})
    return histogram
