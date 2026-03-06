from __future__ import annotations

import hashlib
from datetime import date

from django.db import transaction

from gradebook.models import Exam, ExamImport, ExamQuestionScore, ExamScore, Student
from gradebook.services.excel_parser import parse_exam_excel
from gradebook.services.exam_identity import build_legacy_exam_identity
from gradebook.services.stats_queries import rebuild_question_stats
from gradebook.services.xlsx_parser import ParsedExam, ParsedStudentRow


class DuplicateImportError(Exception):
    """Raised when the same source file or the same exam is imported repeatedly."""


def import_exam_from_excel_bytes(
    file_bytes: bytes,
    exam_name: str,
    exam_date: date | None,
    source_filename: str,
) -> Exam:
    source_hash = compute_sha256(file_bytes)
    if Exam.objects.filter(source_sha256=source_hash).exists():
        raise DuplicateImportError("该文件已导入，请勿重复提交")

    parsed = parse_exam_excel(file_bytes, source_filename=source_filename)
    duplicated_exam = find_equivalent_exam(parsed.identity_key)
    if duplicated_exam is not None:
        raise DuplicateImportError(f"同一场考试已导入：{_duplicate_exam_label(duplicated_exam)}")

    with transaction.atomic():
        exam = Exam.objects.create(
            name=exam_name,
            exam_date=exam_date,
            source_filename=source_filename,
            source_sha256=source_hash,
            identity_key=parsed.identity_key,
            identity_label=parsed.identity_label,
            participants_n=parsed.student_count,
            excluded_n=parsed.excluded_from_stats_count,
        )
        _write_exam_rows(exam, parsed)
        rebuild_question_stats(exam)

    return exam


def import_exam_from_xlsx_bytes(
    file_bytes: bytes,
    exam_name: str,
    exam_date: date | None,
    source_filename: str,
) -> Exam:
    # Backward-compatible entry for existing tests/callers.
    return import_exam_from_excel_bytes(
        file_bytes=file_bytes,
        exam_name=exam_name,
        exam_date=exam_date,
        source_filename=source_filename,
    )


def compute_sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def stage_exam_import(
    file_bytes: bytes,
    exam_name: str,
    exam_date: date | None,
    source_filename: str,
    preview: dict,
) -> ExamImport:
    source_hash = compute_sha256(file_bytes)
    return ExamImport.objects.create(
        source_filename=source_filename,
        source_sha256=source_hash,
        exam_name=exam_name,
        exam_date=exam_date,
        preview_json=preview,
        payload=file_bytes,
    )


def _write_exam_rows(exam: Exam, parsed: ParsedExam) -> None:
    for row in parsed.rows:
        student = _upsert_student(row)
        ExamScore.objects.create(
            exam=exam,
            student=student,
            total_score=row.total_score,
            total_raw=row.total_raw,
            objective_score=row.objective_score,
            subjective_score=row.subjective_score,
            rank_in_class=row.rank_in_class,
            excluded_from_stats=row.excluded_from_stats,
            exclude_reason=row.exclude_reason,
        )
        _write_question_scores(exam.id, student.id, row)


def _upsert_student(row: ParsedStudentRow) -> Student:
    stable_external_id = row.external_id and not row.external_id.startswith("name-only:")
    if stable_external_id:
        student, created = Student.objects.get_or_create(
            external_id=row.external_id,
            defaults={
                "name": row.name,
                "admission_ticket": row.admission_ticket,
                "custom_exam_id": row.custom_exam_id,
                "class_name": row.class_name,
            },
        )

        if created:
            return student

        return _update_student(student, row)

    student = Student.objects.filter(name=row.name).order_by("id").first()
    if student is not None:
        return _update_student(student, row)

    generated_external_id = row.external_id or f"name-only:{row.name}"
    return Student.objects.create(
        external_id=generated_external_id,
        name=row.name,
        admission_ticket=row.admission_ticket,
        custom_exam_id=row.custom_exam_id,
        class_name=row.class_name,
    )


def find_equivalent_exam(identity_key: str) -> Exam | None:
    if not identity_key:
        return None

    direct_match = Exam.objects.filter(identity_key=identity_key).order_by("id").first()
    if direct_match is not None:
        return direct_match

    legacy_candidates = Exam.objects.filter(identity_key="").only("id", "name", "source_filename", "identity_label")
    for exam in legacy_candidates:
        legacy_identity = build_legacy_exam_identity(
            source_filename=exam.source_filename,
            exam_name=exam.name,
            identity_label=exam.identity_label,
        )
        if legacy_identity.key == identity_key:
            return exam
    return None


def _duplicate_exam_label(exam: Exam) -> str:
    if exam.identity_label:
        return exam.identity_label
    if exam.source_filename:
        return exam.source_filename
    return exam.name


def _update_student(student: Student, row: ParsedStudentRow) -> Student:
    dirty = False
    if student.name != row.name:
        student.name = row.name
        dirty = True
    if row.admission_ticket and student.admission_ticket != row.admission_ticket:
        student.admission_ticket = row.admission_ticket
        dirty = True
    if row.custom_exam_id and student.custom_exam_id != row.custom_exam_id:
        student.custom_exam_id = row.custom_exam_id
        dirty = True
    if row.class_name and student.class_name != row.class_name:
        student.class_name = row.class_name
        dirty = True
    if dirty:
        student.save(update_fields=["name", "admission_ticket", "custom_exam_id", "class_name", "updated_at"])
    return student


def _write_question_scores(exam_id: int, student_id: int, row: ParsedStudentRow) -> None:
    question_rows = [
        ExamQuestionScore(
            exam_id=exam_id,
            student_id=student_id,
            question_key=question_key,
            score_value=score_value,
        )
        for question_key, score_value in row.question_scores.items()
    ]
    ExamQuestionScore.objects.bulk_create(question_rows)
