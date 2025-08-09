#!/bin/bash
set -euo pipefail

# リポジトリルート
REPO_ROOT="$(git rev-parse --show-toplevel)"
HOOKS_DIR="$REPO_ROOT/.git/hooks"
SRC_DIR="$REPO_ROOT/scripts/hooks"

mkdir -p "$HOOKS_DIR"

install_hook() {
  local name="$1"
  cp "$SRC_DIR/$name" "$HOOKS_DIR/$name"
  chmod +x "$HOOKS_DIR/$name"
  echo "Installed git hook: $name"
}

install_hook pre-commit
install_hook post-commit
# pre-push は任意
if [ -f "$SRC_DIR/pre-push" ]; then
  install_hook pre-push
fi

echo "Git hooks installed successfully."