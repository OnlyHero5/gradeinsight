# Task Plan — GradeInsight（实现阶段）

## Goal
搭建可部署、可测试的 GradeInsight MVP：上传 Excel → 解析入库 → 班级/学生分析 → 题目筛选 → 任务清单追踪（兼容 PC/iPad，科技玻璃风 UI）。

## Current Phase
- [x] 初始化 Git 仓库并创建开发分支 `feat/gradeinsight-mvp`
- [x] 完成 Django 工程骨架（配置、路由、静态资源、认证）
- [x] 完成核心模型与迁移（gradebook/worklists）
- [x] 完成 Excel 解析与导入服务（含题目统计预计算）
- [x] 完成题目筛选与任务清单提交切换
- [x] 完成核心页面与响应式 UI（PC + iPad）
- [x] 完成部署与备份脚手架（Docker/Caddy/runbook）
- [x] 通过自动化测试（`10 passed`）
- [x] 完成前端重构（Bootstrap 5.3 + 玻璃拟态 + 科技风）与考试分析增强（多维指标 + 4 图表）
- [x] 通过重构后回归测试（`12 passed`）
- [x] 完成 Excel 双格式导入支持（`.xls` + `.xlsx`）并通过回归（`15 passed`）
- [x] 完成学生档案页（学生总览 + 历次成绩 + 班级排名 + 任务完成状态）并通过回归（`18 passed`）
- [x] 修复任务切换按钮无响应（HTMX + CSRF）并通过回归（`20 passed`）

## Deliverables (Code + Docs)
- Django 项目：`config/`, `gradebook/`, `worklists/`, `templates/`, `static/`
- 测试：`gradebook/tests/`, `worklists/tests/`, `tests/test_auth_required.py`
- 部署：`docker-compose.yml`, `docker/web/Dockerfile`, `docker/caddy/Caddyfile`
- 运维文档：`docs/runbook/deploy.md`, `docs/runbook/backup.md`, `ops/backup_pg.sh`

## 2026-02-27 全面审查（代码/安全/运维）
- [x] 运行测试与自检（`pytest`、`manage.py check`）
- [x] 审查 Django settings 生产安全默认值（DEBUG/SECRET_KEY/HTTPS）
- [x] 审查任务状态切换接口的 HTTP 方法约束与 CSRF 语义
- [x] 审查导入暂存（ExamImport）唯一约束与失败重试路径
- [x] 审查 Docker/Caddy 部署链路（collectstatic、密钥、挂载）
- [x] 审查仓库合规性（License、CI、样例数据/凭据）

## Open Questions
- （无）
