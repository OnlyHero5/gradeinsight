# Progress — GradeInsight

## 2026-02-25（实现会话）
- 初始化 Git：`git init -b main`，并创建开发分支 `feat/gradeinsight-mvp`
- 完成 Django 工程搭建：`config`、`gradebook`、`worklists`、统一路由与登录保护
- 按 TDD 流程先写失败测试，再实现以下能力：
  - 模型约束（学生唯一、题目得分唯一）
  - Excel 解析（题号提取、异常统计）
  - 导入服务（去重、事务写入、题目统计预计算）
  - 题目筛选（below_mean 等）
  - 任务状态切换（已交/未交持久化）
- 完成核心页面与样式系统（科技风 + 玻璃拟态 + 响应式）
- 完成部署与运维脚手架：Docker Compose、Caddy、部署与备份文档、备份脚本
- 验证结果：
  - `python3 manage.py check` 通过
  - `python3 -m pytest` 通过（`10 passed`）

- 前端重构：按 ui-ux-pro-max 准则重写 base 与全部页面模板，更新为现代编辑感科技风；完成 iPad/桌面响应式适配
- 运行验证：manage.py check 通过，pytest 10/10 通过，服务已在 0.0.0.0:8000 运行（PID 9883）

- 二次前端推倒重构：重写 tokens/app 样式系统，落实浅色液态玻璃与现代分层排版，统一至所有模板页面
- 技能修复：从 GitHub 拉取 `nextlevelbuilder/ui-ux-pro-max-skill`，恢复本机 `~/.codex/src/ui-ux-pro-max` 并修复软链，`search.py --design-system` 已可执行
- 联网调研：参考 Linear / Vercel / Apple 设计资料提炼色彩、层级、留白与动效策略

## 2026-02-25（本轮重构）
- 执行 TDD：先新增 `gradebook/tests/test_exam_analytics.py`，验证分析增强需求，再落地实现
- 新增后端分析模块：`gradebook/services/exam_analytics.py`
- 扩展考试详情上下文：`gradebook/views/exam_views.py` 增加 `insight_pack` 和多图表 JSON 数据
- 前端推倒重构（Bootstrap 组件化）：
  - `templates/base.html` 接入 Bootstrap 5.3.3 / Bootstrap Icons / Chart.js
  - 全页面模板重写：登录、考试列表、考试详情、学生详情、导入、题目筛选、任务列表/详情
  - 样式系统重写：`static/css/tokens.css` + `static/css/app.css`
- 表单组件规范化：`gradebook/forms.py` 为输入控件统一注入 Bootstrap 类名
- 验证结果：
  - `pytest -q gradebook/tests/test_exam_analytics.py` -> `2 passed`
  - `pytest -q` -> `12 passed`
  - `python3 manage.py check` -> `System check identified no issues`
- 运行状态：
  - 应用运行中：`/home/psx/miniconda3/envs/gradeinsight/bin/python manage.py runserver 0.0.0.0:8000 --noreload`
  - 登录测试用户：`teacher / Teacher@123`（本轮已创建）

## 2026-02-25（Excel 双格式扩展）
- 按用户要求先完整读取两个样例文件，确认多页/多工作表结构均已扫描
- TDD 新增测试：
  - `gradebook/tests/test_xls_parser.py`
  - `test_import_upload_accepts_xls`（补充到 `gradebook/tests/test_import_flow.py`）
  - `test_import_xls_creates_exam_and_question_stats`（补充到 `gradebook/tests/test_import_exam.py`）
- 新增解析与分发：
  - `gradebook/services/xls_parser.py`（解析单科成绩单 `.xls`）
  - `gradebook/services/excel_parser.py`（按后缀分发 `.xls/.xlsx`）
- 导入链路改造：
  - `gradebook/views/import_views.py` 接受 `.xls/.xlsx`
  - `gradebook/services/import_exam.py` 新增 `import_exam_from_excel_bytes`，保留旧 `import_exam_from_xlsx_bytes` 兼容入口
- 依赖更新：`requirements.txt` 增加 `xlrd>=2.0,<3`
- 验证结果：
  - `pytest -q` -> `15 passed`
  - `python3 manage.py check` -> `System check identified no issues`

## 2026-02-25（学生档案页面与任务状态）
- 按 TDD 新增测试：
  - `gradebook/tests/test_student_pages.py`
  - `tests/test_auth_required.py` 增加 `student_list` 登录保护校验
- 新增学生总览页面：
  - 新路由 `gradebook/students/`（`student_list`）
  - 新模板 `gradebook/templates/gradebook/student_list.html`
  - 新聚合服务 `gradebook/services/student_dashboard.py`
- 学生详情页增强：
  - 增加“任务完成情况”区块
  - 展示未完成任务/已完成任务列表与汇总计数
- 导航增强：
  - 顶部导航新增“学生档案”入口，并支持 active 状态
- 验证结果：
  - `pytest -q gradebook/tests/test_student_pages.py tests/test_auth_required.py` -> `4 passed`
  - `pytest -q` -> `18 passed`
  - `python3 manage.py check` -> `System check identified no issues`

## 2026-02-25（任务切换按钮无响应修复）
- 按 `systematic-debugging` 完整复现：
  - 任务切换接口在无 CSRF 头时返回 `403`，导致前端点击“切换状态”看起来无响应
- 按 TDD 先写失败测试：
  - `worklists/tests/test_toggle_submission.py::test_task_detail_includes_htmx_csrf_bridge`
- 修复实现：
  - 在 `templates/base.html` 增加全局 HTMX CSRF 注入脚本（监听 `htmx:configRequest`，写入 `X-CSRFToken`）
- 回归验证：
  - `pytest -q worklists/tests/test_toggle_submission.py` -> `3 passed`
  - `pytest -q` -> `20 passed`
  - `python3 manage.py check` -> `System check identified no issues`
