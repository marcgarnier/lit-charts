#!/usr/bin/env python3
"""Fiabilité — accord entre annotateurs (alpha de Krippendorff).

Compare le codage des formes de charts produit par deux annotateurs :

  - le codage de référence, dans data/interim/codage_manuel_formes.csv ;
  - le classement automatique du modèle local, dans data/interim/vlm/.

Écrit le rapport dans results/accord_inter_codeurs.txt et l'affiche.

POURQUOI L'ALPHA ET NON LE TAUX D'ACCORD. Le taux d'accord brut est
trompeur dès qu'une catégorie domine : sur ce corpus, un annotateur qui
répondrait toujours la même étiquette, sans regarder les images,
obtiendrait déjà 31 à 33 % d'accord. L'alpha rapporte le désaccord
OBSERVÉ au désaccord ATTENDU si les étiquettes étaient distribuées au
hasard en respectant les fréquences de chacun :

    alpha = 1 - (désaccord observé / désaccord attendu)

Il vaut 1 pour un accord parfait, 0 pour un accord équivalent au hasard,
et devient négatif en deçà — ce qui arrive précisément aux annotateurs
constants, démasqués par cette mesure là où le taux d'accord les
flattait. C'est la raison de son adoption en analyse de contenu, avec
l'avantage sur le kappa de Cohen d'accepter plus de deux annotateurs,
des catégories multiples et des données manquantes.

Seuils d'interprétation retenus par Krippendorff :
  alpha >= 0,800  fiable, conclusions permises
  0,667 - 0,800   acceptable pour des conclusions provisoires
  < 0,667         insuffisant, la variable ne doit pas être exploitée

PROVENANCE DU CODAGE DE RÉFÉRENCE — à déclarer dans toute publication.
Il n'a pas été produit par un humain, mais par un modèle vision-langage
distant (Claude), qui a examiné les 264 images. Ce n'est donc pas un
accord entre deux juges symétriques mais une VALIDATION du modèle local
contre un modèle de référence bien plus grand. Deux conséquences : la
référence a servi à construire la taxonomie, ce qui l'avantage
structurellement ; et elle ne fait pas partie du pipeline local et
reproductible, dont elle reste extérieure.
"""

import argparse
import csv
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

# --- Chemins du projet ---
RACINE = Path(__file__).resolve().parents[1]
CODAGE_REF = RACINE / "data" / "interim" / "codage_manuel_formes.csv"
DOSSIER_VLM = RACINE / "data" / "interim" / "vlm"
SORTIE = RACINE / "results" / "accord_inter_codeurs.txt"

SEUILS = [(0.800, "fiable — conclusions permises"),
          (0.667, "acceptable — conclusions provisoires seulement"),
          (0.000, "INSUFFISANT — la variable ne doit pas être exploitée")]


def alpha_krippendorff(paires):
    """Alpha nominal pour deux annotateurs et des unités complètes.

    Chaque unité verse ses deux paires ordonnées dans la matrice de
    coïncidence, pondérées 1/(m-1) = 1 puisque m = 2 annotateurs.
    Renvoie (alpha, désaccord observé, désaccord attendu).
    """
    if len(paires) < 2:
        return float("nan"), float("nan"), float("nan")
    coincidences = defaultdict(float)
    for premier, second in paires:
        coincidences[(premier, second)] += 1.0
        coincidences[(second, premier)] += 1.0

    valeurs = sorted({v for paire in paires for v in paire})
    marges = {c: sum(coincidences[(c, k)] for k in valeurs) for c in valeurs}
    total = sum(marges.values())

    observe = sum(coincidences[(c, k)]
                  for c in valeurs for k in valeurs if c != k) / total
    attendu = sum(marges[c] * marges[k]
                  for c in valeurs for k in valeurs if c != k) / (total * (total - 1))
    if attendu == 0:
        return float("nan"), observe, attendu
    return 1 - observe / attendu, observe, attendu


def qualifier(valeur):
    """Traduit un alpha en verdict d'exploitabilité."""
    if valeur != valeur:          # NaN
        return "incalculable"
    for seuil, libelle in SEUILS:
        if valeur >= seuil:
            return libelle
    return "NÉGATIF — pire que le hasard"


