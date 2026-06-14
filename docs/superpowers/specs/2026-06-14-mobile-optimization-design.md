# 移动端完美适配优化 — 设计文档

- 日期：2026-06-14
- 范围：主界面（分组 / 账号 / 邮件列表 / 邮件详情三栏体系）+ 全部弹窗 modal
- 不在范围：登录页 `login.html`、深色模式
- 执行档位：**P0 + P1 + P2 全量**
- 手势重设计：**物理返回键、下拉刷新邮件、列表项侧滑操作**

## 1. 背景与目标

应用（Outlook 邮件阅读器 v2.0.67）已有较完整的移动端基础：`08-responsive.css` 中
768/480px 断点、抽屉式分组/账号面板、`mobile-quickbar` 快捷栏、邮件列表↔详情切换、
底部 sheet 弹窗、批量操作栏适配等。本次目标是在此基础上**修复真实适配漏洞 +
打磨触控/排版/弹窗体验 + 引入三项现代手势交互**，使移动端（重点 ≤480px 手机）
达到「完美适配、接近原生 App」的体验，且**不回退桌面端**。

### 关键现状事实（审计确认）

- `index.html:6` viewport = `width=device-width, initial-scale=1.0`，**缺 `viewport-fit=cover`**
  → `env(safe-area-inset-*)` 在刘海屏恒为 0，08-responsive.css 中的安全区适配实际未生效。
- 邮件正文用 `<iframe srcdoc>` 渲染（05-emails.js:1455-1482），srcdoc 的 `<head>`
  **缺 `<meta viewport>`**，且只约束了 `img`，未约束 `table/pre/宽元素` → HTML 邮件横向溢出。
- `adjustIframeHeight`（05-emails.js:1488）最小高度写死 `600px` → 短邮件留大片空白。
- 全代码**无 `popstate` / `history` 处理** → 移动端打开详情/抽屉后按返回键直接退出页面。
- CSS 由后端路由 `bundled_index_css`（04_routes_groups_accounts.py:155）把 `01-08.css`
  顺序拼接为 `/assets/index.css`，**新增 CSS 文件必须在此列表注册**。
- 移动端交互 JS 已集中在 `01-core.js`（`isMobileLayout`、抽屉、quickbar、
  `showMobileEmailDetail`、`showEmailList`、事件绑定在 1150+ 行的初始化块）。
- 弹窗内部另有 860/640/979px 等断点（06-modals-toast.css 尾部），与 768px 主断点并存。

## 2. 设计原则

1. **移动端隔离改动**：新增样式全部包裹在 `@media (max-width: 768px)`（及 480px）内，
   桌面端 CSS 规则不动；新增 JS 行为统一用 `isMobileLayout()` 守卫，桌面端早返回。
2. **复用既有机制**：沿用现有的 `.email-list-panel.hidden`、`.show`、`mobile-*` 类名体系与
   `updateMobileContext()` / `syncMobilePanels()` 状态同步函数，不另起炉灶。
3. **渐进增强**：手势（下拉刷新/侧滑/返回键）为增强层，touch 事件不可用或桌面端时
   原有点击路径完全保留可用。
4. **单一断点真相**：以 768px 为移动主断点，480px 为小屏强化；协调弹窗的 860/640 断点避免冲突。
5. **最小侵入正文渲染**：邮件 HTML 在 iframe `srcdoc` 内适配，不改 DOMPurify 净化策略与信任模式逻辑。

## 3. 改动分解（按主题）

### 主题 A — 视口与安全区（P0，工作量 S）
- **A1** `index.html:6` viewport 增加 `viewport-fit=cover`；补 `<meta name="theme-color">`、
  `apple-mobile-web-app-capable` 等 PWA 友好标签（仅 meta，不改行为）。
- **A2** 审查 08-responsive.css 中所有 `env(safe-area-inset-*)` 用点，确认 cover 生效后
  批量操作栏、底部 sheet、quickbar 的底部留白正确；为 `.navbar` 顶部补 `env(safe-area-inset-top)`
  适配横屏刘海。
- 验证项：iPhone 模拟器（含刘海机型）下批量栏不被 home 横条遮挡；横屏导航不被刘海压住。

