#!/usr/bin/env python3

# --- Le code suivant été réalisé via Claude Opus 5.5 Moyen ---

"""Génère les figures et leurs CSV à partir des journaux bruts de raw/.

Usage (depuis la racine du dépôt) :
    python3 scripts/figures.py

Entrées  : raw/p1_<préfixe>.csv, raw/p2_N<N>_C<C>.csv  (produits par bench/locustfile.py)
Sorties  : figures/fig1a.csv/.png, figures/fig1b.csv/.png  (partie 1)
           figures/fig2a.csv/.png, figures/fig2b.csv/.png  (partie 2, pour les N disponibles)
           figures/fig3.csv/.png  (partie 3 : fixed1 avant / workers1 après, si raw/p3_workers1_C<C>.csv existe)

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
BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
N_COLORS = {1: BLUE, 2: ORANGE, 4: AQUA}
P2_N = (1, 2, 4)
P2_C = (1, 2, 4, 8, 16, 32, 64)
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


# ---------------------------------------------------------------- partie 2

def load_capacity(path):
    """Débit et latence d'un run de la partie 2 (fenêtre après le warm-up)."""
    with open(path, newline="") as fh:
        rows = list(csv.DictReader(fh))
    t0 = min(float(r["T_START"]) for r in rows)
    kept = [r for r in rows if float(r["T_START"]) >= t0 + WARMUP_S]
    ok = [r for r in kept if r["STATUS"] == "200"]
    t_end = max(float(r["T_START"]) for r in kept)
    window = t_end - (t0 + WARMUP_S)
    throughput = len(ok) / window
    return {
        "n_kept": len(kept),
        "n_ok": len(ok),
        "n_fail": len(kept) - len(ok),
        "statuses": " ".join(sorted({r["STATUS"] for r in kept})),
        "errors": " | ".join(sorted({r["ERROR"].split("(")[0] for r in kept if r["ERROR"]})),
        "instances": len({r["INSTANCE"] for r in ok if r["INSTANCE"]}),
        "window_s": window,
        "throughput": throughput,
        "client_ms": statistics.median(float(r["LATENCY_MS"]) for r in ok),
        "server_ms": statistics.median(float(r["SERVER_MS"]) for r in ok),
    }


def capacity_table():
    out = []
    for n in P2_N:
        for c in P2_C:
            path = os.path.join(RAW, f"p2_N{n}_C{c}.csv")
            if not os.path.exists(path):
                continue
            s = load_capacity(path)
            s["little_ms"] = c / s["throughput"] * 1000
            out.append({"N": n, "C": c, **s})
    return out


P2_COLUMNS = [
    ("N_instances", "N"), ("C_concurrent_users", "C"), ("window_s", "window_s"),
    ("requests_after_warmup", "n_kept"), ("requests_ok", "n_ok"),
    ("requests_failed", "n_fail"), ("http_statuses", "statuses"),
    ("client_errors", "errors"), ("active_instances", "instances"),
    ("throughput_req_per_s", "throughput"), ("client_median_ms", "client_ms"),
    ("server_median_ms", "server_ms"), ("little_prediction_ms", "little_ms"),
]


def write_p2_csv(path, rows):
    with open(path, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow([c[0] for c in P2_COLUMNS])
        for r in rows:
            w.writerow([f"{r[k]:.1f}" if isinstance(r[k], float) else r[k] for _, k in P2_COLUMNS])


def c_axis(ax):
    ax.set_xscale("log", base=2)
    ax.minorticks_off()
    ax.set_xticks(P2_C)
    ax.set_xticklabels([str(c) for c in P2_C])
    ax.set_xlabel("C (utilisateurs Locust simultanés, échelle log)", color=INK)


def fig2(rows):
    write_p2_csv(os.path.join(OUT, "fig2a.csv"), rows)
    write_p2_csv(os.path.join(OUT, "fig2b.csv"), rows)
    ns = [n for n in P2_N if any(r["N"] == n for r in rows)]

    # Fig. 2a : débit selon C, une courbe par N
    fig, ax = plt.subplots(figsize=(10, 4.5))
    for n in ns:
        rs = [r for r in rows if r["N"] == n]
        ax.plot([r["C"] for r in rs], [r["throughput"] for r in rs], color=N_COLORS[n],
                linewidth=2, marker="o", markersize=8, markeredgecolor="white",
                markeredgewidth=2, label=f"N = {n} instance{'s' if n > 1 else ''}")
    c_axis(ax)
    ax.set_ylabel("Débit (requêtes réussies / s)", color=INK)
    ax.set_ylim(bottom=0)
    ax.legend(frameon=False, fontsize=9, loc="upper left")
    ax.set_title("Fig. 2a : débit selon la concurrence C, une courbe par nombre d'instances N\n"
                 "jeu base (U = 1000, P = 20, F = 20) ; versions fixedN", fontsize=11,
                 color=INK, loc="left")
    style(ax)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "fig2a.png"), dpi=150)
    plt.close(fig)

    # Fig. 2b : latence médiane mesurée et prédiction de Little, un panneau par N
    fig, axes = plt.subplots(1, len(ns), figsize=(4.2 * len(ns), 4.2), sharey=True,
                             squeeze=False)
    for ax, n in zip(axes[0], ns):
        rs = [r for r in rows if r["N"] == n]
        cs = [r["C"] for r in rs]
        ax.plot(cs, [r["client_ms"] for r in rs], color=N_COLORS[n], linewidth=2,
                marker="o", markersize=8, markeredgecolor="white", markeredgewidth=2,
                label="Latence médiane mesurée")
        ax.plot(cs, [r["little_ms"] for r in rs], color=MUTED, linewidth=1.5,
                linestyle="--", label="Little : C / débit")
        c_axis(ax)
        ax.set_xlabel("C (échelle log)", color=INK)
        ax.set_yscale("log")
        ax.set_title(f"N = {n}", fontsize=10, color=MUTED, loc="left")
        style(ax)
    axes[0][0].set_ylabel("Latence (ms, échelle log)", color=INK)
    axes[0][0].legend(frameon=False, fontsize=9, loc="upper left")
    fig.suptitle("Fig. 2b : latence médiane selon C, et prédiction de la loi de Little "
                 "(latence ≈ C / débit)\njeu base ; versions fixedN", fontsize=11,
                 color=INK, x=0.02, ha="left")
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "fig2b.png"), dpi=150)
    plt.close(fig)

    print(f"\n{'N':>2}{'C':>4}{'req.':>7}{'échecs':>8}{'inst.':>6}{'débit/s':>9}"
          f"{'client':>9}{'Little':>9}{'serveur':>9}  erreurs")
    for r in rows:
        print(f"{r['N']:>2}{r['C']:>4}{r['n_ok']:>7}{r['n_fail']:>8}{r['instances']:>6}"
              f"{r['throughput']:>9.1f}{r['client_ms']:>9.1f}{r['little_ms']:>9.1f}"
              f"{r['server_ms']:>9.1f}  {r['errors']}")


