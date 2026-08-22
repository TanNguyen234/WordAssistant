$ErrorActionPreference = "Stop"
python -m pip install --upgrade pip
python -m pip install -e .
wordassistant doctor --json
Write-Host "WordAssistant core is ready. Optional: pip install -e '.[word]'"
