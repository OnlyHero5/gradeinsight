# Same Exam Dedup Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 为不同 Excel 文件中的同一场考试生成稳定等价标识，并在预览与正式导入阶段阻止重复入库。

**Architecture:** 在解析层统一产出 `identity_key` / `identity_label`，再由导入服务和上传视图共同调用重复校验。保留现有 `source_sha256` 文件级去重，同时补上“同场异文件”等价去重。优先做应用层判重，不在本轮引入强唯一约束。

**Tech Stack:** Python 3.12、Django、pytest、openpyxl、xlrd

---

### Task 1: 为同场考试识别补充失败测试

**Files:**
- Modify: `gradebook/tests/test_xlsx_parser.py`
- Modify: `gradebook/tests/test_xls_parser.py`
- Modify: `gradebook/tests/test_import_exam.py`
- Modify: `gradebook/tests/test_import_flow.py`

**Step 1: 写解析层失败测试**

补充真实数据集断言：

- `期末考试 xlsx` 与 `期末考试 xls` 的 `identity_key` 相同
- `模拟1.xlsx` 与 `模拟1(1).xlsx` 的 `identity_key` 相同

**Step 2: 写导入层失败测试**

新增测试：

- 先导入 `模拟1.xlsx`
- 再导入 `模拟1(1).xlsx`
- 断言抛出 `DuplicateImportError`

**Step 3: 写上传预览失败测试**

新增测试：

- 先导入一份 `Exam`
- 再上传另一份等价文件
- 断言页面出现“疑似同一场考试已导入”之类提示

**Step 4: 运行测试确认失败**

Run: `pytest -q gradebook/tests/test_xlsx_parser.py gradebook/tests/test_xls_parser.py gradebook/tests/test_import_exam.py gradebook/tests/test_import_flow.py`

Expected: 新增同场考试相关测试失败

---

### Task 2: 实现考试等价标识提取

**Files:**
- Create: `gradebook/services/exam_identity.py`
- Modify: `gradebook/services/xlsx_parser.py`
- Modify: `gradebook/services/xls_parser.py`

**Step 1: 新增归一化工具**

在 `exam_identity.py` 中实现：

- 提取候选标题文本
- 归一化班级、科目、满分、考试主体名
- 生成 `identity_key` 与 `identity_label`

**Step 2: 让 `.xlsx` 解析器返回等价标识**

从 workbook 顶部标题或文件名中构建考试标识，并写入 `ParsedExam`

**Step 3: 让 `.xls` 解析器返回等价标识**

从第 2 行标题或文件名中构建考试标识，并写入 `ParsedExam`

**Step 4: 跑解析测试**

Run: `pytest -q gradebook/tests/test_xlsx_parser.py gradebook/tests/test_xls_parser.py`

Expected: 标识相关测试通过

---

### Task 3: 在导入与预览阶段拦截同场异文件

**Files:**
- Modify: `gradebook/models.py`
- Modify: `gradebook/services/import_exam.py`
- Modify: `gradebook/views/import_views.py`
- Modify: `gradebook/migrations/`

**Step 1: 模型增加可选标识字段**

为 `Exam` 增加：

- `identity_key`
- `identity_label`

**Step 2: 导入服务增加等价检查**

在 `import_exam_from_excel_bytes()` 中：

- 解析后先检查 `source_sha256`
- 再检查 `identity_key`
- 命中时抛 `DuplicateImportError`

**Step 3: 上传预览阶段增加等价检查**

在 `import_upload()` 中：

- 解析成功后检查是否已有等价考试
- 若命中，给 `file` 字段加错误，不进入预览

**Step 4: 跑导入/页面测试**

Run: `pytest -q gradebook/tests/test_import_exam.py gradebook/tests/test_import_flow.py`

Expected: 导入与上传测试通过

---

### Task 4: 完整回归并补充文档记录

**Files:**
- Modify: `findings.md`
- Modify: `progress.md`

**Step 1: 运行完整验证**

Run:

- `pytest -q`
- `python3 manage.py check`

**Step 2: 记录验证证据**

把关键结果补进 `progress.md`

**Step 3: 记录限制与后续扩展点**

把题型/板块映射仍需独立元数据支撑的事实补进 `findings.md`

---

Plan complete and saved to `docs/plans/2026-03-06-same-exam-dedup-implementation-plan.md`.