# ---------------------------------------------------------------- partie 3

P3_VERSION = "workers1"


def fig3():
    """Avant (fixed1, 1 worker) / après (workers1, gunicorn -w 4), même protocole."""
    rows = []
    for label, pattern in (("avant : fixed1 (1 worker)", "p2_N1_C{c}.csv"),
                           (f"après : {P3_VERSION} (-w 4)", f"p3_{P3_VERSION}_C{{c}}.csv")):
        for c in P2_C:
            path = os.path.join(RAW, pattern.format(c=c))
            if not os.path.exists(path):
                continue
            s = load_capacity(path)
            s["little_ms"] = c / s["throughput"] * 1000
            rows.append({"version": label, "N": 1, "C": c, **s})
    if not any(r["version"].startswith("après") for r in rows):
        return None

    with open(os.path.join(OUT, "fig3.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["version"] + [c[0] for c in P2_COLUMNS])
        for r in rows:
            w.writerow([r["version"]] + [f"{r[k]:.1f}" if isinstance(r[k], float) else r[k]
                                         for _, k in P2_COLUMNS])

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.3))
    for label, color in (("avant", BLUE), ("après", ORANGE)):
        rs = [r for r in rows if r["version"].startswith(label)]
        name = rs[0]["version"]
        cs = [r["C"] for r in rs]
        for ax, key in ((axes[0], "throughput"), (axes[1], "client_ms")):
            ax.plot(cs, [r[key] for r in rs], color=color, linewidth=2, marker="o",
                    markersize=8, markeredgecolor="white", markeredgewidth=2, label=name)
    axes[0].set_ylabel("Débit (requêtes réussies / s)", color=INK)
    axes[0].set_ylim(bottom=0)
    axes[0].set_title("Débit", fontsize=10, color=MUTED, loc="left")
    axes[1].set_ylabel("Latence médiane (ms, échelle log)", color=INK)
    axes[1].set_yscale("log")
    axes[1].set_title("Latence médiane", fontsize=10, color=MUTED, loc="left")
    for ax in axes:
        c_axis(ax)
        ax.set_xlabel("C (échelle log)", color=INK)
        style(ax)
    axes[1].legend(frameon=False, fontsize=9, loc="upper left")
    fig.suptitle("Fig. 3 : avant / après la correction (gunicorn -w 4), même protocole que la partie 2\n"
                 "1 instance B1, jeu base (U = 1000, P = 20, F = 20)", fontsize=11,
                 color=INK, x=0.02, ha="left")
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "fig3.png"), dpi=150)
    plt.close(fig)

    print(f"\n{'version':<28}{'C':>4}{'req.':>7}{'échecs':>8}{'inst.':>6}{'débit/s':>9}"
          f"{'client':>9}{'serveur':>9}  erreurs")
    for r in rows:
        print(f"{r['version']:<28}{r['C']:>4}{r['n_ok']:>7}{r['n_fail']:>8}{r['instances']:>6}"
              f"{r['throughput']:>9.1f}{r['client_ms']:>9.1f}{r['server_ms']:>9.1f}  {r['errors']}")
    return rows


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
    p2 = capacity_table()
    if p2:
        fig2(p2)
    fig3()
    print(f"\nFigures écrites dans {OUT}/ (premières {WARMUP_S:.0f} s de chaque run écartées)")


if __name__ == "__main__":
    main()