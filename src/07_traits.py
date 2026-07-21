#!/usr/bin/env python3
"""Préparation de la phase 4 — Traits mesurables tirés du seul OCR.

Calcule pour chaque chart un vecteur de variables numériques, à partir
des seules sorties de data/interim/ocr/, et l'écrit dans
data/processed/traits.csv. C'est la matrice sur laquelle la phase 4
fera émerger sa typologie.

POURQUOI DES TRAITS PLUTÔT QU'UN LABEL. Demander à un modèle « quelle
est la forme de ce chart ? » impose une taxonomie décidée à l'avance —
celle du prompt. Elle s'est révélée mal ajustée deux fois : la forme la
plus fréquente du corpus, la grille à sections thématiques nommées,
n'y figurait pas, et l'ajouter a aussitôt fait d'elle une catégorie
fourre-tout où le modèle se réfugiait. Or la phase 4 doit faire
l'inverse : dégager une typologie EMPIRIQUE. Il lui faut donc des
variables, pas des étiquettes.

Ces traits sont entièrement déterministes, calculés en quelques
secondes sur les 264 charts, sans modèle et sans mémoire GPU. Ils
mesurent trois choses :

  - la FORME de l'occupation de l'espace (proportions de l'image,
    densité du texte, régularité des rangées et des colonnes) ;
  - la TYPOGRAPHIE (dispersion des hauteurs de ligne, qui trahit une
    hiérarchie de titres et de sous-titres) ;
  - le RÉGIME D'ÉCRITURE (longueur des lignes : des légendes de trois
    mots ne relèvent pas du même geste éditorial qu'un commentaire
    suivi).

Contrôle externe : le codage des formes des 264 charts
(data/interim/codage_manuel_formes.csv, produit par un modèle
vision-langage distant — voir l'en-tête de ce fichier) sert à vérifier
que les groupes obtenus correspondent à des formes reconnaissables ; les
catégories du wiki fournissent un second point de comparaison, avec une
classification indigène. Ces deux colonnes sont dans le tableau mais ne
doivent PAS entrer dans le clustering : elles servent à le juger, pas à
le construire.

Écarts médians observés entre formes : les listes se détachent par des
lignes de 30 caractères contre 12 pour les grilles, les organigrammes
par un format paysage (ratio hauteur/largeur 0,95 contre 1,3-1,4), les
grilles à sections des grilles nues par leur diversité typographique
(0,52 contre 0,67 — les intitulés créent une hiérarchie de tailles).

Le script réécrit le tableau à chaque appel : instantané, rien à
reprendre.
"""

import argparse
import csv
import json
import statistics
import sys
from pathlib import Path

# --- Chemins du projet ---
RACINE = Path(__file__).resolve().parents[1]
DOSSIER_OCR = RACINE / "data" / "interim" / "ocr"
DOSSIER_MARQUEURS = RACINE / "data" / "interim" / "marqueurs"
INVENTAIRE = RACINE / "data" / "interim" / "inventaire_images.csv"
CODAGE_MANUEL = RACINE / "data" / "interim" / "codage_manuel_formes.csv"
SORTIE = RACINE / "data" / "processed" / "traits.csv"

REGISTRES = ["niveaux_nommes", "hierarchie_valeur", "point_entree", "difficulte",
             "prerequis", "optionnel", "recompense", "injonction", "progression"]


def coefficient_variation(valeurs):
    """Écart-type rapporté à la moyenne — sans unité, donc comparable."""
    if len(valeurs) < 2:
        return 0.0
    moyenne = statistics.mean(valeurs)
    return statistics.pstdev(valeurs) / moyenne if moyenne else 0.0


