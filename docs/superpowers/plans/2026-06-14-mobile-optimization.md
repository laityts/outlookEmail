# 移动端完美适配优化 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在已有移动端基础上修复真实适配漏洞、打磨触控/排版/弹窗体验，并引入物理返回键、下拉刷新、列表侧滑三项手势，使 Outlook 邮件阅读器移动端（≤768px，重点 ≤480px）达到接近原生 App 的体验，且桌面端零回退。

**Architecture:** 纯原生前端（无框架/无构建）。CSS 由后端路由 `bundled_index_css` 把 `static/css/index/01-08.css` 顺序拼接为 `/assets/index.css`；本计划新增 `09-mobile.css` 集中手势/骨架样式并注册到该路由。移动端 JS 行为集中在 `01-core.js`，全部用 `isMobileLayout()`（`matchMedia('(max-width: 768px)')`）守卫，桌面端早返回。所有视觉改动锁在 `@media (max-width: 768px)` 内。

**Tech Stack:** HTML + 原生 CSS + 原生 JavaScript（DOMPurify 用于邮件净化）；Flask 后端；测试用 Python `unittest`（无 pytest），沿用项目既有「读取前端源文件断言关键字符串」的静态契约测试模式。

**验证约定：**
- 自动化：所有任务的契约测试集中在 `tests/test_mobile_optimization_frontend.py`，用
  `python3 -m unittest tests.test_mobile_optimization_frontend -v` 运行。
- 手动：纯视觉/手势行为无法静态断言，每个相关任务末尾给出 **DevTools 设备模拟验证清单**
  （Chrome DevTools 设备工具栏：iPhone 12 Pro 390×844、iPhone SE 375×667、横屏）。
  无法用真机验证——手动项执行后如实记录通过/未通过，不得声称未做的验证已通过。
- 回归：每个改动 CSS 的任务，手动确认 ≥769px 桌面三栏布局不变。

---

## File Structure

| 文件 | 职责 | 本计划动作 |
|------|------|-----------|
| `tests/test_mobile_optimization_frontend.py` | 移动端改动的静态契约测试 | 新建，逐任务追加测试方法 |
| `static/css/index/09-mobile.css` | 手势（下拉/侧滑）、骨架屏、触觉相关移动端样式 | 新建并注册到打包路由 |
| `outlook_web/segments/04_routes_groups_accounts.py` | CSS 打包路由 | 注册 `09-mobile.css` |
| `templates/index.html` | 入口 HTML / viewport meta | 改 viewport、补 PWA meta |
| `static/js/index/05-emails.js` | 邮件渲染、iframe srcdoc、高度自适应 | 注入响应式样式、高度逻辑 |
| `static/js/index/01-core.js` | 移动端交互核心：抽屉、quickbar、返回栈、下拉刷新、侧滑、触觉 | 主要 JS 改动 |
| `static/css/index/08-responsive.css` | 移动端响应式样式 | 表单字号、触控热区、弹窗适配 |
| `static/css/index/06-modals-toast.css` | 弹窗样式 | 断点协调（移动段） |

---

## Task 0: 准备测试与样式骨架

**Files:**
- Create: `tests/test_mobile_optimization_frontend.py`
- Create: `static/css/index/09-mobile.css`
- Modify: `outlook_web/segments/04_routes_groups_accounts.py:159-168`

- [ ] **Step 1: 写失败测试 — 路由注册了 09-mobile.css**

创建 `tests/test_mobile_optimization_frontend.py`：

```python
from pathlib import Path
import unittest

ROOT_DIR = Path(__file__).resolve().parents[1]
INDEX_HTML = ROOT_DIR / 'templates' / 'index.html'
EMAILS_JS = ROOT_DIR / 'static' / 'js' / 'index' / '05-emails.js'
CORE_JS = ROOT_DIR / 'static' / 'js' / 'index' / '01-core.js'
RESPONSIVE_CSS = ROOT_DIR / 'static' / 'css' / 'index' / '08-responsive.css'
MOBILE_CSS = ROOT_DIR / 'static' / 'css' / 'index' / '09-mobile.css'
MODALS_CSS = ROOT_DIR / 'static' / 'css' / 'index' / '06-modals-toast.css'
CSS_ROUTE = ROOT_DIR / 'outlook_web' / 'segments' / '04_routes_groups_accounts.py'


class MobileScaffoldTests(unittest.TestCase):
    def test_mobile_css_file_exists(self):
        self.assertTrue(MOBILE_CSS.exists())

    def test_mobile_css_registered_in_bundle(self):
        source = CSS_ROUTE.read_text(encoding='utf-8')
        self.assertIn("'09-mobile.css'", source)
        # 必须排在 08 之后，保证移动端覆盖优先级
        self.assertLess(source.index("'08-responsive.css'"), source.index("'09-mobile.css'"))
```

- [ ] **Step 2: 跑测试确认失败**

Run: `python3 -m unittest tests.test_mobile_optimization_frontend -v`
Expected: FAIL（`09-mobile.css` 不存在 / 路由未注册）

- [ ] **Step 3: 新建 09-mobile.css**

创建 `static/css/index/09-mobile.css`，内容（占位，后续任务填充）：

```css
        /* 移动端手势、骨架屏与触觉相关样式（仅在 <=768px 生效） */
```

> 注意：现有 CSS 文件每行带 8 空格缩进（因历史上由 `<style>` 内联抽出），保持一致。

- [ ] **Step 4: 在打包路由注册 09-mobile.css**

修改 `outlook_web/segments/04_routes_groups_accounts.py`，在 `css_parts` 元组的
`'08-responsive.css',` 之后加一行：

