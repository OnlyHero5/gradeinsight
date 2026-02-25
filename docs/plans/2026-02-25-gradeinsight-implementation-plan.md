# GradeInsight Implementation Plan（单班级/单学科，数据分析平台 P0→P1）

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 在公网 VPS 上部署一个兼容电脑端+iPad 的成绩分析平台：上传 `.xlsx` → 预览校验 → 入库（PostgreSQL）→ 考试/学生趋势分析与可视化 → 题目筛选（阈值/区间/低于题均分）→ 生成任务清单并追踪提交（点名变色持久化）。

**Architecture:** Django 单体应用（服务端渲染模板 + HTMX 局部刷新 + 少量原生 JS/ECharts 图表）。数据写入后预计算“考试统计 + 每题均分/中位数/N”，查询侧完成筛选与任务管理。部署使用 Docker Compose（web + postgres + caddy）。

**Tech Stack:**
- Backend: Python 3.12, Django, psycopg（PostgreSQL）, openpyxl（`.xlsx`）
- Frontend: Django Templates, HTMX, ECharts（CDN 或静态资源）
- Infra: Docker Compose, PostgreSQL, Caddy（HTTPS）, pg_dump 备份
- Tests: pytest + pytest-django（或 Django TestCase，二选一；本计划默认 pytest）

---

## 0) 开始前准备（一次性）

### Task 0.1: 建立独立 worktree（避免污染当前目录）

**Files:** 无

**Step 1: 创建 worktree**

Run:
```bash
git status
git worktree add ../gradeinsight-impl -b feat/gradeinsight-mvp
cd ../gradeinsight-impl
```

Expected:
- 新目录 `../gradeinsight-impl` 存在
- 当前分支为 `feat/gradeinsight-mvp`

**Step 2: 提交现有规划文档（如果未提交）**

Run:
```bash
git add docs/ task_plan.md findings.md progress.md
git commit -m "docs: add GradeInsight PRD and implementation plan inputs"
```

Expected:
- 提交成功

---

## 1) 工程骨架与部署骨架（P0）

### Task 1.1: Docker Compose + Django 项目骨架可启动

**Files:**
- Create: `docker/web/Dockerfile`
- Create: `docker/caddy/Caddyfile`
- Create: `docker-compose.yml`
- Create: `.env.example`
- Create: `requirements.txt`
- Create: `tests/test_smoke.py`
- Create: `manage.py`, `config/settings.py`, `config/urls.py`, `config/wsgi.py`, `config/asgi.py`
- Create: `pytest.ini`

**Step 1: 写一个最小 smoke test（先失败）**

Create `tests/test_smoke.py`:
```python
def test_smoke():
    assert True
```

Run:
```bash
docker compose run --rm web pytest -q
```

Expected: FAIL（此时 web 容器/pytest 还不存在）

**Step 2: 写最小依赖与容器（让 pytest 能跑起来）**

Create `requirements.txt`（版本可先不 pin，后续再锁）：
```txt
Django>=5.0,<6
psycopg[binary]>=3.1,<4
openpyxl>=3.1,<4
defusedxml>=0.7,<1
django-htmx>=1.18,<2
dj-database-url>=2.2,<3
whitenoise>=6.6,<7
gunicorn>=21,<23
pytest>=8,<9
pytest-django>=4.8,<5
```

Create `docker/web/Dockerfile`（示意）：
```dockerfile
FROM python:3.12-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["gunicorn","config.wsgi:application","-b","0.0.0.0:8000"]
```

Create `docker-compose.yml`（示意，P0 先跑通）：
```yaml
services:
  db:
    image: postgres:16
    environment:
      POSTGRES_DB: gradeinsight
      POSTGRES_USER: gradeinsight
      POSTGRES_PASSWORD: gradeinsight
    volumes:
      - pgdata:/var/lib/postgresql/data
  web:
    build:
      context: .
      dockerfile: docker/web/Dockerfile
    env_file:
      - .env
    depends_on:
      - db
    volumes:
      - ./:/app
    ports:
      - "8000:8000"
volumes:
  pgdata:
```

