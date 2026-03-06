# GradeInsight 数据模型与数据流说明

## 1. 这份文档关注什么

本文件聚焦三个问题：

- 当前数据库里有哪些核心实体？
- 这些实体之间如何关联？
- 一次导入、一次筛选、一次任务提交，数据是怎样流动的？

以下内容全部基于当前仓库实现，而不是未来规划。

---

## 2. 核心实体总览

## 2.1 `gradebook` 侧实体

| 模型 | 作用 | 关键字段 |
|---|---|---|
| `Student` | 学生主档 | `name`、`external_id`、`admission_ticket`、`custom_exam_id`、`class_name` |
| `Exam` | 一次考试导入的主记录 | `name`、`exam_date`、`imported_at`、`source_filename`、`source_sha256`、`identity_key`、`identity_label` |
| `ExamScore` | 学生在某次考试的汇总成绩 | `total_score`、`objective_score`、`subjective_score`、`rank_in_class` |
| `ExamQuestionScore` | 学生在某次考试某道题的得分 | `question_key`、`score_value` |
| `ExamQuestionStat` | 某次考试某道题的统计结果 | `mean_score`、`median_score`、`sample_n` |
| `ExamImport` | 导入预览与暂存记录 | `preview_json`、`payload`、`status`、`error` |

## 2.2 `worklists` 侧实体

| 模型 | 作用 | 关键字段 |
|---|---|---|
| `Task` | 一份由筛选结果生成的任务 | `exam`、`name`、`question_key`、`rule_json` |
| `TaskAssignment` | 任务与学生的绑定关系 | `task`、`student`、`submitted_at` |

---

## 3. 模型关系

可以把关系理解为：

- 一个 `Exam` 对应很多 `ExamScore`
- 一个 `ExamScore` 对应一个学生在一次考试的汇总分
- 一个 `Exam` + `Student` 对应很多 `ExamQuestionScore`
- 一个 `Exam` 对应很多 `ExamQuestionStat`
- 一个 `Exam` 可以派生很多 `Task`
- 一个 `Task` 对应很多 `TaskAssignment`

如果用文字版关系图表示：

```text
Student
  ├─< ExamScore >─ Exam
  ├─< ExamQuestionScore >─ Exam
  └─< TaskAssignment >─ Task ─> Exam

Exam
  ├─< ExamScore
  ├─< ExamQuestionScore
  ├─< ExamQuestionStat
  ├─< Task
  └─< ExamImport（通过 source_sha256 间接关联导入来源）
```

---

## 4. 关键字段解释

## 4.1 `Student`

### `external_id`

当前实现里，`Student.external_id` 是 **全局唯一**。
这点非常重要，因为仓库里还没有独立的 `Class` 模型，`class_name` 只是学生表中的普通字符串字段。

这意味着：

- 导入时的去重主键是 `external_id`
- 同一个 `external_id` 会被视为同一个学生跨考试延续
- 目前没有“同班级内唯一、跨班可重复”的实现

### `admission_ticket` / `custom_exam_id`

两者都保留，但导入时的优先级是：

1. 优先 `准考证号`
2. 若为空，则退回 `自定义考号`

如果 `.xlsx` 中两者都存在且不一致，会计入 `mismatched_id_count`，供导入预览提示使用。

---

## 4.2 `Exam`

### `source_sha256`

这是“文件级重复导入保护”的核心字段，具有唯一约束。

- 上传预览阶段就会计算 SHA-256
- 如果 `Exam` 里已经存在同样的 hash，会直接拒绝重复上传
- 正式导入后，该 hash 会和考试记录绑定

### `identity_key` / `identity_label`

这是“同场考试等价去重”的核心字段。

- `identity_key`：程序使用的规范化标识
- `identity_label`：给用户展示的可读标签

它们由解析层从标题行、工作表标题和文件名中归一得到，用于拦截“同一场考试的不同文件”。

### `participants_n` / `excluded_n`

这两个字段记录的是导入结果概况：

- `participants_n`：解析得到的学生记录数
- `excluded_n`：被判定为不参与统计的学生记录数

注意：考试详情页中的“统计人数”不是直接用 `participants_n`，而是来自 `ExamScore` 中 `excluded_from_stats=False` 且 `total_score` 有效的记录数。

---

## 4.3 `ExamScore`

### `excluded_from_stats`

这是当前所有统计口径的关键开关。
只要某条考试成绩被标记为 `True`，它就不会参与：

- 班级均分 / 中位数 / 最高最低
- 分数分布
- 题目均分与题目中位数
- 学生平均成绩统计
- 学生题目强弱项比较

