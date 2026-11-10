
#!/usr/bin/env bash

set -euo pipefail

INSTALL_DIR="$HOME/.local/share/pydoctor"
VENV_DIR="$INSTALL_DIR/venv"

LAUNCHER="$HOME/.local/bin/pydoctor"

echo
echo "pyDoctor Uninstaller"
echo "========================================"

if [ ! -d "$INSTALL_DIR" ] && [ ! -L "$LAUNCHER" ]; then
    echo "pyDoctor does not appear to be installed."
    exit 0
fi

echo "Installation directory: $INSTALL_DIR"
echo "Launcher: $LAUNCHER"
echo

read -r -p "Are you sure you want to uninstall pyDoctor? [y/N]: " answer

case "${answer,,}" in
    y|yes)
        ;;
    *)
        echo "Uninstallation cancelled."
        exit 0
        ;;
esac

echo
echo "[1/2] Removing launcher..."

if [ -L "$LAUNCHER" ]; then
    CURRENT_TARGET="$(readlink "$LAUNCHER")"

    if [ "$CURRENT_TARGET" = "$VENV_DIR/bin/pydoctor" ]; then
        rm "$LAUNCHER"
    else
        echo "Warning: Launcher points to another installation."
        echo "Leaving it untouched."
    fi
fi

echo "[2/2] Removing isolated environment..."

if [ -d "$INSTALL_DIR" ]; then
    rm -rf -- "$INSTALL_DIR"
fi

echo
echo "========================================"
echo "pyDoctor has been uninstalled."
echo "Your project files and PYDZ records were not touched."
echo "========================================"