Create `.env.example`：
```dotenv
DJANGO_SECRET_KEY=dev-secret-change-me
DJANGO_DEBUG=1
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
DATABASE_URL=postgresql://gradeinsight:gradeinsight@db:5432/gradeinsight
```

**Step 3: 创建 Django 工程**

Run:
```bash
cp .env.example .env
docker compose run --rm web django-admin startproject config .
docker compose run --rm web python manage.py migrate
```

Expected:
- `config/` 与 `manage.py` 生成
- migrate 成功

**Step 4: 配置 settings（DB/静态/HTMX）并让 smoke test 通过**

Create `pytest.ini`：
```ini
[pytest]
DJANGO_SETTINGS_MODULE = config.settings
python_files = tests.py test_*.py *_tests.py
```

Modify `config/settings.py`（关键片段，示意；用 `DATABASE_URL` + WhiteNoise + HTMX）：
```python
import os
from pathlib import Path
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "dev")
DEBUG = os.environ.get("DJANGO_DEBUG", "0") == "1"
ALLOWED_HOSTS = [h for h in os.environ.get("DJANGO_ALLOWED_HOSTS","").split(",") if h]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_htmx",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django_htmx.middleware.HtmxMiddleware",
]

DATABASES = {"default": dj_database_url.config(default=os.environ["DATABASE_URL"], conn_max_age=60)}

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
```

Run:
```bash
docker compose run --rm web pytest -q
```

Expected: PASS

**Step 5: Commit**

Run:
```bash
git add docker-compose.yml docker/ requirements.txt .env.example manage.py config/ pytest.ini tests/
git commit -m "chore: bootstrap Django + docker compose + pytest"
```

---

## 2) 数据模型（P0）

### Task 2.1: 建立核心模型与约束（Student/Exam/Score/Question/Task）

**Files:**
- Create: `gradebook/apps.py`, `gradebook/models.py`, `gradebook/admin.py`
- Create: `worklists/apps.py`, `worklists/models.py`, `worklists/admin.py`
- Modify: `config/settings.py`, `config/urls.py`
- Test: `gradebook/tests/test_models.py`

**Step 1: 写失败测试（模型约束）**

Create `gradebook/tests/test_models.py`：
```python
import pytest
from django.db import IntegrityError
from gradebook.models import Student

@pytest.mark.django_db
def test_student_external_id_unique_in_system():
    Student.objects.create(name="A", external_id="1001", admission_ticket="1001", custom_exam_id="1001")
    with pytest.raises(IntegrityError):
        Student.objects.create(name="B", external_id="1001", admission_ticket="1001", custom_exam_id="1001")
```

Run:
```bash
docker compose run --rm web pytest gradebook/tests/test_models.py -q
```

Expected: FAIL（app/model 未存在）

**Step 2: 最小模型实现**

