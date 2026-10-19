#!/bin/bash
set -e

echo "=== Initializing Thesis Workspace ==="

# 1. Create .venv with Python 3.12 via uv
uv venv --python 3.12 .venv

# 2. Activate the newly created virtual environment
source .venv/bin/activate

# 3. Install MQT QMAP and benchmark requirements
echo "Installing MQT QMAP and core dependencies..."
uv pip install mqt.qmap

# 4. Install ZAP dependencies if requirements.txt exists
if [ -f "ZAP/requirements.txt" ]; then
    echo "Installing ZAP requirements..."
    uv pip install -r ZAP/requirements.txt
fi

# 6. Freeze snapshot into root requirements.txt
uv pip freeze > requirements.txt

echo "=== Setup Complete! Environment is ready in .venv/ ==="