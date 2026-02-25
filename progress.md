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
