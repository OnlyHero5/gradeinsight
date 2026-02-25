from __future__ import annotations

import re
from io import BytesIO

import xlrd

from gradebook.services.number_utils import to_decimal
from gradebook.services.xlsx_parser import ParsedExam, ParsedStudentRow

QUESTION_KEY_PATTERN = re.compile(r"^\d+(?:\(\d+\))?$")
STUDENT_BLOCK_PATTERN = re.compile(r"^(?P<name>.+)\((?P<external_id>[^()]+)\)_成绩单$")


def parse_exam_xls(file_bytes: bytes) -> ParsedExam:
    workbook = xlrd.open_workbook(file_contents=BytesIO(file_bytes).read())
    sheet = workbook.sheet_by_index(0)

    rows: list[ParsedStudentRow] = []
    question_order: list[str] = []
    question_seen: set[str] = set()

    for row_index in range(sheet.nrows):
        title = _cell_text(sheet, row_index, 0)
        if not title.endswith("_成绩单"):
            continue

        parsed_row = _parse_student_block(sheet, row_index)
        if parsed_row is None:
            continue

        rows.append(parsed_row)
        for question_key in parsed_row.question_scores:
            if question_key in question_seen:
                continue
            question_seen.add(question_key)
            question_order.append(question_key)

    if not rows:
        raise ValueError("无法在 .xls 文件中定位学生成绩单块")

    excluded_count = len([item for item in rows if item.excluded_from_stats])
    return ParsedExam(
        question_keys=question_order,
        rows=rows,
        student_count=len(rows),
        excluded_from_stats_count=excluded_count,
        mismatched_id_count=0,
    )


def _parse_student_block(sheet: xlrd.sheet.Sheet, start_row: int) -> ParsedStudentRow | None:
    title = _cell_text(sheet, start_row, 0)
    match = STUDENT_BLOCK_PATTERN.match(title)
    if match is None:
        return None

    name = match.group("name").strip()
    external_id = match.group("external_id").strip()
    class_name = _extract_class_name(_cell_text(sheet, start_row + 1, 0))

    question_scores: dict[str, object] = {}
    total_raw = ""
    total_score = None

    for question_row, score_row in ((start_row + 5, start_row + 6), (start_row + 7, start_row + 8), (start_row + 9, start_row + 10)):
        if question_row >= sheet.nrows or score_row >= sheet.nrows:
            continue

        for column in range(1, sheet.ncols):
            question_key = _cell_text(sheet, question_row, column)
            if not question_key:
                continue

            score_raw = sheet.cell_value(score_row, column) if column < sheet.ncols else None
            if question_key == "总分":
                total_raw = "" if score_raw in (None, "") else str(score_raw).strip()
                total_score = to_decimal(score_raw)
                continue

            if QUESTION_KEY_PATTERN.match(question_key):
                question_scores[question_key] = to_decimal(score_raw)

    excluded = total_score is None
    exclude_reason = "non_numeric_total_score" if excluded and total_raw else ""
    return ParsedStudentRow(
        name=name,
        external_id=external_id,
        admission_ticket=external_id,
        custom_exam_id=external_id,
        class_name=class_name,
        total_score=total_score,
        total_raw=total_raw,
        objective_score=None,
        subjective_score=None,
        rank_in_class=None,
        excluded_from_stats=excluded,
        exclude_reason=exclude_reason,
        question_scores=question_scores,
    )


def _extract_class_name(raw_value: str) -> str:
    if not raw_value:
        return ""
    if "_" not in raw_value:
        return raw_value.strip()
    return raw_value.rsplit("_", 1)[-1].strip()


def _cell_text(sheet: xlrd.sheet.Sheet, row: int, column: int) -> str:
    if row < 0 or row >= sheet.nrows or column < 0 or column >= sheet.ncols:
        return ""
    value = sheet.cell_value(row, column)
    return "" if value is None else str(value).strip()
