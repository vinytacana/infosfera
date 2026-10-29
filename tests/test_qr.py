"""Testes do utilitário de QR; não geram um QR de divulgação do Vértice."""
import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET


SCRIPT = Path(__file__).resolve().parents[1] / 'scripts' / 'gerar_qr.py'
SPEC = importlib.util.spec_from_file_location('gerar_qr', SCRIPT)
QR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(QR)


class QRTests(unittest.TestCase):
    def test_public_https(self):
        url = 'https://docs.python.org/3/'
        self.assertEqual(QR.validar_url(url), url)

    def test_rejects_local_examples_and_repository(self):
        for url in (
            'file:///tmp/index.html', 'http://docs.python.org/3/',
            'https://localhost/', 'https://127.0.0.1/', 'https://10.0.0.2/',
            'https://[::1]/', 'https://preview.local/', 'https://preview.test/',
            'https://example.com/', 'https://github.com/vinytacana/infosfera',
        ):
            with self.subTest(url=url), self.assertRaises(ValueError):
                QR.validar_url(url)

    def test_rejects_malformed_and_credentials(self):
        for url in (
            'https://bad..host/', 'https://-bad.host/', 'https://docs.python.org:abc/',
            'https://docs.python.org:8765/', 'https://u:p@docs.python.org/',
            'https://docs.python.org/with space', 'https://docs.python.org/\n',
        ):
            with self.subTest(url=url), self.assertRaises(ValueError):
                QR.validar_url(url)

    def test_creates_png_svg_and_protects_existing_files(self):
        with tempfile.TemporaryDirectory() as directory:
            prefix = Path(directory) / 'qr.v1'
            command = [sys.executable, str(SCRIPT), 'https://docs.python.org/3/', '--output', str(prefix)]
            generated = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(generated.returncode, 0, generated.stderr)
            png = Path(f'{prefix}.png')
            svg = Path(f'{prefix}.svg')
            self.assertTrue(png.read_bytes().startswith(b'\x89PNG\r\n\x1a\n'))
            self.assertEqual(ET.parse(svg).getroot().tag, '{http://www.w3.org/2000/svg}svg')
            original = png.read_bytes()
            refused = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(refused.returncode, 2)
            self.assertEqual(png.read_bytes(), original)
            forced = subprocess.run(command + ['--force'], capture_output=True, text=True)
            self.assertEqual(forced.returncode, 0, forced.stderr)

    def test_missing_output_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run(
                [sys.executable, str(SCRIPT), 'https://docs.python.org/3/', '--output', str(Path(directory) / 'missing' / 'qr')],
                capture_output=True, text=True,
            )
            self.assertEqual(result.returncode, 2)
            self.assertIn('pasta de saída', result.stderr)


if __name__ == '__main__':
    unittest.main()