当前触发条件来自解析层：**总分不是可转成数值的值**。

### `exclude_reason`

目前主要使用：

- `non_numeric_total_score`

也就是原始总分有值，但不是合法数值，例如“未扫，不计排名”。

---

## 4.4 `ExamQuestionScore`

### `question_key`

题号统一存为字符串，例如：

- `1`
- `51`
- `31(1)`
- `51(3)`

题号格式由解析层用正则识别，规则是：

```text
^\d+(?:\(\d+\))?$
```

这保证了“整题”和“子题”可以并存。

---

## 4.5 `ExamQuestionStat`

这是导入后按考试维度重建出的题目统计快照。

包含：

- `mean_score`
- `median_score`
- `sample_n`

重建逻辑在 `gradebook/services/stats_queries.py` 中，特点是：

- 只统计 `excluded_from_stats=False` 的学生
- 只统计 `score_value` 非空的题目得分
- 每次导入会先删掉该考试已有统计，再整体重算

---

## 4.6 `ExamImport`

`ExamImport` 用来承接“先预览、后确认”的导入体验。

关键字段：

- `preview_json`：前端预览页展示的数据摘要
- `payload`：原始文件二进制内容
- `status`：`staged` / `imported` / `failed`
- `error`：失败原因

当前 `preview_json` 至少包含：

- `student_count`
- `question_count`
- `excluded_from_stats_count`
- `mismatched_id_count`
- `question_keys`

---

## 4.7 `Task` 与 `TaskAssignment`

### `Task.rule_json`

保存题目筛选时使用的规则，例如：

- 操作符 `op`
- 比较值 `value`
- 区间边界 `min` / `max`

它的作用不是再次实时筛选，而是保留“这份任务从何而来”的规则上下文。

### `TaskAssignment.submitted_at`

这是任务状态的唯一事实来源：

- `null`：未交
- 非 `null`：已交

当前没有单独的布尔状态字段，状态切换就是更新时间戳是否存在。

---

## 5. 关键约束与实现口径

| 约束/规则 | 当前实现 |
|---|---|
| 学生去重 | `Student.external_id` 全局唯一 |
| 文件去重 | `Exam.source_sha256` 唯一 |
| 同场考试等价去重 | `Exam.identity_key` 应用层判重 |
| 一场考试同一学生仅一条汇总成绩 | `ExamScore(exam, student)` 唯一 |
| 一场考试同一学生同一题仅一条题目得分 | `ExamQuestionScore(exam, student, question_key)` 唯一 |
| 一场考试同一题仅一条统计结果 | `ExamQuestionStat(exam, question_key)` 唯一 |
| 一份任务同一学生仅一条任务分配 | `TaskAssignment(task, student)` 唯一 |

---

## 6. 两类 Excel 的解析口径

## 6.1 `.xlsx`

解析器：`gradebook/services/xlsx_parser.py`

特点：

- 优先读取名为 `得分明细` 的工作表
- 如果没有该工作表，则退回到第一个工作表
- 先扫描前 12 行寻找包含“姓名”和“总分”的表头
- 从表头中提取所有题号列
- 支持读取：
  - 姓名
  - 准考证号
  - 自定义考号
  - 班级
  - 总分
  - 客观分
  - 主观分
  - 班次

## 6.2 `.xls`

解析器：`gradebook/services/xls_parser.py`

特点：

- 读取第一个工作表
- 按 `姓名(外部ID)_成绩单` 形式识别“学生成绩单块”
- 从固定行区段提取题号和得分
- 当前不会解析客观分、主观分、班级排名，因此这些字段会是 `None`

---

## 7. 三条核心数据流

## 7.1 导入流：原始文件 -> 统计结果

### 阶段 1：上传与预览

1. 用户上传 Excel
2. `ImportUploadForm` 做字段校验
3. `import_upload` 检查：
   - 文件大小
   - 后缀是否合法
   - SHA-256 是否已存在
4. `parse_exam_excel()` 分发到 `.xlsx` 或 `.xls` 解析器
5. 解析器返回 `ParsedExam`（含 `identity_key` / `identity_label`）
6. 视图用 `identity_key` 检查是否命中已导入的等价考试
7. 预览信息写入 `ExamImport`

### 阶段 2：确认导入

