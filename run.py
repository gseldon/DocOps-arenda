#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Единая точка запуска (Windows, Linux, macOS).

    python run.py                    веб-конструктор в браузере
    python run.py --port 8765        то же на заданном порту
    python run.py --no-browser       не открывать браузер автоматически
    python run.py test               автотесты
    python run.py contract [...]     договор из JSON (параметры как у create_contract.py)
    python run.py summary  [...]     сводка из JSON (параметры как у create_summary.py)
"""

import argparse
import os
import sys

if sys.version_info < (3, 8):
    sys.exit('Нужен Python 3.8 или новее, сейчас {}.{}'.format(*sys.version_info[:2]))

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)
sys.path.insert(0, ROOT)

# консоль Windows может быть не в UTF-8
for stream in (sys.stdout, sys.stderr):
    try:
        stream.reconfigure(encoding='utf-8', errors='replace')
    except (AttributeError, ValueError):
        pass


def serve(argv):
    parser = argparse.ArgumentParser(prog='run.py', description='Веб-конструктор договора аренды')
    parser.add_argument('--port', type=int, default=0, help='порт (по умолчанию свободный)')
    parser.add_argument('--no-browser', action='store_true', help='не открывать браузер')
    parser.add_argument('--quiet', action='store_true', help='не печатать запросы')
    args = parser.parse_args(argv)

    import webapp
    try:
        server = webapp.make_server(args.port, quiet=args.quiet)
    except OSError as e:
        sys.exit('Не удалось занять порт {}: {}'.format(args.port, e))
    url = 'http://127.0.0.1:{}/'.format(server.server_address[1])
    print('Конструктор договора: {}'.format(url))
    print('Данные остаются на этом компьютере. Остановить: Ctrl+C', flush=True)
    if not args.no_browser:
        import webbrowser
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\nОстановлено')
    finally:
        server.server_close()
    return 0


def run_tests(argv):
    import unittest
    suite = unittest.defaultTestLoader.discover(os.path.join(ROOT, 'tests'))
    result = unittest.TextTestRunner(verbosity=1 if '-q' in argv else 2).run(suite)
    return 0 if result.wasSuccessful() else 1


def main(argv):
    command = argv[0] if argv and not argv[0].startswith('-') else 'serve'
    rest = argv[1:] if command != 'serve' or (argv and argv[0] == 'serve') else argv
    if command == 'serve':
        return serve(rest)
    if command == 'test':
        return run_tests(rest)
    if command == 'contract':
        import create_contract
        from contract_utils import run_cli
        return run_cli('Создает договор аренды квартиры в формате DOCX', 'doc',
                       'Договор_аренды_квартиры_v', create_contract._build, rest)
    if command == 'summary':
        import create_summary
        from contract_utils import run_cli
        return run_cli('Создает сводку по договору аренды в формате DOCX', os.path.join('doc', 'summary'),
                       'СВОДКА_ДОГОВОРА_v', create_summary._build, rest)
    print(__doc__)
    return 0 if command in ('help', '-h', '--help') else 2


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
