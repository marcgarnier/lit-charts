#!/usr/bin/env python3
"""Figures pour la page de présentation du projet (marcgarnier.github.io).

Régénère les figures aux couleurs du site — anthracite, bleu glacier,
IBM Plex — plutôt que d'y plaquer les figures de travail sur fond blanc,
qui y feraient des rectangles éblouissants. Le fond est transparent : les
figures se posent sur le panneau du site sans coutures.

Les valeurs de couleur sont celles de css/style.css. Si le site change de
palette, les modifier ici en conséquence.

Sortie : --sortie (par défaut le dossier assets/figures/ du site).
"""

import argparse
import csv
import itertools
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

RACINE = Path(__file__).resolve().parents[1]
PROC = RACINE / "data" / "processed"

# --- Jetons de style repris de css/style.css ---
ENCRE = "#e8ebee"
ENCRE_ATTENUEE = "#9aa4af"
ENCRE_FAIBLE = "#6b7682"
ACCENT = "#8ec9ea"
ACCENT_VIF = "#aedbf5"
BORDURE = "#262e38"
PANNEAU = "#181e25"
# Les quatre teintes d'annotation du site, pour les séries catégorielles.
TEINTES = ["#8ec9ea", "#86d3a5", "#d8b46f", "#b3a1e6", "#e59a9a"]

plt.rcParams.update({
    "figure.dpi": 120, "savefig.dpi": 200,
    "savefig.bbox": "tight", "savefig.transparent": True,
    "font.family": ["IBM Plex Sans", "DejaVu Sans"],
    "font.size": 11,
    "text.color": ENCRE, "axes.labelcolor": ENCRE_ATTENUEE,
    "xtick.color": ENCRE_ATTENUEE, "ytick.color": ENCRE_ATTENUEE,
    "axes.edgecolor": BORDURE, "axes.facecolor": "none", "figure.facecolor": "none",
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.spines.left": False, "axes.spines.bottom": False,
    "axes.grid": False,
})

LIBELLES = {"grid": "plain grid", "sectioned_grid": "sectioned grid",
            "flowchart": "flowchart", "tier_list": "tier list",
            "list": "text list", "collage": "collage", "map": "map"}
REGISTRES = ["m_progression", "m_injonction", "m_point_entree", "m_prerequis",
             "m_difficulte", "m_optionnel", "m_recompense", "m_niveaux_nommes",
             "m_hierarchie_valeur"]
NOMS_EN = {"m_progression": "prescribed order", "m_injonction": "imperative address",
           "m_point_entree": "entry point", "m_prerequis": "prerequisites",
           "m_difficulte": "graded difficulty", "m_optionnel": "optional / bonus",
           "m_recompense": "promised reward", "m_niveaux_nommes": "named tiers",
           "m_hierarchie_valeur": "value hierarchy"}


def lire(chemin):
    with open(chemin, newline="", encoding="utf-8") as f:
        return list(csv.DictReader([l for l in f if not l.startswith("#")]))


def enregistrer(fig, chemin):
    fig.savefig(chemin)
    plt.close(fig)
    print(f"  {chemin.name}")


def barres_horizontales(valeurs, etiquettes, titre, chemin, suffixe=lambda v: f"{v}",
                        couleur=ACCENT, hauteur=None):
    """Barres horizontales à étiquettes directes — sans axe ni grille."""
    fig, ax = plt.subplots(figsize=(7.4, hauteur or (0.46 * len(valeurs) + 0.9)))
    y = np.arange(len(valeurs))[::-1]
    ax.barh(y, valeurs, height=0.6, color=couleur)
    ax.set_yticks(y, etiquettes)
    for yi, v in zip(y, valeurs):
        ax.text(v + max(valeurs) * 0.02, yi, suffixe(v), va="center",
                color=ENCRE_ATTENUEE, fontsize=10)
    ax.set_xticks([])
    ax.set_xlim(0, max(valeurs) * 1.2)
    ax.set_title(titre, loc="left", color=ENCRE, fontsize=12, pad=14)
    enregistrer(fig, chemin)


def figure_formes(traits, sortie):
    c = Counter(t["layout_manuel"] for t in traits)
    ordre = [f for f, _ in c.most_common()]
    barres_horizontales(
        [c[f] for f in ordre], [LIBELLES[f] for f in ordre],
        "Chart forms across the corpus (n = 264)", sortie / "fig-forms.png",
        suffixe=lambda v: f"{v}  ({v/len(traits):.0%})")


def figure_mecaniques(traits, sortie):
    parts = {r: sum(1 for t in traits if int(t[r] or 0) > 0) / len(traits)
             for r in REGISTRES}
    ordre = sorted(parts, key=parts.get)
    barres_horizontales(
        [parts[r] * 100 for r in ordre], [NOMS_EN[r] for r in ordre],
        "Share of charts carrying each gamified marker", sortie / "fig-mechanics.png",
        suffixe=lambda v: f"{v:.0f}%")


