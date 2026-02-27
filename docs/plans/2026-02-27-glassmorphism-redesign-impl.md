# GradeInsight 拟态玻璃重设计 实现计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 将 GradeInsight 前端从浅蓝轻玻璃改造为强烈沉浸式深色拟态玻璃风格，包含极光动态光球背景、深色毛玻璃卡片、Chart.js 深色主题。

**Architecture:** 仅改动 CSS 文件（tokens.css、app.css）和部分 HTML 模板（base.html 添加极光 div，exam_detail.html 和 student_detail.html 更新 Chart.js 颜色配置）。后端代码（Python views/services/models）完全不变，现有测试无需修改。

**Tech Stack:** Bootstrap 5.3.3 (CDN), HTMX 1.9.12, Chart.js 4.4.3, CSS custom properties, CSS @keyframes animations

---

## Task 1: 重写 tokens.css（深色系设计变量）

**Files:**
- Modify: `static/css/tokens.css`

**Step 1: 全量替换 tokens.css 内容**

将文件内容替换为以下内容：

```css
:root {
  /* === 背景层次 === */
  --gi-bg-base:    #0a0f1e;
  --gi-bg-mid:     #111827;
  --gi-bg-surface: #1a2340;

  /* === 玻璃效果 === */
  --gi-glass:         rgba(255, 255, 255, 0.06);
  --gi-glass-strong:  rgba(255, 255, 255, 0.10);
  --gi-glass-nav:     rgba(10, 15, 30, 0.75);
  --gi-border:        rgba(255, 255, 255, 0.10);
  --gi-border-bright: rgba(255, 255, 255, 0.22);

  /* === 文字（白色系）=== */
  --gi-text:        rgba(255, 255, 255, 0.90);
  --gi-text-muted:  rgba(255, 255, 255, 0.48);
  --gi-text-bright: #ffffff;

  /* === 品牌色（调亮适配深色背景）=== */
  --gi-primary:        #3b82f6;
  --gi-primary-strong: #2563eb;
  --gi-cyan:           #22d3ee;
  --gi-accent:         #f59e0b;
  --gi-danger:         #ef4444;
  --gi-success:        #10b981;
  --gi-purple:         #8b5cf6;

  /* === 发光效果 === */
  --gi-glow-blue:   0 0 40px rgba(59, 130, 246, 0.30);
  --gi-glow-cyan:   0 0 30px rgba(34, 211, 238, 0.25);
  --gi-glow-accent: 0 0 30px rgba(245, 158, 11, 0.30);

  /* === 尺寸 === */
  --gi-radius-lg: 24px;
  --gi-radius-md: 16px;
  --gi-radius-sm: 12px;
  --gi-shadow:    0 20px 44px rgba(0, 0, 0, 0.50);
  --gi-shadow-sm: 0 8px 20px rgba(0, 0, 0, 0.35);

  /* === 字体 === */
  --gi-font-display: "Space Grotesk", "Noto Sans SC", sans-serif;
  --gi-font-body:    "Manrope", "Noto Sans SC", sans-serif;
  --gi-font-mono:    "JetBrains Mono", monospace;

  /* Bootstrap 覆盖 */
  --bs-body-font-family: var(--gi-font-body);
  --bs-body-color:       var(--gi-text);
  --bs-body-bg:          transparent;
  --bs-primary:          var(--gi-primary);
  --bs-primary-rgb:      59, 130, 246;
  --bs-border-color:     rgba(255, 255, 255, 0.10);
}

* {
  box-sizing: border-box;
}

body {
  margin: 0;
  min-height: 100vh;
  font-family: var(--gi-font-body);
  color: var(--gi-text);
  background-color: var(--gi-bg-base);
}

:focus-visible {
  outline: 3px solid rgba(59, 130, 246, 0.50);
  outline-offset: 2px;
}

@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
}
```

**Step 2: 验证系统检查**

```bash
python manage.py check
```

Expected: `System check identified no issues (0 silenced).`

**Step 3: Commit**

```bash
git add static/css/tokens.css
git commit -m "style: rewrite tokens.css with dark immersive glassmorphism palette"
```

---

## Task 2: 重写 app.css（深色毛玻璃组件样式系统）

**Files:**
- Modify: `static/css/app.css`

