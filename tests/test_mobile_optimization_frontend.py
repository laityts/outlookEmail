from pathlib import Path
import unittest

ROOT_DIR = Path(__file__).resolve().parents[1]
INDEX_HTML = ROOT_DIR / 'templates' / 'index.html'
LAYOUT_HTML = ROOT_DIR / 'templates' / 'partials' / 'index' / 'layout.html'
EMAILS_JS = ROOT_DIR / 'static' / 'js' / 'index' / '05-emails.js'
CORE_JS = ROOT_DIR / 'static' / 'js' / 'index' / '01-core.js'
RESPONSIVE_CSS = ROOT_DIR / 'static' / 'css' / 'index' / '08-responsive.css'
MOBILE_CSS = ROOT_DIR / 'static' / 'css' / 'index' / '09-mobile.css'
MODALS_CSS = ROOT_DIR / 'static' / 'css' / 'index' / '06-modals-toast.css'
CSS_ROUTE = ROOT_DIR / 'outlook_web' / 'segments' / '04_routes_groups_accounts.py'


class ViewportSafeAreaTests(unittest.TestCase):
    def test_viewport_has_fit_cover(self):
        html = INDEX_HTML.read_text(encoding='utf-8')
        self.assertIn('viewport-fit=cover', html)

    def test_viewport_keeps_user_scalable(self):
        html = INDEX_HTML.read_text(encoding='utf-8')
        self.assertNotIn('user-scalable=no', html)
        self.assertNotIn('maximum-scale=1', html)

    def test_theme_color_meta_present(self):
        html = INDEX_HTML.read_text(encoding='utf-8')
        self.assertIn('name="theme-color"', html)

    def test_navbar_uses_top_safe_area(self):
        css = RESPONSIVE_CSS.read_text(encoding='utf-8')
        self.assertIn('safe-area-inset-top', css)


class MobileScaffoldTests(unittest.TestCase):
    def test_mobile_css_file_exists(self):
        self.assertTrue(MOBILE_CSS.exists())

    def test_mobile_css_registered_in_bundle(self):
        source = CSS_ROUTE.read_text(encoding='utf-8')
        self.assertIn("'09-mobile.css'", source)
        self.assertLess(source.index("'08-responsive.css'"), source.index("'09-mobile.css'"))


class EmailIframeResponsiveTests(unittest.TestCase):
    def test_srcdoc_injects_viewport_meta(self):
        js = EMAILS_JS.read_text(encoding='utf-8')
        self.assertIn('name="viewport"', js)
        self.assertIn('width=device-width', js)

    def test_srcdoc_constrains_wide_elements(self):
        js = EMAILS_JS.read_text(encoding='utf-8')
        self.assertIn('max-width: 100%', js)
        self.assertIn('overflow-x: auto', js)
        self.assertIn('word-break', js)

    def test_iframe_min_height_relaxed_for_short_mail(self):
        js = EMAILS_JS.read_text(encoding='utf-8')
        self.assertNotIn('Math.max(height + 100, 600)', js)

    def test_fullscreen_clone_preserves_document(self):
        js = EMAILS_JS.read_text(encoding='utf-8')
        self.assertIn('documentElement.outerHTML', js)

    def test_wide_table_scoped_to_mobile_in_iframe(self):
        js = EMAILS_JS.read_text(encoding='utf-8')
        self.assertIn('@media (max-width: 768px)', js)


class FormZoomTests(unittest.TestCase):
    def test_mobile_form_controls_use_16px(self):
        css = RESPONSIVE_CSS.read_text(encoding='utf-8')
        self.assertRegex(css, r'\.form-input[^}]*font-size:\s*16px')
        self.assertRegex(css, r'\.form-select[^}]*font-size:\s*16px')
        self.assertRegex(css, r'\.form-textarea[^}]*font-size:\s*16px')


