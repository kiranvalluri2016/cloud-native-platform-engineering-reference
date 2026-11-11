#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
python_command="${PYTHON_COMMAND:-python3.12}"

"$python_command" -m pytest
kubectl kustomize "$project_root/k8s/overlays/dev" >/tmp/cloud-native-reference-dev.yaml
kubectl kustomize "$project_root/k8s/overlays/prod" >/tmp/cloud-native-reference-prod.yaml

if find "$project_root" -path "$project_root/.git" -prune -o -path '*/.github/workflows/*' -type f -print | grep -q .; then
  echo "GitHub Actions workflows are prohibited in this reference." >&2
  exit 1
fi

if rg -n --hidden --glob '!.git/**' --glob '!.venv/**' --glob '!**/.venv/**' '(?i)(password[[:space:]]*[:=]|client[_-]?secret[[:space:]]*[:=]|api[_-]?key[[:space:]]*[:=]|accountkey[[:space:]]*[:=]|connectionstring[[:space:]]*[:=])' "$project_root"; then
  echo "Potential credential pattern found." >&2
  exit 1
fi

echo "Local validation completed. No kubectl apply, cluster access, cloud authentication, or image publication command was executed."