Create `gradebook/models.py`（关键字段，示意）：
```python
from django.db import models

class Student(models.Model):
    name = models.CharField(max_length=64)
    external_id = models.CharField(max_length=64, unique=True)  # 默认=准考证号
    admission_ticket = models.CharField(max_length=64, blank=True)  # 准考证号（冗余保存）
    custom_exam_id = models.CharField(max_length=64, blank=True)  # 自定义考号（冗余保存）
    note = models.CharField(max_length=255, blank=True)

    def __str__(self) -> str:
        return f"{self.name}({self.external_id})"

class Exam(models.Model):
    name = models.CharField(max_length=255)
    exam_date = models.DateField(null=True, blank=True)  # 选填
    imported_at = models.DateTimeField(auto_now_add=True)
    source_filename = models.CharField(max_length=255, blank=True)
    source_sha256 = models.CharField(max_length=64, unique=True)
    participants_n = models.IntegerField(default=0)
    excluded_n = models.IntegerField(default=0)

class ExamScore(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    total_score = models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True)
    total_raw = models.CharField(max_length=255, blank=True)
    objective_score = models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True)
    subjective_score = models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True)
    rank_in_class = models.IntegerField(null=True, blank=True)
    excluded_from_stats = models.BooleanField(default=False)
    exclude_reason = models.CharField(max_length=255, blank=True)

    class Meta:
        unique_together = (("exam","student"),)

class ExamQuestionScore(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    question_key = models.CharField(max_length=32)  # "51", "51(3)" ...
    score_value = models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True)

    class Meta:
        unique_together = (("exam","student","question_key"),)
        indexes = [
            models.Index(fields=["exam","question_key"]),
            models.Index(fields=["exam","question_key","score_value"]),
        ]

class ExamQuestionStat(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE)
    question_key = models.CharField(max_length=32)
    mean_score = models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True)
    median_score = models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True)
    sample_n = models.IntegerField(default=0)

    class Meta:
        unique_together = (("exam","question_key"),)

class ExamImport(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    source_filename = models.CharField(max_length=255, blank=True)
    source_sha256 = models.CharField(max_length=64, unique=True)
    exam_name = models.CharField(max_length=255)
    exam_date = models.DateField(null=True, blank=True)
    preview_json = models.JSONField(default=dict)
    status = models.CharField(max_length=32, default="staged")  # staged/imported/failed
    error = models.TextField(blank=True)
```

Create `worklists/models.py`（示意）：
```python
from django.db import models
from gradebook.models import Exam, Student

class Task(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    question_key = models.CharField(max_length=32, blank=True)
    rule_json = models.JSONField(default=dict)  # 保存筛选条件（阈值/区间/低于题均分等）
    created_at = models.DateTimeField(auto_now_add=True)

class TaskAssignment(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    submitted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = (("task","student"),)
        indexes = [models.Index(fields=["task","submitted_at"])]
```

Modify `config/settings.py`：
- `INSTALLED_APPS` 加 `gradebook`, `worklists`, `django_htmx`
- DB 使用 `DATABASE_URL`（本计划统一使用 `dj-database-url` 解析）

**Step 3: 迁移与测试**

Run:
```bash
docker compose run --rm web python manage.py makemigrations gradebook worklists
docker compose run --rm web python manage.py migrate
docker compose run --rm web pytest gradebook/tests/test_models.py -q
```

Expected: PASS

**Step 4: Commit**

Run:
```bash
git add gradebook/ worklists/ config/settings.py
git commit -m "feat: add core models for students, exams, question scores, tasks"
```

---

## 3) `.xlsx` 解析与导入（P0）

### Task 3.1: 解析器（从样例抽取题目列、识别异常）

**Files:**
- Create: `gradebook/services/xlsx_parser.py`
- Test: `gradebook/tests/test_xlsx_parser.py`

**Step 1: 写失败测试（基于仓库样例文件）**

Create `gradebook/tests/test_xlsx_parser.py`：
```python
from pathlib import Path
from gradebook.services.xlsx_parser import parse_exam_xlsx

def test_parse_exam_xlsx_extracts_question_keys():
    data = Path(\"2025-2026学年度第一学期期末考试【八年级】(英语)-八年级7班.xlsx\").read_bytes()
    parsed = parse_exam_xlsx(data)
    assert \"51\" in parsed.question_keys
    assert \"51(3)\" in parsed.question_keys
    assert parsed.student_count == 48
    assert parsed.excluded_from_stats_count >= 1  # 未扫/非数值总分
    assert parsed.mismatched_id_count >= 1  # 准考证号 vs 自定义考号 不一致
```

Run:
```bash
docker compose run --rm web pytest gradebook/tests/test_xlsx_parser.py -q
```

Expected: FAIL（parser 未实现）

**Step 2: 最小解析实现**

