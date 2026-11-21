
# --- Le code suivant été réalisé par Claude Opus 5.5 Moyen ---

"""
Génère les figures et leurs CSV à partir des journaux bruts de raw/.

Usage (depuis la racine du dépôt) :
    python3 scripts/figures.py

Entrées  : raw/p1_<préfixe>.csv  (produits par bench/locustfile.py)
Sorties  : figures/fig1a.csv, figures/fig1a.png
           figures/fig1b.csv, figures/fig1b.png

Choix de traitement :
  - on écarte les WARMUP_S premières secondes de chaque run (cold start, montée en charge) ;
  - seules les réponses HTTP 200 entrent dans les médianes ; les autres sont comptées à part.
"""
import csv
import os
import statistics

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

RAW = "raw"
OUT = "figures"
WARMUP_S = 5.0

# Jeux de données de la partie 1 (section 2 du sujet) : préfixe -> (U, P, F)
U_SETS = {"u100": (100, 20, 20), "base": (1000, 20, 20), "u10000": (10000, 20, 20)}
P_SETS = {"p10": (100, 10, 20), "p100": (100, 100, 20), "p1000": (100, 1000, 20)}
F_SETS = {f"f{f:02d}": (120, 20, f) for f in range(5, 101, 5)}

# Couleurs (palette catégorielle par défaut, ordre fixe)
BLUE, ORANGE = "#2a78d6", "#eb6834"
INK, MUTED = "#2b2b2b", "#6b6b6b"


def load_run(path):
    """Lit un CSV de locustfile.py et renvoie les statistiques du run."""
    with open(path, newline="") as fh:
        rows = list(csv.DictReader(fh))
    if not rows:
        raise ValueError(f"{path} est vide")
    t0 = min(float(r["T_START"]) for r in rows)
    kept = [r for r in rows if float(r["T_START"]) >= t0 + WARMUP_S]
    ok = [r for r in kept if r["STATUS"] == "200"]
    statuses = sorted({r["STATUS"] for r in rows})
    return {
        "n_total": len(rows),
        "n_kept": len(kept),
        "n_ok": len(ok),
        "n_fail": len(kept) - len(ok),
        "statuses": " ".join(statuses),
        "instances": len({r["INSTANCE"] for r in ok if r["INSTANCE"]}),
        "server_ms": statistics.median(float(r["SERVER_MS"]) for r in ok),
        "client_ms": statistics.median(float(r["LATENCY_MS"]) for r in ok),
        # part réseau + frontal, calculée requête par requête puis médiane
        "network_ms": statistics.median(
            float(r["LATENCY_MS"]) - float(r["SERVER_MS"]) for r in ok
        ),
    }


def table(sets, part="p1"):
    out = []
    for prefix, (u, p, f) in sets.items():
        s = load_run(os.path.join(RAW, f"{part}_{prefix}.csv"))
        out.append({"prefix": prefix, "U": u, "P": p, "F": f, **s})
    return out


COLUMNS = [
    ("dataset", "prefix"), ("U_users", "U"), ("P_posts_per_user", "P"),
    ("F_followees", "F"), ("requests_total", "n_total"),
    ("requests_after_warmup", "n_kept"), ("requests_ok", "n_ok"),
    ("requests_failed", "n_fail"), ("http_statuses", "statuses"),
    ("active_instances", "instances"), ("server_median_ms", "server_ms"),
    ("client_median_ms", "client_ms"), ("network_median_ms", "network_ms"),
]