### 主题 B — 邮件正文渲染（P0，工作量 M）
- **B1** iframe `srcdoc` 模板（05-emails.js:1455）`<head>` 注入
  `<meta name="viewport" content="width=device-width, initial-scale=1">`。
- **B2** 注入响应式兜底样式：`html,body{overflow-x:hidden} img,table,video,pre{max-width:100%!important}`
  `table{display:block;overflow-x:auto}`（宽表格改为容器内横向滚动，而非撑破页面）
  `* {word-break:break-word}` 针对超长不可断 URL。
- **B3** `adjustIframeHeight`：移动端最小高度由 600px 降到一个合理值（如 200px）或纯自适应；
  全屏复制 iframe 分支（1568+）同步注入相同 viewport/样式。
- 验证项：构造含 700px 固定宽度 `<table>`、超长 URL、大图的 HTML 邮件，
  在 375px 视口下无横向滚动、无内容溢出、短邮件无大片空白。

### 主题 C — 表单与 iOS 缩放（P0，工作量 S）
- **C1** 移动端（`@media max-width:768px`）统一 `.form-input/.form-select/.form-textarea`、
  标签搜索框、各 modal 内输入控件 `font-size: 16px`，消除聚焦自动放大。
- **C2** 为关键输入补合适 `type`/`inputmode`（如端口号 `inputmode="numeric"`、
  URL 字段 `type="url"`），不改校验逻辑。
- 验证项：iOS Safari 模拟下聚焦任意弹窗输入框，页面不缩放。

### 主题 D — 触控目标与误触（P1，工作量 M）
- **D1** 移动端将 `< 44px` 的可点击元素热区提升到 ≥44px：`panel-action-btn`(34→44)、
  `account-menu-trigger`(32→40+)、`modal-close`、`folder-tab`、各图标按钮。
  优先用 `min-height/min-width` + padding，必要时用透明伪元素扩大热区以不改视觉尺寸。
- **D2** 相邻按钮间距检查（导航操作菜单、面板头部图标组、批量按钮），保证 ≥8px。
- **D3** 触摸设备禁用「仅 hover 才显示」的功能入口：`.group-actions{opacity:0}` 在移动端常显
  （现 768px 已处理，补查 480px 与其它 hover-only 元素）。
- 验证项：375px 下逐一点击所有图标按钮无误触；hover-only 操作在触摸下可达。

### 主题 E — 弹窗与软键盘（P1，工作量 M）
- **E1** 协调断点：把 modal 的 640/860px 媒体查询与 768px 主断点对齐，消除中间地带样式冲突
  （统一在 768px 切换为底部 sheet 全宽）。
- **E2** 软键盘遮挡：底部 sheet 弹窗高度改用 `100dvh` 体系并结合
  `interactiveWidget=resizes-content`（viewport meta）或 JS 监听 `visualViewport.resize`
  抬起 footer/输入框，确保聚焦输入时确认按钮可见。
- **E3** 统一 sheet 关闭：所有 modal 在移动端均可点遮罩关闭 + 顶部抓手提示（视觉），
  保留现有关闭按钮。
- 验证项：设置/导入/Token 刷新等长弹窗在 375px 聚焦输入时 footer 按钮不被键盘挡住。

### 主题 F — 物理返回键（P1 / 重设计，工作量 M）
- **F1** 引入轻量「移动端导航栈」：在 `01-core.js` 用 `history.pushState` 为
  「打开抽屉」「进入邮件详情」压入状态；监听 `popstate`：
  返回键优先级 = 关弹窗 > 收抽屉 > 详情回列表 > 默认（离开）。
- **F2** 与现有 `openMobilePanel`/`closeMobilePanels`/`showMobileEmailDetail`/`showEmailList`
  打通，确保状态机一致、不重复入栈、桌面端不介入（`isMobileLayout()` 守卫）。
- 风险：history 状态与浏览器前进/刷新的边界；需保证刷新后不卡在脏状态。以 `state.mobileView` 标记自有状态，非自有状态不拦截。
- 验证项：手机打开抽屉→返回键收抽屉；进详情→返回键回列表；列表态→返回键正常离开。

### 主题 G — 下拉刷新（P2 / 重设计，工作量 M）
- **G1** 在 `#emailList` 顶部实现下拉刷新：touchstart/touchmove 监测顶部下拉距离，
  超阈值显示「释放刷新」指示器，松手调用现有 `refreshEmails()`。
