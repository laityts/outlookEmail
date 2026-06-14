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
        self.assertLess(source.index("'08-responsive.css'"), source.index("'09-mobile.css'"))
