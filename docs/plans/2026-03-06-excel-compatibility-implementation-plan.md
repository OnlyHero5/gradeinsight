# Excel 测试数据集兼容 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 兼容 `测试数据集/` 中全部 6 个 Excel 文件，支持“题目明细考试”与“仅总分考试”两种导入结构，并让无题目考试在页面上正确降级。

**Architecture:** 继续使用统一的 `ParsedExam` / `ParsedStudentRow` 作为导入中间结构，在 `gradebook/services/xlsx_parser.py` 中增加“仅总分 `.xlsx`”回退解析能力。导入层只在学生归并策略上做最小扩展：优先学号，缺学号时按姓名匹配，再退回 `name-only:<姓名>`。页面层仅对“无题目考试”的题目筛选做友好降级，不伪造题目数据。

**Tech Stack:** Python 3.12、Django、pytest、openpyxl、xlrd

---

### Task 1: 为全部测试数据集建立解析回归测试

**Files:**
- Modify: `gradebook/tests/test_xlsx_parser.py`
- Modify: `gradebook/tests/test_xls_parser.py`
- Modify: `gradebook/tests/test_import_exam.py`

**Step 1: 写失败测试，覆盖 3 个仅总分 `.xlsx`**

在 `gradebook/tests/test_xlsx_parser.py` 中新增基于 `测试数据集/` 的测试，至少包含：

```python
from pathlib import Path

from gradebook.services.excel_parser import parse_exam_excel


def test_parse_total_only_xlsx_from_summary_sheet() -> None:
    path = Path("测试数据集/（必）八年级英语模拟1(英语)-八年级7班(1).xlsx")
    parsed = parse_exam_excel(path.read_bytes(), source_filename=path.name)

    assert parsed.student_count == 44
    assert parsed.question_keys == []
    assert parsed.excluded_from_stats_count >= 1
```

再补一条只含 `姓名 + 得分` 的简表型测试。

**Step 2: 修正旧测试数据路径**

把仍然直接读取仓库根目录旧文件名的测试，改为读取 `测试数据集/` 下真实文件：

```python
data = Path("测试数据集/2025-2026学年度第一学期期末考试【八年级】(英语)-八年级7班.xlsx").read_bytes()
```

**Step 3: 运行解析相关测试，确认当前失败**

Run:

```bash
pytest gradebook/tests/test_xlsx_parser.py gradebook/tests/test_xls_parser.py gradebook/tests/test_import_exam.py -q
```

Expected:

- 新增的仅总分 `.xlsx` 测试失败
- 旧测试路径修正后，失败集中在 `xlsx_parser` 与导入兼容逻辑

**Step 4: Commit**

```bash
git add gradebook/tests/test_xlsx_parser.py gradebook/tests/test_xls_parser.py gradebook/tests/test_import_exam.py
git commit -m "test: cover total-only excel dataset compatibility"
```

---

### Task 2: 扩展 `.xlsx` 解析器支持仅总分考试

**Files:**
- Modify: `gradebook/services/xlsx_parser.py`
- Read: `gradebook/services/excel_parser.py`
- Test: `gradebook/tests/test_xlsx_parser.py`

**Step 1: 写出失败测试后的最小解析实现**

在 `gradebook/services/xlsx_parser.py` 中增加如下结构：

```python
def parse_exam_xlsx(file_bytes: bytes) -> ParsedExam:
    workbook = _load_workbook(file_bytes)

    try:
        return _parse_detail_workbook(workbook)
    except ValueError:
        return _parse_total_only_workbook(workbook)
```

同时把当前 `_load_sheet()` 重构为返回 workbook，而不是直接返回单个 sheet。

**Step 2: 实现“汇总表优先、简表兜底”的识别顺序**

新增辅助函数，优先查找：

- `班级英语成绩汇总`
- `班级英语成绩简表`
- 兜底扫描所有 sheet

最小实现形态：

```python
def _find_total_only_sheet(workbook) -> tuple[Worksheet, int, dict[str, int], str]:
    ...
    return worksheet, header_row, header_map, mode
```

其中 `mode` 取值可为：

- `"summary"`
- `"simple"`

**Step 3: 统一产出 `ParsedStudentRow`**

对仅总分考试：

```python
row = ParsedStudentRow(
    name=name,
    external_id=external_id,
    admission_ticket=admission_ticket,
    custom_exam_id=custom_exam_id,
    class_name=class_name,
    total_score=total_score,
    total_raw=total_raw,
    objective_score=None,
    subjective_score=None,
    rank_in_class=rank_in_class,
    excluded_from_stats=excluded,
    exclude_reason=exclude_reason,
    question_scores={},
)
```

并确保：

```python
ParsedExam(
    question_keys=[],
    rows=rows,
    student_count=len(rows),
    excluded_from_stats_count=excluded_count,
    mismatched_id_count=mismatch_count,
)
```

**Step 4: 运行解析测试，确认通过**

Run:

```bash
pytest gradebook/tests/test_xlsx_parser.py -q
```

Expected:

- 明细型 `.xlsx` 测试通过
- 仅总分 `.xlsx` 测试通过

**Step 5: Commit**

