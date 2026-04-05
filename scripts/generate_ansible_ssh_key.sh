#!/usr/bin/env bash

set -euo pipefail

KEY_PATH="${1:-$HOME/.ssh/ansible_key}"
KEY_COMMENT="${2:-ansible@$(hostname -s)}"
KEY_TYPE="${KEY_TYPE:-ed25519}"

usage() {
  cat <<'EOF'
Usage:
  generate_ansible_ssh_key.sh [key_path] [comment]

Examples:
  ./scripts/generate_ansible_ssh_key.sh
  ./scripts/generate_ansible_ssh_key.sh ~/.ssh/ansible_key "ansible@control-node"

Environment variables:
  KEY_TYPE   SSH key type to generate. Default: ed25519
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

if ! command -v ssh-keygen >/dev/null 2>&1; then
  echo "ssh-keygen not found" >&2
  exit 1
fi

SSH_DIR="$(dirname "$KEY_PATH")"
PUB_PATH="${KEY_PATH}.pub"

mkdir -p "$SSH_DIR"
chmod 700 "$SSH_DIR"

if [[ -e "$KEY_PATH" || -e "$PUB_PATH" ]]; then
  echo "Refusing to overwrite existing key: $KEY_PATH" >&2
  exit 1
fi

ssh-keygen \
  -t "$KEY_TYPE" \
  -f "$KEY_PATH" \
  -C "$KEY_COMMENT" \
  -N ""

chmod 600 "$KEY_PATH"
chmod 644 "$PUB_PATH"

cat <<EOF
Generated SSH key pair:
  Private: $KEY_PATH
  Public : $PUB_PATH

Use this public key on target hosts:
  ssh-copy-id -i "$PUB_PATH" user@host
EOF
