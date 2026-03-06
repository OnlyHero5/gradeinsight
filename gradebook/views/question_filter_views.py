from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from gradebook.forms import QuestionFilterForm
from gradebook.models import Exam, ExamQuestionScore, ExamQuestionStat, Student
from gradebook.services.number_utils import question_key_sort_key
from gradebook.services.question_filter import filter_students_by_question_rule
from worklists.models import Task, TaskAssignment


@login_required
def question_filter(request, exam_id: int):
    exam = get_object_or_404(Exam, id=exam_id)
    question_keys = _load_question_keys(exam_id)
    question_filter_available = bool(question_keys)
    form = QuestionFilterForm(request.POST or None, question_keys=question_keys)

    matched_students = []
    matched_ids: list[int] = []

    if question_filter_available and request.method == "POST" and form.is_valid():
        rule = _build_rule(form.cleaned_data)
        matched_ids = filter_students_by_question_rule(
            exam_id=exam.id,
            question_key=form.cleaned_data["question_key"],
            rule=rule,
            include_excluded=form.cleaned_data["include_excluded"],
        )
        matched_students = list(Student.objects.filter(id__in=matched_ids).order_by("name"))

        if request.POST.get("action") == "create_task" and matched_ids:
            task_name = request.POST.get("task_name", "").strip()
            if not task_name:
                task_name = f"{exam.name}-{form.cleaned_data['question_key']}-{form.cleaned_data['op']}"

            task = Task.objects.create(
                exam=exam,
                name=task_name,
                question_key=form.cleaned_data["question_key"],
                rule_json=rule,
            )
            assignments = [
                TaskAssignment(task=task, student_id=student_id)
                for student_id in sorted(set(matched_ids))
            ]
            TaskAssignment.objects.bulk_create(assignments)
            messages.success(request, f"任务已创建，共 {len(assignments)} 人")
            return redirect("task_detail", task_id=task.id)

    context = {
        "exam": exam,
        "form": form,
        "question_filter_available": question_filter_available,
        "matched_students": matched_students,
        "matched_count": len(matched_students),
        "has_result": question_filter_available and request.method == "POST" and form.is_valid(),
    }
    return render(request, "gradebook/question_filter.html", context)


def _load_question_keys(exam_id: int) -> list[str]:
    keys = list(ExamQuestionStat.objects.filter(exam_id=exam_id).values_list("question_key", flat=True))
    if not keys:
        keys = list(
            ExamQuestionScore.objects.filter(exam_id=exam_id).values_list("question_key", flat=True).distinct()
        )
    keys.sort(key=question_key_sort_key)
    return keys


def _build_rule(cleaned_data: dict) -> dict:
    rule = {
        "op": cleaned_data["op"],
    }
    if cleaned_data.get("value") is not None:
        rule["value"] = str(cleaned_data["value"])
    if cleaned_data.get("min") is not None:
        rule["min"] = str(cleaned_data["min"])
    if cleaned_data.get("max") is not None:
        rule["max"] = str(cleaned_data["max"])
    return rule