- **G2** 仅 `scrollTop===0` 时启用，配合 `overscroll-behavior: contain` 防误触；
  无邮件账号/桌面端不启用。
- 验证项：列表顶部下拉出现指示器并触发刷新；列表中部滚动不误触发。

### 主题 H — 列表项侧滑操作（P2 / 重设计，工作量 L）
- **H1** 邮件项 `.email-item` 左滑露出「删除」、右滑露出「标记已读」（复用现有
  删除/标记已读 API）；账号项 `.account-item` 左滑露出「删除」。
- **H2** 用 touch 事件 + transform 实现，带回弹与阈值；点击仍进入详情，与现有
  `account-menu`/批量选择模式互斥（选择模式下禁用侧滑）。
- 风险：与纵向滚动的手势冲突、与 `.account-item` 拖拽排序冲突——用主轴判定（横向位移
  显著大于纵向才进入侧滑）规避。
- 验证项：左/右滑出现对应操作并能执行；纵向滚动顺畅不误触；选择模式下侧滑禁用。

### 主题 I — 反馈与加载态（P2，工作量 S-M）
- **I1** 骨架屏：邮件列表/账号列表加载时用骨架占位替换当前 spinner（移动端优先）。
- **I2** 触觉反馈：关键操作（删除、刷新成功、侧滑确认）在支持的设备调用
  `navigator.vibrate()`（特性检测，桌面/不支持则跳过）。
- **I3** `prefers-reduced-motion`：为新增动画（下拉、侧滑、骨架微光）加降级，尊重系统设置。
- 验证项：开启 reduced-motion 时新增动效关闭；列表加载呈现骨架；删除时轻震动（支持设备）。

## 4. 文件改动清单（预估）

| 文件 | 改动 |
|------|------|
| `templates/index.html` | A1 viewport / PWA meta |
| `static/js/index/05-emails.js` | B1/B2/B3 iframe srcdoc viewport+响应式样式、高度自适应 |
| `static/js/index/01-core.js` | F 导航栈/popstate、G 下拉刷新、H 侧滑、I 触觉，及事件绑定 |
| `static/js/index/04-accounts.js` | H 账号项侧滑挂接（如需） |
| `static/css/index/08-responsive.css` | A2/C1/D1-D3/E1-E3 移动端样式；G/H/I 手势与骨架样式 |
| `static/css/index/09-mobile-gestures.css`（可选新建） | 若 08 过大，手势/骨架样式单列；**须在 `bundled_index_css` 列表注册** |
| `static/css/index/06-modals-toast.css` | E1 断点协调（仅移动端段） |

> 是否新建 09 文件在实现阶段按 08 体量决定；若新建，必须同步修改
> `outlook_web/segments/04_routes_groups_accounts.py` 的 CSS 列表。

## 5. 测试与验证策略

无法用真机验证，采用以下替代手段（逐项在计划中落为可勾选验证点）：
- **静态/逻辑核对**：CSS 媒体查询断点连续性、`isMobileLayout()` 守卫覆盖、
  history 状态机分支完备性。
- **浏览器 DevTools 设备模拟**：375×667 / 390×844（含安全区）/ 横屏，逐主题验证项过一遍。
- **构造测试邮件**：宽表格 + 超长 URL + 大图的 HTML 邮件验证 B 主题。
- **桌面回归**：≥769px 下确认三栏布局、批量栏定位、弹窗尺寸与改动前一致（防回退）。
- 失败/无法验证项**显式报告**，不声称已通过。

## 6. 风险与回滚

- **最大风险**：F（history）与 H（侧滑）涉及 JS 行为，可能与现有滚动/拖拽/选择模式冲突。
  缓解：严格 `isMobileLayout()` 守卫 + 主轴手势判定 + 互斥状态检查；每项独立提交便于回滚。
- **桌面回退风险**：所有视觉改动限定在移动媒体查询内，桌面规则零改动。
- **提交粒度**：按主题原子提交（A→I），每提交可单独回滚；先做 P0（A/B/C）跑通验证再推进。

## 7. 实施顺序

P0 优先：A（视口）→ B（正文）→ C（表单）→
P1：D（触控）→ E（弹窗）→ F（返回键）→
P2：G（下拉刷新）→ H（侧滑）→ I（反馈）。