```python
    css_parts = (
        '01-base.css',
        '02-navbar.css',
        '03-layout.css',
        '04-account-panel.css',
        '05-email-content.css',
        '06-modals-toast.css',
        '07-meta.css',
        '08-responsive.css',
        '09-mobile.css',
    )
```

- [ ] **Step 5: 跑测试确认通过**

Run: `python3 -m unittest tests.test_mobile_optimization_frontend -v`
Expected: PASS（2 tests）

- [ ] **Step 6: 提交**

```bash
git add tests/test_mobile_optimization_frontend.py static/css/index/09-mobile.css outlook_web/segments/04_routes_groups_accounts.py
git commit -m "test(mobile): 搭建移动端优化契约测试与 09-mobile.css 样式文件"
```

---

## Task 1: 视口与安全区（主题 A，P0）

**Files:**
- Modify: `templates/index.html:6`
- Modify: `static/css/index/08-responsive.css`（navbar 顶部安全区）
- Test: `tests/test_mobile_optimization_frontend.py`

- [ ] **Step 1: 写失败测试**

在 `tests/test_mobile_optimization_frontend.py` 追加：

```python
class ViewportSafeAreaTests(unittest.TestCase):
    def test_viewport_has_fit_cover(self):
        html = INDEX_HTML.read_text(encoding='utf-8')
        self.assertIn('viewport-fit=cover', html)

    def test_viewport_keeps_user_scalable(self):
        # 不得禁用缩放（可访问性）：不出现 user-scalable=no / maximum-scale=1
        html = INDEX_HTML.read_text(encoding='utf-8')
        self.assertNotIn('user-scalable=no', html)
        self.assertNotIn('maximum-scale=1', html)

    def test_theme_color_meta_present(self):
        html = INDEX_HTML.read_text(encoding='utf-8')
        self.assertIn('name="theme-color"', html)

    def test_navbar_uses_top_safe_area(self):
        css = RESPONSIVE_CSS.read_text(encoding='utf-8')
        self.assertIn('safe-area-inset-top', css)
```

- [ ] **Step 2: 跑测试确认失败**

Run: `python3 -m unittest tests.test_mobile_optimization_frontend.ViewportSafeAreaTests -v`
Expected: FAIL

- [ ] **Step 3: 改 viewport 与补 meta**

`templates/index.html:6` 改为：

```html
    <meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
    <meta name="theme-color" content="#ffffff">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="default">
```

- [ ] **Step 4: navbar 顶部安全区**

在 `static/css/index/08-responsive.css` 的 `@media (max-width: 768px)` 内、`.navbar` 规则块补充
（找到现有 `.navbar { padding: 0 12px; gap: 12px; }` 并扩展为）：

```css
            .navbar {
                padding: 0 12px;
                gap: 12px;
                padding-top: env(safe-area-inset-top, 0px);
                height: calc(56px + env(safe-area-inset-top, 0px));
            }
```

同时把 `.main-container` 的 `margin-top: 56px;` 与 `.group-panel,.account-panel` 的 `top: 56px;`
改为 `calc(56px + env(safe-area-inset-top, 0px))`（移动段内，逐处替换）。

- [ ] **Step 5: 跑测试确认通过**

Run: `python3 -m unittest tests.test_mobile_optimization_frontend.ViewportSafeAreaTests -v`
Expected: PASS（4 tests）

- [ ] **Step 6: DevTools 手动验证**

- iPhone 12 Pro 模拟 + 显示安全区：导航栏内容不被刘海/状态栏压住；
- 账号面板批量操作栏底部不被 home 横条遮挡（之前 `env(safe-area-inset-bottom)` 现已生效）；
- 横屏：导航与抽屉顶部正确避让。
- 桌面 ≥769px：导航高度仍为 56px，无变化。

- [ ] **Step 7: 提交**

```bash
git add templates/index.html static/css/index/08-responsive.css tests/test_mobile_optimization_frontend.py
git commit -m "fix(mobile): viewport-fit=cover 启用安全区适配并补 PWA meta"
```

---

## Task 2: 邮件正文 iframe 响应式渲染（主题 B，P0）

**Files:**
- Modify: `static/js/index/05-emails.js:1455-1482`（srcdoc 模板）
- Modify: `static/js/index/05-emails.js:1505`（高度最小值）
- Modify: `static/js/index/05-emails.js:1568-1582`（全屏复制 iframe 分支）
- Test: `tests/test_mobile_optimization_frontend.py`

- [ ] **Step 1: 写失败测试**

追加：

```python
class EmailIframeResponsiveTests(unittest.TestCase):
    def test_srcdoc_injects_viewport_meta(self):
        js = EMAILS_JS.read_text(encoding='utf-8')
        self.assertIn('name="viewport"', js)
        self.assertIn('width=device-width', js)

    def test_srcdoc_constrains_wide_elements(self):
        js = EMAILS_JS.read_text(encoding='utf-8')
        # 宽元素兜底：table/pre/video 不撑破，超长词可断
        self.assertIn('max-width: 100%', js)
        self.assertIn('overflow-x: auto', js)
        self.assertIn('word-break', js)

    def test_iframe_min_height_relaxed_for_short_mail(self):
        js = EMAILS_JS.read_text(encoding='utf-8')
        # 不再硬编码 600 作为最小高度
        self.assertNotIn("Math.max(height + 100, 600)", js)
```

- [ ] **Step 2: 跑测试确认失败**

Run: `python3 -m unittest tests.test_mobile_optimization_frontend.EmailIframeResponsiveTests -v`
Expected: FAIL

- [ ] **Step 3: 改 srcdoc 模板**

`static/js/index/05-emails.js` 的 `htmlContent` 模板（约 1455-1481），把 `<head>` 内
`<meta charset="UTF-8">` 之后补 viewport，并把 `<style>` 块替换为：

