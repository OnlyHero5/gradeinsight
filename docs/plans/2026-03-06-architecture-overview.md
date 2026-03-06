# GradeInsight 系统架构总览

## 1. 这份文档解决什么问题

本仓库已经有需求文档、PRD 和 README，但开发者真正接手时，通常先想回答下面几个问题：

- 页面入口在哪里定义？
- 一次成绩导入到底会写哪些表？
- “考试分析 / 学生档案 / 题目筛选 / 任务追踪”分别由哪些视图和服务负责？
- 想改某个功能，应该先看哪个模块？

这份文档只回答 **当前仓库已经实现** 的系统架构与代码入口，不重复业务背景。

---

## 2. 目录与职责

| 目录 | 作用 | 说明 |
|---|---|---|
| `config/` | Django 项目配置 | 包含 `settings.py`、根路由、WSGI/ASGI 入口 |
| `gradebook/` | 成绩导入与分析主模块 | 负责学生、考试、成绩、题目统计、导入流程、分析页与学生页 |
| `worklists/` | 任务追踪模块 | 负责任务实例、学生提交状态、未交导出 |
| `templates/` | 全局模板 | 包含基座模板、登录页、消息提示等共享页面结构 |
| `static/` | 前端样式资源 | 主要是 Bootstrap 之上的主题样式与 UI token |
| `docs/` | 需求、设计、计划、运维文档 | 当前文档也属于该目录的一部分 |
| `docker/` | 容器部署配置 | Web 镜像、Caddy 反向代理配置 |
| `ops/` | 运维脚本 | 当前包含 PostgreSQL 备份脚本 |

---

## 3. 模块边界

### 3.1 `config/`

- `config/settings.py`
  - 定义 Django 基础配置
  - 通过 `dj_database_url` 读取 `DATABASE_URL`
  - 默认数据库是 `db.sqlite3`
  - 配置 `whitenoise`、`django-htmx`、上传大小与 epsilon 参数
- `config/urls.py`
  - 根路由入口
  - 提供 `/login/`、`/logout/`
  - 将 `/gradebook/` 与 `/worklists/` 分发到各自 app

### 3.2 `gradebook/`

这是系统的核心业务模块，覆盖：

- 学生、考试、成绩、题目统计等核心领域模型
- Excel 解析与导入
- 考试详情分析页
- 学生列表与学生详情页
- 题目筛选页

按分层看：

| 层次 | 主要文件 | 作用 |
|---|---|---|
| 模型层 | `gradebook/models.py` | 定义学生、考试、成绩、题目统计、导入暂存等表 |
| 表单层 | `gradebook/forms.py` | 定义导入表单、题目筛选表单 |
| 视图层 | `gradebook/views/*.py` | 处理页面请求与上下文拼装 |
| 服务层 | `gradebook/services/*.py` | 负责解析、导入、统计、排序、弱项判断等纯业务逻辑 |
| 模板层 | `gradebook/templates/gradebook/*.html` | 页面渲染与图表容器 |

### 3.3 `worklists/`

任务追踪是独立 app，但依赖 `gradebook` 中的 `Exam` 与 `Student`。

- `worklists/models.py`
  - `Task` 表示一份由筛选结果生成的任务
  - `TaskAssignment` 表示任务与学生的绑定关系及提交时间
- `worklists/views.py`
  - 任务列表
  - 任务详情
  - 已交/未交状态切换
  - 未交 CSV 导出

### 3.4 前端层

- `templates/base.html` 是全站基座模板
- UI 主要依赖：
  - Bootstrap 5.3
  - HTMX
  - Chart.js
  - 自定义样式：`static/css/tokens.css`、`static/css/app.css`

`base.html` 里还承担了两个重要职责：

- 统一 HTMX 的 CSRF header 注入
- 明暗主题切换与持久化

---

## 4. 页面与路由地图

### 4.1 根入口

| 路径 | 作用 | 代码入口 |
|---|---|---|
| `/login/` | 登录页 | `config/urls.py` |
| `/logout/` | 退出登录 | `config/urls.py` |
| `/` | 默认跳转到考试列表 | `config/urls.py` |

### 4.2 `gradebook` 页面

