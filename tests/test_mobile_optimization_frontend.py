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
