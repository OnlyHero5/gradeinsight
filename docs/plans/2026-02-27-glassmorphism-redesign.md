# GradeInsight 强烈沉浸式拟态玻璃视觉重设计

**日期**: 2026-02-27
**状态**: 已批准，待实现
**范围**: 全局前端重化（CSS + HTML 模板）

---

## 背景

当前前端基于浅蓝色背景 + 初步毛玻璃效果，视觉冲击力不足，缺少层次感和精致度。本次重设计将切换至**强烈沉浸式拟态玻璃**风格，打造深海黑蓝极光背景，配合半透明毛玻璃卡片，实现现代科技感数据平台的视觉体验。

---

## 设计决策

### 方案选择
选择**方案 B（CSS + HTML 模板全局重做）**，因为：
- 仅改 CSS 无法添加动态光晕 `div` 元素
- 需要改写 Chart.js JS 配置以适配深色主题
- 全局改造一步到位，后端代码（views/services/models）完全不动

### 风格基调
**强烈沉浸式**（用户选择）：
- 深色/深蓝渐变背景 #0a0f1e → #1a2340
- 卡片：`rgba(255,255,255,0.08)` blur(40px)
- 边框：`rgba(255,255,255,0.15)`
- 光晕：蓝/青/紫彩色散射

---

## 视觉规格

### 1. 颜色系统（tokens.css 重写）

```css
/* === 背景层次 === */
--gi-bg-base:    #0a0f1e;   /* 最深基础 */
--gi-bg-mid:     #111827;   /* 中层 */
--gi-bg-surface: #1a2340;   /* 表面层 */

/* === 玻璃效果 === */
--gi-glass:        rgba(255, 255, 255, 0.06);
--gi-glass-strong: rgba(255, 255, 255, 0.10);
--gi-glass-nav:    rgba(10, 15, 30, 0.75);
--gi-border:       rgba(255, 255, 255, 0.10);
--gi-border-bright:rgba(255, 255, 255, 0.22);

/* === 光晕颜色 === */
--gi-orb-blue:   rgba(59, 130, 246, 0.15);
--gi-orb-cyan:   rgba(16, 167, 191, 0.12);
--gi-orb-purple: rgba(139, 92, 246, 0.10);

/* === 文字（白色系）=== */
--gi-text:       rgba(255, 255, 255, 0.92);
--gi-text-muted: rgba(255, 255, 255, 0.50);
--gi-text-bright:#ffffff;

/* === 品牌色（调亮适配深色）=== */
--gi-primary:        #3b82f6;   /* 主蓝 */
--gi-primary-strong: #2563eb;   /* 深蓝悬停 */
--gi-cyan:           #10a7bf;   /* 青色 */
--gi-accent:         #f59e0b;   /* 金色 */
--gi-danger:         #ef4444;   /* 错误红 */
--gi-success:        #10b981;   /* 成功绿 */
--gi-purple:         #8b5cf6;   /* 紫色强调（新增）*/

/* === 发光效果 === */
--gi-glow-blue:   0 0 40px rgba(59, 130, 246, 0.30);
--gi-glow-cyan:   0 0 30px rgba(16, 167, 191, 0.25);
--gi-glow-accent: 0 0 30px rgba(245, 158, 11, 0.30);

/* === 尺寸（保持不变）=== */
--gi-radius-lg: 24px;
--gi-radius-md: 16px;
--gi-radius-sm: 12px;
--gi-shadow:    0 20px 44px rgba(0, 0, 0, 0.50);
--gi-shadow-sm: 0 10px 24px rgba(0, 0, 0, 0.30);
```

### 2. 背景系统

页面背景 = 深色渐变 + 3 个缓慢浮动的极光光球（CSS `@keyframes`）：

| 光球 | 颜色 | 位置 | 尺寸 |
|-----|-----|-----|-----|
| 蓝球 | rgba(59,130,246,0.15) | 左上 | 600px |
| 青球 | rgba(16,167,191,0.12) | 右中 | 500px |
| 紫球 | rgba(139,92,246,0.10) | 下方 | 400px |

每个光球独立浮动动画，周期 8-15s，`transform: translate()` 轻微位移。

### 3. 组件设计