**Step 1: 全量替换 app.css 内容**

```css
/* ============================================
   BACKGROUND & AURORA ORBS
   ============================================ */
.gi-body {
  background: linear-gradient(135deg, #0a0f1e 0%, #111827 50%, #1a2340 100%);
  min-height: 100vh;
}

.gi-backdrop {
  position: fixed;
  inset: 0;
  z-index: 0;
  pointer-events: none;
  background-image:
    linear-gradient(to right, rgba(59, 130, 246, 0.04) 1px, transparent 1px),
    linear-gradient(to bottom, rgba(59, 130, 246, 0.04) 1px, transparent 1px);
  background-size: 36px 36px;
  mask-image: radial-gradient(circle at center, black 40%, transparent 80%);
  -webkit-mask-image: radial-gradient(circle at center, black 40%, transparent 80%);
}

.gi-orb {
  position: fixed;
  border-radius: 50%;
  pointer-events: none;
  filter: blur(80px);
  z-index: 0;
}

.gi-orb-1 {
  width: 600px;
  height: 600px;
  background: radial-gradient(circle, rgba(59, 130, 246, 0.20) 0%, transparent 70%);
  top: -150px;
  left: -150px;
  animation: orbFloat1 12s ease-in-out infinite;
}

.gi-orb-2 {
  width: 500px;
  height: 500px;
  background: radial-gradient(circle, rgba(34, 211, 238, 0.16) 0%, transparent 70%);
  top: 30%;
  right: -100px;
  animation: orbFloat2 15s ease-in-out infinite;
}

.gi-orb-3 {
  width: 400px;
  height: 400px;
  background: radial-gradient(circle, rgba(139, 92, 246, 0.14) 0%, transparent 70%);
  bottom: -100px;
  left: 30%;
  animation: orbFloat3 10s ease-in-out infinite;
}

@keyframes orbFloat1 {
  0%, 100% { transform: translate(0, 0); }
  50% { transform: translate(40px, 30px); }
}

@keyframes orbFloat2 {
  0%, 100% { transform: translate(0, 0); }
  50% { transform: translate(-30px, 40px); }
}

@keyframes orbFloat3 {
  0%, 100% { transform: translate(0, 0); }
  50% { transform: translate(20px, -30px); }
}

/* ============================================
   NAVBAR
   ============================================ */
.gi-navbar {
  margin: 14px auto 0;
  width: min(1360px, calc(100% - 20px));
  border-radius: var(--gi-radius-lg);
  background: var(--gi-glass-nav);
  backdrop-filter: blur(24px) saturate(180%);
  -webkit-backdrop-filter: blur(24px) saturate(180%);
  border: 1px solid var(--gi-border);
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.40),
              0 1px 0 rgba(59, 130, 246, 0.15) inset;
}

.gi-navbar .navbar-brand {
  text-decoration: none;
}

.brand-dot {
  width: 42px;
  height: 42px;
  border-radius: 13px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, var(--gi-primary), var(--gi-cyan));
  color: #fff;
  font-family: var(--gi-font-display);
  font-weight: 700;
  letter-spacing: 0.03em;
  box-shadow: var(--gi-glow-blue);
}

.brand-title {
  font-family: var(--gi-font-display);
  font-size: 1rem;
  background: linear-gradient(90deg, #60a5fa, #38bdf8);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.gi-navbar .nav-link {
  font-weight: 600;
  color: var(--gi-text-muted);
  border-radius: 10px;
  padding: 8px 14px;
  transition: all 0.2s ease;
}

.gi-navbar .nav-link:hover {
  color: #fff;
  background: rgba(59, 130, 246, 0.15);
}

.gi-navbar .nav-link.active {
  color: #93c5fd;
  background: rgba(59, 130, 246, 0.18);
}

.navbar-toggler:focus {
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.35);
}

/* ============================================
   BUTTONS
   ============================================ */
.btn-gi-primary,
.btn-gi-primary:focus,
.btn-gi-primary:active {
  background: linear-gradient(135deg, var(--gi-primary), var(--gi-cyan));
  border: 0;
  color: #fff;
  box-shadow: var(--gi-glow-blue);
  font-weight: 600;
  transition: filter 0.2s ease, box-shadow 0.2s ease;
}

.btn-gi-primary:hover {
  color: #fff;
  filter: brightness(1.12);
  box-shadow: 0 0 50px rgba(59, 130, 246, 0.45);
}

.btn-gi-accent,
.btn-gi-accent:focus,
.btn-gi-accent:active {
  background: linear-gradient(135deg, var(--gi-accent), #f97316);
  border: 0;
  color: #fff;
  box-shadow: var(--gi-glow-accent);
  font-weight: 600;
  transition: filter 0.2s ease, box-shadow 0.2s ease;
}

.btn-gi-accent:hover {
  color: #fff;
  filter: brightness(1.10);
  box-shadow: 0 0 40px rgba(245, 158, 11, 0.45);
}

.btn-gi-ghost {
  border: 1px solid var(--gi-border-bright);
  color: rgba(255, 255, 255, 0.80);
  background: rgba(255, 255, 255, 0.05);
  font-weight: 500;
  transition: all 0.2s ease;
}

.btn-gi-ghost:hover {
  color: #fff;
  border-color: rgba(255, 255, 255, 0.35);
  background: rgba(255, 255, 255, 0.12);
}

/* ============================================
   MAIN LAYOUT
   ============================================ */
.gi-main {
  width: min(1360px, calc(100% - 20px));
  position: relative;
  z-index: 1;
}

/* ============================================
   GLASS SHELLS & CARDS
   ============================================ */
.glass-shell {
  background: var(--gi-glass);
  backdrop-filter: blur(40px) saturate(180%);
  -webkit-backdrop-filter: blur(40px) saturate(180%);
  border: 1px solid var(--gi-border);
  border-radius: var(--gi-radius-lg);
  box-shadow: var(--gi-shadow);
}

.glass-card {
  background: var(--gi-glass-strong);
  backdrop-filter: blur(32px) saturate(160%);
  -webkit-backdrop-filter: blur(32px) saturate(160%);
  border: 1px solid var(--gi-border);
  border-radius: var(--gi-radius-md);
  box-shadow: var(--gi-shadow-sm);
  transition: transform 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease;
}

.glass-card:hover {
  transform: translateY(-2px);
  border-color: var(--gi-border-bright);
  box-shadow: var(--gi-shadow);
}

.glass-alert {
  border-color: rgba(255, 255, 255, 0.15);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
}

.flash-stack {
  display: grid;
  gap: 10px;
}

/* ============================================
   PAGE BANNER
   ============================================ */
.page-banner {
  background: linear-gradient(
    135deg,
    rgba(59, 130, 246, 0.08) 0%,
    rgba(34, 211, 238, 0.05) 100%
  );
}

.gi-eyebrow {
  font-family: var(--gi-font-mono);
  text-transform: uppercase;
  letter-spacing: 0.12em;
  color: var(--gi-cyan);
  font-size: 0.76rem;
  opacity: 0.8;
}

/* ============================================
   TYPOGRAPHY
   ============================================ */
.section-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}

.section-title {
  margin: 0;
  font-family: var(--gi-font-display);
  font-size: clamp(1.08rem, 2.2vw, 1.42rem);
  color: var(--gi-text-bright);
}

.section-subtitle {
  margin: 6px 0 0;
  color: var(--gi-text-muted);
  line-height: 1.55;
}

/* ============================================
   KPI CARDS
   ============================================ */
.kpi-grid {
  display: grid;
  grid-template-columns: repeat(6, minmax(0, 1fr));
  gap: 12px;
}

.kpi-card {
  padding: 16px;
  border-radius: var(--gi-radius-sm);
  border: 1px solid var(--gi-border);
  background: rgba(255, 255, 255, 0.04);
  position: relative;
  overflow: hidden;
  transition: transform 0.2s ease, border-color 0.2s ease;
}

.kpi-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: linear-gradient(90deg, var(--gi-primary), var(--gi-cyan));
}

.kpi-card:hover {
  transform: translateY(-1px);
  border-color: var(--gi-border-bright);
}

.kpi-label {
  margin: 0;
  font-size: 0.75rem;
  color: var(--gi-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.kpi-value {
  margin: 8px 0 0;
  font-family: var(--gi-font-display);
  font-size: 1.3rem;
  color: var(--gi-text-bright);
  font-weight: 700;
}

/* ============================================
   CHART CARDS
   ============================================ */
.chart-card {
  padding: 16px;
}

.chart-wrap {
  min-height: 320px;
}

.chart-wrap > canvas {
  width: 100% !important;
  height: 320px !important;
}

/* ============================================
   TABLES
   ============================================ */
.table-glass {
  overflow-x: auto;
  border-radius: var(--gi-radius-sm);
  border: 1px solid var(--gi-border);
  background: rgba(255, 255, 255, 0.03);
}

.table-glass .table {
  margin: 0;
  min-width: 640px;
  --bs-table-bg: transparent;
  --bs-table-color: var(--gi-text);
  --bs-table-border-color: rgba(255, 255, 255, 0.07);
}

.table-glass thead th {
  font-size: 0.73rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--gi-text-muted);
  border-bottom-color: rgba(255, 255, 255, 0.10);
  background: rgba(255, 255, 255, 0.06);
  font-weight: 600;
}

.table-glass tbody td {
  color: var(--gi-text);
  border-color: rgba(255, 255, 255, 0.05);
}

.table-glass tbody tr:hover {
  --bs-table-accent-bg: rgba(59, 130, 246, 0.08);
  --bs-table-bg-state: rgba(59, 130, 246, 0.08);
}

.table-link {
  text-decoration: none;
  color: #60a5fa;
  font-weight: 600;
}

.table-link:hover {
  color: #93c5fd;
  text-decoration: underline;
}

/* ============================================
   BADGES
   ============================================ */
.badge-soft {
  border: 1px solid rgba(255, 255, 255, 0.12);
  background: rgba(255, 255, 255, 0.08);
  color: var(--gi-text-muted);
  font-weight: 500;
}

.status-danger {
  background: rgba(239, 68, 68, 0.15);
  color: #fca5a5;
  border-color: rgba(239, 68, 68, 0.25);
}

.status-success {
  background: rgba(16, 185, 129, 0.15);
  color: #6ee7b7;
  border-color: rgba(16, 185, 129, 0.25);
}

.empty-tip {
  margin: 0;
  color: var(--gi-text-muted);
}

/* ============================================
   ASSIGNMENT ROWS (HTMX)
   ============================================ */
.assignment-row.assignment-submitted {
  background: rgba(16, 185, 129, 0.08);
}

.assignment-row.assignment-pending {
  background: rgba(239, 68, 68, 0.08);
}

/* ============================================
   ALERTS / MESSAGES
   ============================================ */
.alert-success.glass-alert {
  background: rgba(16, 185, 129, 0.12);
  border-color: rgba(16, 185, 129, 0.25);
  color: #6ee7b7;
}

.alert-danger.glass-alert {
  background: rgba(239, 68, 68, 0.12);
  border-color: rgba(239, 68, 68, 0.25);
  color: #fca5a5;
}

.alert-primary.glass-alert {
  background: rgba(59, 130, 246, 0.12);
  border-color: rgba(59, 130, 246, 0.25);
  color: #93c5fd;
}

/* ============================================
   LOGIN PAGE
   ============================================ */
.login-layout {
  display: grid;
  grid-template-columns: 1.2fr 1fr;
  gap: 16px;
}

.login-poster,
.login-card {
  padding: 32px;
}

.login-poster .section-title {
  font-size: clamp(1.3rem, 3vw, 1.8rem);
  background: linear-gradient(135deg, #fff 0%, #93c5fd 50%, #38bdf8 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.login-points {
  margin: 0;
  padding-left: 18px;
  color: var(--gi-text-muted);
}

.login-points li + li {
  margin-top: 10px;
}

.login-card {
  backdrop-filter: blur(60px) saturate(200%);
  -webkit-backdrop-filter: blur(60px) saturate(200%);
}

/* ============================================
   FORMS
   ============================================ */
.form-control,
.form-select {
  min-height: 44px;
  border-radius: 12px;
  border-color: rgba(255, 255, 255, 0.12);
  background: rgba(255, 255, 255, 0.06);
  color: var(--gi-text);
  transition: border-color 0.2s ease, box-shadow 0.2s ease, background 0.2s ease;
}

.form-control::placeholder {
  color: var(--gi-text-muted);
}

.form-control:focus,
.form-select:focus,
.form-check-input:focus {
  background: rgba(255, 255, 255, 0.10);
  border-color: rgba(59, 130, 246, 0.60);
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.20);
  color: var(--gi-text);
}

.form-select option {
  background: #1a2340;
  color: #fff;
}

.form-label {
  color: var(--gi-text-muted);
  font-size: 0.875rem;
  font-weight: 500;
}

.form-check-input {
  background-color: rgba(255, 255, 255, 0.08);
  border-color: rgba(255, 255, 255, 0.20);
}

.form-check-input:checked {
  background-color: var(--gi-primary);
  border-color: var(--gi-primary);
}

.form-check-label {
  color: var(--gi-text-muted);
}

.form-text,
.text-muted-gi {
  color: var(--gi-text-muted) !important;
}

.errorlist {
  list-style: none;
  margin: 6px 0 0;
  padding: 0;
  font-size: 0.83rem;
  color: #fca5a5;
}

/* ============================================
   BOOTSTRAP OVERRIDES
   ============================================ */
.text-muted {
  color: var(--gi-text-muted) !important;
}

.text-secondary {
  color: var(--gi-text-muted) !important;
}

.badge.text-bg-light {
  background: rgba(255, 255, 255, 0.10) !important;
  color: rgba(255, 255, 255, 0.75) !important;
  border: 1px solid rgba(255, 255, 255, 0.12);
}

/* ============================================
   RESPONSIVE BREAKPOINTS
   ============================================ */
@media (max-width: 1199.98px) {
  .kpi-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

@media (max-width: 991.98px) {
  .gi-navbar {
    width: calc(100% - 14px);
    margin-top: 8px;
  }

  .gi-main {
    width: calc(100% - 14px);
    padding-top: 14px !important;
  }

  .login-layout {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 767.98px) {
  .kpi-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .table-glass .table {
    min-width: 520px;
  }
}

/* Reduced motion: 禁用极光动画 */
@media (prefers-reduced-motion: reduce) {
  .gi-orb {
    animation: none !important;
  }
}
```