def figure_croisement(traits, sortie):
    """Forme × mécanique — là où se lit la répartition du travail prescriptif."""
    ordre_f = ["grid", "sectioned_grid", "flowchart", "tier_list", "list", "collage"]
    eff = Counter(t["layout_manuel"] for t in traits)
    M = np.array([[sum(1 for t in traits
                       if t["layout_manuel"] == f and int(t[r] or 0) > 0) / eff[f] * 100
                   for r in REGISTRES] for f in ordre_f])

    fig, ax = plt.subplots(figsize=(9.2, 3.9))
    cmap = matplotlib.colors.LinearSegmentedColormap.from_list(
        "glacier", ["#141a21", ACCENT])
    ax.imshow(M, cmap=cmap, vmin=0, vmax=80, aspect="auto")
    ax.set_xticks(range(len(REGISTRES)), [NOMS_EN[r] for r in REGISTRES],
                  rotation=38, ha="right", fontsize=9.5)
    ax.set_yticks(range(len(ordre_f)),
                  [f"{LIBELLES[f]}  ({eff[f]})" for f in ordre_f], fontsize=10)
    for i in range(M.shape[0]):
        for j in range(M.shape[1]):
            v = M[i, j]
            ax.text(j, i, f"{v:.0f}", ha="center", va="center", fontsize=9,
                    color="#0f1216" if v > 45 else ENCRE_ATTENUEE)
    ax.set_title("Prescription is shared between layout and language  (% of charts)",
                 loc="left", color=ENCRE, fontsize=12, pad=14)
    enregistrer(fig, sortie / "fig-form-x-mechanic.png")


def figure_typologie(traits, sortie):
    """Confrontation des groupes empiriques aux trois types théoriques.

    Les trois types du papier sont approchés depuis les formes codées :
    guides initiatiques = organigrammes et tier lists (parcours prescrit),
    canons culturels = grilles, cartographies ludiques = cartes et
    collages. C'est une approximation, déclarée comme telle sur la page.
    """
    TYPE = {"flowchart": "initiatory guides", "tier_list": "initiatory guides",
            "grid": "cultural canons", "sectioned_grid": "cultural canons",
            "list": "cultural canons", "map": "playful cartographies",
            "collage": "playful cartographies"}
    from sklearn.preprocessing import StandardScaler
    from sklearn.cluster import KMeans
    from sklearn.metrics import adjusted_rand_score

    VARS = ["ratio_hauteur_largeur", "nb_lignes", "densite_texte",
            "couverture_verticale", "part_bandes_peuplees", "regularite_colonnes",
            "cv_hauteurs_lignes", "longueur_moyenne_ligne", "part_lignes_courtes",
            "confiance_mediane"] + REGISTRES
    X = np.array([[float(t[v]) for v in VARS] for t in traits])
    for j, v in enumerate(VARS):
        if v == "nb_lignes" or v in REGISTRES:
            X[:, j] = np.log1p(X[:, j])
    X = StandardScaler().fit_transform(X)
    lab = KMeans(2, n_init=10, random_state=42).fit_predict(X)

    theo = [TYPE[t["layout_manuel"]] for t in traits]
    ari = adjusted_rand_score(lab, theo)
    ordre_t = ["initiatory guides", "cultural canons", "playful cartographies"]
    M = np.array([[sum(1 for k in range(len(traits)) if lab[k] == g and theo[k] == t)
                   for t in ordre_t] for g in (0, 1)], dtype=float)
    parts = M / M.sum(axis=1, keepdims=True) * 100

    fig, ax = plt.subplots(figsize=(8.4, 2.9))
    gauche = np.zeros(2)
    for j, t in enumerate(ordre_t):
        ax.barh([1, 0], parts[:, j], left=gauche, height=0.52,
                color=TEINTES[j], label=t, edgecolor=PANNEAU, linewidth=2)
        for i, y in enumerate((1, 0)):
            if parts[i, j] > 7:
                ax.text(gauche[i] + parts[i, j] / 2, y, f"{parts[i, j]:.0f}%",
                        ha="center", va="center", fontsize=10, color="#0f1216")
        gauche += parts[:, j]
    noms = [f"cluster {g}  (n={int(M[g].sum())})" for g in (0, 1)]
    ax.set_yticks([1, 0], noms, fontsize=10)
    ax.set_xticks([])
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=3,
              frameon=False, fontsize=9.5, labelcolor=ENCRE_ATTENUEE)
    ax.set_title(f"Emergent clusters vs. the paper's three types  —  ARI = {ari:.2f}",
                 loc="left", color=ENCRE, fontsize=12, pad=14)
    enregistrer(fig, sortie / "fig-typology.png")
    return ari, Counter(lab)