1. `import_confirm` 读取暂存的 `ExamImport`
2. `import_exam_from_excel_bytes()` 再次做重复导入保护
3. 先按 `source_sha256` 检查“同文件重复”
4. 再按 `identity_key` 检查“同场异文件重复”
5. 创建 `Exam`
6. 对每条学生记录执行 `_upsert_student()`
7. 创建 `ExamScore`
8. 批量写入 `ExamQuestionScore`
9. 调用 `rebuild_question_stats(exam)`
10. 将 `ExamImport.status` 更新为 `imported`

### 阶段 3：统计可用

导入一旦完成，考试详情页和学生详情页就能使用：

- `ExamScore`
- `ExamQuestionScore`
- `ExamQuestionStat`

来生成页面分析结果。

---

## 7.2 筛选流：题目条件 -> 任务清单

1. 用户进入 `/gradebook/exams/<exam_id>/filter/`
2. 页面先加载题号列表
3. 表单提交后，`QuestionFilterForm` 校验规则
4. `filter_students_by_question_rule()` 先确定“可参与筛选的学生集合”
   - 默认只取 `excluded_from_stats=False`
   - 若勾选“包含未扫/缺考”，则不过滤这层
5. 根据规则筛出符合条件的学生 ID
6. 若用户选择创建任务：
   - 创建 `Task`
   - 批量创建 `TaskAssignment`
   - 跳转到任务详情页

这条链路的关键点是：
**筛选和任务创建解耦**。先得到结果，再决定是否落成任务。

---

## 7.3 学生详情流：成绩趋势 + 弱势题目 + 任务快照

1. `student_detail` 先取该学生所有 `ExamScore`
2. 按考试日期或导入时间排序
3. 构造：
   - 总分趋势数据
   - 排名趋势数据
4. 根据当前选中的考试，调用 `build_question_deltas(exam_id, student_id)`
5. `build_question_deltas()` 会：
   - 拿到该学生本次考试的 `ExamScore`
   - 如果该条记录被排除统计，则直接返回空结果
   - 将该学生每道题得分与 `ExamQuestionStat.mean_score` 比较
   - 按差值分类为 `weak` / `avg` / `good`
6. 同时调用 `build_student_task_snapshot(student)` 生成任务摘要

这样页面能同时看到：

- 长期趋势
- 单场考试细粒度题目表现
- 当前任务完成状态

---

## 8. 统计与筛选规则

## 8.1 题目强弱项分类

在 `gradebook/services/weakness.py` 中，分类逻辑是：

- `delta < -EPS`：`weak`
- `delta > EPS`：`good`
- 否则：`avg`

其中 `EPS` 来自环境变量 `GRADEINSIGHT_EPSILON`，默认 `0.01`。

---

## 8.2 高于 / 低于本题平均分

在 `gradebook/services/question_filter.py` 中：

- `below_mean` 使用 `mean_score - EPS`
- `above_mean` 使用 `mean_score + EPS`

这能避免浮点边界导致“刚好等于平均分”的学生被误筛入。

---

## 8.3 分数分布与成绩段

考试详情页的两套口径来自不同服务：

- `score_histogram()`：按固定步长（默认 10 分）做分箱
- `build_exam_insight_pack()`：按预设成绩段 `<60`、`60-79`、`80-89`、`90+` 统计

---

## 9. 当前实现的几个重要现实

### 9.1 目前没有独立 `Class` 模型

如果后续要做“真正多班级隔离”，当前模型需要调整。
现在的 `class_name` 只是冗余业务属性，还不是独立实体。

### 9.2 `.xls` 信息不如 `.xlsx` 丰富

当前旧版 Excel 解析只保证：

- 学生标识
- 题目得分
- 总分

因此如果要依赖客观/主观分、班级排名等字段，优先使用 `.xlsx` 数据源更稳妥。

### 9.3 题目统计是导入后重建快照

这使查询更简单，但也意味着：

- 统计结果依赖导入时的数据状态
- 如果后续人工改分或补数据，需要重新生成统计才会同步

当前仓库还没有“增量重算 / 后台重算”入口。

---

## 10. 结论

当前数据模型设计的核心思路是：

- 用 `Student` 与 `Exam` 建立长期成绩沉淀
- 用 `ExamScore` + `ExamQuestionScore` 保存“汇总 + 明细”双层成绩
- 用 `ExamQuestionStat` 存放可快速读取的统计快照
- 用 `Task` + `TaskAssignment` 把分析结果落成教学行动

如果后续要扩展功能，最关键的是先判断新需求应该落在：

- **原始数据层**（模型）
- **统计规则层**（services）
- **交互与呈现层**（views/templates）

这样才能避免把业务规则散落到模板或视图里。