**Step 2: 验证系统检查**

```bash
python manage.py check
```

Expected: `System check identified no issues (0 silenced).`

**Step 3: Commit**

```bash
git add static/css/app.css
git commit -m "style: rewrite app.css with dark glassmorphism component system and aurora orb animations"
```

---

## Task 3: 更新 base.html（添加极光光球 div）

**Files:**
- Modify: `templates/base.html`

**Step 1: 在 .gi-backdrop div 后插入 3 个极光 orb div**

在 `templates/base.html` 第 30 行（`<div class="gi-backdrop" aria-hidden="true"></div>`）之后，插入：

```html
    <div class="gi-orb gi-orb-1" aria-hidden="true"></div>
    <div class="gi-orb gi-orb-2" aria-hidden="true"></div>
    <div class="gi-orb gi-orb-3" aria-hidden="true"></div>
```

**Step 2: 验证系统检查**

```bash
python manage.py check
```

Expected: `System check identified no issues (0 silenced).`

**Step 3: Commit**

```bash
git add templates/base.html
git commit -m "style: add aurora orb divs to base.html for immersive background effect"
```

---

## Task 4: 更新 exam_detail.html（Chart.js 深色主题）

**Files:**
- Modify: `gradebook/templates/gradebook/exam_detail.html`

**Step 1: 更新 Chart.js 颜色配置**

