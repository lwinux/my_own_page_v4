#!/usr/bin/env bash
# Read .env and upload each variable to GitHub repository secrets via gh CLI.
# Usage: ./sync-env-to-gh-secrets.sh [--repo OWNER/REPO]
# Requires: gh auth login
#
# Set default repo below (used when --repo is not passed). Example: owner/repo
REPO_DEFAULT="lwinux/my_own_page_v4"

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${SCRIPT_DIR}/.env"
REPO_ARG=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo)
      if [[ -z "${2:-}" ]]; then
        echo "Error: --repo requires OWNER/REPO" >&2
        exit 1
      fi
      REPO_ARG=(--repo "$2")
      shift 2
      ;;
    *)
      echo "Usage: $0 [--repo OWNER/REPO]" >&2
      exit 1
      ;;
  esac
done

if [[ ${#REPO_ARG[@]} -eq 0 && -n "$REPO_DEFAULT" ]]; then
  REPO_ARG=(--repo "$REPO_DEFAULT")
fi

if [[ ! -f "$ENV_FILE" ]]; then
  echo "Error: .env not found at $ENV_FILE" >&2
  exit 1
fi

if ! command -v gh &>/dev/null; then
  echo "Error: gh CLI not found. Install: https://cli.github.com/" >&2
  exit 1
fi

if ! gh auth status &>/dev/null; then
  echo "Error: gh not authenticated. Run: gh auth login" >&2
  exit 1
fi

count=0
while IFS= read -r line; do
  # Skip comments and empty lines
  [[ "$line" =~ ^[[:space:]]*# ]] && continue
  [[ -z "${line//[[:space:]]}" ]] && continue
  # Require KEY=value (key until first =)
  if [[ ! "$line" =~ ^([A-Za-z_][A-Za-z0-9_]*)=(.*)$ ]]; then
    continue
  fi
  key="${BASH_REMATCH[1]}"
  value="${BASH_REMATCH[2]}"
  # Strip optional surrounding quotes (one layer)
  if [[ "$value" =~ ^\"(.*)\"$ ]]; then value="${BASH_REMATCH[1]}"; fi
  if [[ "$value" =~ ^\'(.*)\'$ ]]; then value="${BASH_REMATCH[1]}"; fi
  printf '%s' "$value" | gh secret set "$key" "${REPO_ARG[@]}"
  echo "Set secret: $key"
  ((count++)) || true
done < "$ENV_FILE"

echo "Done. $count secret(s) updated."