def calculer_traits(donnees):
    """Vecteur de traits d'un chart, à partir de son OCR."""
    lignes = [l for l in donnees.get("lignes", []) if l.get("texte", "").strip()]
    largeur, hauteur_img = donnees.get("taille_origine", [0, 0])
    if not lignes or not largeur or not hauteur_img:
        return None

    hauteurs = [l["bbox"][3] - l["bbox"][1] for l in lignes]
    largeurs = [l["bbox"][2] - l["bbox"][0] for l in lignes]
    longueurs = [len(l["texte"]) for l in lignes]
    hauteur_ligne = statistics.median(hauteurs) or 1

    # Regroupement en bandes horizontales : une rangée de légendes en
    # peuple plusieurs à la fois, un paragraphe une seule.
    bandes = {}
    for ligne in lignes:
        centre = (ligne["bbox"][1] + ligne["bbox"][3]) / 2
        bandes.setdefault(int(centre // hauteur_ligne), []).append(ligne)
    peuplees = [v for v in bandes.values() if len(v) >= 3]

    # Régularité des colonnes : proche de 0 sur une grille dont les
    # colonnes sont équidistantes, élevé sur une disposition libre.
    ecarts = []
    for bande in peuplees:
        xs = sorted(l["bbox"][0] for l in bande)
        ecarts += [suivant - courant for courant, suivant in zip(xs, xs[1:])]

    aire_texte = sum(h * w for h, w in zip(hauteurs, largeurs))
    return {
        "ratio_hauteur_largeur": round(hauteur_img / largeur, 3),
        "nb_lignes": len(lignes),
        "densite_texte": round(aire_texte / (largeur * hauteur_img), 4),
        "couverture_verticale": round(len(bandes) * hauteur_ligne / hauteur_img, 3),
        "part_bandes_peuplees": round(len(peuplees) / len(bandes), 3),
        "regularite_colonnes": round(coefficient_variation(ecarts), 3),
        "cv_hauteurs_lignes": round(coefficient_variation(hauteurs), 3),
        "longueur_moyenne_ligne": round(statistics.mean(longueurs), 1),
        "part_lignes_courtes": round(sum(1 for x in longueurs if x <= 25) / len(lignes), 3),
        "confiance_mediane": round(statistics.median(
            [l.get("confiance") or 0 for l in lignes]), 4),
    }


def charger_csv(chemin, cle):
    """Indexe un CSV par une colonne, {} s'il est absent.

    Les lignes commençant par « # » sont ignorées : le fichier de
    codage porte en tête sa provenance, qui doit voyager avec lui.
    """
    if not chemin.exists():
        return {}
    with open(chemin, newline="", encoding="utf-8") as fichier:
        lignes = [l for l in fichier if not l.startswith("#")]
    return {l[cle]: l for l in csv.DictReader(lignes)}


def principal():
    parseur = argparse.ArgumentParser(
        description="Calcule les traits mesurables des charts à partir de l'OCR.")
    parseur.add_argument("--sortie", default=str(SORTIE),
                         help="fichier CSV de destination (défaut : %(default)s)")
    args = parseur.parse_args()

    fichiers = sorted(DOSSIER_OCR.glob("*.json"))
    if not fichiers:
        sys.exit(f"Aucun OCR dans {DOSSIER_OCR} : lancer d'abord src/01_ocr.py")

    inventaire = charger_csv(INVENTAIRE, "fichier")
    manuel = charger_csv(CODAGE_MANUEL, "fichier")

    lignes_sortie, sans_traits = [], 0
    for chemin in fichiers:
        donnees = json.loads(chemin.read_text(encoding="utf-8"))
        traits = calculer_traits(donnees)
        if traits is None:
            sans_traits += 1
            continue
        nom = donnees.get("fichier", chemin.stem)

        # Marqueurs lexicaux (phase 3, volet déterministe) : ils entrent
        # dans la même matrice, la forme et le discours devant être
        # confrontés dans une même typologie.
        marqueurs = {}
        chemin_m = DOSSIER_MARQUEURS / chemin.name
        if chemin_m.exists():
            registres = json.loads(chemin_m.read_text(encoding="utf-8")).get("registres", {})
            marqueurs = {f"m_{r}": registres.get(r, {}).get("occurrences", 0)
                         for r in REGISTRES}

        lignes_sortie.append({
            "fichier": nom,
            "categorie": inventaire.get(nom, {}).get("categorie", ""),
            # Vide sauf pour les 30 charts du contrôle manuel : c'est la
            # colonne qui permettra de juger les groupes obtenus.
            "layout_manuel": manuel.get(nom, {}).get("layout_manuel", ""),
            **traits,
            **marqueurs,
        })

    if not lignes_sortie:
        sys.exit("Aucun trait calculable.")

    colonnes = list(lignes_sortie[0].keys())
    chemin_sortie = Path(args.sortie)
    chemin_sortie.parent.mkdir(parents=True, exist_ok=True)
    with open(chemin_sortie, "w", newline="", encoding="utf-8") as fichier:
        writer = csv.DictWriter(fichier, fieldnames=colonnes)
        writer.writeheader()
        writer.writerows(lignes_sortie)

    controle = sum(1 for l in lignes_sortie if l["layout_manuel"])
    print(f"{chemin_sortie} : {len(lignes_sortie)} charts, "
          f"{len(colonnes) - 3} variables.")
    print(f"  dont {controle} avec forme codée à la main (contrôle externe).")
    if sans_traits:
        print(f"  {sans_traits} chart(s) sans texte exploitable, écarté(s).")


if __name__ == "__main__":
    principal()
