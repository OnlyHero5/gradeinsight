from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Iterable

SUBJECTS = ("语文", "数学", "英语", "物理", "化学", "生物", "历史", "地理", "政治", "道法")
EXAM_KEYWORDS = ("考试", "模拟", "月考", "期中", "期末", "联考", "学情", "学业", "测验", "卷")
STRUCTURE_TERMS = (
    "得分明细",
    "成绩汇总",
    "成绩简表",
    "单科成绩单",
    "成绩单",
    "英语得分明细",
    "英语成绩汇总",
    "英语成绩简表",
)

CLASS_PATTERNS = (
    re.compile(r"([七八九789])年级\s*(\d+)班"),
    re.compile(r"([七八九])\s*(\d+)班"),
)
FULL_MARK_PATTERN = re.compile(r"(\d+)\s*分")
COPY_SUFFIX_PATTERN = re.compile(r"\(\d+\)$")
NOISE_PATTERN = re.compile(r"[^\w\u4e00-\u9fff]+")
MULTI_SPACE_PATTERN = re.compile(r"\s+")

GRADE_TO_CN = {
    "7": "七",
    "8": "八",
    "9": "九",
    "七": "七",
    "八": "八",
    "九": "九",
}


@dataclass(frozen=True)
class ExamIdentity:
    key: str
    label: str


def build_exam_identity(
    *,
    title_candidates: Iterable[str],
    source_filename: str,
    fallback_class_name: str = "",
) -> ExamIdentity:
    raw_candidates = [item for item in title_candidates if str(item or "").strip()]
    raw_candidates.append(source_filename)

    class_name = _extract_class_name(raw_candidates, fallback_class_name)
    subject = _extract_subject(raw_candidates)
    full_mark = _extract_full_mark(raw_candidates)
    exam_name = _extract_exam_name(raw_candidates, fallback_class_name=fallback_class_name, subject=subject)

    key_parts = [
        _slug(class_name),
        _slug(subject),
        _slug(exam_name),
    ]
    key = "|".join(part for part in key_parts if part)
    if not key:
        key = _slug(source_filename)

    label_parts = [part for part in (exam_name, subject, class_name) if part]
    if full_mark:
        label_parts.append(f"{full_mark}分")
    label = " / ".join(label_parts) or source_filename

    return ExamIdentity(key=key, label=label)


def build_legacy_exam_identity(source_filename: str, exam_name: str, identity_label: str = "") -> ExamIdentity:
    return build_exam_identity(
        title_candidates=[identity_label, source_filename, exam_name],
        source_filename=source_filename or exam_name,
    )


def looks_like_exam_text(text: str) -> bool:
    normalized = _normalize_text(text)
    return any(keyword in normalized for keyword in EXAM_KEYWORDS)


def _extract_class_name(candidates: Iterable[str], fallback_class_name: str) -> str:
    for text in list(candidates) + [fallback_class_name]:
        normalized = _normalize_text(text)
        for pattern in CLASS_PATTERNS:
            match = pattern.search(normalized)
            if match is None:
                continue
            grade = GRADE_TO_CN.get(match.group(1), match.group(1))
            return f"{grade}年级{int(match.group(2))}班"
    return _normalize_class_name(fallback_class_name)


def _extract_subject(candidates: Iterable[str]) -> str:
    for text in candidates:
        normalized = _normalize_text(text)
        for subject in SUBJECTS:
            if subject in normalized:
                return subject
    return ""


def _extract_full_mark(candidates: Iterable[str]) -> str:
    for text in candidates:
        normalized = _normalize_text(text)
        marks = FULL_MARK_PATTERN.findall(normalized)
        if marks:
            return marks[0]
    return ""


def _extract_exam_name(candidates: Iterable[str], fallback_class_name: str, subject: str) -> str:
    cleaned_candidates: list[str] = []
    fallback_candidates: list[str] = []

    for raw in candidates:
        normalized = _normalize_text(raw)
        if not normalized:
            continue
        cleaned = _strip_exam_noise(normalized, fallback_class_name=fallback_class_name, subject=subject)
        if not cleaned:
            continue
        if looks_like_exam_text(raw):
            cleaned_candidates.append(cleaned)
        else:
            fallback_candidates.append(cleaned)

    if cleaned_candidates:
        return max(cleaned_candidates, key=len)
    if fallback_candidates:
        return max(fallback_candidates, key=len)
    return ""


def _strip_exam_noise(text: str, *, fallback_class_name: str, subject: str) -> str:
    cleaned = text
    cleaned = re.sub(r"\.xlsx?$", "", cleaned, flags=re.IGNORECASE)
    cleaned = COPY_SUFFIX_PATTERN.sub("", cleaned)

    class_name = _normalize_class_name(fallback_class_name)
    if class_name:
        cleaned = cleaned.replace(class_name, " ")
        short_class_name = class_name.replace("年级", "")
        cleaned = cleaned.replace(short_class_name, " ")

    for pattern in CLASS_PATTERNS:
        cleaned = pattern.sub(" ", cleaned)

    if subject:
        cleaned = cleaned.replace(subject, " ")
    for subject_name in SUBJECTS:
        cleaned = cleaned.replace(subject_name, " ")

    for term in STRUCTURE_TERMS:
        cleaned = cleaned.replace(term, " ")

    cleaned = re.sub(r"序号|姓名|准考证号|自定义考号|班级|得分|总分|校次|班次|学生属性", " ", cleaned)
    cleaned = re.sub(r"同学在本次满分\d+\s*分的考试中成绩为\d+\s*分", " ", cleaned)
    cleaned = re.sub(r"满分\d+\s*分", " ", cleaned)
    cleaned = FULL_MARK_PATTERN.sub(" ", cleaned)
    cleaned = cleaned.replace("(", " ").replace(")", " ")
    cleaned = cleaned.replace("[", " ").replace("]", " ")
    cleaned = cleaned.replace("{", " ").replace("}", " ")
    cleaned = cleaned.replace("【", " ").replace("】", " ")
    cleaned = cleaned.replace("_", " ").replace("-", " ").replace("/", " ")
    cleaned = NOISE_PATTERN.sub(" ", cleaned)
    cleaned = MULTI_SPACE_PATTERN.sub(" ", cleaned).strip()
    return cleaned


def _slug(text: str) -> str:
    normalized = _normalize_text(text)
    if not normalized:
        return ""
    stripped = _strip_exam_noise(normalized, fallback_class_name="", subject="")
    return MULTI_SPACE_PATTERN.sub("", stripped.lower())


def _normalize_text(text: str) -> str:
    return unicodedata.normalize("NFKC", str(text or "")).strip()


def _normalize_class_name(text: str) -> str:
    normalized = _normalize_text(text)
    if not normalized:
        return ""
    for pattern in CLASS_PATTERNS:
        match = pattern.search(normalized)
        if match is None:
            continue
        grade = GRADE_TO_CN.get(match.group(1), match.group(1))
        return f"{grade}年级{int(match.group(2))}班"
    return normalized