| 路径 | 页面 | 视图 |
|---|---|---|
| `/gradebook/exams/` | 考试列表 | `gradebook/views/exam_views.py` 中的 `exam_list` |
| `/gradebook/exams/<exam_id>/` | 考试详情 | `gradebook/views/exam_views.py` 中的 `exam_detail` |
| `/gradebook/exams/<exam_id>/filter/` | 题目筛选 | `gradebook/views/question_filter_views.py` 中的 `question_filter` |
| `/gradebook/students/` | 学生列表 | `gradebook/views/student_views.py` 中的 `student_list` |
| `/gradebook/students/<student_id>/` | 学生详情 | `gradebook/views/student_views.py` 中的 `student_detail` |
| `/gradebook/import/` | 导入上传 | `gradebook/views/import_views.py` 中的 `import_upload` |
| `/gradebook/import/<import_id>/confirm/` | 确认导入 | `gradebook/views/import_views.py` 中的 `import_confirm` |

### 4.3 `worklists` 页面

| 路径 | 页面 | 视图 |
|---|---|---|
| `/worklists/tasks/` | 任务列表 | `worklists/views.py` 中的 `task_list` |
| `/worklists/tasks/<task_id>/` | 任务详情 | `worklists/views.py` 中的 `task_detail` |
| `/worklists/tasks/<task_id>/assignments/<assignment_id>/toggle/` | 切换提交状态 | `worklists/views.py` 中的 `assignment_toggle` |
| `/worklists/tasks/<task_id>/export/pending.csv` | 导出未交 CSV | `worklists/views.py` 中的 `task_export_pending_csv` |

---

## 5. 四条主业务流

## 5.1 导入流：`import_upload -> import_confirm -> exam_detail`

### 请求流

1. 用户在导入页提交考试名称、日期和 Excel 文件。
2. `ImportUploadForm` 做基本字段校验。
3. `import_upload` 额外做三类校验：
   - 上传大小不能超过 `GRADEINSIGHT_UPLOAD_MAX_BYTES`
   - 文件后缀必须是 `.xls` 或 `.xlsx`
   - 文件 SHA-256 不能与已导入考试重复
4. `parse_exam_excel` 按扩展名分发到：
   - `parse_exam_xlsx`
   - `parse_exam_xls`
5. 解析完成后，先把预览数据写入 `ExamImport`，状态为 `staged`。
6. 用户确认后进入 `import_confirm`。
7. `import_exam_from_excel_bytes` 在事务中完成正式入库：
   - 创建 `Exam`
   - upsert `Student`
   - 创建 `ExamScore`
   - 批量写入 `ExamQuestionScore`
   - 调用 `rebuild_question_stats` 重建 `ExamQuestionStat`
8. 完成后跳转到考试详情页。

### 关键文件

- 视图：`gradebook/views/import_views.py`
- 表单：`gradebook/forms.py`
- 解析入口：`gradebook/services/excel_parser.py`
- 导入服务：`gradebook/services/import_exam.py`
- 统计重建：`gradebook/services/stats_queries.py`

### 设计特点

- 预览与正式导入拆开，降低误导入风险
- 用 `source_sha256` 防止重复导入同一文件
- 用 `identity_key` 拦截同一场考试的不同文件
- 正式入库走事务，避免写入一半
- 题目统计在导入完成后统一重建，不在循环中实时算

---

## 5.2 考试分析流：`exam_detail`

考试详情页不是直接堆 SQL，而是把“基础汇总”和“扩展分析包”拆开计算。

### 页面数据来源

- `exam_basic_summary(exam)`
  - 统计人数
  - 平均分
  - 中位数
  - 最高分 / 最低分
- `score_histogram(exam)`
  - 用于分数分布柱状图
- `build_exam_insight_pack(exam)`
  - 通过率 / 优秀率
  - 成绩段分布
  - 分位数
  - 标准差 / IQR
  - 客观 / 主观均分
  - 薄弱题 / 高表现题
  - 低分关注学生
- `ExamQuestionStat`
  - 支撑页面下方“题目平均分”表格

### 页面职责

`gradebook/views/exam_views.py` 负责把上面的结果组织成模板与图表所需上下文，并序列化成 JSON 交给 `Chart.js`。

### 模板职责

`gradebook/templates/gradebook/exam_detail.html` 负责：

- 展示 KPI 卡片
- 放置图表容器
- 渲染 Top 成绩和关注学生表
- 渲染题目平均分表格

---

## 5.3 学生分析流：`student_list -> student_detail`

### 学生列表

`student_list` 页面依赖 `build_student_overview_rows()` 生成聚合视图，而不是逐个学生在模板里查库。

每一行会聚合出：

- 考试次数
- 最近成绩
- 平均总分（只算参与统计且总分有效的记录）
- 待完成任务数
- 已完成任务数
- 全部任务数

### 学生详情

`student_detail` 页面同时展示三类信息：

1. 历次考试趋势
   - 总分趋势
   - 班级排名趋势
