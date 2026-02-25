from __future__ import annotations

import json
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from gradebook.models import Exam, ExamQuestionStat, ExamScore, Student
from gradebook.services.exam_analytics import build_exam_insight_pack


@pytest.mark.django_db
def test_build_exam_insight_pack_returns_multi_dimensional_metrics() -> None:
    exam = Exam.objects.create(name="Midterm", source_sha256="m" * 64)

    for idx, score in enumerate(["55", "62", "78", "88", "95"], start=1):
        student = Student.objects.create(
            name=f"S{idx}",
            external_id=f"20{idx:02d}",
            admission_ticket=f"20{idx:02d}",
            custom_exam_id=f"20{idx:02d}",
        )
        ExamScore.objects.create(
            exam=exam,
            student=student,
            total_score=Decimal(score),
            objective_score=Decimal(score) * Decimal("0.6"),
            subjective_score=Decimal(score) * Decimal("0.4"),
            excluded_from_stats=False,
        )

    excluded_student = Student.objects.create(
        name="Excluded",
        external_id="2999",
        admission_ticket="2999",
        custom_exam_id="2999",
    )
    ExamScore.objects.create(
        exam=exam,
        student=excluded_student,
        total_score=Decimal("40"),
        objective_score=Decimal("20"),
        subjective_score=Decimal("20"),
        excluded_from_stats=True,
    )

    pack = build_exam_insight_pack(exam)

    assert pack["rates"]["pass_rate"] == Decimal("80.00")
    assert pack["rates"]["excellent_rate"] == Decimal("40.00")

    bands = {item["label"]: item["count"] for item in pack["score_bands"]}
    assert bands["<60"] == 1
    assert bands["60-79"] == 2
    assert bands["80-89"] == 1
    assert bands["90+"] == 1

    assert pack["dispersion"]["std_dev"] is not None
    assert pack["percentiles"]["p25"] <= pack["percentiles"]["p50"] <= pack["percentiles"]["p75"]

    assert pack["components"]["objective_mean"] is not None
    assert pack["components"]["subjective_mean"] is not None


@pytest.mark.django_db
def test_exam_detail_exposes_richer_analytics_context(client) -> None:
    user_model = get_user_model()
    user_model.objects.create_user(username="teacher", password="pass123")
    assert client.login(username="teacher", password="pass123")

    exam = Exam.objects.create(name="Final", source_sha256="f" * 64)

    for idx, score in enumerate(["61", "74", "83", "92"], start=1):
        student = Student.objects.create(
            name=f"N{idx}",
            external_id=f"30{idx:02d}",
            admission_ticket=f"30{idx:02d}",
            custom_exam_id=f"30{idx:02d}",
        )
        ExamScore.objects.create(
            exam=exam,
            student=student,
            total_score=Decimal(score),
            objective_score=Decimal(score) * Decimal("0.55"),
            subjective_score=Decimal(score) * Decimal("0.45"),
            excluded_from_stats=False,
        )

    ExamQuestionStat.objects.create(
        exam=exam,
        question_key="11",
        mean_score=Decimal("2.30"),
        median_score=Decimal("2.00"),
        sample_n=4,
    )
    ExamQuestionStat.objects.create(
        exam=exam,
        question_key="12",
        mean_score=Decimal("4.80"),
        median_score=Decimal("5.00"),
        sample_n=4,
    )

    response = client.get(reverse("exam_detail", args=[exam.id]))

    assert response.status_code == 200
    html = response.content.decode("utf-8")
    assert "成绩段分布" in html
    assert "客观/主观得分结构" in html
    assert "题目得分表现" in html

    score_bands = json.loads(response.context["score_bands_json"])
    question_focus = json.loads(response.context["question_focus_json"])

    assert score_bands
    assert set(question_focus.keys()) == {"strong", "weak"}
    assert response.context["insight_pack"]["rates"]["pass_rate"] is not None
