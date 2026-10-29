#!/usr/bin/env python3
"""Gera QR Code PNG + SVG para uma URL HTTPS publicada."""
import argparse
import ipaddress
import re
from pathlib import Path
from urllib.parse import urlparse


def validar_url(url):
    """Valida o destino informado; a publicação precisa ser confirmada no Pages."""
    if re.search(r'\s|[\x00-\x1f\x7f]', url):
        raise ValueError('A URL não pode conter espaços ou caracteres de controle.')
    try:
        parsed = urlparse(url)
        hostname = (parsed.hostname or '').lower().rstrip('.')
        port = parsed.port
    except ValueError as error:
        raise ValueError('Informe uma URL HTTPS válida.') from error
    if parsed.scheme != 'https' or not hostname or parsed.username or parsed.password:
        raise ValueError('Informe a URL HTTPS pública do site, sem credenciais.')
    if port not in (None, 443):
        raise ValueError('Use o endereço HTTPS público, sem porta de desenvolvimento.')
    if hostname in ('github.com', 'www.github.com'):
        raise ValueError('Use a URL do site no GitHub Pages, não a página do repositório.')
    try:
        address = ipaddress.ip_address(hostname)
    except ValueError:
        if '.' not in hostname or not all(re.fullmatch(r'[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?', part) for part in hostname.split('.')):
            raise ValueError('Informe um nome de domínio público válido.') from None
        if hostname.endswith(('.localhost', '.local', '.test', '.invalid', '.example')) or hostname in ('example.com', 'example.org', 'example.net'):
            raise ValueError('Endereços locais ou de exemplo não são destinos de divulgação.')
    else:
        if not address.is_global:
            raise ValueError('Endereços de rede local não são destinos de divulgação.')
    return url


def main():
    parser = argparse.ArgumentParser(description='Gera QR Code para seu site no GitHub Pages')
    parser.add_argument('url', help='URL real publicada, incluindo https://')
    parser.add_argument('--output', default='qr-site', help='Prefixo dos arquivos (sem extensão)')
    parser.add_argument('--force', action='store_true', help='Permite substituir arquivos QR existentes')
    args = parser.parse_args()
    try:
        validar_url(args.url)
    except ValueError as error:
        parser.error(str(error))

    prefix = Path(args.output)
    png = Path(f'{prefix}.png')
    svg = Path(f'{prefix}.svg')
    if not args.force and (png.exists() or svg.exists()):
        parser.error('O destino já existe. Escolha outro --output ou use --force.')
    if not prefix.parent.is_dir():
        parser.error('A pasta de saída não existe. Crie-a antes de gerar o QR Code.')

    try:
        import qrcode
        import qrcode.image.svg
    except ImportError:
        parser.error('Instale a dependência com: python -m pip install -r scripts/requirements-qr.txt')

    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_H, box_size=18, border=4)
    qr.add_data(args.url)
    qr.make(fit=True)
    qr.make_image(fill_color='#071d1b', back_color='white').save(png)
    qr_svg = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_H,
                          image_factory=qrcode.image.svg.SvgPathImage, border=4)
    qr_svg.add_data(args.url)
    qr_svg.make(fit=True)
    qr_svg.make_image().save(svg)
    print(f'QR Code: {png} e {svg}')
    print(f'Destino: {args.url}')


if __name__ == '__main__':
    main()
