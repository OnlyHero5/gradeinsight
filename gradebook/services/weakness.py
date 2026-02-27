from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from django.conf import settings

from gradebook.models import ExamQuestionScore, ExamQuestionStat, ExamScore
from gradebook.services.number_utils import question_key_sort_key

EPS = Decimal(str(getattr(settings, "EPSILON_STR", "0.01")))


@dataclass(frozen=True)
class QuestionDelta:
    question_key: str
    student_score: Decimal
    mean_score: Decimal
    delta: Decimal
    level: str


def classify_delta(delta: Decimal, eps: Decimal = EPS) -> str:
    if delta < -eps:
        return "weak"
    if delta > eps:
        return "good"
    return "avg"


def build_question_deltas(exam_id: int, student_id: int) -> tuple[bool, list[QuestionDelta]]:
    score = ExamScore.objects.filter(exam_id=exam_id, student_id=student_id).first()
    if score is None or score.excluded_from_stats:
        return False, []

    stat_map = {
        stat.question_key: stat
        for stat in ExamQuestionStat.objects.filter(exam_id=exam_id)
    }

    deltas: list[QuestionDelta] = []
    query = ExamQuestionScore.objects.filter(exam_id=exam_id, student_id=student_id).exclude(
        score_value__isnull=True
    )
    for question_score in query:
        stat = stat_map.get(question_score.question_key)
        if stat is None or stat.mean_score is None or question_score.score_value is None:
            continue

        delta = question_score.score_value - stat.mean_score
        deltas.append(
            QuestionDelta(
                question_key=question_score.question_key,
                student_score=question_score.score_value,
                mean_score=stat.mean_score,
                delta=delta,
                level=classify_delta(delta),
            )
        )

    deltas.sort(key=lambda item: (item.delta, question_key_sort_key(item.question_key)))
    return True, deltas
