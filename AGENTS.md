# Repository Guidelines

## 项目结构与模块组织

本仓库是一个基于 Django 的成绩分析与任务追踪系统。`config/` 存放项目配置与入口；`gradebook/` 负责成绩导入、分析、学生视图与服务层；`worklists/` 负责任务清单与提交状态；`templates/` 与 `static/` 存放页面模板和样式资源；`docs/` 保存需求、计划和运维文档；`docker/` 保存容器部署配置。测试主要位于 `gradebook/tests/`、`worklists/tests/`，根目录 `tests/` 放跨模块测试。

## 构建、测试与开发命令

- `pip install -r requirements.txt`：安装 Python 依赖。
- `python manage.py migrate`：执行数据库迁移。
- `python manage.py runserver 0.0.0.0:8000`：本地启动开发服务。
- `pytest -q`：运行全部测试。
- `python manage.py check`：执行 Django 配置与系统检查。
- `docker compose up -d --build`：按容器方式构建并启动服务。

## 代码风格与命名规范

Python 使用 4 空格缩进，保持类型标注、短函数和清晰分层；业务逻辑优先放在 `services/`，视图保持轻量。模块、文件、函数使用 `snake_case`，类名使用 `PascalCase`。模板命名应与页面职责一致，例如 `gradebook/templates/gradebook/exam_detail.html`。当前仓库未配置独立格式化工具，提交前请保持风格与现有代码一致。

## 测试要求

测试使用 `pytest` 与 `pytest-django`，配置见 `pytest.ini`。测试文件命名遵循 `test_*.py`。新增功能或修复缺陷时，应优先补充对应模块测试，例如解析逻辑放在 `gradebook/tests/`，任务流转放在 `worklists/tests/`。提交前至少运行 `pytest -q`；若涉及 Django 配置、模板或路由，也运行 `python manage.py check`。

## 提交与 Pull Request 规范

提交信息遵循现有历史风格，推荐使用前缀：`feat:`、`fix:`、`docs:`、`style:`。每次提交应聚焦单一变更，避免混入无关重构。PR 需说明变更目的、影响范围、验证方式；涉及页面改动时附截图，涉及导入或分析逻辑时注明测试数据与结果。

## 中文协作与文档要求

本仓库默认使用中文协作：对话、评审说明、提交补充说明、运行记录优先使用中文。设计、需求、实施方案与运维操作请保存到 `docs/requirements/`、`docs/plans/`、`docs/runbook/` 对应目录，而不是只留在聊天记录里。代码注释如确有必要，使用简洁中文，解释“为什么”而不是重复“做了什么”；同时保留已有有效注释，不随意删除有价值的文档沉淀。
