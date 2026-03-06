# GradeInsight 开发者上手手册

## 1. 适用对象

这份手册给两类人看：

- 第一次接手本仓库的开发者
- 需要快速定位“某块功能改哪里、改完跑哪些验证”的维护者

建议先配合阅读：

- `README.md`
- `docs/plans/2026-03-06-architecture-overview.md`
- `docs/plans/2026-03-06-data-model-and-flow.md`

---

## 2. 本地启动最小流程

## 2.1 安装依赖

```bash
pip install -r requirements.txt
```

如果你习惯用 Conda，也可以按 `README.md` 中的方式先创建 Python 3.12 环境。

## 2.2 初始化数据库

```bash
python manage.py migrate
python manage.py createsuperuser
```

当前仓库没有预置演示账号。
本地手工验证页面时，最简单的做法就是先创建一个 superuser。

## 2.3 启动开发服务

```bash
python manage.py runserver 0.0.0.0:8000
```

访问：

- 登录页：`http://127.0.0.1:8000/login/`
- 默认首页：`http://127.0.0.1:8000/`（会跳转到考试列表）

## 2.4 数据库口径

- 不配置 `DATABASE_URL` 时，默认使用仓库根目录下的 `db.sqlite3`
- 容器部署时，`docker-compose.yml` 默认接 PostgreSQL

这意味着：

- 本地快速开发可以直接用 SQLite
- 接近生产环境联调时，建议切换到 PostgreSQL 验证

---

## 3. 建议的阅读顺序

如果你对项目完全陌生，建议按下面顺序建立认知：

1. 路由入口
   - `config/urls.py`
   - `gradebook/urls.py`
   - `worklists/urls.py`
2. 核心模型
   - `gradebook/models.py`
   - `worklists/models.py`
3. 关键视图
   - `gradebook/views/import_views.py`
   - `gradebook/views/exam_views.py`
   - `gradebook/views/student_views.py`
   - `gradebook/views/question_filter_views.py`
   - `worklists/views.py`
4. 服务层
   - `gradebook/services/import_exam.py`
   - `gradebook/services/exam_identity.py`
   - `gradebook/services/stats_queries.py`
   - `gradebook/services/exam_analytics.py`
   - `gradebook/services/student_dashboard.py`
   - `gradebook/services/weakness.py`
   - `gradebook/services/question_filter.py`

---

## 4. 常见改动入口

## 4.1 改导入逻辑

优先查看：

- 表单与上传流程：`gradebook/forms.py`、`gradebook/views/import_views.py`
- 解析分发：`gradebook/services/excel_parser.py`
- `.xlsx` 解析：`gradebook/services/xlsx_parser.py`
- `.xls` 解析：`gradebook/services/xls_parser.py`
- 考试等价标识：`gradebook/services/exam_identity.py`
- 正式入库：`gradebook/services/import_exam.py`
- 题目统计重建：`gradebook/services/stats_queries.py`

典型场景：

- 新增导入校验
- 调整题号识别规则
- 修复旧版 Excel 兼容性
- 修改重复导入判断（同文件 / 同场异文件）

---

## 4.2 改考试详情分析

优先查看：

- 页面入口：`gradebook/views/exam_views.py`
- 基础统计：`gradebook/services/stats_queries.py`
- 扩展分析：`gradebook/services/exam_analytics.py`
- 展示模板：`gradebook/templates/gradebook/exam_detail.html`

典型场景：

- 修改成绩段
- 调整通过率 / 优秀率口径
- 增加新图表
- 修改“关注学生”规则

---

## 4.3 改学生列表或学生详情

优先查看：

- 视图：`gradebook/views/student_views.py`
- 列表聚合：`gradebook/services/student_dashboard.py`
- 题目强弱项：`gradebook/services/weakness.py`
- 模板：
  - `gradebook/templates/gradebook/student_list.html`
  - `gradebook/templates/gradebook/student_detail.html`

典型场景：

- 新增学生维度统计
- 调整趋势排序
- 修改弱势题目判定口径
- 优化任务完成情况展示

---

## 4.4 改题目筛选与任务追踪

优先查看：

- 表单：`gradebook/forms.py`
- 题目筛选视图：`gradebook/views/question_filter_views.py`
- 题目筛选规则：`gradebook/services/question_filter.py`
- 任务模型：`worklists/models.py`
- 任务页面与导出：`worklists/views.py`
- 模板：
  - `gradebook/templates/gradebook/question_filter.html`
  - `worklists/templates/worklists/task_detail.html`
  - `worklists/templates/worklists/_assignment_row.html`

典型场景：

- 增减筛选操作符
- 修改“高于/低于平均分”判定
- 调整任务命名
- 修改已交/未交切换交互

---

## 4.5 改全局样式与前端交互

优先查看：

- 基座模板：`templates/base.html`
- 样式：
  - `static/css/tokens.css`
  - `static/css/app.css`

当前前端有三个重要事实：

- Bootstrap、Chart.js、HTMX 通过 CDN 加载
- HTMX 的 CSRF 头统一在 `base.html` 中注入
- 主题切换逻辑也在 `base.html` 中统一处理

