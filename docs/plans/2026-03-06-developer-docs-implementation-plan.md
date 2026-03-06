# 开发维护文档补全实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 为 `GradeInsight` 补齐面向开发维护者的核心文档，使开发者可以快速理解系统架构、数据模型、开发入口与运维检查方式。

**Architecture:** 以当前代码、测试、配置和运维脚本为唯一事实来源，新增 4 份中文文档并在 `README.md` 中增加导航入口。文档分层遵循“README 负责导航、`docs/plans/` 负责系统设计认知、`docs/runbook/` 负责操作与维护手册”，避免重复现有需求文档。

**Tech Stack:** Markdown、Django、pytest、Docker Compose、PostgreSQL、HTMX、Chart.js

---

### Task 1: 编写系统架构总览

**Files:**
- Create: `docs/plans/2026-03-06-architecture-overview.md`
- Read: `README.md`
- Read: `config/urls.py`
- Read: `gradebook/urls.py`
- Read: `worklists/urls.py`
- Read: `gradebook/views/import_views.py`
- Read: `gradebook/views/exam_views.py`
- Read: `gradebook/views/student_views.py`
- Read: `gradebook/views/question_filter_views.py`
- Read: `worklists/views.py`

**Step 1: 整理模块与入口**

梳理 `config/`、`gradebook/`、`worklists/`、`templates/`、`static/`、`docs/`、`docker/` 的职责边界，并提炼用户能感知的主页面入口。

**Step 2: 写出四条主流程**

描述并落盘以下流程：
- 导入预览与确认导入
- 考试分析与题目统计展示
- 学生档案与题目强弱项
- 题目筛选生成任务与提交追踪

**Step 3: 交叉核对代码路径**

确保文档中提到的视图、服务、模板和路由，都能在对应文件中找到实现。

---

### Task 2: 编写数据模型与数据流说明

**Files:**
- Create: `docs/plans/2026-03-06-data-model-and-flow.md`
- Read: `gradebook/models.py`
- Read: `worklists/models.py`
- Read: `gradebook/services/import_exam.py`
- Read: `gradebook/services/student_dashboard.py`
- Read: `gradebook/services/weakness.py`
- Read: `gradebook/services/question_filter.py`
- Read: `gradebook/services/exam_analytics.py`

**Step 1: 整理核心模型关系**

说明 `Student`、`Exam`、`ExamScore`、`ExamQuestionScore`、`ExamQuestionStat`、`ExamImport`、`Task`、`TaskAssignment` 之间的关系与用途。

**Step 2: 整理关键字段与业务口径**

重点解释：
- `source_sha256` 去重
- `excluded_from_stats` / `exclude_reason` 统计排除口径
- `question_key` 的存储方式
- `rule_json` 与 `submitted_at` 的含义

**Step 3: 写出数据流**

分别写出：
- Excel 导入到统计重建的数据流
- 题目筛选到任务创建的数据流
- 学生详情页的趋势与弱势题目数据流

---

### Task 3: 编写开发者上手手册

**Files:**
- Create: `docs/runbook/developer-onboarding.md`
- Read: `requirements.txt`
- Read: `pytest.ini`
- Read: `README.md`
- Read: `gradebook/tests/test_import_flow.py`
- Read: `gradebook/tests/test_student_pages.py`
- Read: `worklists/tests/test_toggle_submission.py`

**Step 1: 写本地开发最小流程**

写明依赖安装、迁移、启动服务、登录入口、常用命令与推荐的检查顺序。

**Step 2: 写常见改动入口**

说明以下改动应该优先查看哪些文件：
- 导入逻辑
- 考试详情分析
- 学生档案
- 题目筛选
- 任务提交流程

**Step 3: 写测试地图与回归建议**

基于现有测试说明“改哪里跑哪些测试”，并给出 `pytest -q` 与 `python manage.py check` 的使用建议。

---

### Task 4: 补强运维文档与 README 导航

**Files:**
- Create: `docs/runbook/env-and-ops.md`
- Modify: `README.md`
- Read: `.env.example`
- Read: `docker-compose.yml`
- Read: `docs/runbook/deploy.md`
- Read: `docs/runbook/backup.md`
- Read: `ops/backup_pg.sh`

**Step 1: 写环境变量与运维检查清单**

整理 `.env.example` 中变量含义，并补充容器启动、数据库健康检查、静态资源、备份与恢复相关说明。

**Step 2: 在 README 增加文档导航**

新增“开发维护文档”章节，指向新文档与现有 runbook，帮助后续开发者快速定位资料。

**Step 3: 核对路径与命令**

逐项检查文档中涉及的路径、命令、容器服务名、脚本名与当前仓库一致。

---

### Task 5: 验证文档准确性

**Files:**
- Review: `docs/plans/2026-03-06-architecture-overview.md`
- Review: `docs/plans/2026-03-06-data-model-and-flow.md`
- Review: `docs/runbook/developer-onboarding.md`
- Review: `docs/runbook/env-and-ops.md`
- Review: `README.md`

**Step 1: 执行 Django 检查**

Run: `python manage.py check`

Expected: 系统检查通过，无配置错误。

**Step 2: 自检文档一致性**

检查文档中的文件路径、命令、模型名、环境变量和流程描述是否与当前代码一致。

**Step 3: 记录交付内容**

在最终说明中列出新增/修改文档、验证命令与后续可选动作，不做额外功能改动。
