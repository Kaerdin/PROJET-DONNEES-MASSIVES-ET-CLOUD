#!/usr/bin/env bash
# Partie 3 : comme deploy_fixed.sh, mais gunicorn lancé avec 4 workers (-w 4)
# au lieu de la valeur par défaut (1 worker). Version "workersN".
#   ./deploy_workers.sh 1   -> version workers1 (1 instance fixe)
set -euo pipefail
N="${1:?usage: ./deploy_workers.sh N}"
cd "$(dirname "$0")"
YAML="app-workers-${N}.yaml"
trap 'rm -f "$YAML"' EXIT
cat > "$YAML" <<EOF
runtime: python312
entrypoint: gunicorn -b :\$PORT -w 4 main:app

instance_class: B1
manual_scaling:
  instances: ${N}

handlers:
- url: /
  script: auto
env_variables:
  SEED_TOKEN: "change-me-seed-token"
EOF
gcloud app deploy "$YAML" --version "workers${N}" --no-promote --quiet
