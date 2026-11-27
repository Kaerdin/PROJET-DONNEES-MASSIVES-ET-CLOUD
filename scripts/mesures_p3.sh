# Partie 3 : même protocole que la partie 2 avec N = 1, mais sur la version workers1 (gunicorn -w 4).
# 7 runs (C = 1, 2, 4, 8, 16, 32, 64), jeu base, 45 s par run.
# Usage : depuis la racine du dépôt tinyinsta-2026, après ./deploy_workers.sh 1

set -euo pipefail
V=workers1
URL=$(gcloud app versions describe $V --service default --format='value(versionUrl)')

# Vérification : la réponse doit contenir X-Instance et Server-Timing
curl -sI "$URL/api/timeline?user=base_u00001" | grep -iE "x-instance|server-timing"

# TINY_PREFIX = jeu de données, TINY_USERS = nombre d'utilisateurs, TINY_LOG = fichier CSV de sortie
run() {
  TINY_PREFIX=base TINY_USERS=1000 TINY_LOG=raw/p3_${V}_C$1.csv \
    locust -f bench/locustfile.py --headless -u $1 -r $1 -t 45s --only-summary --host "$URL" || true
}

for C in 1 2 4 8 16 32 64; do run $C; done

# Arrêt de la version : en manual scaling, une instance est facturée tant qu'elle tourne
gcloud app versions stop $V --quiet