Create `gradebook/services/xlsx_parser.py`（建议实现要点）：
- 仅解析 `得分明细`
- 表头行固定读取第 2 行：定位基础列（姓名/准考证号/自定义考号/总分/客观/主观/班次），以及题目列（表头为数字或 `xx(x)`）
- 逐行读取学生数据（从第 3 行起）
- `total_score` 非数值 → `excluded_from_stats=True`
- `准考证号 != 自定义考号` → 计入 mismatch

**Step 3: 运行测试**

Run:
```bash
docker compose run --rm web pytest gradebook/tests/test_xlsx_parser.py -q
```

Expected: PASS

**Step 4: Commit**

Run:
```bash
git add gradebook/services/xlsx_parser.py gradebook/tests/test_xlsx_parser.py
git commit -m "feat: add xlsx parser with question keys and data quality checks"
```

### Task 3.2: 导入服务（写库 + 预计算统计）

**Files:**
- Create: `gradebook/services/import_exam.py`
- Test: `gradebook/tests/test_import_exam.py`

**Step 1: 写失败测试（导入后生成 Exam/Score/QuestionStat）**

Create `gradebook/tests/test_import_exam.py`：
```python
import pytest
from pathlib import Path
from gradebook.models import Exam, ExamQuestionStat
from gradebook.services.import_exam import import_exam_from_xlsx_bytes

@pytest.mark.django_db
def test_import_creates_exam_and_question_stats():
    data = Path(\"2025-2026学年度第一学期期末考试【八年级】(英语)-八年级7班.xlsx\").read_bytes()
    exam = import_exam_from_xlsx_bytes(data, exam_name=\"英语期末\", exam_date=None, source_filename=\"sample.xlsx\")
    assert Exam.objects.filter(id=exam.id).exists()
    stat = ExamQuestionStat.objects.get(exam=exam, question_key=\"51\")
    assert stat.sample_n > 0
```

**Step 2: 最小实现（事务 + 幂等）**

`import_exam_from_xlsx_bytes(...)` 应做：
- 计算 SHA256，若已存在同 hash 的 `Exam` → 抛出可读异常 `DuplicateImportError`
- 事务内：upsert 学生（external_id=准考证号），写入 ExamScore、ExamQuestionScore
- 预计算并写入 ExamQuestionStat（仅统计 `excluded_from_stats=False` 的学生）
- （可选）写入考试基础统计（后续页面用）

**Step 3: 测试通过 + Commit**

Run:
```bash
docker compose run --rm web pytest gradebook/tests/test_import_exam.py -q
```

Commit:
```bash
git add gradebook/services/import_exam.py gradebook/tests/test_import_exam.py
git commit -m "feat: import exam into db and precompute question stats"
```

---

## 4) Web 功能（P0）：登录、导入预览、考试/学生分析、题目筛选、任务清单

### Task 4.1: 登录保护（单账号）

**Files:**
- Modify: `config/settings.py`, `config/urls.py`
- Create: `templates/registration/login.html`
- Test: `tests/test_auth_required.py`

**Step 1: 写失败测试（未登录访问被重定向）**

Create `tests/test_auth_required.py`：
```python
import pytest
from django.urls import reverse

@pytest.mark.django_db
def test_exam_list_requires_login(client):
    resp = client.get(reverse(\"exam_list\"))
    assert resp.status_code in (302, 301)
```

**Step 2: 最小实现**
- 启用 Django auth：`LOGIN_URL`, `LOGIN_REDIRECT_URL`, `LOGOUT_REDIRECT_URL`
- `exam_list` view 加 `@login_required`

**Step 3: 测试通过**

Run:
```bash
docker compose run --rm web pytest tests/test_auth_required.py -q
```

Expected: PASS（状态码 302/301）

**Step 4: Commit**

Run:
```bash
git add config/settings.py config/urls.py templates/registration/login.html tests/test_auth_required.py
git commit -m "feat: require login for app pages"
```

---

### Task 4.2: 导入页面（上传→预览→确认入库）

