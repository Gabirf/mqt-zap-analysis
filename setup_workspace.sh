#!/bin/bash
set -e

echo "=== Initializing Thesis Workspace ==="

if [ -d ".git" ]; then
    echo "--> Syncing Git submodules (ZAP and QMAP)..."
    git submodule update --init --recursive
fi

echo "--> Creating Python 3.12 virtual environment..."
rm -rf .venv
uv venv --python 3.12 .venv
source .venv/bin/activate

if [ -f "requirements.txt" ]; then
    echo "--> Restoring dependencies from requirements.txt..."
    uv pip install -r requirements.txt
else
    echo "--> Initial run: Installing base quantum stack and build tools..."
    uv pip install qiskit networkx matplotlib mqt.bench setuptools-scm scikit-build-core nanobind cmake ninja psutil
fi

echo "--> Installing quantum dependencies..."
uv pip install qiskit networkx matplotlib mqt.bench

if [ -d "QMAP" ]; then
    echo "--> Compiling and installing editable QMAP from ./QMAP..."
    # Let uv isolate build requirements (resolves scikit-build-core and vcs_versioning automatically)
    uv pip install -e QMAP
else
    echo "--> Warning: QMAP directory not found! Installing pre-built wheel..."
    uv pip install mqt.qmap
    SITE_PACKAGES=$(.venv/bin/python -c "import site; print(site.getsitepackages()[0])")
    if [ -d "$SITE_PACKAGES/mqt/qmap" ]; then
        cp -f QMAP/python/mqt/qmap/*.py "$SITE_PACKAGES/mqt/qmap/" 2>/dev/null || true
    fi
fi

if [ -f "ZAP/requirements.txt" ]; then
    echo "--> Installing ZAP submodule dependencies..."
    uv pip install -r ZAP/requirements.txt
fi

echo "--> Freezing dependencies to requirements.txt..."
uv pip freeze > requirements.txt

echo "--> Verifying installation..."
python -c "
import qiskit
import networkx
try:
    from mqt.qmap.na.zoned import ZonedNeutralAtomArchitecture
    print('  [OK] QMAP and ZonedNeutralAtomArchitecture loaded successfully!')
except Exception as e:
    print('  [FAIL] QMAP import failed:', e)
"

echo "=== Setup Complete! Environment is ready in .venv/ ==="