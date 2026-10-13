#!/bin/zsh
set -e
cd "$(dirname "$0")"
PY="/Users/wuzhangzhang/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3"
if [[ ! -x "$PY" ]]; then PY="python3"; fi
"$PY" src/build.py --vectors
print "向量构建完成。请使用『启动问答网页.command』打开网页；测试题可单独运行 src/evaluate.py --answers。"