#### 导航栏
- `background: var(--gi-glass-nav)`，`backdrop-filter: blur(24px)`
- 底部边框：`rgba(255,255,255,0.08)` 带轻微蓝色 glow 线
- Logo 文字：蓝→青渐变文字
- 当前菜单项：`rgba(59,130,246,0.15)` 背景 + 蓝色文字

#### 玻璃卡片
- `background: var(--gi-glass)`
- `backdrop-filter: blur(40px) saturate(180%)`
- `border: 1px solid var(--gi-border)`
- hover：上浮 `translateY(-2px)` + 边框亮度提升

#### KPI 卡片
- 顶边 3px 彩色线条（按指标类型：蓝=均分/中位，绿=通过率，金=优秀率，红=警示）
- hover 时顶边发光 `box-shadow` 同色

#### 按钮
- **主按钮**：`#3b82f6 → #10a7bf` 渐变 + `var(--gi-glow-blue)` 阴影
- **强调按钮**：`#f59e0b → #f97316` 渐变 + `var(--gi-glow-accent)` 阴影
- **幽灵按钮**：透明 + `var(--gi-border-bright)` 边框 + 白色文字

#### 表格
- 表头：`rgba(255,255,255,0.08)` 背景，白色文字
- 行 hover：`rgba(59,130,246,0.08)` 蓝色微高亮
- 奇偶行：微妙 `rgba(255,255,255,0.02)` 对比

#### Chart.js 深色主题
所有图表配置更新：
- `color: 'rgba(255,255,255,0.7)'`（轴标签）
- `grid: { color: 'rgba(255,255,255,0.06)' }`
- 数据集颜色调亮：蓝 `#3b82f6`，青 `#10a7bf`，金 `#f59e0b`，紫 `#8b5cf6`，绿 `#10b981`，红 `#ef4444`

#### 登录页
- 全屏深色背景（与全站一致）
- 两栏保持：左侧文案纯白渐变文字，右侧表单卡片 `blur(60px)` 最强玻璃
- 表单输入框：深色背景 `rgba(255,255,255,0.08)` + 白色文字 + focus 蓝色边框 glow

---

## 实现范围

### 需改动的文件

| 文件 | 改动类型 | 说明 |
|-----|--------|-----|
| `static/css/tokens.css` | **全面重写** | 深色系 CSS 变量 |
| `static/css/app.css` | **全面重写** | 深色毛玻璃样式系统 |
| `templates/base.html` | **改写** | 添加光晕 div、深色背景 body |
| `templates/registration/login.html` | **改写** | 沉浸式登录页 |
| `templates/includes/messages.html` | **调整** | 深色主题消息组件 |
| `gradebook/templates/gradebook/exam_list.html` | **调整** | 深色表格样式 |
| `gradebook/templates/gradebook/exam_detail.html` | **改写** | Chart.js 深色主题（4个图表）|
| `gradebook/templates/gradebook/import_upload.html` | **调整** | 表单深色样式 |
| `gradebook/templates/gradebook/import_preview.html` | **调整** | KPI 卡 + 表格深色 |
| `gradebook/templates/gradebook/question_filter.html` | **调整** | 筛选表单深色 |
| `gradebook/templates/gradebook/student_list.html` | **调整** | 学生表格深色 |
| `gradebook/templates/gradebook/student_detail.html` | **改写** | Chart.js 深色主题（1个图表）|
| `worklists/templates/worklists/task_list.html` | **调整** | 任务表格深色 |
| `worklists/templates/worklists/task_detail.html` | **调整** | 任务详情深色 |
| `worklists/templates/worklists/_assignment_row.html` | **调整** | HTMX 行深色 |

### 不改动的文件
- 所有 Python 后端代码
- URL 配置 (`urls.py`)
- 测试文件 (`tests/`)
- CDN 依赖版本

---

## 测试策略

1. `pytest -q` — 确认所有后端测试通过（后端未改动）
2. `python manage.py check` — Django 系统检查
3. 视觉验收：登录页、考试列表、考试详情（图表）、任务详情（HTMX）

---

## 成功标准

- [ ] 所有页面背景为深色沉浸式极光风格
- [ ] 毛玻璃卡片效果清晰可见（blur + 边框）
- [ ] Chart.js 图表在深色背景下清晰可读
- [ ] 按钮有发光效果
- [ ] KPI 卡片有彩色顶边线条
- [ ] 登录页完整重设计
- [ ] `pytest -q` 全部通过
- [ ] `python manage.py check` 无错误
