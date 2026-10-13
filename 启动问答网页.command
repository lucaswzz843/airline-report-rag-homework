#!/bin/zsh
set -e
cd "$(dirname "$0")"
PY="/Users/wuzhangzhang/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3"
if [[ ! -x "$PY" ]]; then PY="python3"; fi
open "http://127.0.0.1:8765/"
"$PY" src/server.py