**Files:**
- Create: `gradebook/views/import_views.py`, `gradebook/urls.py`
- Create: `gradebook/forms.py`
- Create: `gradebook/templates/gradebook/import_upload.html`
- Create: `gradebook/templates/gradebook/import_preview.html`
- Modify: `config/urls.py`
- Test: `gradebook/tests/test_import_flow.py`

**验收点：**
- 预览显示：学生数、题目数、不参与统计人数、ID 不一致行数
- 确认后写库；重复 hash 给出提示并阻止重复导入

**Step 1: 写失败测试（上传后出现预览页）**

Create `gradebook/tests/test_import_flow.py`（示意）：
```python
import pytest
from pathlib import Path
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth.models import User

@pytest.mark.django_db
def test_import_upload_returns_preview(client):
    User.objects.create_user(username="t", password="p")
    assert client.login(username="t", password="p")

    data = Path("2025-2026学年度第一学期期末考试【八年级】(英语)-八年级7班.xlsx").read_bytes()
    upload = SimpleUploadedFile(
        "sample.xlsx",
        data,
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

    resp = client.post(
        reverse("import_upload"),
        data={"exam_name": "英语期末", "exam_date": "", "file": upload},
    )
    assert resp.status_code == 200
    body = resp.content.decode("utf-8")
    assert "导入预览" in body
    assert "学生数" in body
```

Run:
```bash
docker compose run --rm web pytest gradebook/tests/test_import_flow.py -q
```

Expected: FAIL（url/view/template 未实现）

**Step 2: 最小实现（staging + confirm 两阶段）**

实现建议：
- `import_upload`：
  1) 保存上传文件到 `ExamImport`（或 `MEDIA_ROOT` 临时文件）并计算 sha256
  2) 调用 `parse_exam_xlsx` 生成 `preview_json`（含 students/questions/excluded/mismatch）
  3) 返回 `import_preview.html`（显示统计口径提示：未扫/缺考不参与统计）
- `import_confirm`：读取 staging 记录 → 调用 `import_exam_from_xlsx_bytes` → 标记 `status=imported` → redirect 到 `exam_detail`

**Step 3: 测试通过**

Run:
```bash
docker compose run --rm web pytest gradebook/tests/test_import_flow.py -q
```

Expected: PASS

**Step 4: Commit**

Run:
```bash
git add gradebook/views/import_views.py gradebook/urls.py gradebook/forms.py gradebook/templates/gradebook/import_*.html gradebook/tests/test_import_flow.py config/urls.py
git commit -m "feat: add xlsx import flow with preview and confirm"
```

---

### Task 4.3: 考试列表/详情（基础统计 + 分布图 + 题目均分表）

**Files:**
- Create: `gradebook/views/exam_views.py`
- Create: `gradebook/templates/gradebook/exam_list.html`
- Create: `gradebook/templates/gradebook/exam_detail.html`
- Create: `gradebook/services/stats_queries.py`
- Test: `gradebook/tests/test_exam_pages.py`

**说明：**
- 统计口径：仅 `excluded_from_stats=False` 参与
- 图表：ECharts（考试分数直方图）
- 题目均分表：来自 `ExamQuestionStat`

**Step 1: 写失败测试（页面可访问）**

Create `gradebook/tests/test_exam_pages.py`：
```python
import pytest
from django.urls import reverse
from django.contrib.auth.models import User

@pytest.mark.django_db
def test_exam_list_page_ok(client):
    User.objects.create_user(username="t", password="p")
    assert client.login(username="t", password="p")
    resp = client.get(reverse("exam_list"))
    assert resp.status_code == 200
```

Run:
```bash
docker compose run --rm web pytest gradebook/tests/test_exam_pages.py -q
```

Expected: FAIL（view/url/template 未实现或未返回 200）

**Step 2: 最小实现**
- `exam_list`：列出 Exam（排序：优先 `exam_date`，为空则按 `imported_at`）
- `exam_detail`：展示统计口径提示 + 基础统计（均分/中位数/最高最低/参与人数）+ 题目均分表（来自 `ExamQuestionStat`）
- 图表（ECharts）可先用静态 demo 数据占位，后续补齐真实 histogram