def write_csv(path, rows, extra=None):
    cols = ([extra] if extra else []) + COLUMNS
    with open(path, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow([c[0] for c in cols])
        for r in rows:
            w.writerow([r[c[1]] if not isinstance(r[c[1]], float) else f"{r[c[1]]:.1f}"
                        for c in cols])


def style(ax):
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color("#c9c9c9")
    ax.tick_params(colors=MUTED, labelsize=9)
    ax.grid(axis="y", color="#e6e6e6", linewidth=0.8)
    ax.set_axisbelow(True)


def fig1a(u_rows, p_rows):
    rows = [dict(r, factor="U") for r in u_rows] + [dict(r, factor="P") for r in p_rows]
    write_csv(os.path.join(OUT, "fig1a.csv"), rows, extra=("factor_varied", "factor"))

    fig, axes = plt.subplots(1, 2, figsize=(10, 4), sharey=True)
    panels = [
        (axes[0], u_rows, "U", "U (utilisateurs du jeu, échelle log)", "P = 20, F = 20"),
        (axes[1], p_rows, "P", "P (posts par utilisateur, échelle log)", "U = 100, F = 20"),
    ]
    ymax = max(r["server_ms"] for r in u_rows + p_rows) * 1.4
    for ax, rows_, key, xlabel, fixed in panels:
        xs = [r[key] for r in rows_]
        ys = [r["server_ms"] for r in rows_]
        ax.plot(xs, ys, color=BLUE, linewidth=2, marker="o", markersize=8,
                markeredgecolor="white", markeredgewidth=2)
        for x, y in zip(xs, ys):
            ax.annotate(f"{y:.1f} ms", (x, y), textcoords="offset points",
                        xytext=(0, 10), ha="center", fontsize=9, color=INK)
        ax.set_xscale("log")
        ax.minorticks_off()
        ax.margins(x=0.12)
        ax.set_xticks(xs)
        ax.set_xticklabels([f"{x:,}".replace(",", " ") for x in xs])
        ax.set_xlabel(xlabel, color=INK)
        ax.set_title(f"Facteur {key}  ({fixed})", fontsize=10, color=MUTED, loc="left")
        ax.set_ylim(0, ymax)
        style(ax)
    axes[0].set_ylabel("Temps serveur médian (ms)", color=INK)
    fig.suptitle("Fig. 1a : temps serveur médian d'une timeline selon U et P\n"
                 "fixed1 (1 instance), 1 requête à la fois", fontsize=11, color=INK,
                 x=0.02, ha="left")
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "fig1a.png"), dpi=150)
    plt.close(fig)


def fig1b(f_rows):
    write_csv(os.path.join(OUT, "fig1b.csv"), f_rows)

    xs = [r["F"] for r in f_rows]
    fig, ax = plt.subplots(figsize=(10, 4.5))
    for key, color, label in (("client_ms", ORANGE, "Latence client médiane"),
                              ("server_ms", BLUE, "Temps serveur médian")):
        ys = [r[key] for r in f_rows]
        ax.plot(xs, ys, color=color, linewidth=2, marker="o", markersize=8,
                markeredgecolor="white", markeredgewidth=2, label=label)
    ax.axvline(29.5, color=MUTED, linewidth=1, linestyle="--")
    ax.annotate("F + 1 > 30 valeurs dans le IN", (29.5, ax.get_ylim()[1] * 0.92),
                textcoords="offset points", xytext=(6, 0), fontsize=9, color=MUTED)
    ax.set_xticks(xs)
    ax.set_xlabel("F (comptes suivis par utilisateur)", color=INK)
    ax.set_ylabel("Temps (ms)", color=INK)
    ax.set_ylim(bottom=0)
    ax.legend(frameon=False, fontsize=9, loc="upper left")
    ax.set_title("Fig. 1b : temps serveur et latence client médians selon F\n"
                 "U = 120, P = 20 ; fixed1 (1 instance), 1 requête à la fois",
                 fontsize=11, color=INK, loc="left")
    style(ax)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "fig1b.png"), dpi=150)
    plt.close(fig)


def main():
    os.makedirs(OUT, exist_ok=True)
    u_rows, p_rows, f_rows = table(U_SETS), table(P_SETS), table(F_SETS)
    fig1a(u_rows, p_rows)
    fig1b(f_rows)

    print(f"{'jeu':<8}{'U':>6}{'P':>6}{'F':>5}{'req.':>7}{'échecs':>8}{'inst.':>6}"
          f"{'serveur':>10}{'client':>9}{'réseau':>9}")
    for r in u_rows + p_rows + f_rows:
        print(f"{r['prefix']:<8}{r['U']:>6}{r['P']:>6}{r['F']:>5}{r['n_ok']:>7}"
              f"{r['n_fail']:>8}{r['instances']:>6}{r['server_ms']:>10.1f}"
              f"{r['client_ms']:>9.1f}{r['network_ms']:>9.1f}")
    print(f"\nFigures écrites dans {OUT}/ (premières {WARMUP_S:.0f} s de chaque run écartées)")


if __name__ == "__main__":
    main()