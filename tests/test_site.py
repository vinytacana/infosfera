"""Regressões da página pública e dos recortes aprovados."""
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('verificar_site', ROOT / 'scripts' / 'verificar_site.py')
CHECK = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECK)


class SiteTests(unittest.TestCase):
    def setUp(self):
        self.page = CHECK.Pagina()
        self.page.feed((ROOT / 'index.html').read_text())
        self.urls = self.page.verificar()

    def test_links_e_estrutura(self):
        self.assertEqual(self.page.errors, [])
        self.assertEqual(len(self.page.groups), 6)
        self.assertEqual(sorted(len(group) for group in self.page.groups), [1, 1, 1, 1, 2, 2])
        self.assertIn('https://tcgeo.tcero.tc.br/vertice', self.urls)

    def test_recortes_originais_preservados(self):
        expected = json.loads((ROOT / 'tests' / 'fixtures' / 'recortes.json').read_text())
        actual = [url for url in self.urls if '?' in url]
        self.assertCountEqual(actual, [row['url'] for row in expected])

    def test_sem_javascript_e_saero_publico(self):
        self.assertEqual(self.page.scripts, 0)
        self.assertFalse((ROOT / 'script.js').exists())
        self.assertFalse(any('/saero' in url for url in self.urls))


if __name__ == '__main__':
    unittest.main()
