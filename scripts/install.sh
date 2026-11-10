
#!/usr/bin/env bash

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

INSTALL_DIR="$HOME/.local/share/pydoctor"
VENV_DIR="$INSTALL_DIR/venv"
BIN_DIR="$HOME/.local/bin"
LAUNCHER="$BIN_DIR/pydoctor"

PYTHON="${PYTHON:-python3}"

echo
echo "pyDoctor Installer"
echo "========================================"

if ! command -v "$PYTHON" >/dev/null 2>&1; then
    echo "Error: Python was not found."
    echo "Install Python 3.11 or newer first."
    exit 1
fi

if ! "$PYTHON" -c \
    'import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)'
then
    echo "Error: pyDoctor requires Python 3.11 or newer."
    exit 1
fi

echo "[1/4] Checking installation directories..."

mkdir -p "$INSTALL_DIR"
mkdir -p "$BIN_DIR"

echo "[2/4] Creating isolated environment..."

if [ ! -x "$VENV_DIR/bin/python" ]; then
    "$PYTHON" -m venv "$VENV_DIR"
fi

if ! "$VENV_DIR/bin/python" -c \
    'import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)'
then
    echo "Error: Existing pyDoctor environment uses an incompatible Python."
    echo "Run the uninstaller and install again with Python 3.11 or newer."
    exit 1
fi

echo "[3/4] Installing pyDoctor..."

"$VENV_DIR/bin/python" -m pip install --upgrade "$PROJECT_ROOT"

echo "[4/4] Creating command launcher..."

if [ -e "$LAUNCHER" ] && [ ! -L "$LAUNCHER" ]; then
    echo "Error: $LAUNCHER already exists and is not a symlink."
    echo "Refusing to overwrite it."
    exit 1
fi

if [ -L "$LAUNCHER" ]; then
    CURRENT_TARGET="$(readlink "$LAUNCHER")"

    if [ "$CURRENT_TARGET" != "$VENV_DIR/bin/pydoctor" ]; then
        echo "Error: An unrelated pydoctor launcher already exists."
        echo "Refusing to replace it."
        exit 1
    fi
fi

ln -sfn "$VENV_DIR/bin/pydoctor" "$LAUNCHER"

echo
echo "========================================"
echo "pyDoctor installed successfully!"
echo
echo "Installation: $INSTALL_DIR"
echo "Launcher:     $LAUNCHER"
echo

case ":$PATH:" in
    *":$BIN_DIR:"*)
        echo "You can now run: pydoctor --help"
        ;;
    *)
        echo "Add the following directory to your PATH:"
        echo "$BIN_DIR"
        echo
        echo "For Bash, add this to ~/.bashrc:"
        echo 'export PATH="$HOME/.local/bin:$PATH"'
        echo
        echo "Then reload your shell:"
        echo "source ~/.bashrc"
        ;;
esac

echo "========================================"