def figure_reseau(auteurs, sortie):
    import networkx as nx
    par_chart = defaultdict(set)
    charts_de = defaultdict(set)
    for l in auteurs:
        par_chart[l["fichier"]].add(l["auteur"])
        charts_de[l["auteur"]].add(l["fichier"])
    noyau = {a for a, c in charts_de.items() if len(c) >= 5}

    G = nx.Graph()
    for ens in par_chart.values():
        for a, b in itertools.combinations(sorted(ens & noyau), 2):
            G.add_edge(a, b, weight=G.get_edge_data(a, b, {"weight": 0})["weight"] + 1)
    densite = nx.density(G)
    btw = sorted(nx.betweenness_centrality(G).items(), key=lambda kv: -kv[1])

    H = nx.Graph((u, v, d) for u, v, d in G.edges(data=True) if d["weight"] >= 5)
    H.remove_nodes_from(list(nx.isolates(H)))
    pos = nx.spring_layout(H, seed=42, k=3.4 / np.sqrt(max(H.number_of_nodes(), 1)))
    deg = dict(H.degree)

    fig, ax = plt.subplots(figsize=(8.6, 6.2))
    nx.draw_networkx_edges(H, pos, ax=ax, alpha=0.13, width=0.6, edge_color=ACCENT)
    nx.draw_networkx_nodes(H, pos, ax=ax, node_color=ACCENT, alpha=0.75,
                           linewidths=0, node_size=[14 + 8 * deg[n] for n in H])
    posees = []
    for a, _ in btw:
        if a not in pos or len(posees) >= 10:
            continue
        x, y = pos[a]
        if all(abs(x - px) > 0.34 or abs(y - py) > 0.13 for px, py in posees):
            ax.annotate(a, (x, y), textcoords="offset points", xytext=(0, 11),
                        ha="center", fontsize=10, color=ACCENT_VIF)
            posees.append((x, y))
    ax.set_axis_off()
    ax.set_title(f"The canon travels as one block  —  core density {densite:.0%}",
                 loc="left", color=ENCRE, fontsize=12, pad=14)
    enregistrer(fig, sortie / "fig-network.png")

    # Palmarès de présence : le canon tel qu'il se lit, sans détour par
    # une mesure de centralité qui demanderait une explication.
    presence = sorted(((a, len(c)) for a, c in charts_de.items()),
                      key=lambda kv: (-kv[1], kv[0]))[:20]
    barres_horizontales(
        [n for _, n in presence[::-1]], [a for a, _ in presence[::-1]],
        "The canon in numbers — authors present on the most charts",
        sortie / "fig-top-authors.png",
        suffixe=lambda v: f"{v} charts", hauteur=6.4)
    return densite, G.number_of_nodes(), presence


def principal():
    p = argparse.ArgumentParser(description="Figures aux couleurs du site.")
    p.add_argument("--sortie",
                   default="/Users/marc/Desktop/projet site/assets/figures",
                   help="dossier de destination (défaut : %(default)s)")
    args = p.parse_args()
    sortie = Path(args.sortie)
    sortie.mkdir(parents=True, exist_ok=True)

    traits = lire(PROC / "traits.csv")
    auteurs = lire(PROC / "auteurs.csv")
    if not traits:
        sys.exit("traits.csv vide — lancer src/07_traits.py")

    print(f"Figures ({len(traits)} charts) dans {sortie} :")
    figure_formes(traits, sortie)
    figure_mecaniques(traits, sortie)
    figure_croisement(traits, sortie)
    ari, tailles = figure_typologie(traits, sortie)
    densite, n_noyau, presence = figure_reseau(auteurs, sortie)

    # Chiffres à reporter dans la page, pour éviter toute divergence.
    resume = {
        "n_charts": len(traits),
        "formes": dict(Counter(t["layout_manuel"] for t in traits)),
        "part_catalogues": round(sum(1 for t in traits if t["layout_manuel"] in
                                     ("grid", "sectioned_grid", "collage")) / len(traits), 4),
        "part_prescriptifs": round(sum(1 for t in traits if t["layout_manuel"] in
                                       ("flowchart", "tier_list")) / len(traits), 4),
        "ari_types": round(ari, 3),
        "tailles_clusters": {str(k): v for k, v in tailles.items()},
        "densite_noyau": round(densite, 4),
        "n_noyau": n_noyau,
        "top_auteurs": presence[:20],
    }
    (sortie / "chiffres.json").write_text(
        json.dumps(resume, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nchiffres.json : {json.dumps(resume, ensure_ascii=False)[:220]}…")


if __name__ == "__main__":
    principal()
