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