**Step 3: 测试通过**

Run:
```bash
docker compose run --rm web pytest gradebook/tests/test_exam_pages.py -q
```

Expected: PASS

**Step 4: Commit**

Run:
```bash
git add gradebook/views/exam_views.py gradebook/templates/gradebook/exam_*.html gradebook/services/stats_queries.py gradebook/tests/test_exam_pages.py
git commit -m "feat: add exam list/detail pages with basic stats and question averages"
```

---

### Task 4.4: 学生详情（历史趋势 + 弱势/良好题目）

**Files:**
- Create: `gradebook/views/student_views.py`
- Create: `gradebook/templates/gradebook/student_detail.html`
- Create: `gradebook/services/weakness.py`
- Test: `gradebook/tests/test_weakness.py`

**Step 1: 写失败测试（弱势/良好判定函数）**

Create `gradebook/tests/test_weakness.py`：
```python
from decimal import Decimal
from gradebook.services.weakness import classify_delta

def test_classify_delta():
    assert classify_delta(Decimal(\"-0.1\")) == \"weak\"
    assert classify_delta(Decimal(\"0.1\")) == \"good\"
    assert classify_delta(Decimal(\"0.0\")) == \"avg\"
```

**Step 2: 最小实现**

Create `gradebook/services/weakness.py`：
```python
from decimal import Decimal

EPS = Decimal(\"0.01\")

def classify_delta(delta: Decimal, eps: Decimal = EPS) -> str:
    if delta < -eps:
        return \"weak\"
    if delta > eps:
        return \"good\"
    return \"avg\"
```

**规则：**
- 若该学生该次考试 `excluded_from_stats=True`：页面显示状态提示，不输出弱势/良好清单

**Step 3: 测试通过**

Run:
```bash
docker compose run --rm web pytest gradebook/tests/test_weakness.py -q
```

Expected: PASS

**Step 4: 视图/模板（最小可用）**
- `student_detail`：展示该学生所有考试的总分趋势数据（JSON 注入页面，ECharts 折线图）
- 选择某次考试后：查询该次考试所有 `ExamQuestionScore` + 对应 `ExamQuestionStat`，计算 `delta=student_score-mean_score` 并分类展示“弱势/良好/接近平均”

**Step 5: Commit**

Run:
```bash
git add gradebook/services/weakness.py gradebook/views/student_views.py gradebook/templates/gradebook/student_detail.html gradebook/tests/test_weakness.py
git commit -m "feat: add student detail with trend and weakness/good questions"
```

---

### Task 4.5: 题目筛选（阈值/区间/低于题均分/高于题均分）

**Files:**
- Create: `gradebook/views/question_filter_views.py`
- Create: `gradebook/templates/gradebook/question_filter.html`
- Create: `gradebook/services/question_filter.py`
- Test: `gradebook/tests/test_question_filter.py`

**Step 1: 写失败测试（低于题均分）**

Create `gradebook/tests/test_question_filter.py`（示意，建议用工厂创建小数据集）：
```python
import pytest
from decimal import Decimal
from gradebook.models import Exam, Student, ExamScore, ExamQuestionScore, ExamQuestionStat
from gradebook.services.question_filter import filter_students_by_question_rule

@pytest.fixture
def seed_exam_with_question_stats():
    exam = Exam.objects.create(name="E", source_sha256="y" * 64)
    s1 = Student.objects.create(name="S1", external_id="1001", admission_ticket="1001", custom_exam_id="1001")
    s2 = Student.objects.create(name="S2", external_id="1002", admission_ticket="1002", custom_exam_id="1002")

    ExamScore.objects.create(exam=exam, student=s1, total_score=Decimal("60"), excluded_from_stats=False)
    ExamScore.objects.create(exam=exam, student=s2, total_score=Decimal("80"), excluded_from_stats=False)

    ExamQuestionScore.objects.create(exam=exam, student=s1, question_key="51", score_value=Decimal("1.0"))
    ExamQuestionScore.objects.create(exam=exam, student=s2, question_key="51", score_value=Decimal("3.0"))

    ExamQuestionStat.objects.create(exam=exam, question_key="51", mean_score=Decimal("2.0"), median_score=Decimal("2.0"), sample_n=2)
    return exam, s1, s2

@pytest.mark.django_db
def test_filter_below_mean_returns_expected_students(seed_exam_with_question_stats):
    exam, s1, s2 = seed_exam_with_question_stats  # s1 得分低于均分
    rule = {\"op\": \"below_mean\"}
    result_ids = filter_students_by_question_rule(exam.id, question_key=\"51\", rule=rule)
    assert s1.id in result_ids
    assert s2.id not in result_ids
```

