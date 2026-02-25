from __future__ import annotations

import re
import warnings
from dataclasses import dataclass
from decimal import Decimal
from io import BytesIO
from typing import Any

from openpyxl import load_workbook
from openpyxl.worksheet.worksheet import Worksheet

from .number_utils import to_decimal, to_int

QUESTION_KEY_PATTERN = re.compile(r"^\d+(?:\(\d+\))?$")


@dataclass(frozen=True)
class ParsedStudentRow:
    name: str
    external_id: str
    admission_ticket: str
    custom_exam_id: str
    class_name: str
    total_score: Decimal | None
    total_raw: str
    objective_score: Decimal | None
    subjective_score: Decimal | None
    rank_in_class: int | None
    excluded_from_stats: bool
    exclude_reason: str
    question_scores: dict[str, Decimal | None]


@dataclass(frozen=True)
class ParsedExam:
    question_keys: list[str]
    rows: list[ParsedStudentRow]
    student_count: int
    excluded_from_stats_count: int
    mismatched_id_count: int


def parse_exam_xlsx(file_bytes: bytes) -> ParsedExam:
    worksheet = _load_sheet(file_bytes)
    header_row = _find_header_row(worksheet)
    header_map = _build_header_map(worksheet, header_row)
    question_columns = _extract_question_columns(header_map)
    rows, excluded_count, mismatch_count = _parse_rows(worksheet, header_row, header_map, question_columns)

    return ParsedExam(
        question_keys=[question_key for question_key, _ in question_columns],
        rows=rows,
        student_count=len(rows),
        excluded_from_stats_count=excluded_count,
        mismatched_id_count=mismatch_count,
    )


def _load_sheet(file_bytes: bytes) -> Worksheet:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        workbook = load_workbook(BytesIO(file_bytes), data_only=True)

    if "得分明细" in workbook.sheetnames:
        return workbook["得分明细"]
    return workbook[workbook.sheetnames[0]]


def _find_header_row(worksheet: Worksheet) -> int:
    max_scan_rows = min(worksheet.max_row, 12)
    for row in range(1, max_scan_rows + 1):
        values = {str(worksheet.cell(row=row, column=col).value or "").strip() for col in range(1, 80)}
        if {"姓名", "总分"}.issubset(values):
            return row

    raise ValueError("无法定位表头，请确认文件包含“姓名/总分”列")


def _build_header_map(worksheet: Worksheet, header_row: int) -> dict[str, int]:
    mapping: dict[str, int] = {}
    for col in range(1, worksheet.max_column + 1):
        header = str(worksheet.cell(row=header_row, column=col).value or "").strip()
        if header:
            mapping[header] = col
    return mapping


def _extract_question_columns(header_map: dict[str, int]) -> list[tuple[str, int]]:
    question_items = [
        (header, col)
        for header, col in sorted(header_map.items(), key=lambda item: item[1])
        if QUESTION_KEY_PATTERN.match(header)
    ]
    if not question_items:
        raise ValueError("未找到题号列（如 1、51、51(3)）")
    return question_items


def _parse_rows(
    worksheet: Worksheet,
    header_row: int,
    header_map: dict[str, int],
    question_columns: list[tuple[str, int]],
) -> tuple[list[ParsedStudentRow], int, int]:
    rows: list[ParsedStudentRow] = []
    excluded_count = 0
    mismatch_count = 0

    for row_index in range(header_row + 1, worksheet.max_row + 1):
        name = _read_text(worksheet, row_index, header_map.get("姓名"))
        if not name:
            continue

        admission_ticket = _read_text(worksheet, row_index, header_map.get("准考证号"))
        custom_exam_id = _read_text(worksheet, row_index, header_map.get("自定义考号"))
        external_id = admission_ticket or custom_exam_id
        if not external_id:
            continue

        if admission_ticket and custom_exam_id and admission_ticket != custom_exam_id:
            mismatch_count += 1

        total_raw_value = worksheet.cell(row=row_index, column=header_map.get("总分", 0)).value
        total_raw = "" if total_raw_value is None else str(total_raw_value).strip()
        total_score = to_decimal(total_raw_value)
        excluded = total_score is None
        exclude_reason = "non_numeric_total_score" if excluded and total_raw else ""

        if excluded:
            excluded_count += 1

        question_scores = {
            question_key: to_decimal(worksheet.cell(row=row_index, column=column).value)
            for question_key, column in question_columns
        }

        row = ParsedStudentRow(
            name=name,
            external_id=external_id,
            admission_ticket=admission_ticket,
            custom_exam_id=custom_exam_id,
            class_name=_read_text(worksheet, row_index, header_map.get("班级")),
            total_score=total_score,
            total_raw=total_raw,
            objective_score=to_decimal(_read_value(worksheet, row_index, header_map.get("客观分"))),
            subjective_score=to_decimal(_read_value(worksheet, row_index, header_map.get("主观分"))),
            rank_in_class=to_int(_read_value(worksheet, row_index, header_map.get("班次"))),
            excluded_from_stats=excluded,
            exclude_reason=exclude_reason,
            question_scores=question_scores,
        )
        rows.append(row)

    return rows, excluded_count, mismatch_count


def _read_text(worksheet: Worksheet, row: int, column: int | None) -> str:
    value = _read_value(worksheet, row, column)
    return "" if value is None else str(value).strip()


def _read_value(worksheet: Worksheet, row: int, column: int | None) -> Any:
    if column is None:
        return None
    return worksheet.cell(row=row, column=column).value