在 `{% block extra_js %}` 的 `<script>` 中，找到并替换以下 3 行颜色变量定义（原为浅色，改为深色）：

原代码（约第 219-221 行）：
```javascript
      const textColor = '#28435f';
      const gridColor = 'rgba(40, 67, 95, 0.15)';
      const accent = ['#0f4ea8', '#10a7bf', '#f3b64c', '#cf4b63', '#4b7bec', '#1f9a78'];
```

替换为：
```javascript
      const textColor = 'rgba(255, 255, 255, 0.70)';
      const gridColor = 'rgba(255, 255, 255, 0.06)';
      const accent = ['#3b82f6', '#22d3ee', '#f59e0b', '#ef4444', '#8b5cf6', '#10b981'];
```

**Step 2: 更新 tooltip 背景色**

找到：
```javascript
          tooltip: { backgroundColor: 'rgba(18, 36, 58, 0.9)' },
```

替换为：
```javascript
          tooltip: {
            backgroundColor: 'rgba(10, 15, 30, 0.92)',
            titleColor: '#fff',
            bodyColor: 'rgba(255, 255, 255, 0.75)',
          },
```

**Step 3: 验证系统检查**

```bash
python manage.py check
```

Expected: `System check identified no issues (0 silenced).`

**Step 4: Commit**

