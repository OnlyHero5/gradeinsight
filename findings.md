# Findings — GradeInsight

## Excel 样例结构（更新）
- 核心 sheet：`得分明细`
- 实测表头行为第 2 行，字段包含：`姓名`、`准考证号`、`自定义考号`、`总分`、`客观分`、`主观分`、题号列（如 `51`、`51(3)`）
- 本样例实测学生数据行：`44` 行
- 本样例实测数据质量：
  - 非数值总分（应排除统计）：`2` 行
  - `准考证号` 与 `自定义考号` 不一致：`1` 行

## 本轮实现结论
- 完成 Django 单体架构：`gradebook`（导入/分析）+ `worklists`（任务追踪）
- 完成服务层拆分：
  - `xlsx_parser.py`（解析/质量检查）
  - `import_exam.py`（事务导入、去重、预计算触发）
  - `stats_queries.py`（题目统计、考试摘要、分布）
  - `question_filter.py`（阈值/区间/低于题均分）
  - `weakness.py`（弱势/良好题目判定）
- 前端采用模块化科技玻璃风，触控目标与布局兼容 iPad/桌面

## 运行与验证证据
- Django 自检：`python3 manage.py check` → `System check identified no issues`
- 测试：`python3 -m pytest` → `10 passed`

## 环境注意事项
- 运行机最初缺少 `pip` 与 `venv` 组件，已通过 `get-pip.py`（`--break-system-packages`）完成用户级 pip 引导
- 当前可直接用 `python3 -m pip` 安装依赖并执行测试

## UI/UX 重构补充
- 用户指定使用 `ui-ux-pro-max`，已执行其规则并完成全页面推倒重构
- 技能脚本入口缺失：`/home/psx/.codex/skills/ui-ux-pro-max/scripts/search.py` 不存在（指针损坏），因此改为手工应用其设计规则完成设计系统落地
- 新视觉方向：现代编辑感 + 科技质感（浅色玻璃材质、强层级排版、低噪动画）

## 2026-02-25 UI/UX 二次重构发现
- 原技能损坏根因：`/home/psx/.codex/skills/ui-ux-pro-max/scripts` 与 `data` 被错误安装为文本指针文件，且目标路径不存在
- 修复方式：
  1) 从 GitHub 仓库 `https://github.com/nextlevelbuilder/ui-ux-pro-max-skill` 拉取源码
  2) 回填 `~/.codex/src/ui-ux-pro-max/{scripts,data}`
  3) 软链修正至 `../../src/ui-ux-pro-max/...`
- 验证：
  - `python3 ~/.codex/skills/ui-ux-pro-max/scripts/search.py ... --design-system` 成功
  - 生成 `design-system/gradeinsight/MASTER.md`

## 2026-02-25 前端/分析重构补充
- UI 栈升级：接入 `Bootstrap 5.3.3`（组件库）+ `Bootstrap Icons` + `Chart.js 4.4`，不再是纯手写组件
- 视觉方向：冷白底 + 深海蓝 + 青色点缀 + 琥珀高亮，保留玻璃拟态层、网格氛围背景、低时长动效
- 新增考试分析服务层：`gradebook/services/exam_analytics.py`
  - 通过率/优秀率
  - 成绩段分布（<60 / 60-79 / 80-89 / 90+）
  - 分位数（P25/P50/P75/P90）
  - 离散度（标准差/IQR）
  - 客观/主观均分
  - 题目强弱项聚焦（高表现题/薄弱题）
  - 关注学生列表（低分段）
- 页面能力增强：考试详情页升级为 4 图（分数分布、成绩段分布、客观主观结构、题目表现）+ 多组指标卡片 + 双列表

## 2026-02-25 Excel 双格式支持发现
- 样例 `xlsx` 包含 3 个工作表：
  - `得分明细`（50x54）
  - `班级英语成绩简表`（46x6）
  - `班级英语成绩汇总`（46x9）
