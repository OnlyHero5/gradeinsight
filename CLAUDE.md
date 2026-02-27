# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

GradeInsight is a classroom grade analysis and task tracking platform for teachers. The core workflow: **upload Excel → parse & import → generate analytics → filter students by question rules → create and track tasks**.

The UI is in Chinese (zh-hans). All content, labels, and messages are in Chinese.

## Commands

```bash
# Run tests
pytest -q

# Django system check
python manage.py check

# Run a single test file
pytest gradebook/tests/test_exam_analytics.py -q

# Run a single test function
pytest gradebook/tests/test_exam_analytics.py::test_function_name -q

# Start dev server
python manage.py runserver 0.0.0.0:8000

# Create/apply migrations
python manage.py makemigrations
python manage.py migrate
```

## Architecture

**Stack**: Django 5 + Bootstrap 5.3 + HTMX 1.9 + Chart.js 4.4 (all frontend via CDN, no npm/node).

**Two Django apps:**
- `gradebook` — exam import, parsing, analytics, student profiles
- `worklists` — task creation from question filters, assignment tracking with submission toggle

**Service layer** (`gradebook/services/`): All business logic lives here, not in views.
- `excel_parser.py` → dispatches to `xlsx_parser.py` or `xls_parser.py` by file extension
- `import_exam.py` → orchestrates import with SHA256 dedup and atomic transactions
- `exam_analytics.py` → builds multi-dimensional insight pack (rates, score bands, percentiles, dispersion, components, question focus, attention students)
- `stats_queries.py` → basic summaries, histograms, question stat rebuilds
- `student_dashboard.py` → student list overview with task snapshot
- `question_filter.py` → filters students by question score rules (eq, ne, lt, lte, gt, gte, between, below_mean, above_mean)
- `weakness.py` → topic/question weakness analysis
- `number_utils.py` → Decimal conversion, quantize to 2 decimals with ROUND_HALF_UP

**Views** (`gradebook/views/`, `worklists/views.py`): Thin wrappers that call services and render templates.

**Templates**: `templates/base.html` is the layout shell. App templates in `gradebook/templates/gradebook/` and `worklists/templates/worklists/`. HTMX partials use `_` prefix (e.g., `_assignment_row.html`).

**Models** (`gradebook/models.py`, `worklists/models.py`):
- `Student` → `ExamScore` (per-exam totals) → `ExamQuestionScore` (per-question scores)
- `Exam` → `ExamQuestionStat` (per-question aggregate stats)
- `ExamImport` (staging table: staged → imported/failed)
- `Task` → `TaskAssignment` (per-student, nullable `submitted_at` indicates completion)

Key constraints: unique (exam, student) on ExamScore; unique (exam, student, question_key) on ExamQuestionScore; SHA256 dedup on Exam and ExamImport.

**Auth**: All views use `@login_required`. Login at `/login/`, redirects to `exam_list`.

## Key Patterns

- **Excel parsing**: XLSX looks for "得分明细" sheet, scans for "姓名"/"总分" headers. XLS parses consecutive student score blocks matching `{Name}({ID})_成绩单`. Both return `ParsedExam` dataclass.
- **Two-step import**: Upload stages an `ExamImport` with preview JSON → user confirms → `import_exam_from_excel_bytes()` creates Exam + scores atomically.
- **HTMX interactions**: Task assignment toggle is a POST that returns a partial `_assignment_row.html`. CSRF token is read from cookie via JS in `base.html`.
- **Chart rendering**: Analytics views serialize metrics as JSON in template context; Chart.js renders client-side.
- **Database**: SQLite for dev (default), PostgreSQL for production (via `DATABASE_URL` env var).

## Environment

Key env vars (see `.env.example`): `DJANGO_SECRET_KEY`, `DJANGO_DEBUG`, `DJANGO_ALLOWED_HOSTS`, `DATABASE_URL`, `GRADEINSIGHT_UPLOAD_MAX_BYTES`, `GRADEINSIGHT_EPSILON`.

Settings: `config/settings.py`. Locale is `zh-hans`, timezone is `Asia/Shanghai`.