如果页面样式或图表异常，先检查这里。

---

## 5. 测试地图

## 5.1 导入与解析

| 测试文件 | 覆盖点 |
|---|---|
| `gradebook/tests/test_import_flow.py` | 上传后是否能进入预览页、是否接受 `.xls` / `.xlsx`、是否拦截同场异文件 |
| `gradebook/tests/test_import_exam.py` | 正式导入、模型写入、同场异文件去重 |
| `gradebook/tests/test_xlsx_parser.py` | `.xlsx` 解析细节、考试等价标识 |
| `gradebook/tests/test_xls_parser.py` | `.xls` 解析细节、跨格式等价标识 |

## 5.2 分析与页面

| 测试文件 | 覆盖点 |
|---|---|
| `gradebook/tests/test_exam_analytics.py` | 考试详情页统计分析逻辑 |
| `gradebook/tests/test_exam_pages.py` | 考试列表 / 考试详情页面访问 |
| `gradebook/tests/test_student_pages.py` | 学生列表与学生详情聚合展示 |
| `gradebook/tests/test_weakness.py` | 学生题目强弱项分类逻辑 |
| `gradebook/tests/test_number_utils.py` | 题号排序与数值工具 |

## 5.3 筛选与任务

| 测试文件 | 覆盖点 |
|---|---|
| `gradebook/tests/test_question_filter.py` | 题目筛选逻辑 |
| `worklists/tests/test_toggle_submission.py` | 提交状态切换、HTMX 与 CSRF 交互 |

---

## 6. 改哪里，跑哪些测试

## 6.1 导入/解析相关

```bash
pytest gradebook/tests/test_import_flow.py \
  gradebook/tests/test_import_exam.py \
  gradebook/tests/test_xlsx_parser.py \
  gradebook/tests/test_xls_parser.py -q
```

## 6.2 考试分析相关

```bash
pytest gradebook/tests/test_exam_analytics.py \
  gradebook/tests/test_exam_pages.py -q
```

## 6.3 学生详情与弱项相关

```bash
pytest gradebook/tests/test_student_pages.py \
  gradebook/tests/test_weakness.py -q
```

## 6.4 题目筛选与任务相关

```bash
pytest gradebook/tests/test_question_filter.py \
  worklists/tests/test_toggle_submission.py -q
```

## 6.5 全量回归

```bash
pytest -q
python manage.py check
```

---

## 7. 常见排查顺序

## 7.1 上传失败或导入失败

先看：

1. `gradebook/views/import_views.py`
2. `gradebook/services/excel_parser.py`
3. 对应解析器 `xlsx_parser.py` / `xls_parser.py`
4. `gradebook/services/import_exam.py`

重点排查：

- 后缀是否合法
- 文件是否超大小限制
- `source_sha256` 是否已导入
- `identity_key` 是否命中已存在考试（同一场考试的其他文件）
- 表头是否包含“姓名 / 总分”
- 旧版 `.xls` 是否符合“成绩单块”结构

## 7.2 页面有数据但图表不显示

先看：

- `templates/base.html`
- 具体页面模板中的图表初始化脚本

重点排查：

- `Chart.js` CDN 是否可访问
- JSON 序列化是否成功
- DOM id 是否和脚本一致

## 7.3 HTMX 切换任务状态失败

先看：

- `templates/base.html` 中 `htmx:configRequest`
- `worklists/views.py` 中 `assignment_toggle`
- `worklists/tests/test_toggle_submission.py`

重点排查：

- 是否是 `POST`
- 是否带了 `X-CSRFToken`
- 是否通过 HTMX 请求触发

## 7.4 学生强弱项结果不对

先看：

- `gradebook/services/weakness.py`
- `gradebook/services/stats_queries.py`
- `ExamScore.excluded_from_stats` 的实际值

重点排查：

- 该学生该场考试是否被排除统计
- 题目均分是否已重建
- `GRADEINSIGHT_EPSILON` 是否影响边界判断

---

## 8. 本地开发时值得注意的现实

### 8.1 导入相关测试依赖样例 Excel

导入流测试会读取仓库中的样例 Excel 文件。
如果你本地误删了这些样例文件，导入相关测试会直接失败。

### 8.2 本地默认是 SQLite，生产常用 PostgreSQL

涉及排序、事务行为、约束细节时，建议至少在 PostgreSQL 环境再验证一次。

### 8.3 前端依赖外部 CDN

如果你的开发网络无法访问：

- `fonts.googleapis.com`
- `cdn.jsdelivr.net`
- `unpkg.com`

那么页面可能出现：

- 字体缺失
- 图表脚本未加载
- HTMX 交互失效

这不是 Django 视图本身的问题，而是静态依赖加载失败。

---

## 9. 推荐的日常工作流

1. 先定位你要改的是：
   - 数据模型
   - 服务规则
   - 视图拼装
   - 模板展示
2. 优先跑与改动最接近的测试
3. 再跑 `pytest -q`
4. 最后跑 `python manage.py check`

如果你遵循这个顺序，通常能比较快地判断问题是在数据层、规则层还是页面层。