- 样例 `xls` 仅 1 个工作表 `八年级7班`（503x16），但内部为连续成绩单块结构，实测识别到 `42` 个学生成绩单块（每块包含题号/得分分段行）
- 结论：`xls` 与 `xlsx` 数据组织方式不同，需拆分解析器并做按后缀分发

## 2026-02-25 学生档案页增强发现
- 现有系统已有 `student_detail`（考试趋势 + 题目表现），但缺失学生总览入口与任务状态分区
- 新需求核心：同一页面体系中打通三类数据
  - 学生基础信息（来自导入后的 `Student`）
  - 历次考试得分/班级排名（`ExamScore`）
  - 任务完成状态（`TaskAssignment`）
- 实现策略：新增服务层聚合 `student_dashboard.py`，避免在视图里写大段统计逻辑，提高可维护性

## 2026-02-25 任务状态切换无响应（HTMX）排障结论
- 复现证据：登录后对 `POST /worklists/tasks/<id>/assignments/<id>/toggle/` 发起请求，不携带 CSRF 头时返回 `403`
- 根因：`_assignment_row.html` 使用 `hx-post` 发送异步请求，但前端未给 HTMX 请求注入 `X-CSRFToken`
- 修复：在全局基座 `templates/base.html` 增加 `htmx:configRequest` 监听，从 `csrftoken` cookie 自动写入 `X-CSRFToken`
- 验证：
  - 页面 HTML 包含 `htmx:configRequest` 与 `X-CSRFToken`
  - 同一接口无 header 为 `403`，带 header 为 `200`

## 2026-02-27 全面审查发现（不足点）

### Critical
- 任务状态切换接口未限制 HTTP 方法，导致 GET 也会触发“写操作”，构成 CSRF 语义漏洞（即使有登录保护也仍可被跨站触发）。
  - 位置：`worklists/views.py` 的 `assignment_toggle()`（未做 `require_POST`）。
- 安全默认值偏危险：`DEBUG` 默认开启、`SECRET_KEY` 默认 dev 值；如果部署时漏配环境变量，会直接以不安全姿态上线。
  - 位置：`config/settings.py` 的 `SECRET_KEY` / `DEBUG` 默认值。

### Important
- 导入暂存（ExamImport）失败后重试路径存在潜在 500：`ExamImport.source_sha256` 是唯一键，但暂存逻辑只复用 `status=staged` 的记录；若一次导入进入 `failed`，再次上传同一文件将尝试新建记录而触发唯一约束冲突（IntegrityError）。
  - 位置：`gradebook/views/import_views.py` 暂存查询条件 + `gradebook/models.py` 唯一约束。
- Docker 部署链路缺少 `collectstatic`，但静态存储配置使用 `CompressedManifestStaticFilesStorage`；在“全新环境/容器内无 staticfiles 产物”的情况下，模板里 `{% static %}` 可能因 manifest 缺失而报错。
  - 位置：`config/settings.py` 静态存储配置 + `docker/web/Dockerfile` 未运行 collectstatic + `templates/base.html` 引用静态资源。
- `docker-compose.yml`/`.env.example` 中数据库口令为弱默认值（`gradeinsight/gradeinsight`），建议至少通过 `.env` 注入并在文档中强调更换。
- 仓库内文档出现明文测试账号口令（`progress.md` 中的 `teacher / Teacher@123`），容易被误当生产凭据复制使用。
- 样例 Excel 文件被提交进仓库，通常包含学生姓名/学号等信息，存在数据合规与泄漏风险（建议匿名化或放入私有存储）。

### Minor
- `docker/caddy/Caddyfile` 仅配置 `:80`，但 compose 暴露 `443:443`，容易误导部署期望（是否需要 TLS/域名站点块）。
- 前端依赖多处 CDN（Google Fonts / unpkg / jsdelivr），部分资源未提供 SRI；在校园网/离线或供应链风险场景下不够稳。
- 依赖版本区间未锁定（无 lockfile），构建可复现性一般；缺少 CI（如 GitHub Actions）来持续跑 `pytest`/安全检查。