class TouchTargetTests(unittest.TestCase):
    def test_mobile_panel_action_btn_enlarged(self):
        css = RESPONSIVE_CSS.read_text(encoding='utf-8')
        self.assertRegex(css, r'\.panel-action-btn[^}]*width:\s*44px')
        self.assertRegex(css, r'\.panel-action-btn[^}]*height:\s*44px')

    def test_mobile_account_menu_trigger_enlarged(self):
        css = RESPONSIVE_CSS.read_text(encoding='utf-8')
        self.assertRegex(css, r'\.account-menu-trigger[^}]*width:\s*4[0-4]px')

    def test_mobile_modal_close_min_size(self):
        css = RESPONSIVE_CSS.read_text(encoding='utf-8')
        self.assertIn('.modal-close', css)


class ModalKeyboardTests(unittest.TestCase):
    def test_visual_viewport_listener_present(self):
        js = CORE_JS.read_text(encoding='utf-8')
        self.assertIn('visualViewport', js)
        self.assertIn('--keyboard-inset', js)

    def test_modal_uses_keyboard_inset(self):
        css = MODALS_CSS.read_text(encoding='utf-8')
        self.assertIn('--keyboard-inset', css)

    def test_modal_content_full_width_on_mobile(self):
        css = RESPONSIVE_CSS.read_text(encoding='utf-8')
        self.assertRegex(css, r'\.modal-content[^}]*width:\s*100%\s*!important')


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

    def test_pull_indicator_is_sibling_not_child_of_email_list(self):
        # 指示器必须是 #emailList 的兄弟节点，而非子节点；
        # 否则首次 loadEmails 的 container.innerHTML 会永久销毁该节点，使下拉视觉反馈静默失效。
        html = LAYOUT_HTML.read_text(encoding='utf-8')
        indicator_pos = html.index('id="pullRefreshIndicator"')
        list_open = html.index('id="emailList"')
        list_close = html.index('</div>', list_open)
        # 指示器不应位于 #emailList 起始标签与其首个闭合 </div> 之间（即不是直接子节点占位）
        self.assertFalse(
            list_open < indicator_pos < list_close,
            '#pullRefreshIndicator 不应作为 #emailList 的子节点，会被 innerHTML 覆盖销毁',
        )

    def test_pull_indicator_not_reacquired_inside_email_list(self):
        # JS 不应依赖指示器位于 #emailList 内，setupPullToRefresh 一次查询的引用须稳定。
        js = CORE_JS.read_text(encoding='utf-8')
        start = js.index('function setupPullToRefresh')
        end = js.index('\n        }\n', start)
        self.assertIn("getElementById('pullRefreshIndicator')", js[start:end])


class SwipeActionTests(unittest.TestCase):
    def test_swipe_attach_function_present(self):
        js = CORE_JS.read_text(encoding='utf-8')
        self.assertIn('function attachSwipeActions', js)

    def test_swipe_axis_lock_logic(self):
        js = CORE_JS.read_text(encoding='utf-8')
        start = js.index('function attachSwipeActions')
        end = js.index('\n        }\n', start)
        seg = js[start:end]
        self.assertIn('Math.abs', seg)
        self.assertIn('isMobileLayout', seg)

    def test_swipe_styles_present(self):
        css = MOBILE_CSS.read_text(encoding='utf-8')
        self.assertIn('is-swiping', css)

    def test_swipe_action_hint_removed(self):
        css = MOBILE_CSS.read_text(encoding='utf-8')
        self.assertNotIn('swipe-action-hint', css)

    def test_email_swipe_guards_batch_selection(self):
        js = EMAILS_JS.read_text(encoding='utf-8')
        start = js.index('attachSwipeActions(el,')
        # 守卫代码须在侧滑挂载块内引用批量选择集变量
        seg = js[start:start + 400]
        self.assertIn('selectedEmailIds', seg)

    def test_swipe_click_suppression(self):
        js = CORE_JS.read_text(encoding='utf-8')
        start = js.index('function attachSwipeActions')
        end = js.index('\n        }\n', start)
        seg = js[start:end]
        # click 监听与侧滑时间标记须在 attachSwipeActions 函数体内
        self.assertIn("addEventListener('click'", seg)
        self.assertIn('swipeActionAt', seg)


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