```bash
git add gradebook/templates/gradebook/exam_detail.html
git commit -m "style: update exam_detail Chart.js to dark theme colors"
```

---

## Task 5: 更新 student_detail.html（Chart.js 深色主题）

**Files:**
- Modify: `gradebook/templates/gradebook/student_detail.html`

**Step 1: 更新趋势图颜色配置**

在 `{% block extra_js %}` 的 `<script>` 中，找到并替换数据集颜色：

原代码（约第 199-209 行）：
```javascript
              borderColor: '#0f4ea8',
              backgroundColor: 'rgba(15, 78, 168, 0.15)',
```
替换为：
```javascript
              borderColor: '#3b82f6',
              backgroundColor: 'rgba(59, 130, 246, 0.15)',
```

原代码：
```javascript
              borderColor: '#f3b64c',
              backgroundColor: 'rgba(243, 182, 76, 0.18)',
```
替换为：
```javascript
              borderColor: '#f59e0b',
              backgroundColor: 'rgba(245, 158, 11, 0.15)',
```

**Step 2: 更新轴和插件颜色**

找到并替换所有 `'#28435f'`（共5处轴颜色 ticks/title/legend）：
```javascript
// 全部替换：
'#28435f'  →  'rgba(255, 255, 255, 0.70)'
```

