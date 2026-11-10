
#!/usr/bin/env bash

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "$PROJECT_ROOT"

echo
echo "pyDoctor Package Builder"
echo "========================================"

PYTHON="${PYTHON:-python3}"

if ! command -v "$PYTHON" >/dev/null 2>&1; then
    echo "Error: Python was not found."
    exit 1
fi

if ! "$PYTHON" -c \
    'import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)'
then
    echo "Error: Python 3.11 or newer is required."
    exit 1
fi

echo "[1/3] Checking build dependencies..."

if ! "$PYTHON" -m build --version >/dev/null 2>&1; then
    echo "Build module not found."
    echo "Install development dependencies first:"
    echo 'pip install -e ".[dev]"'
    exit 1
fi

echo "[2/3] Building distributions..."

"$PYTHON" -m build --outdir dist

echo "[3/3] Generated distributions:"

find dist -maxdepth 1 -type f -print

echo
echo "========================================"
echo "Build completed successfully."
echo "Output directory: $PROJECT_ROOT/dist"
echo "========================================"
