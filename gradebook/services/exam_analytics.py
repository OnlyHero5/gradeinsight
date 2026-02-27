from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_CEILING, ROUND_FLOOR
from typing import Iterable

from gradebook.models import Exam, ExamQuestionStat, ExamScore
from gradebook.services.number_utils import question_key_sort_key, quantize_two


@dataclass(frozen=True)
class ScoreBand:
    label: str
    lower: Decimal | None
    upper: Decimal | None


SCORE_BANDS = (
    ScoreBand(label="<60", lower=None, upper=Decimal("60")),
    ScoreBand(label="60-79", lower=Decimal("60"), upper=Decimal("80")),
    ScoreBand(label="80-89", lower=Decimal("80"), upper=Decimal("90")),
    ScoreBand(label="90+", lower=Decimal("90"), upper=None),
)


def build_exam_insight_pack(exam: Exam) -> dict:
    score_rows = list(
        ExamScore.objects.filter(exam=exam, excluded_from_stats=False)
        .exclude(total_score__isnull=True)
        .select_related("student")
        .order_by("total_score", "student_id")
    )
    total_scores = [row.total_score for row in score_rows if row.total_score is not None]
    ordered_scores = sorted(total_scores)

    return {
        "rates": _build_rate_metrics(ordered_scores),
        "score_bands": _build_score_bands(ordered_scores),
        "percentiles": _build_percentiles(ordered_scores),
        "dispersion": _build_dispersion(ordered_scores),
        "components": _build_component_means(score_rows),
        "question_focus": _build_question_focus(exam),
        "attention_students": _build_attention_students(score_rows),
    }


def _build_rate_metrics(scores: list[Decimal]) -> dict[str, Decimal | None]:
    if not scores:
        return {"pass_rate": None, "excellent_rate": None}

    count = len(scores)
    pass_count = len([score for score in scores if score >= Decimal("60")])
    excellent_count = len([score for score in scores if score >= Decimal("85")])
    return {
        "pass_rate": _ratio_to_percent(pass_count, count),
        "excellent_rate": _ratio_to_percent(excellent_count, count),
    }


def _build_score_bands(scores: Iterable[Decimal]) -> list[dict[str, int | str]]:
    values = list(scores)
    if not values:
        return [{"label": band.label, "count": 0} for band in SCORE_BANDS]

    distribution = []
    for band in SCORE_BANDS:
        distribution.append(
            {
                "label": band.label,
                "count": len([score for score in values if _score_in_band(score, band)]),
            }
        )
    return distribution


def _score_in_band(score: Decimal, band: ScoreBand) -> bool:
    if band.lower is not None and score < band.lower:
        return False
    if band.upper is not None and score >= band.upper:
        return False
    return True


def _build_percentiles(scores: list[Decimal]) -> dict[str, Decimal | None]:
    if not scores:
        return {"p25": None, "p50": None, "p75": None, "p90": None}

    return {
        "p25": quantize_two(_interpolated_percentile(scores, Decimal("0.25"))),
        "p50": quantize_two(_interpolated_percentile(scores, Decimal("0.50"))),
        "p75": quantize_two(_interpolated_percentile(scores, Decimal("0.75"))),
        "p90": quantize_two(_interpolated_percentile(scores, Decimal("0.90"))),
    }


def _interpolated_percentile(sorted_scores: list[Decimal], ratio: Decimal) -> Decimal:
    if len(sorted_scores) == 1:
        return sorted_scores[0]

    position = Decimal(len(sorted_scores) - 1) * ratio
    lower_index = int(position.to_integral_value(rounding=ROUND_FLOOR))
    upper_index = int(position.to_integral_value(rounding=ROUND_CEILING))
    if lower_index == upper_index:
        return sorted_scores[lower_index]

    weight = position - Decimal(lower_index)
    lower = sorted_scores[lower_index]
    upper = sorted_scores[upper_index]
    return lower + (upper - lower) * weight


def _build_dispersion(scores: list[Decimal]) -> dict[str, Decimal | None]:
    if len(scores) < 2:
        return {"std_dev": None, "iqr": None}

    mean = sum(scores) / len(scores)
    variance = sum((score - mean) ** 2 for score in scores) / len(scores)
    std_dev = quantize_two(variance.sqrt())
    iqr = quantize_two(_interpolated_percentile(scores, Decimal("0.75")) - _interpolated_percentile(scores, Decimal("0.25")))
    return {"std_dev": std_dev, "iqr": iqr}


def _build_component_means(score_rows: list[ExamScore]) -> dict[str, Decimal | None]:
    objective_values = [row.objective_score for row in score_rows if row.objective_score is not None]
    subjective_values = [row.subjective_score for row in score_rows if row.subjective_score is not None]

    return {
        "objective_mean": _mean_or_none(objective_values),
        "subjective_mean": _mean_or_none(subjective_values),
    }


def _mean_or_none(values: list[Decimal]) -> Decimal | None:
    if not values:
        return None
    return quantize_two(sum(values) / len(values))


def _build_question_focus(exam: Exam) -> dict[str, list[dict[str, str | Decimal]]]:
    rows = list(ExamQuestionStat.objects.filter(exam=exam).exclude(mean_score__isnull=True))
    ordered = sorted(rows, key=lambda item: (item.mean_score or Decimal("0"), question_key_sort_key(item.question_key)))
    weak = ordered[:6]
    strong = list(reversed(ordered[len(weak):]))
    strong = strong[:6]

    return {
        "weak": [{"question_key": row.question_key, "mean_score": row.mean_score} for row in weak],
        "strong": [{"question_key": row.question_key, "mean_score": row.mean_score} for row in strong],
    }


def _build_attention_students(score_rows: list[ExamScore]) -> list[dict[str, int | Decimal | str | None]]:
    rows = score_rows[:8]
    return [
        {
            "student_id": row.student_id,
            "student_name": row.student.name,
            "total_score": row.total_score,
            "rank_in_class": row.rank_in_class,
        }
        for row in rows
    ]


def _ratio_to_percent(part: int, total: int) -> Decimal:
    return quantize_two((Decimal(part) * Decimal("100")) / Decimal(total))