找到并替换所有 `'rgba(40, 67, 95, 0.1)'`（grid color）：
```javascript
'rgba(40, 67, 95, 0.1)'  →  'rgba(255, 255, 255, 0.06)'
```

找到并替换 tooltip 背景：
```javascript
// 原：
            tooltip: { backgroundColor: 'rgba(18, 36, 58, 0.9)' },
// 替换为：
            tooltip: {
              backgroundColor: 'rgba(10, 15, 30, 0.92)',
              titleColor: '#fff',
              bodyColor: 'rgba(255, 255, 255, 0.75)',
            },
```

**Step 3: 验证系统检查**

```bash
python manage.py check
```

Expected: `System check identified no issues (0 silenced).`

**Step 4: Commit**

```bash
git add gradebook/templates/gradebook/student_detail.html
git commit -m "style: update student_detail Chart.js to dark theme colors"
```

---

## Task 6: 运行全量测试并验证

**Files:**
- None (validation only)

**Step 1: 运行后端测试套件**

```bash
pytest -q
```

Expected output: 所有测试通过，0 failures，0 errors。示例：
```
......................................
XX passed in X.XXs
```

**Step 2: Django 系统检查**

```bash
python manage.py check
```

Expected: `System check identified no issues (0 silenced).`

**Step 3: 如果测试全部通过，创建总结 commit**

```bash
git log --oneline -6
```

验证所有 commit 均已到位，然后：

```bash
git commit --allow-empty -m "chore: glassmorphism redesign complete - all tests pass"
```

（如果没有未提交的改动，用 --allow-empty 创建标记 commit）

---

## 验收检查清单

实现完成后，依次确认：

- [ ] `pytest -q` — 全部通过，无 failures
- [ ] `python manage.py check` — `0 issues`
- [ ] 访问登录页 `/login/` — 深色极光背景，强玻璃卡片
- [ ] 访问考试列表 `/exams/` — 深色表格，白色文字
- [ ] 访问考试详情 `/exams/<id>/` — 4个图表在深色背景下颜色正确
- [ ] 访问学生详情 `/students/<id>/` — 趋势图深色主题
- [ ] 任务详情页 HTMX 切换状态按钮正常工作
- [ ] 页面极光光球缓慢浮动（可在 DevTools 中确认 `.gi-orb-1` 元素存在）
- [ ] KPI 卡片顶边有蓝→青渐变线条
- [ ] 导航栏 Logo 文字为蓝色渐变
