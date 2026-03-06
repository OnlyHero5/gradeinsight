# Repository Guidelines Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 产出一个简洁、准确、可直接供贡献者使用的根目录 `AGENTS.md`。

**Architecture:** 基于现有 `README.md`、`pytest.ini`、目录结构与提交历史提炼规则，覆盖根目录 `AGENTS.md`，不改动应用逻辑。额外加入仓库级中文协作要求，确保后续文档与注释规范统一。

**Tech Stack:** Markdown、Django、pytest、git

---

### Task 1: 汇总仓库事实

**Files:**
- Read: `README.md`
- Read: `pytest.ini`
- Read: `requirements.txt`
- Read: `docs/runbook/deploy.md`

**Step 1: 确认项目结构与命令**

记录 `config/`、`gradebook/`、`worklists/`、`templates/`、`static/`、`docs/`、`docker/` 等目录职责。

**Step 2: 确认测试与提交惯例**

记录 `pytest -q`、`python manage.py check`，以及 `feat:`、`fix:`、`docs:`、`style:` 提交前缀。

### Task 2: 编写贡献指南

**Files:**
- Modify: `AGENTS.md`

**Step 1: 按章节组织内容**

写入以下部分：
- 项目结构与模块组织
- 构建、测试与开发命令
- 代码风格与命名规范
- 测试要求
- 提交与 PR 规范
- 中文协作与文档要求

**Step 2: 纳入仓库特定规则**

明确：
- 对话、文档、评审说明优先中文
- 设计/计划/运维文档保存到 `docs/requirements/`、`docs/plans/`、`docs/runbook/`
- 必要代码注释使用简洁中文，并保留已有有效注释

### Task 3: 自检内容

**Files:**
- Review: `AGENTS.md`

**Step 1: 检查字数与结构**

确认文档简洁、标题清晰、示例命令准确。

**Step 2: 检查与仓库事实一致**

确认所有路径、命令、测试习惯和提交风格均与当前仓库一致。