def collecter():
    """Apparie les deux codages sur les charts communs."""
    if not CODAGE_REF.exists():
        sys.exit(f"Codage de référence absent : {CODAGE_REF}")
    with open(CODAGE_REF, newline="", encoding="utf-8") as fichier:
        # Les lignes « # » en tête portent la provenance du codage.
        lignes = [l for l in fichier if not l.startswith("#")]
    reference = {l["fichier"]: l for l in csv.DictReader(lignes)}

    formes, fleches = [], []
    for chemin in sorted(DOSSIER_VLM.glob("*.json")):
        if chemin.name.endswith(".erreur.json"):
            continue
        donnees = json.loads(chemin.read_text(encoding="utf-8"))
        extraction = donnees.get("extraction") or {}
        nom = donnees.get("fichier")
        if nom not in reference:
            continue
        if extraction.get("layout_type"):
            formes.append((reference[nom]["layout_manuel"], extraction["layout_type"]))
        if extraction.get("has_arrows") is not None:
            fleches.append((reference[nom]["fleches"] == "oui",
                            bool(extraction["has_arrows"])))
    return reference, formes, fleches


def rapport_variable(titre, paires, lignes):
    """Ajoute au rapport le bloc d'une variable."""
    if not paires:
        lignes.append(f"{titre} : aucun chart en commun.")
        return
    valeur, observe, attendu = alpha_krippendorff(paires)
    accord = sum(1 for a, b in paires if a == b)
    lignes += [
        f"{titre}  ({len(paires)} charts communs)",
        f"    alpha de Krippendorff : {valeur:.3f}   -> {qualifier(valeur)}",
        f"    désaccord observé     : {observe:.3f}",
        f"    désaccord attendu     : {attendu:.3f}",
        f"    accord brut           : {accord}/{len(paires)} = {accord/len(paires):.0%}",
        "",
    ]


def principal():
    parseur = argparse.ArgumentParser(
        description="Accord inter-codeurs (alpha de Krippendorff).")
    parseur.add_argument("--sortie", default=str(SORTIE),
                         help="fichier de rapport (défaut : %(default)s)")
    args = parseur.parse_args()

    reference, formes, fleches = collecter()
    if not formes and not fleches:
        sys.exit("Aucun chart classé par le modèle local : lancer src/03_vlm.py.")

    lignes = [
        "ACCORD INTER-CODEURS — formes des charts de /lit/",
        f"généré le {datetime.now(timezone.utc).isoformat(timespec='seconds')}",
        "",
        "Annotateur A (référence) : modèle vision-langage distant (Claude),",
        "                           codage des 264 images, taxonomie construite",
        "                           inductivement sur le corpus.",
        "Annotateur B             : modèle local qwen2.5vl:3b via Ollama (src/03_vlm.py).",
        "",
        f"Corpus codé en référence : {len(reference)} charts.",
        "",
        "-" * 68,
        "",
    ]
    rapport_variable("LAYOUT_TYPE  (nominal, 7 catégories)", formes, lignes)
    rapport_variable("HAS_ARROWS   (nominal, binaire)", fleches, lignes)

    if formes:
        # Repère : ce qu'obtiendrait un annotateur constant. Il rend
        # lisible d'un coup d'œil ce que l'alpha corrige.
        vrais = [a for a, _ in formes]
        dominante = Counter(vrais).most_common(1)[0][0]
        constant = list(zip(vrais, [dominante] * len(vrais)))
        valeur, _, _ = alpha_krippendorff(constant)
        accord = sum(1 for a, b in constant if a == b)
        lignes += [
            "-" * 68, "",
            "REPÈRE — annotateur constant (répond toujours « "
            f"{dominante} », sans regarder les images) :",
            f"    accord brut {accord/len(constant):.0%}, alpha {valeur:.3f}",
            "    Un taux d'accord d'un tiers s'obtient donc sans aucune compétence :",
            "    c'est exactement ce que l'alpha corrige.",
            "",
            "Répartition des étiquettes :",
            f"    référence     : {dict(Counter(a for a, _ in formes))}",
            f"    modèle local  : {dict(Counter(b for _, b in formes))}",
            "",
        ]

    texte = "\n".join(lignes)
    chemin = Path(args.sortie)
    chemin.parent.mkdir(parents=True, exist_ok=True)
    chemin.write_text(texte, encoding="utf-8")
    print(texte)
    print(f"[écrit dans {chemin}]")


if __name__ == "__main__":
    principal()
