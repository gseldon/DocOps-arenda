# -*- coding: utf-8 -*-
"""Тесты локального веб-сервера (webapp.py)."""

import http.client
import io
import json
import os
import sys
import threading
import unittest
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import webapp  # noqa: E402

EXAMPLE = os.path.join(ROOT, 'example', 'contract_data.example.json')


def example():
    with open(EXAMPLE, encoding='utf-8') as f:
        return json.load(f)


class WebApp(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = webapp.make_server(0, quiet=True)
        cls.port = cls.server.server_address[1]
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def request(self, method, path, body=None, headers=None):
        conn = http.client.HTTPConnection('127.0.0.1', self.port, timeout=10)
        hdrs = {'Host': '127.0.0.1:{}'.format(self.port)}
        if body is not None and not isinstance(body, bytes):
            body = json.dumps(body, ensure_ascii=False).encode('utf-8')
            hdrs['Content-Type'] = 'application/json'
        hdrs.update(headers or {})
        conn.request(method, path, body=body, headers=hdrs)
        resp = conn.getresponse()
        data = resp.read()
        conn.close()
        return resp, data

    def test_static(self):
        for path, marker in (('/', b'<!doctype html>'), ('/app.js', b'use strict'), ('/style.css', b':root')):
            resp, data = self.request('GET', path)
            self.assertEqual(resp.status, 200, path)
            self.assertIn(marker, data)
            self.assertIn("default-src 'self'", resp.getheader('Content-Security-Policy'))
        resp, data = self.request('GET', '/example.json')
        self.assertEqual(json.loads(data.decode('utf-8')), example())

    def test_no_path_traversal(self):
        for path in ('/../webapp.py', '/webapp.py', '/web/app.js', '/%2e%2e/run.py', '/contract_data.json'):
            resp, _ = self.request('GET', path)
            self.assertEqual(resp.status, 404, path)

    def test_contract_docx(self):
        resp, data = self.request('POST', '/api/contract', example())
        self.assertEqual(resp.status, 200)
        self.assertEqual(resp.getheader('Content-Type'), webapp.DOCX_MIME)
        self.assertIn("filename*=UTF-8''", resp.getheader('Content-Disposition'))
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            self.assertIsNone(z.testzip())
            text = z.read('word/document.xml').decode('utf-8')
        for expected in ('Серийный номер', 'MW20K-4410', '2 шт.', 'исправна'):
            self.assertIn(expected, text)

    def test_summary_docx(self):
        resp, data = self.request('POST', '/api/summary', example())
        self.assertEqual(resp.status, 200)
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            self.assertIn('Сводка', z.read('docProps/core.xml').decode('utf-8'))

    def test_validation_errors(self):
        data = example()
        data['bank_details']['bik'] = '123'
        data['inventory'][0]['quantity'] = 0
        resp, body = self.request('POST', '/api/contract', data)
        self.assertEqual(resp.status, 422)
        paths = {e['path'] for e in json.loads(body.decode('utf-8'))['errors']}
        self.assertIn('bank_details.bik', paths)
        self.assertIn('inventory[0].quantity', paths)

        resp, body = self.request('POST', '/api/validate', example())
        self.assertEqual(resp.status, 200)
        self.assertEqual(json.loads(body.decode('utf-8')), {'errors': []})

    def test_bad_requests(self):
        resp, _ = self.request('POST', '/api/contract', b'{', {'Content-Type': 'application/json'})
        self.assertEqual(resp.status, 400)
        resp, _ = self.request('POST', '/api/contract', b'{}', {'Content-Type': 'text/plain'})
        self.assertEqual(resp.status, 415)
        # сервер отказывает по заголовку Content-Length, не читая тело
        conn = http.client.HTTPConnection('127.0.0.1', self.port, timeout=10)
        conn.putrequest('POST', '/api/contract', skip_host=True)
        conn.putheader('Host', '127.0.0.1:{}'.format(self.port))
        conn.putheader('Content-Type', 'application/json')
        conn.putheader('Content-Length', str(webapp.MAX_BODY + 1))
        conn.endheaders()
        resp = conn.getresponse()
        self.assertEqual(resp.status, 413)
        conn.close()
        resp, _ = self.request('POST', '/api/unknown', {})
        self.assertEqual(resp.status, 404)

    def test_host_and_origin_checks(self):
        resp, _ = self.request('GET', '/', headers={'Host': 'evil.example:{}'.format(self.port)})
        self.assertEqual(resp.status, 403)
        resp, _ = self.request('POST', '/api/contract', example(), {'Origin': 'http://evil.example'})
        self.assertEqual(resp.status, 403)
        resp, _ = self.request('POST', '/api/validate', example(),
                               {'Origin': 'http://localhost:{}'.format(self.port),
                                'Host': 'localhost:{}'.format(self.port)})
        self.assertEqual(resp.status, 200)

    def test_split_errors(self):
        self.assertEqual(webapp.split_errors(['a.b: плохо', 'без пути']),
                         [{'path': 'a.b', 'message': 'плохо'}, {'path': '', 'message': 'без пути'}])


if __name__ == '__main__':
    unittest.main()
