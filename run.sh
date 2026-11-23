#!/bin/bash
set -e

# Ensure .venv exists before running
if [ ! -d ".venv" ]; then
    echo "Error: .venv not found. Run ./setup.sh first!"
    exit 1
fi

# Activate the existing virtual environment
source .venv/bin/activate

# Run whatever python script or arguments you pass to ./run.sh
python ./src/benchmarks.py