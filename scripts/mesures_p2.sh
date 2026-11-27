# Partie 2 : 7 runs sur fixedN (C = 1, 2, 4, 8, 16, 32, 64 utilisateurs simultanés), jeu base, 45 s par run.
# N = Nombre d'instance

# Usage : depuis la racine du dépôt tinyinsta-2026, après ./deploy_fixed.sh N (ou gcloud app versions start fixedN)
# --> bash scripts/mesures_p2.sh 1     -> mesures sur fixed1
# --> bash scripts/mesures_p2.sh 2     -> mesures sur fixed2
# --> ...
# --> bash scripts/mesures_p64.sh 64   -> mesures sur fixed64

# Arrête le script à la moindre erreur (arrêter manuellement l'instance à la main si ça arrive)
set -euo pipefail
N=$1
URL=$(gcloud app versions describe fixed$N --service default --format='value(versionUrl)')

# Vérifie que l'URL vise bien la bonne version : la réponse doit contenir les en-têtes X-Instance et Server-Timing.
curl -sI "$URL/api/timeline?user=base_u00001" | grep -iE "x-instance|server-timing"

# TINY_PREFIX = jeu de données, TINY_USERS = nombre d'utilisateur, TINY_LOG = fichier CSV de sortie
# -u et -r = C, le nombre d'utilisateurs Locust simultanés
run() {
  TINY_PREFIX=base TINY_USERS=1000 TINY_LOG=raw/p2_N${N}_C$1.csv \
    locust -f bench/locustfile.py --headless -u $1 -r $1 -t 45s --only-summary --host "$URL" || true
}

# Exécution de la fonction pour chaque valeur de C 
for C in 1 2 4 8 16 32 64; do run $C; done

# Arrête l'instance pour ne pas être facturé plus qu'au besoin
gcloud app versions stop fixed$N