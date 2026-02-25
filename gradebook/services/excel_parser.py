from __future__ import annotations

from pathlib import Path

from gradebook.services.xls_parser import parse_exam_xls
from gradebook.services.xlsx_parser import ParsedExam, parse_exam_xlsx

SUPPORTED_EXCEL_EXTENSIONS = {".xlsx", ".xls"}


def is_supported_excel_filename(filename: str) -> bool:
    return _extract_suffix(filename) in SUPPORTED_EXCEL_EXTENSIONS


def parse_exam_excel(file_bytes: bytes, source_filename: str) -> ParsedExam:
    suffix = _extract_suffix(source_filename)
    if suffix == ".xlsx":
        return parse_exam_xlsx(file_bytes)
    if suffix == ".xls":
        return parse_exam_xls(file_bytes)
    raise ValueError("仅支持 .xls 或 .xlsx 文件")


def _extract_suffix(filename: str) -> str:
    return Path(filename).suffix.lower().strip()
