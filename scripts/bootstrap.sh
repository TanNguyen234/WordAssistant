#!/usr/bin/env sh
set -eu
python -m pip install --upgrade pip
python -m pip install -e .
wordassistant doctor --json
printf '%s\n' "WordAssistant core is ready. Optional: pip install -e '.[word]'"
