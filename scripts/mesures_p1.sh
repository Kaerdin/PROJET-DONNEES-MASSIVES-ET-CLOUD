# Partie 1 : 26 runs sur fixed1, 1 requête à la fois (-u 1), 45 s par run.
# Usage : depuis la racine du dépôt tinyinsta-2026, après ./deploy_fixed.sh 1

set -euo pipefail
URL=$(gcloud app versions describe fixed1 --service default --format='value(versionUrl)')

run() {
  TINY_PREFIX=$1 TINY_USERS=$2 TINY_LOG=raw/p1_$1.csv \
    locust -f bench/locustfile.py --headless -u 1 -r 1 -t 45s --only-summary --host "$URL"
}

run base 1000
run u100 100
run u10000 10000
for p in 10 100 1000; do run p$p 100; done
for f in $(seq 5 5 100); do run $(printf 'f%02d' $f) 120; done