**实现要点：**
- 默认仅筛选参与统计学生；提供开关包含 excluded
- `below_mean` 使用 `ExamQuestionStat.mean_score` + EPS

**Step 2: 最小实现**
- `filter_students_by_question_rule(exam_id, question_key, rule, include_excluded=False)`：
  - 若 `op in (below_mean, above_mean)`：取 `ExamQuestionStat.mean_score`，按 EPS 做比较
  - 若 `op` 为阈值/区间：对 `ExamQuestionScore.score_value` 做比较
  - 默认 student 范围为 `ExamScore(exam_id, excluded_from_stats=False)`
- `question_filter` view：解析表单 → 调用 service → 返回名单（并支持“创建任务”按钮）

**Step 3: 测试通过**

Run:
```bash
docker compose run --rm web pytest gradebook/tests/test_question_filter.py -q
```

Expected: PASS

**Step 4: Commit**

Run:
```bash
git add gradebook/services/question_filter.py gradebook/views/question_filter_views.py gradebook/templates/gradebook/question_filter.html gradebook/tests/test_question_filter.py
git commit -m "feat: add question filter (threshold/range/below-mean/above-mean)"
```

---

### Task 4.6: 任务清单（从筛选结果创建任务 + 点名变色持久化 + 导出未交）

**Files:**
- Create: `worklists/views.py`, `worklists/urls.py`
- Create: `worklists/templates/worklists/task_list.html`
- Create: `worklists/templates/worklists/task_detail.html`
- Create: `worklists/templates/worklists/_assignment_row.html`
- Test: `worklists/tests/test_toggle_submission.py`

**验收点：**
- 创建任务时写入 assignments（快照）
- 点击学生切换 submitted 状态：颜色变化；刷新后仍保持
- 支持“仅看未交/已交”
- 导出未交 CSV

**Step 1: 写失败测试（toggle 会改变 submitted_at）**

Create `worklists/tests/test_toggle_submission.py`（示意）：
```python
import pytest
from django.urls import reverse
from gradebook.models import Student, Exam
from worklists.models import Task, TaskAssignment

@pytest.mark.django_db
def test_toggle_submission_marks_submitted(client, django_user_model):
    django_user_model.objects.create_user(username="t", password="p")
    assert client.login(username="t", password="p")

    s = Student.objects.create(name="A", external_id="1001", admission_ticket="1001", custom_exam_id="1001")
    e = Exam.objects.create(name="E", source_sha256="z" * 64)
    t = Task.objects.create(exam=e, name="T", question_key="51", rule_json={})
    a = TaskAssignment.objects.create(task=t, student=s, submitted_at=None)

    resp = client.post(reverse("assignment_toggle", kwargs={"task_id": t.id, "assignment_id": a.id}))
    assert resp.status_code == 200
    a.refresh_from_db()
    assert a.submitted_at is not None
```

Run:
```bash
docker compose run --rm web pytest worklists/tests/test_toggle_submission.py -q
```

Expected: FAIL（url/view 未实现）

