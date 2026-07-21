#!/usr/bin/env python3
"""Consolidation — des JSON par chart aux tableaux d'analyse.

Rassemble les sorties des phases 2 et 3, éparpillées en un JSON par
chart, en deux tableaux CSV dans data/processed/ :

  charts.csv   une ligne par chart : catégorie d'origine, type de mise
               en page, effectifs, mécaniques de gamification, ton.
               C'est la matrice d'entrée de la phase 4 (typologie par
               clustering) — chaque ligne y devient un individu.

  oeuvres.csv  une ligne par (chart, œuvre) : le chart, sa section, et
               l'œuvre avec son auteur. C'est la table d'incidence dont
               part la phase 5 (réseaux d'auteurs) : deux auteurs sont
               liés dès qu'ils partagent un chart.

Le format long d'oeuvres.csv est délibéré : il supporte aussi bien un
comptage d'occurrences qu'une projection en graphe, sans retraitement.

Tolérance aux étapes manquantes : un chart sans classement visuel ou
sans codage est conservé, colonnes vides. On peut donc consolider en
cours de route, sur un corpus partiellement traité, et relancer plus
tard sans rien perdre — le script réécrit les tableaux à chaque appel,
il n'y a pas de reprise à gérer.
"""

import argparse
import csv
import json
import sys
from pathlib import Path

# --- Chemins du projet ---
RACINE = Path(__file__).resolve().parents[1]
DOSSIER_BLOCS = RACINE / "data" / "interim" / "blocs"
DOSSIER_VLM = RACINE / "data" / "interim" / "vlm"
DOSSIER_CODAGE = RACINE / "data" / "interim" / "codage"
DOSSIER_MARQUEURS = RACINE / "data" / "interim" / "marqueurs"
INVENTAIRE = RACINE / "data" / "interim" / "inventaire_images.csv"
DOSSIER_SORTIE = RACINE / "data" / "processed"

MECANIQUES = ["progression", "prerequis", "niveaux_de_difficulte",
              "embranchements", "recompenses", "injonction"]

# Registres lexicaux relevés en phase 3 (volet déterministe). Préfixés
# « m_ » dans le tableau pour les distinguer sans ambiguïté du codage
# par LLM : les deux mesurent des choses voisines mais par des voies
# différentes, et les confronter est un contrôle de l'étude.
REGISTRES = ["niveaux_nommes", "hierarchie_valeur", "point_entree", "difficulte",
             "prerequis", "optionnel", "recompense", "injonction", "progression"]

COLONNES_CHARTS = [
    "fichier", "categorie", "sous_categorie",
    "layout_type", "has_arrows", "regime",
    "largeur", "hauteur", "nb_blocs", "nb_oeuvres", "nb_tiers",
    *MECANIQUES, "ton", "point_entree", "nb_ordinal_labels", "justification",
    "score_marqueurs", *[f"m_{r}" for r in REGISTRES],
]
COLONNES_OEUVRES = ["fichier", "categorie", "layout_type", "tier",
                    "auteur", "titre"]


def lire_json(chemin):
    """Lit un JSON s'il existe, renvoie {} sinon."""
    if not chemin.exists():
        return {}
    return json.loads(chemin.read_text(encoding="utf-8"))


def charger_inventaire():
    """Associe à chaque image sa catégorie thématique d'origine.

    Ces catégories viennent du classement du wiki /lit/, préservé lors
    de l'aplatissement du corpus. Elles ne servent PAS à construire la
    typologie — ce serait circulaire — mais à la confronter ensuite à
    une classification indigène, ce qui en fait un point de validation
    externe.
    """
    if not INVENTAIRE.exists():
        return {}
    with open(INVENTAIRE, newline="", encoding="utf-8") as fichier:
        return {ligne["fichier"]: ligne for ligne in csv.DictReader(fichier)}


