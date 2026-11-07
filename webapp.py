# -*- coding: utf-8 -*-
"""
Локальный веб-сервер конструктора договора.

Слушает только 127.0.0.1. Ничего не пишет на диск и не логирует содержимое запросов:
данные приходят из браузера, документ собирается в памяти и сразу отдаётся обратно.
"""

import io
import json
import os
import re
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import quote

import contract_utils as cu
import create_contract
import create_summary

WEB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'web')
MAX_BODY = 1024 * 1024  # 1 МБ
DOCX_MIME = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'

# только эти файлы отдаются как статика
STATIC = {
    '/': ('index.html', 'text/html; charset=utf-8'),
    '/index.html': ('index.html', 'text/html; charset=utf-8'),
    '/style.css': ('style.css', 'text/css; charset=utf-8'),
    '/app.js': ('app.js', 'text/javascript; charset=utf-8'),
    '/example.json': (None, 'application/json; charset=utf-8'),
}
EXAMPLE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            'example', 'contract_data.example.json')

DOCUMENTS = {
    '/api/contract': (create_contract._build, 'Договор_аренды_квартиры'),
    '/api/summary': (create_summary._build, 'Сводка_договора'),
}

_ERROR_RE = re.compile(r'^([\w.\[\]]+): (.*)$', re.S)


def split_errors(errors):
    """'path: message' -> [{'path', 'message'}]; строки без пути получают path ''."""
    result = []
    for e in errors:
        m = _ERROR_RE.match(e)
        result.append({'path': m.group(1), 'message': m.group(2)} if m
                      else {'path': '', 'message': e})
    return result


def build_document(builder, data):
    """Собирает DOCX в память. Возвращает bytes."""
    buf = io.BytesIO()
    builder(cu.with_defaults(data), buf)
    return buf.getvalue()


class Handler(BaseHTTPRequestHandler):
    server_version = 'DocOps-arenda'
    sys_version = ''

    # --- служебное -------------------------------------------------------

    def log_message(self, fmt, *args):
        # только метод, путь и код, без содержимого запросов
        pass

    def log_request(self, code='-', size='-'):
        if self.server.quiet:
            return
        print('{} {} {}'.format(self.command, self.path.split('?')[0], code))

    def _allowed_hosts(self):
        port = self.server.server_address[1]
        return {'127.0.0.1:{}'.format(port), 'localhost:{}'.format(port)}

    def _host_ok(self):
        return (self.headers.get('Host') or '') in self._allowed_hosts()

    def _origin_ok(self):
        origin = self.headers.get('Origin')
        if origin is None:
            return True
        return origin in {'http://' + h for h in self._allowed_hosts()}

    def _send(self, code, body, ctype, extra=None):
        self.send_response(code)
        self.send_header('Content-Type', ctype)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Referrer-Policy', 'no-referrer')
        self.send_header('Content-Security-Policy',
                         "default-src 'self'; img-src 'self' data:; style-src 'self'; "
                         "script-src 'self'; connect-src 'self'; frame-ancestors 'none'")
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        if self.command != 'HEAD':
            self.wfile.write(body)

    def _json(self, code, obj):
        self._send(code, json.dumps(obj, ensure_ascii=False).encode('utf-8'),
                   'application/json; charset=utf-8')

    # --- GET -------------------------------------------------------------

    def do_GET(self):
        if not self._host_ok():
            return self._json(403, {'error': 'host'})
        path = self.path.split('?')[0]
        entry = STATIC.get(path)
        if entry is None:
            return self._json(404, {'error': 'not found'})
        name, ctype = entry
        filename = EXAMPLE_FILE if name is None else os.path.join(WEB_DIR, name)
        try:
            with open(filename, 'rb') as f:
                body = f.read()
        except OSError:
            return self._json(404, {'error': 'not found'})
        self._send(200, body, ctype)

    do_HEAD = do_GET

    # --- POST ------------------------------------------------------------

    def _read_json(self):
        if (self.headers.get('Content-Type') or '').split(';')[0].strip() != 'application/json':
            self._json(415, {'error': 'ожидается application/json'})
            return None
        try:
            length = int(self.headers.get('Content-Length') or 0)
        except ValueError:
            length = -1
        if length < 0 or length > MAX_BODY:
            self._json(413, {'error': 'слишком большой запрос'})
            return None
        try:
            return json.loads(self.rfile.read(length).decode('utf-8'))
        except (UnicodeDecodeError, ValueError):
            self._json(400, {'errors': [{'path': '', 'message': 'некорректный JSON'}]})
            return None

    def do_POST(self):
        if not self._host_ok() or not self._origin_ok():
            return self._json(403, {'error': 'origin'})
        path = self.path.split('?')[0]
        if path != '/api/validate' and path not in DOCUMENTS:
            return self._json(404, {'error': 'not found'})
        data = self._read_json()
        if data is None:
            return
        errors = cu.validate(data)
        if path == '/api/validate':
            return self._json(200, {'errors': split_errors(errors)})
        if errors:
            return self._json(422, {'errors': split_errors(errors)})

        builder, prefix = DOCUMENTS[path]
        try:
            body = build_document(builder, data)
        except Exception as exc:  # данные прошли проверку, но сборка упала
            return self._json(500, {'errors': [{'path': '', 'message': 'ошибка сборки: {}'.format(exc)}]})
        name = '{}_{}.docx'.format(prefix, datetime.now().strftime('%Y-%m-%d_%H-%M'))
        self._send(200, body, DOCX_MIME, {
            'Content-Disposition': "attachment; filename=\"document.docx\"; filename*=UTF-8''{}"
                                   .format(quote(name)),
        })


def make_server(port=0, quiet=False):
    server = ThreadingHTTPServer(('127.0.0.1', port), Handler)
    server.quiet = quiet
    return server
