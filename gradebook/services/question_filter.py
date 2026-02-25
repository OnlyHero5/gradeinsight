from __future__ import annotations

from decimal import Decimal

from django.conf import settings
from django.db.models import QuerySet

from gradebook.models import ExamQuestionScore, ExamQuestionStat, ExamScore
from gradebook.services.number_utils import to_decimal

EPS = Decimal(str(getattr(settings, "EPSILON_STR", "0.01")))


def filter_students_by_question_rule(
    exam_id: int,
    question_key: str,
    rule: dict,
    include_excluded: bool = False,
) -> list[int]:
    eligible_student_ids = _eligible_student_ids(exam_id, include_excluded)
    scores = ExamQuestionScore.objects.filter(
        exam_id=exam_id,
        question_key=question_key,
        student_id__in=eligible_student_ids,
    ).exclude(score_value__isnull=True)

    op = str(rule.get("op") or "eq").strip()
    if op in {"below_mean", "above_mean"}:
        return _filter_by_mean(scores, exam_id, question_key, op)
    return _filter_by_threshold(scores, op, rule)


def _eligible_student_ids(exam_id: int, include_excluded: bool) -> QuerySet[int]:
    base = ExamScore.objects.filter(exam_id=exam_id)
    if not include_excluded:
        base = base.filter(excluded_from_stats=False)
    return base.values_list("student_id", flat=True)


def _filter_by_mean(
    scores: QuerySet[ExamQuestionScore],
    exam_id: int,
    question_key: str,
    op: str,
) -> list[int]:
    stat = ExamQuestionStat.objects.filter(exam_id=exam_id, question_key=question_key).first()
    if stat is None or stat.mean_score is None:
        return []

    mean = stat.mean_score
    if op == "below_mean":
        queryset = scores.filter(score_value__lt=mean - EPS)
    else:
        queryset = scores.filter(score_value__gt=mean + EPS)
    return list(queryset.values_list("student_id", flat=True))


def _filter_by_threshold(
    scores: QuerySet[ExamQuestionScore],
    op: str,
    rule: dict,
) -> list[int]:
    value = to_decimal(rule.get("value"))
    min_value = to_decimal(rule.get("min"))
    max_value = to_decimal(rule.get("max"))

    if op == "eq" and value is not None:
        queryset = scores.filter(score_value=value)
    elif op == "ne" and value is not None:
        queryset = scores.exclude(score_value=value)
    elif op == "lt" and value is not None:
        queryset = scores.filter(score_value__lt=value)
    elif op == "lte" and value is not None:
        queryset = scores.filter(score_value__lte=value)
    elif op == "gt" and value is not None:
        queryset = scores.filter(score_value__gt=value)
    elif op == "gte" and value is not None:
        queryset = scores.filter(score_value__gte=value)
    elif op == "between" and min_value is not None and max_value is not None:
        queryset = scores.filter(score_value__gte=min_value, score_value__lte=max_value)
    else:
        return []

    return list(queryset.values_list("student_id", flat=True))