def principal():
    parseur = argparse.ArgumentParser(
        description="Consolidation des sorties en tableaux d'analyse.")
    parseur.add_argument("--sortie", default=str(DOSSIER_SORTIE),
                         help="dossier de destination (défaut : %(default)s)")
    args = parseur.parse_args()

    if not DOSSIER_BLOCS.exists():
        sys.exit(f"Rien à consolider : {DOSSIER_BLOCS} est absent "
                 f"(lancer src/01_ocr.py puis src/02_blocs.py).")
    fichiers = sorted(DOSSIER_BLOCS.glob("*.json"))
    if not fichiers:
        sys.exit(f"Rien à consolider : aucun JSON dans {DOSSIER_BLOCS}.")

    dossier_sortie = Path(args.sortie)
    dossier_sortie.mkdir(parents=True, exist_ok=True)
    inventaire = charger_inventaire()

    lignes_charts, lignes_oeuvres = [], []
    sans_vlm = sans_codage = 0

    for chemin in fichiers:
        blocs = lire_json(chemin)
        vlm = lire_json(DOSSIER_VLM / chemin.name).get("extraction", {})
        codage = lire_json(DOSSIER_CODAGE / chemin.name).get("codage", {})
        marqueurs = lire_json(DOSSIER_MARQUEURS / chemin.name)
        registres = marqueurs.get("registres", {})
        if not vlm:
            sans_vlm += 1
        if not codage:
            sans_codage += 1

        nom = blocs.get("fichier") or chemin.stem
        meta = inventaire.get(nom, {})
        categorie = meta.get("categorie", "")
        taille = blocs.get("taille_origine") or ["", ""]
        mecaniques = codage.get("mecaniques", {})

        lignes_charts.append({
            "fichier": nom,
            "categorie": categorie,
            "sous_categorie": meta.get("sous_categorie", ""),
            "layout_type": vlm.get("layout_type", ""),
            "has_arrows": vlm.get("has_arrows", ""),
            "regime": blocs.get("regime", ""),
            "largeur": taille[0],
            "hauteur": taille[1],
            "nb_blocs": blocs.get("nb_blocs", 0),
            "nb_oeuvres": blocs.get("nb_noeuds", 0),
            "nb_tiers": len(blocs.get("tiers") or []),
            **{cle: mecaniques.get(cle, "") for cle in MECANIQUES},
            "ton": codage.get("ton", ""),
            "point_entree": codage.get("point_entree", "") or "",
            "nb_ordinal_labels": len(codage.get("ordinal_labels") or []),
            "justification": codage.get("justification", ""),
            "score_marqueurs": marqueurs.get("score_total", ""),
            **{f"m_{r}": registres.get(r, {}).get("occurrences", "")
               for r in REGISTRES},
        })

        for bloc in blocs.get("blocs", []):
            for noeud in bloc.get("noeuds", []):
                lignes_oeuvres.append({
                    "fichier": nom,
                    "categorie": categorie,
                    "layout_type": vlm.get("layout_type", ""),
                    "tier": bloc.get("tier") or "",
                    "auteur": noeud.get("auteur") or "",
                    "titre": noeud.get("titre") or "",
                })

    for nom_table, colonnes, lignes in (
        ("charts.csv", COLONNES_CHARTS, lignes_charts),
        ("oeuvres.csv", COLONNES_OEUVRES, lignes_oeuvres),
    ):
        chemin = dossier_sortie / nom_table
        with open(chemin, "w", newline="", encoding="utf-8") as fichier:
            writer = csv.DictWriter(fichier, fieldnames=colonnes)
            writer.writeheader()
            writer.writerows(lignes)
        print(f"  {chemin} : {len(lignes)} lignes")

    print(f"Consolidé : {len(lignes_charts)} charts, {len(lignes_oeuvres)} œuvres.")
    if sans_vlm:
        print(f"  dont {sans_vlm} sans classement visuel (lancer src/03_vlm.py)")
    if sans_codage:
        print(f"  dont {sans_codage} sans codage (lancer src/04_codage.py)")


if __name__ == "__main__":
    principal()
