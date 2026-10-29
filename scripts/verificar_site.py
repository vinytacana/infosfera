#!/usr/bin/env python3
"""Verifica a página de links sem dependências ou acesso à rede."""
from html.parser import HTMLParser
from pathlib import Path
import re
from urllib.parse import parse_qs, urlsplit

ROOT = Path(__file__).resolve().parents[1]


class Pagina(HTMLParser):
    def __init__(self, root=ROOT):
        super().__init__()
        self.root = root
        self.ids = []
        self.references = []
        self.groups = []
        self.links = []
        self.current = None
        self.errors = []
        self.h1 = 0
        self.scripts = 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        classes = a.get('class', '').split()
        if 'id' in a:
            self.ids.append(a['id'])
        for attr in ('aria-controls', 'aria-labelledby'):
            self.references.extend(a.get(attr, '').split())
        if tag == 'h1':
            self.h1 += 1
        if tag == 'script':
            self.scripts += 1
        if tag == 'li' and 'link-group' in classes:
            self.current = []
            self.groups.append(self.current)
        if tag == 'a':
            href = a.get('href', '')
            link = {'url': href, 'primary': 'application-link' in classes}
            self.links.append(link)
            if self.current is not None:
                self.current.append(link)
            try:
                parsed = urlsplit(href)
                valid = (parsed.scheme == 'https' and parsed.hostname
                         and not parsed.username and not parsed.password
                         and not re.search(r'\s|%(?![0-9a-fA-F]{2})', href))
            except ValueError:
                valid = False
            if not valid:
                self.errors.append(f'URL vazia, malformada ou não HTTPS: {href}')
            if a.get('target') != '_blank' or not {'noopener', 'noreferrer'} <= set(a.get('rel', '').split()):
                self.errors.append(f'Link externo sem proteção ou nova aba: {href}')
        if tag in ('link', 'img'):
            asset = a.get('src' if tag == 'img' else 'href', '')
            if not asset or asset.startswith(('/', 'http:', 'https:')) or not (self.root / asset).is_file():
                self.errors.append(f'Asset ausente ou sem caminho relativo: {asset}')

    def handle_endtag(self, tag):
        if tag == 'li':
            self.current = None

    def verificar(self):
        if len(self.ids) != len(set(self.ids)):
            self.errors.append('Há IDs duplicados.')
        if set(self.references) - set(self.ids):
            self.errors.append('Há referências ARIA sem destino.')
        if self.h1 != 1 or not self.groups:
            self.errors.append('A página precisa de um h1 e uma lista de aplicações.')
        if self.scripts:
            self.errors.append('A página de links não deve carregar JavaScript.')
        for group in self.groups:
            primary = [link for link in group if link['primary']]
            if len(primary) != 1:
                self.errors.append('Cada aplicação precisa de exatamente um acesso principal.')
                continue
            try:
                app = urlsplit(primary[0]['url'])
                for link in group:
                    parsed = urlsplit(link['url'])
                    if (parsed.netloc, parsed.path) != (app.netloc, app.path):
                        self.errors.append('Visualização alternativa aponta para outra aplicação.')
            except ValueError:
                pass  # A URL malformada já foi identificada durante a leitura.
        urls = [link['url'] for link in self.links]
        if len(urls) != len(set(urls)):
            self.errors.append('Há links idênticos duplicados.')
        for url in urls:
            try:
                params = parse_qs(urlsplit(url).query, keep_blank_values=True)
                if not {'centro', 'zoom', 'camadas'} & params.keys():
                    continue
                center = [float(n) for n in params['centro'][0].split(',')]
                valid = (len(center) == 2 and -180 <= center[0] <= 180
                         and -90 <= center[1] <= 90 and 0 <= float(params['zoom'][0]) <= 24
                         and bool(params['camadas'][0]))
            except (KeyError, ValueError):
                valid = False
            if not valid:
                self.errors.append(f'Parâmetros do recorte ausentes ou inválidos: {url}')
        return urls


if __name__ == '__main__':
    page = Pagina()
    page.feed((ROOT / 'index.html').read_text())
    urls = page.verificar()
    if page.errors:
        raise SystemExit('\n'.join(page.errors))
    print(f'OK: {len(page.groups)} aplicações, {len(urls)} links únicos; URLs, recortes, assets e proteção dos links válidos; sem JavaScript.')