**Step 2: 最小实现**
- `assignment_toggle` view：若 `submitted_at is None` → 设为 `timezone.now()`；否则置空
- 返回 `_assignment_row.html`（HTMX swap）以实现“点名变色”
- `task_detail`：提供 “仅未交/已交” 筛选与“导出未交 CSV”入口

**Step 3: 测试通过 + Commit**

Run:
```bash
docker compose run --rm web pytest worklists/tests/test_toggle_submission.py -q
```

Commit:
```bash
git add worklists/ worklists/tests/test_toggle_submission.py
git commit -m "feat: add task list with submission toggle and csv export"
```

---

## 5) 运维与交付（P0）

### Task 5.1: 生产部署（Caddy HTTPS + gunicorn + 静态文件）

**Files:**
- Create: `docker/caddy/Caddyfile`
- Modify: `docker-compose.yml`
- Create: `docs/runbook/deploy.md`

**内容：**
- `DJANGO_DEBUG=0`、`ALLOWED_HOSTS`、`CSRF_TRUSTED_ORIGINS`
- 静态文件：WhiteNoise 或收集到 volume
- 迁移命令与初始账号创建命令

**Step 1: 写部署文档先行（便于审查）**

Create `docs/runbook/deploy.md`，至少包含：
- 启动：`docker compose up -d --build`
- 初始化：`docker compose run --rm web python manage.py migrate`
- 创建账号：`docker compose run --rm web python manage.py createsuperuser`
- 日志：`docker compose logs -f --tail=200 web`

**Step 2: 增加 Caddy（prod 使用）**

Create `docker/caddy/Caddyfile`（示意）：
```caddyfile
your.domain.com {
  encode zstd gzip
  reverse_proxy web:8000
}
```

Modify `docker-compose.yml`：增加 `caddy` service（80/443）并挂载 `Caddyfile` 与数据卷。

**Step 3: Commit**

Run:
```bash
git add docker-compose.yml docker/caddy/Caddyfile docs/runbook/deploy.md
git commit -m "docs+ops: add production deploy runbook and caddy reverse proxy"
```

### Task 5.2: 备份脚本（pg_dump）

**Files:**
- Create: `ops/backup_pg.sh`
- Create: `docs/runbook/backup.md`

**要求：**
- 每日定时任务（cron）
- 保留 7/30 天策略
- 失败告警（最简：exit code + 日志）

**Step 1: 写脚本 + 写 runbook**

Create `ops/backup_pg.sh`（示意）：
```bash
#!/usr/bin/env bash
set -euo pipefail

OUT_DIR="${OUT_DIR:-/var/backups/gradeinsight}"
KEEP_DAYS="${KEEP_DAYS:-30}"
TS="$(date +%F)"
mkdir -p "$OUT_DIR"

docker compose exec -T db pg_dump -U gradeinsight gradeinsight > "$OUT_DIR/gradeinsight_${TS}.sql"
find "$OUT_DIR" -type f -name "gradeinsight_*.sql" -mtime +"$KEEP_DAYS" -delete
```

Create `docs/runbook/backup.md`：如何配置 cron、如何验证备份可恢复（最小：`psql < backup.sql`）。

**Step 2: Commit**

Run:
```bash
git add ops/backup_pg.sh docs/runbook/backup.md
git commit -m "ops: add postgres backup script and runbook"
```

---

## 6) P1（增强，不阻塞上线）

仅列清单（不在 P0 阻塞项中实现）：
- `.xls` 导入（或自动提示用户转换为 `.xlsx`）
- 班级多次考试趋势图（均分/中位数/及格率）
- 进步/退步榜（相对上次考试）
- 题目分析面板（相关性/异常题提示）
- 报表导出（考试汇总、个人成绩单）

---

## 执行方式（二选一）

Plan 已保存为 `docs/plans/2026-02-25-gradeinsight-implementation-plan.md`。

两种执行选项：
1) **Subagent-Driven（本会话）**：逐 Task 实现+复核  
2) **Parallel Session**：新会话使用 `superpowers:executing-plans` 按 Task 执行

请选择一种方式开始实现。