```bash
git add gradebook/services/xlsx_parser.py gradebook/tests/test_xlsx_parser.py
git commit -m "feat: support total-only xlsx exam parsing"
```

---

### Task 3: 扩展导入层的按姓名归并策略

**Files:**
- Modify: `gradebook/services/import_exam.py`
- Test: `gradebook/tests/test_import_exam.py`

**Step 1: 写失败测试，验证按姓名归并**

在 `gradebook/tests/test_import_exam.py` 中新增：

```python
@pytest.mark.django_db
def test_import_total_only_xlsx_merges_student_by_name_when_ids_missing() -> None:
    ...
```

测试流程：

1. 先导入一个带学号的明细考试
2. 再导入一个只有姓名与得分的仅总分考试
3. 断言同名学生没有重复建档
4. 断言第二场考试成绩挂在已有学生名下

**Step 2: 实现最小归并逻辑**

将 `_upsert_student()` 调整为：

```python
def _upsert_student(row: ParsedStudentRow) -> Student:
    if row.external_id and not row.external_id.startswith("name-only:"):
        ...

    student = Student.objects.filter(name=row.name).order_by("id").first()
    if student is not None:
        return student

    external_id = row.external_id or f"name-only:{row.name}"
    ...
```

同时确保：

- 仅姓名考试在解析阶段若缺学号，会生成空 `external_id` 或 `name-only:` 兜底值
- 创建新学生时不会违反唯一约束

**Step 3: 跑导入测试**

Run:

```bash
pytest gradebook/tests/test_import_exam.py -q
```

Expected:

- 明细型导入测试通过
- `.xls` 导入测试通过
- 仅总分 `.xlsx` 导入与姓名归并测试通过

**Step 4: Commit**

```bash
git add gradebook/services/import_exam.py gradebook/tests/test_import_exam.py
git commit -m "feat: merge total-only exam students by name"
```

---

### Task 4: 让无题目考试的题目筛选页友好降级

**Files:**
- Modify: `gradebook/views/question_filter_views.py`
- Modify: `gradebook/templates/gradebook/question_filter.html`
- Test: `gradebook/tests/test_question_filter.py`

**Step 1: 写失败测试**

在 `gradebook/tests/test_question_filter.py` 中新增：

```python
@pytest.mark.django_db
def test_question_filter_page_shows_disabled_message_for_total_only_exam(client) -> None:
    ...
```

断言：

- 页面能正常打开
- 显示“该考试不含题目明细，无法按题号筛选学生”之类提示
- 不展示可提交筛选的有效表单，或表单提交被禁用

**Step 2: 视图中判断题号是否存在**

在 `question_filter()` 中增加类似逻辑：

```python
question_keys = _load_question_keys(exam_id)
question_filter_available = bool(question_keys)
```

若不可用：

- 不执行筛选逻辑
- 只渲染说明文案

**Step 3: 模板中渲染降级提示**

在 `gradebook/templates/gradebook/question_filter.html` 中增加：

```django
{% if not question_filter_available %}
  <div class="alert alert-info">该考试不含题目明细，无法按题号筛选学生。</div>
{% else %}
  ...原表单...
{% endif %}
```

**Step 4: 跑筛选相关测试**

Run:

```bash
pytest gradebook/tests/test_question_filter.py -q
```

Expected:

- 原有筛选测试继续通过
- 新增降级测试通过

**Step 5: Commit**

```bash
git add gradebook/views/question_filter_views.py gradebook/templates/gradebook/question_filter.html gradebook/tests/test_question_filter.py
git commit -m "feat: degrade question filter for total-only exams"
```

---

### Task 5: 完成全链路回归验证

**Files:**
- Review: `gradebook/services/xlsx_parser.py`
- Review: `gradebook/services/import_exam.py`
- Review: `gradebook/views/question_filter_views.py`
- Review: `gradebook/templates/gradebook/question_filter.html`
- Review: `gradebook/tests/test_xlsx_parser.py`
- Review: `gradebook/tests/test_xls_parser.py`
- Review: `gradebook/tests/test_import_exam.py`
- Review: `gradebook/tests/test_question_filter.py`

**Step 1: 运行定向测试**

Run:

```bash
pytest gradebook/tests/test_xlsx_parser.py \
  gradebook/tests/test_xls_parser.py \
  gradebook/tests/test_import_exam.py \
  gradebook/tests/test_question_filter.py -q
```

Expected:

- 相关解析、导入、筛选测试全部通过

**Step 2: 运行全量测试**

Run:

```bash
pytest -q
```

Expected:

- 全部测试通过

**Step 3: 运行 Django 检查**

Run:

```bash
python3 manage.py check
```

Expected:

- `System check identified no issues (0 silenced).`

**Step 4: Commit**

```bash
git add gradebook/services/xlsx_parser.py \
  gradebook/services/import_exam.py \
  gradebook/views/question_filter_views.py \
  gradebook/templates/gradebook/question_filter.html \
  gradebook/tests/test_xlsx_parser.py \
  gradebook/tests/test_xls_parser.py \
  gradebook/tests/test_import_exam.py \
  gradebook/tests/test_question_filter.py
git commit -m "feat: support total-only excel exams in test dataset"
```