2. 某次考试下的题目强弱项
   - 通过 `build_question_deltas()` 完成
3. 当前任务完成情况
   - 通过 `build_student_task_snapshot()` 完成

### 时间排序口径

- 有 `exam_date` 时，按 `exam_date` 排序
- 没有 `exam_date` 时，回退到 `imported_at`

这和 README、PRD 中“未填写考试日期时按导入时间排序”的产品口径是一致的。

---

## 5.4 行动流：`question_filter -> task_detail -> assignment_toggle`

这条链路把“分析结果”转成“可执行任务”。

### 题目筛选

`question_filter` 页面会先加载考试下可用题号：

- 优先从 `ExamQuestionStat` 中取
- 如果统计尚未生成，则退回到 `ExamQuestionScore` 去重取值

用户提交后：

1. `QuestionFilterForm` 校验操作符与分值输入
2. `_build_rule()` 将表单值整理为规则字典
3. `filter_students_by_question_rule()` 执行筛选

支持的规则包括：

- 相等 / 不等于
- 大于 / 小于 / 大于等于 / 小于等于
- 区间
- 高于本题平均分
- 低于本题平均分

### 生成任务

当筛选结果非空且用户触发 `create_task`：

- 创建 `Task`
- 为每个命中学生创建 `TaskAssignment`
- 重定向到任务详情页

### 任务详情与状态切换

`task_detail` 会统计：

- 总人数
- 已交数
- 未交数

`assignment_toggle` 只允许 `POST`，并通过是否设置 `submitted_at` 在“已交/未交”之间切换。
配合 `base.html` 中的 HTMX + CSRF 桥接，前端可以实现无刷新变色更新。

---

## 6. 服务层速查

| 文件 | 职责 |
|---|---|
| `gradebook/services/excel_parser.py` | 按后缀选择 `.xls` / `.xlsx` 解析器 |
| `gradebook/services/xlsx_parser.py` | 解析新版 Excel，定位“得分明细”工作表、识别表头和题号列 |
| `gradebook/services/xls_parser.py` | 解析旧版 Excel，按“学生成绩单块”抽取成绩 |
| `gradebook/services/import_exam.py` | 防重复、事务入库、学生 upsert、题目分数批量写入 |
| `gradebook/services/stats_queries.py` | 重建题目统计、考试基础汇总、分数直方图 |
| `gradebook/services/exam_analytics.py` | 产出考试详情页的扩展分析包 |
| `gradebook/services/student_dashboard.py` | 组装学生列表和学生任务快照 |
| `gradebook/services/weakness.py` | 计算学生题目相对班均的差值与强弱分类 |
| `gradebook/services/question_filter.py` | 执行题号 + 规则筛选 |
| `gradebook/services/number_utils.py` | 数值转换、量化、题号自然排序 |

---

## 7. 配置与部署骨架

### 本地默认配置

- 默认数据库：SQLite
- 入口命令：`python manage.py runserver 0.0.0.0:8000`
- 静态文件：`whitenoise`

### 容器部署

`docker-compose.yml` 中定义了三个服务：

- `db`：PostgreSQL 16
- `web`：Django + Gunicorn
- `caddy`：反向代理

当前 `docker/caddy/Caddyfile` 只配置了 `:80` 反代到 `web:8000`。
如果要上正式 HTTPS，需要按真实域名进一步调整 Caddy 配置。

---

## 8. 开发者怎么读这套代码

如果你刚接手，建议按下面顺序阅读：

1. 先看 `config/urls.py`、`gradebook/urls.py`、`worklists/urls.py`
2. 再看核心模型：`gradebook/models.py`、`worklists/models.py`
3. 然后按主流程读视图：
   - `gradebook/views/import_views.py`
   - `gradebook/views/exam_views.py`
   - `gradebook/views/student_views.py`
   - `gradebook/views/question_filter_views.py`
   - `worklists/views.py`
4. 最后按需深入服务层

如果目标是“改功能”，先看视图；如果目标是“改规则”，先看服务层；如果目标是“改展示”，再进入模板层。

---

## 9. 结论

`GradeInsight` 的整体结构比较清晰：

- `gradebook` 负责分析与数据沉淀
- `worklists` 负责行动闭环
- 服务层承载业务规则，视图层相对轻量
- 前端采用 Django Template + Bootstrap + HTMX + Chart.js 的轻量组合

这意味着后续扩展时，最值得坚持的原则是：

- 业务口径继续放到 `services/`
- 视图保持“取数据 + 组上下文”
- 任务闭环继续依赖题目筛选结果，不在模板层拼业务逻辑
