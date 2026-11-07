#!/usr/bin/env sh
# Запуск на Linux/macOS: ./project.sh [команда] — см. python3 run.py help
cd "$(dirname "$0")" || exit 1
if command -v python3 >/dev/null 2>&1; then PY=python3; else PY=python; fi
exec "$PY" run.py "$@"
