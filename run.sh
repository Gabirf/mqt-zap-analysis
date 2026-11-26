#!/bin/bash
set -e

# Always run from the workspace directory containing this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Ensure .venv exists before running
if [ ! -d ".venv" ]; then
    echo "Error: .venv not found. Run ./setup.sh first!"
    exit 1
fi

# Ensure workspace root, src/, and ZAP/ are in PYTHONPATH:
# - $SCRIPT_DIR: for 'from ZAP.zap.zap import Zap'
# - $SCRIPT_DIR/src: for 'from config import *' and 'import utils'
# - $SCRIPT_DIR/ZAP: for ZAP internal imports like 'from zap.scheduler...'
export PYTHONPATH="$SCRIPT_DIR:$SCRIPT_DIR/src:$SCRIPT_DIR/ZAP:${PYTHONPATH:-}"

# Run benchmarks using uv targeting the local .venv without requiring a pyproject.toml
uv run --no-project src/benchmarks.py "$@"