```javascript
                    const htmlContent = `
                        <!DOCTYPE html>
                        <html>
                        <head>
                            <meta charset="UTF-8">
                            <meta name="viewport" content="width=device-width, initial-scale=1">
                            <style>
                                html, body { overflow-x: hidden; }
                                body {
                                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                                    font-size: 15px;
                                    line-height: 1.6;
                                    color: #333;
                                    margin: 0;
                                    padding: 0;
                                    background-color: #ffffff;
                                    word-break: break-word;
                                }
                                img, video { max-width: 100%; height: auto; }
                                table { max-width: 100%; display: block; overflow-x: auto; }
                                pre { max-width: 100%; overflow-x: auto; white-space: pre-wrap; word-break: break-word; }
                                a { color: #0078d4; word-break: break-all; }
                            </style>
                        </head>
                        <body>${sanitizedBody}</body>
                        </html>
                    `;
                    iframe.srcdoc = htmlContent;
```

- [ ] **Step 4: 放宽 iframe 最小高度**

`static/js/index/05-emails.js` 约 1505 行，把：

```javascript
                        iframe.style.height = Math.max(height + 100, 600) + 'px';
```

改为：

```javascript
                        const minHeight = (typeof isMobileLayout === 'function' && isMobileLayout()) ? 200 : 400;
                        iframe.style.height = Math.max(height + 24, minHeight) + 'px';
```

- [ ] **Step 5: 全屏复制 iframe 同步注入**

`static/js/index/05-emails.js` 约 1568-1582，全屏分支用
`iframe.contentDocument.documentElement.outerHTML` 复制内容到 `newIframe.srcdoc`——
该 outerHTML 已包含 Step 3 注入的 viewport 与样式，无需额外改动。**仅核对**该分支复制的是
注入后的文档（含 viewport meta），若复制的是原始 body 则同样补注入。在测试中加断言：

```python
    def test_fullscreen_clone_preserves_document(self):
        js = EMAILS_JS.read_text(encoding='utf-8')
        self.assertIn('documentElement.outerHTML', js)
```

- [ ] **Step 6: 跑测试确认通过**

Run: `python3 -m unittest tests.test_mobile_optimization_frontend.EmailIframeResponsiveTests -v`
Expected: PASS（4 tests）

- [ ] **Step 7: DevTools 手动验证**

构造一封测试 HTML 邮件（含 `<table width="700">` 固定宽表格、一条 80 字符无空格 URL、一张大图）：
- 375px 视口下打开详情：无横向滚动条，宽表格在自身容器内可横滑，长 URL 自动换行，图片不溢出；
- 一封两行纯文本短邮件：iframe 不再留 ~600px 空白；
- 全屏查看：同样无横向溢出。
- 桌面：正文渲染与改动前一致。

- [ ] **Step 8: 提交**

```bash
git add static/js/index/05-emails.js tests/test_mobile_optimization_frontend.py
git commit -m "fix(mobile): 邮件正文 iframe 注入 viewport 与响应式兜底样式，高度自适应"
```

---

## Task 3: 表单字号防 iOS 缩放（主题 C，P0）

**Files:**
- Modify: `static/css/index/08-responsive.css`（移动段补表单字号）
- Modify: `templates/partials/index/*.html`（关键输入补 inputmode/type，按需）
- Test: `tests/test_mobile_optimization_frontend.py`

- [ ] **Step 1: 写失败测试**

追加：

```python
import re

class FormZoomTests(unittest.TestCase):
    def test_mobile_form_controls_use_16px(self):
        css = RESPONSIVE_CSS.read_text(encoding='utf-8')
        # 移动段内存在统一 16px 的表单控件规则
        self.assertRegex(css, r'\.form-input[^}]*font-size:\s*16px')
        self.assertRegex(css, r'\.form-select[^}]*font-size:\s*16px')
        self.assertRegex(css, r'\.form-textarea[^}]*font-size:\s*16px')
```

- [ ] **Step 2: 跑测试确认失败**

Run: `python3 -m unittest tests.test_mobile_optimization_frontend.FormZoomTests -v`
Expected: FAIL

- [ ] **Step 3: 移动端统一表单字号 16px**

在 `static/css/index/08-responsive.css` 的 `@media (max-width: 768px)` 块末尾（`}` 之前）追加：

```css
            .form-input,
            .form-select,
            .form-textarea,
            .tag-filter-search-input,
            .import-tag-trigger,
            .cloudflare-global-filter-input,
            .refresh-pagination input,
            .refresh-pagination select {
                font-size: 16px;
            }
```

> 说明：`.search-input` 已在现有移动段设为 16px，此处补齐弹窗与其它输入控件。

- [ ] **Step 4: 跑测试确认通过**

Run: `python3 -m unittest tests.test_mobile_optimization_frontend.FormZoomTests -v`
Expected: PASS

- [ ] **Step 5: DevTools 手动验证**

iPhone SE 模拟（iOS Safari UA）：依次聚焦设置弹窗、导入弹窗、Token 刷新弹窗内的输入框/下拉，
页面**不发生自动放大**；端口等数字字段（如已加 `inputmode="numeric"`）弹出数字键盘。
桌面：表单控件视觉尺寸不变（桌面规则仍为 14px）。

- [ ] **Step 6: 提交**

```bash
git add static/css/index/08-responsive.css tests/test_mobile_optimization_frontend.py
git commit -m "fix(mobile): 统一移动端表单控件字号 16px 消除 iOS 聚焦缩放"
```

---

## Task 4: 触控热区 ≥44px（主题 D，P1）

**Files:**
- Modify: `static/css/index/08-responsive.css`（移动段触控尺寸）
- Test: `tests/test_mobile_optimization_frontend.py`

- [ ] **Step 1: 写失败测试**

追加：

```python
class TouchTargetTests(unittest.TestCase):
    def test_mobile_panel_action_btn_enlarged(self):
        css = RESPONSIVE_CSS.read_text(encoding='utf-8')
        # 已存在 .panel-action-btn 38x38（现状），本任务提升到 44
        self.assertRegex(css, r'\.panel-action-btn[^}]*width:\s*44px')
        self.assertRegex(css, r'\.panel-action-btn[^}]*height:\s*44px')

    def test_mobile_account_menu_trigger_enlarged(self):
        css = RESPONSIVE_CSS.read_text(encoding='utf-8')
        self.assertRegex(css, r'\.account-menu-trigger[^}]*width:\s*4[0-4]px')

    def test_mobile_modal_close_min_size(self):
        css = RESPONSIVE_CSS.read_text(encoding='utf-8')
        self.assertIn('.modal-close', css)
```

- [ ] **Step 2: 跑测试确认失败**

Run: `python3 -m unittest tests.test_mobile_optimization_frontend.TouchTargetTests -v`
Expected: FAIL

- [ ] **Step 3: 提升移动端触控热区**

在 `static/css/index/08-responsive.css` 移动段内调整/追加（`.panel-action-btn` 现状为 38×38，改为 44×44）：

```css
            .panel-action-btn {
                width: 44px;
                height: 44px;
            }

            .account-menu-trigger {
                width: 40px;
                height: 40px;
            }

            .modal-close {
                min-width: 40px;
                min-height: 40px;
                display: inline-flex;
                align-items: center;
                justify-content: center;
            }

            .account-action-btn,
            .tag-filter-option {
                min-height: 44px;
            }
```

- [ ] **Step 4: hover-only 入口在触摸设备常显**

在 `static/css/index/09-mobile.css` 追加（用 `@media (hover: none)` 精准命中触摸设备，避免影响桌面）：

```css
        @media (hover: none) and (max-width: 768px) {
            .group-actions {
                opacity: 1;
            }
        }
```

- [ ] **Step 5: 跑测试确认通过**

Run: `python3 -m unittest tests.test_mobile_optimization_frontend.TouchTargetTests -v`
Expected: PASS

- [ ] **Step 6: DevTools 手动验证**

375px 下逐一点击：分组面板「+」、账号面板头部四个图标、账号项「⋯」菜单、弹窗关闭「×」、
分组项操作按钮——均易点中、不误触相邻元素。桌面：图标按钮视觉尺寸不变。

- [ ] **Step 7: 提交**

```bash
git add static/css/index/08-responsive.css static/css/index/09-mobile.css tests/test_mobile_optimization_frontend.py
git commit -m "fix(mobile): 触控热区提升至推荐尺寸并使 hover-only 操作在触屏常显"
```

---

## Task 5: 弹窗断点协调与软键盘避让（主题 E，P1）

**Files:**
- Modify: `static/css/index/06-modals-toast.css`（断点协调）
- Modify: `static/js/index/01-core.js`（visualViewport 监听）
- Test: `tests/test_mobile_optimization_frontend.py`

- [ ] **Step 1: 写失败测试**

追加：

```python
class ModalKeyboardTests(unittest.TestCase):
    def test_visual_viewport_listener_present(self):
        js = CORE_JS.read_text(encoding='utf-8')
        self.assertIn('visualViewport', js)
        self.assertIn('--keyboard-inset', js)

    def test_modal_uses_keyboard_inset(self):
        css = MODALS_CSS.read_text(encoding='utf-8')
        self.assertIn('--keyboard-inset', css)
```

- [ ] **Step 2: 跑测试确认失败**

Run: `python3 -m unittest tests.test_mobile_optimization_frontend.ModalKeyboardTests -v`
Expected: FAIL

- [ ] **Step 3: visualViewport 暴露键盘高度为 CSS 变量**

在 `static/js/index/01-core.js` 的初始化事件绑定块（约 1150-1175，`window.addEventListener('resize'...)` 附近）追加：

```javascript
            if (window.visualViewport) {
                const updateKeyboardInset = () => {
                    const vv = window.visualViewport;
                    const inset = Math.max(0, window.innerHeight - vv.height - vv.offsetTop);
                    document.documentElement.style.setProperty('--keyboard-inset', inset + 'px');
                };
                window.visualViewport.addEventListener('resize', updateKeyboardInset);
                window.visualViewport.addEventListener('scroll', updateKeyboardInset);
                updateKeyboardInset();
            }
```

- [ ] **Step 4: 弹窗底部为键盘让位**

在 `static/css/index/06-modals-toast.css` 顶部 `:root` 缺省值（文件开头加）：

```css
        :root {
            --keyboard-inset: 0px;
        }
```

在 `static/css/index/08-responsive.css` 移动段的 `.modal-content` 规则补充
（找到现有 `.modal-content, #refreshErrorModal .modal-content { ... }` 块）追加：

```css
                padding-bottom: var(--keyboard-inset, 0px);
                max-height: calc(100dvh - 12px - var(--keyboard-inset, 0px));
```

- [ ] **Step 5: 协调弹窗内部断点**

`static/css/index/06-modals-toast.css` 中现有 `@media (max-width: 640px)` 与 `@media (max-width: 860px)`
段落保持不动（它们处理弹窗内栅格塌缩，与 768px 主断点不冲突——栅格塌缩在 860 先于 sheet 化在 768，
属于渐进，无矛盾）。**仅核对**：768px 下 `.modal` 变底部 sheet 时，`.edit-account-modal-content` /
`.settings-modal-content` 等自定义宽度被 08-responsive 的 `width:100%!important` 正确覆盖。
加断言确认覆盖规则存在：

```python
    def test_modal_content_full_width_on_mobile(self):
        css = RESPONSIVE_CSS.read_text(encoding='utf-8')
        self.assertRegex(css, r'\.modal-content[^}]*width:\s*100%\s*!important')
```

- [ ] **Step 6: 跑测试确认通过**

Run: `python3 -m unittest tests.test_mobile_optimization_frontend.ModalKeyboardTests -v`
Expected: PASS（3 tests）

- [ ] **Step 7: DevTools 手动验证**

iPhone 模拟，打开设置弹窗，聚焦靠底部的输入框并触发软键盘（DevTools 无真键盘——
改在真实移动浏览器或用 `visualViewport` 手动缩小窗口模拟）：footer 确认按钮随键盘上移、保持可见。
640–768px 区间逐档拖动：弹窗在 768px 切换为全宽底部 sheet，无样式错乱。桌面：弹窗居中、尺寸不变。

- [ ] **Step 8: 提交**

```bash
git add static/css/index/06-modals-toast.css static/css/index/08-responsive.css static/js/index/01-core.js tests/test_mobile_optimization_frontend.py
git commit -m "feat(mobile): 弹窗软键盘避让与断点协调"
```

---

## Task 6: 物理返回键导航栈（主题 F，P1 / 重设计）

**Files:**
- Modify: `static/js/index/01-core.js`（history 状态机 + popstate；接入 openMobilePanel / showMobileEmailDetail / showEmailList / closeMobilePanels）
- Test: `tests/test_mobile_optimization_frontend.py`

**设计：** 维护一个「移动视图层级」概念。当移动端进入更深层级（打开抽屉 / 进入邮件详情）时
`history.pushState({ mobileView: <name> }, '')`；监听 `popstate`，按优先级回退：
关弹窗 > 收抽屉 > 详情回列表 > 不拦截（交给浏览器默认离开）。仅 `isMobileLayout()` 为真时入栈/拦截。
用 `state.mobileView` 标记自有状态，非自有状态不处理，避免污染浏览器历史。

- [ ] **Step 1: 写失败测试**

追加：

```python
class BackButtonNavTests(unittest.TestCase):
    def test_popstate_listener_present(self):
        js = CORE_JS.read_text(encoding='utf-8')
        self.assertIn("addEventListener('popstate'", js)

    def test_pushes_mobile_view_state(self):
        js = CORE_JS.read_text(encoding='utf-8')
        self.assertIn('mobileView', js)
        self.assertIn('history.pushState', js)

    def test_back_handler_guarded_by_mobile_layout(self):
        js = CORE_JS.read_text(encoding='utf-8')
        start = js.index('function handleMobileBack')
        end = js.index('\n        }', start)
        self.assertIn('isMobileLayout', js[start:end])
```

- [ ] **Step 2: 跑测试确认失败**

Run: `python3 -m unittest tests.test_mobile_optimization_frontend.BackButtonNavTests -v`
Expected: FAIL

- [ ] **Step 3: 实现 history 状态机**

在 `static/js/index/01-core.js` 增加函数（建议放在 `syncMobilePanels` 附近）：

```javascript
        function pushMobileViewState(name) {
            if (!isMobileLayout()) return;
            if (window.history.state && window.history.state.mobileView === name) return;
            window.history.pushState({ mobileView: name }, '');
        }

        function hasOpenMobileModal() {
            return !!document.querySelector('.modal.show');
        }

        function handleMobileBack(event) {
            if (!isMobileLayout()) return;
            // 1) 关弹窗
            if (hasOpenMobileModal() && typeof closeAllModals === 'function') {
                closeAllModals();
                pushMobileViewState('root');
                return;
            }
            // 2) 收抽屉
            if (document.querySelector('#groupPanel.show, #accountPanel.show')) {
                closeMobilePanels();
                pushMobileViewState('root');
                return;
            }
            // 3) 详情回列表
            const listPanel = document.getElementById('emailListPanel');
            if (listPanel && listPanel.classList.contains('hidden')) {
                showEmailList();
                pushMobileViewState('root');
                return;
            }
            // 4) 其余：不拦截（浏览器默认行为已发生，无需再处理）
        }
```

- [ ] **Step 4: 接入入栈点与监听**

- 在 `openMobilePanel` 末尾（`syncMobilePanels()` 之后）加 `pushMobileViewState('panel');`
- 在 `showMobileEmailDetail` 末尾（`updateMobileContext()` 之后）加 `pushMobileViewState('detail');`
- 在初始化事件绑定块加：`window.addEventListener('popstate', handleMobileBack);`
- 在 `01-core.js` 顶部初始化时确保根状态：`if (!window.history.state) { window.history.replaceState({ mobileView: 'root' }, ''); }`

- [ ] **Step 5: 跑测试确认通过**

Run: `python3 -m unittest tests.test_mobile_optimization_frontend.BackButtonNavTests -v`
Expected: PASS（3 tests）

- [ ] **Step 6: DevTools 手动验证**

移动模拟下：① 打开账号抽屉→点浏览器返回→抽屉收起（不离开页面）；
② 进入邮件详情→返回→回到邮件列表；③ 打开弹窗→返回→弹窗关闭；
④ 列表根态→返回→正常离开/后退；⑤ 刷新页面后状态不卡死。
桌面：返回键行为与改动前一致（不被拦截）。

- [ ] **Step 7: 提交**

```bash
git add static/js/index/01-core.js tests/test_mobile_optimization_frontend.py
git commit -m "feat(mobile): 物理返回键先收抽屉/关弹窗/详情回列表"
```

---

## Task 7: 下拉刷新邮件列表（主题 G，P2 / 重设计）

**Files:**
- Modify: `static/js/index/01-core.js`（下拉手势）
- Modify: `static/css/index/09-mobile.css`（下拉指示器样式）
- Modify: `templates/partials/index/layout.html`（在 `#emailList` 内加指示器节点，或由 JS 注入）
- Test: `tests/test_mobile_optimization_frontend.py`

**设计：** 仅 `isMobileLayout()` 且 `#emailList.scrollTop === 0` 时启用。touchstart 记起点，
touchmove 计算下拉距离（带阻尼），超阈值（如 64px）显示「释放刷新」；touchend 超阈值调用现有
`refreshEmails()`，否则回弹。临时邮箱/无账号不触发。

- [ ] **Step 1: 写失败测试**

追加：

```python
class PullToRefreshTests(unittest.TestCase):
    def test_pull_to_refresh_setup_present(self):
        js = CORE_JS.read_text(encoding='utf-8')
        self.assertIn('function setupPullToRefresh', js)
        self.assertIn("addEventListener('touchstart'", js)
        self.assertIn("addEventListener('touchmove'", js)
        self.assertIn("addEventListener('touchend'", js)

    def test_pull_to_refresh_calls_refresh(self):
        js = CORE_JS.read_text(encoding='utf-8')
        start = js.index('function setupPullToRefresh')
        end = js.index('\n        }\n', start)
        self.assertIn('refreshEmails', js[start:end])
        self.assertIn('isMobileLayout', js[start:end])

    def test_pull_indicator_styles_present(self):
        css = MOBILE_CSS.read_text(encoding='utf-8')
        self.assertIn('pull-refresh-indicator', css)
```

- [ ] **Step 2: 跑测试确认失败**

Run: `python3 -m unittest tests.test_mobile_optimization_frontend.PullToRefreshTests -v`
Expected: FAIL

- [ ] **Step 3: 加指示器节点**

在 `templates/partials/index/layout.html` 的 `<div class="email-list" id="emailList">` 起始标签后插入：

```html
                    <div class="pull-refresh-indicator" id="pullRefreshIndicator" aria-hidden="true">
                        <span class="pull-refresh-indicator__spinner"></span>
                        <span class="pull-refresh-indicator__text">下拉刷新</span>
                    </div>
```

- [ ] **Step 4: 实现下拉手势**

在 `static/js/index/01-core.js` 增加函数，并在初始化时调用 `setupPullToRefresh()`：

```javascript
        function setupPullToRefresh() {
            const list = document.getElementById('emailList');
            const indicator = document.getElementById('pullRefreshIndicator');
            if (!list || !indicator) return;

            const THRESHOLD = 64;
            let startY = 0;
            let pulling = false;
            let distance = 0;

            list.addEventListener('touchstart', (e) => {
                if (!isMobileLayout() || list.scrollTop > 0 || !currentAccount) return;
                startY = e.touches[0].clientY;
                pulling = true;
                distance = 0;
            }, { passive: true });

            list.addEventListener('touchmove', (e) => {
                if (!pulling) return;
                distance = Math.max(0, (e.touches[0].clientY - startY) * 0.5);
                if (distance > 0 && list.scrollTop <= 0) {
                    indicator.style.height = Math.min(distance, THRESHOLD + 16) + 'px';
                    indicator.classList.toggle('is-ready', distance >= THRESHOLD);
                }
            }, { passive: true });

            list.addEventListener('touchend', () => {
                if (!pulling) return;
                pulling = false;
                const shouldRefresh = distance >= THRESHOLD;
                indicator.style.height = '';
                indicator.classList.remove('is-ready');
                if (shouldRefresh && typeof refreshEmails === 'function') {
                    triggerHaptic(10);
                    refreshEmails();
                }
            });
        }
```

> `triggerHaptic` 在 Task 9 定义；此处先用可选链保护：若未定义则跳过。改为：
> `if (typeof triggerHaptic === 'function') triggerHaptic(10);`

- [ ] **Step 5: 指示器样式**

在 `static/css/index/09-mobile.css` 追加：

```css
        @media (max-width: 768px) {
            .pull-refresh-indicator {
                height: 0;
                overflow: hidden;
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 8px;
                color: #64748b;
                font-size: 12px;
                transition: height 0.18s ease;
            }
            .pull-refresh-indicator__spinner {
                width: 16px;
                height: 16px;
                border: 2px solid #cbd5e1;
                border-top-color: #1a1a1a;
                border-radius: 50%;
            }
            .pull-refresh-indicator.is-ready .pull-refresh-indicator__spinner {
                animation: spin 0.8s linear infinite;
            }
        }
        @media (min-width: 769px) {
            .pull-refresh-indicator { display: none; }
        }
```

- [ ] **Step 6: 跑测试确认通过**

Run: `python3 -m unittest tests.test_mobile_optimization_frontend.PullToRefreshTests -v`
Expected: PASS（3 tests）

- [ ] **Step 7: DevTools 手动验证**

移动模拟（触摸模式）：选中账号后在邮件列表顶部下拉→出现「下拉刷新」指示器→超阈值松手触发刷新；
列表中部滚动不触发；无选中账号时下拉无效。桌面：指示器隐藏、无任何手势。

- [ ] **Step 8: 提交**

```bash
git add static/js/index/01-core.js static/css/index/09-mobile.css templates/partials/index/layout.html tests/test_mobile_optimization_frontend.py
git commit -m "feat(mobile): 邮件列表下拉刷新"
```

---

## Task 8: 列表项侧滑操作（主题 H，P2 / 重设计）

**Files:**
- Modify: `static/js/index/01-core.js`（通用侧滑挂载函数）
- Modify: `static/css/index/09-mobile.css`（侧滑动作层样式）
- Test: `tests/test_mobile_optimization_frontend.py`

**设计：** 通用 `attachSwipeActions(item, { left, right })`：touch 主轴判定——横向位移显著大于纵向
（如 |dx| > |dy| * 1.5 且 |dx| > 10）才进入侧滑，避免与纵向滚动/拖拽排序冲突。账号选择模式下禁用。
邮件项：左滑「删除」、右滑「标记已读」；账号项：左滑「删除」。复用现有删除/标记已读函数。

- [ ] **Step 1: 写失败测试**

追加：

```python
class SwipeActionTests(unittest.TestCase):
    def test_swipe_attach_function_present(self):
        js = CORE_JS.read_text(encoding='utf-8')
        self.assertIn('function attachSwipeActions', js)

    def test_swipe_axis_lock_logic(self):
        js = CORE_JS.read_text(encoding='utf-8')
        start = js.index('function attachSwipeActions')
        end = js.index('\n        }\n', start)
        seg = js[start:end]
        self.assertIn('Math.abs', seg)  # 主轴判定
        self.assertIn('isMobileLayout', seg)

    def test_swipe_styles_present(self):
        css = MOBILE_CSS.read_text(encoding='utf-8')
        self.assertIn('swipe-action', css)
```

- [ ] **Step 2: 跑测试确认失败**

Run: `python3 -m unittest tests.test_mobile_optimization_frontend.SwipeActionTests -v`
Expected: FAIL

- [ ] **Step 3: 实现通用侧滑**

在 `static/js/index/01-core.js` 增加：

```javascript
        function attachSwipeActions(item, handlers) {
            if (!isMobileLayout() || !item) return;
            let startX = 0, startY = 0, dx = 0, locked = null;

            item.addEventListener('touchstart', (e) => {
                if (document.body.classList.contains('account-selection-active')) return;
                startX = e.touches[0].clientX;
                startY = e.touches[0].clientY;
                dx = 0; locked = null;
            }, { passive: true });

            item.addEventListener('touchmove', (e) => {
                const cx = e.touches[0].clientX, cy = e.touches[0].clientY;
                const ddx = cx - startX, ddy = cy - startY;
                if (locked === null) {
                    if (Math.abs(ddx) > 10 && Math.abs(ddx) > Math.abs(ddy) * 1.5) locked = 'x';
                    else if (Math.abs(ddy) > 10) locked = 'y';
                }
                if (locked === 'x') {
                    dx = ddx;
                    item.style.transform = `translateX(${Math.max(-96, Math.min(96, dx))}px)`;
                    item.classList.add('is-swiping');
                }
            }, { passive: true });

            item.addEventListener('touchend', () => {
                item.classList.remove('is-swiping');
                item.style.transform = '';
                if (locked !== 'x') return;
                if (dx <= -64 && handlers.left) { if (typeof triggerHaptic === 'function') triggerHaptic(10); handlers.left(); }
                else if (dx >= 64 && handlers.right) { if (typeof triggerHaptic === 'function') triggerHaptic(10); handlers.right(); }
            });
        }
```

- [ ] **Step 4: 在渲染后挂载**

在邮件项渲染处（`renderEmailList` 之后，05-emails.js）与账号项渲染处（02-groups.js 渲染账号列表后）
对每个 `.email-item` / `.account-item` 调用 `attachSwipeActions`。示例（邮件项，按实际现有删除/已读函数名接入）：

```javascript
            document.querySelectorAll('#emailList .email-item').forEach((el) => {
                const emailId = el.dataset.emailId;
                attachSwipeActions(el, {
                    left: () => confirmDeleteEmailById ? confirmDeleteEmailById(emailId) : null,
                    right: () => markEmailReadById ? markEmailReadById(emailId) : null,
                });
            });
```

> 实现时核对现有删除/标记已读的实际函数签名（在 05-emails.js / 10-batch-actions.js 中查），
> 用真实可调用的入口；若仅有批量接口，则包装单封调用。**不得留占位函数名**。

- [ ] **Step 5: 侧滑动作层样式**

在 `static/css/index/09-mobile.css` 追加：

```css
        @media (max-width: 768px) {
            .email-item, .account-item {
                transition: transform 0.18s ease;
            }
            .email-item.is-swiping, .account-item.is-swiping {
                transition: none;
            }
            .swipe-action-hint {
                position: absolute;
                top: 0; bottom: 0;
                display: flex;
                align-items: center;
                font-size: 12px;
                font-weight: 700;
            }
        }
```

- [ ] **Step 6: 跑测试确认通过**

Run: `python3 -m unittest tests.test_mobile_optimization_frontend.SwipeActionTests -v`
Expected: PASS（3 tests）

- [ ] **Step 7: DevTools 手动验证**

移动触摸模拟：邮件项左滑触发删除确认、右滑标记已读；账号项左滑触发删除；
纵向滚动列表顺畅、不误触发侧滑；进入账号选择模式后侧滑禁用；账号拖拽排序不受影响。
桌面：无侧滑、点击进入详情如常。

- [ ] **Step 8: 提交**

```bash
git add static/js/index/01-core.js static/js/index/05-emails.js static/js/index/02-groups.js static/css/index/09-mobile.css tests/test_mobile_optimization_frontend.py
git commit -m "feat(mobile): 邮件/账号列表项侧滑快捷操作"
```

---

## Task 9: 反馈与加载态（主题 I，P2）

**Files:**
- Modify: `static/js/index/01-core.js`（triggerHaptic）
- Modify: `static/css/index/09-mobile.css`（骨架屏 + reduced-motion）
- Modify: `static/js/index/05-emails.js` / `02-groups.js`（加载时渲染骨架，按需）
- Test: `tests/test_mobile_optimization_frontend.py`

- [ ] **Step 1: 写失败测试**

追加：

```python
class FeedbackLoadingTests(unittest.TestCase):
    def test_haptic_helper_present(self):
        js = CORE_JS.read_text(encoding='utf-8')
        self.assertIn('function triggerHaptic', js)
        self.assertIn('navigator.vibrate', js)

    def test_skeleton_styles_present(self):
        css = MOBILE_CSS.read_text(encoding='utf-8')
        self.assertIn('skeleton', css)

    def test_reduced_motion_respected(self):
        css = MOBILE_CSS.read_text(encoding='utf-8')
        self.assertIn('prefers-reduced-motion', css)
```

- [ ] **Step 2: 跑测试确认失败**

Run: `python3 -m unittest tests.test_mobile_optimization_frontend.FeedbackLoadingTests -v`
Expected: FAIL

- [ ] **Step 3: 触觉反馈助手**

在 `static/js/index/01-core.js` 增加（供 Task 7/8 调用）：

```javascript
        function triggerHaptic(durationMs) {
            try {
                if (typeof navigator !== 'undefined' && typeof navigator.vibrate === 'function') {
                    navigator.vibrate(durationMs || 10);
                }
            } catch (e) { /* 不支持则忽略 */ }
        }
```

- [ ] **Step 4: 骨架屏 + reduced-motion 样式**

在 `static/css/index/09-mobile.css` 追加：

```css
        @media (max-width: 768px) {
            .skeleton-item {
                margin: 0 12px 10px;
                height: 84px;
                border-radius: 16px;
                background: linear-gradient(90deg, #eef1f5 25%, #f7f9fc 37%, #eef1f5 63%);
                background-size: 400% 100%;
                animation: skeleton-shimmer 1.4s ease infinite;
            }
            @keyframes skeleton-shimmer {
                0% { background-position: 100% 50%; }
                100% { background-position: 0 50%; }
            }
        }
        @media (prefers-reduced-motion: reduce) {
            .skeleton-item { animation: none; }
            .pull-refresh-indicator { transition: none; }
            .email-item, .account-item { transition: none; }
        }
```

- [ ] **Step 5: 加载时渲染骨架（移动端）**

在邮件列表加载开始处（`loadEmails`/`refreshEmails` 设置 loading 时，05-emails.js），
移动端用骨架替换 spinner。示例辅助函数（放 01-core.js）：

```javascript
        function renderSkeletonList(container, count) {
            if (!container) return;
            container.innerHTML = Array.from({ length: count || 6 })
                .map(() => '<div class="skeleton-item"></div>').join('');
        }
```

在现有 loading 分支：`if (isMobileLayout()) { renderSkeletonList(document.getElementById('emailList'), 6); }`
（保留桌面原有 spinner）。

- [ ] **Step 6: 跑测试确认通过**

Run: `python3 -m unittest tests.test_mobile_optimization_frontend.FeedbackLoadingTests -v`
Expected: PASS（3 tests）

- [ ] **Step 7: DevTools 手动验证**

移动模拟：邮件/账号列表加载时显示骨架占位（非空白）；删除/下拉刷新/侧滑确认时设备震动（支持的设备）；
系统开启「减少动态效果」后骨架微光/过渡停止。桌面：仍为原 spinner，无震动。

- [ ] **Step 8: 提交**

```bash
git add static/js/index/01-core.js static/js/index/05-emails.js static/css/index/09-mobile.css tests/test_mobile_optimization_frontend.py
git commit -m "feat(mobile): 骨架屏加载态、触觉反馈与 reduced-motion 降级"
```

---

## Task 10: 全量回归与收尾

**Files:**
- Test: `tests/test_mobile_optimization_frontend.py`（全跑）

- [ ] **Step 1: 跑全部移动端契约测试**

Run: `python3 -m unittest tests.test_mobile_optimization_frontend -v`
Expected: 全部 PASS

- [ ] **Step 2: 跑既有测试套件防回归**

Run: `python3 -m unittest discover -s tests -v`
Expected: 全部 PASS（确认未破坏既有前端契约测试与后端测试）

- [ ] **Step 3: 桌面端整体回归（DevTools ≥769px）**

逐一确认：三栏布局、批量操作栏右侧浮层定位、各弹窗居中与自定义宽度、邮件正文渲染、
导航栏——均与本次改动前一致。

- [ ] **Step 4: 移动端整体走查（375px / 390px / 横屏）**

按 P0→P2 顺序复核每个主题的 DevTools 验证清单，记录通过情况；未通过项回到对应 Task 修复。

- [ ] **Step 5: 收尾提交（如有走查中的小修）**

```bash
git add -A
git commit -m "chore(mobile): 移动端优化全量回归收尾"
```

---

## Self-Review 记录

- **Spec 覆盖**：主题 A→Task1、B→Task2、C→Task3、D→Task4、E→Task5、F→Task6、G→Task7、
  H→Task8、I→Task9，文件清单与 spec 第 4 节一致；新建 09-mobile.css 注册（spec 风险点）落到 Task0。✓
- **占位符**：Task8 Step4 明确要求实现期核对真实删除/已读函数名、禁止占位；其余步骤均给出完整代码。✓
- **命名一致**：`triggerHaptic`（Task9 定义，Task7/8 以特性检测方式调用）、`isMobileLayout`、
  `pushMobileViewState`/`handleMobileBack`、`attachSwipeActions`、`setupPullToRefresh`、
  `renderSkeletonList`、`--keyboard-inset`、`pull-refresh-indicator` 全计划一致。✓
- **依赖顺序**：`triggerHaptic` 在 Task9 才定义，Task7/8 用 `typeof ... === 'function'` 守卫，
  执行顺序上 7/8 先于 9 时不报错（仅暂无震动），9 完成后生效。已在步骤中说明。✓
