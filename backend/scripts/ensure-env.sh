#!/usr/bin/env bash
set -euo pipefail

ENV_FILE="$(dirname "$0")/../.env"
TMPL_FILE="$(dirname "$0")/../.env.tmpl"

# If no .env exists, copy from template
if [ ! -f "$ENV_FILE" ]; then
  echo "No .env found — creating from template..."
  cp "$TMPL_FILE" "$ENV_FILE"
fi

# Check for a valid ANTHROPIC_API_KEY
KEY=$(grep -E '^ANTHROPIC_API_KEY=' "$ENV_FILE" | cut -d= -f2- | xargs)

if [ -z "$KEY" ] || [ "$KEY" = "sk-ant-..." ]; then
  echo ""
  echo "An Anthropic API key is required."
  echo "Get one at: https://console.anthropic.com/"
  echo ""
  read -rp "Paste your API key (sk-ant-...): " KEY

  if [[ ! "$KEY" == sk-ant-* ]]; then
    echo "Error: key must start with 'sk-ant-'. Aborting."
    exit 1
  fi

  # Replace the placeholder or existing key
  if grep -q '^ANTHROPIC_API_KEY=' "$ENV_FILE"; then
    sed -i.bak "s|^ANTHROPIC_API_KEY=.*|ANTHROPIC_API_KEY=$KEY|" "$ENV_FILE"
    rm -f "$ENV_FILE.bak"
  else
    echo "ANTHROPIC_API_KEY=$KEY" >> "$ENV_FILE"
  fi

  echo "API key saved to $ENV_FILE"
elif [[ ! "$KEY" == sk-ant-* ]]; then
  echo "Warning: ANTHROPIC_API_KEY in .env doesn't start with 'sk-ant-' — it may be invalid."
  exit 1
else
  echo "ANTHROPIC_API_KEY found (sk-ant-...)"
fi
