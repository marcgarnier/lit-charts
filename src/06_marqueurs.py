#!/usr/bin/env python3
"""Phase 3 (volet déterministe) — Marqueurs lexicaux de gamification.

Cherche dans le texte intégral de chaque chart (data/interim/ocr/) le
vocabulaire propre aux dispositifs gamifiés — paliers nommés, hiérarchie
de valeur, point d'entrée, difficulté, prérequis, injonctions — et écrit
un JSON par chart dans data/interim/marqueurs/ : le compte par registre
et les extraits qui le justifient.

POURQUOI CE VOLET EXISTE. La reconstruction fine de la structure ne
tient pas sur tout le corpus : certains charts ne portent leurs œuvres
que sous forme de couvertures, sans aucune légende, et aucun OCR n'en
tirera de titres. Or ce qui importe à l'étude n'est pas le catalogue
exact des œuvres mais la NATURE du dispositif. Or celle-ci se lit dans
les mots employés, indépendamment de toute mise en page : un chart qui
écrit « God-Tier », « start with the Greeks » ou « do not skip » se
déclare comme dispositif prescriptif, que ses sections soient
correctement découpées ou non.

Cette étape est donc robuste là où la géométrie échoue, et elle est
entièrement déterministe : mêmes entrées, mêmes sorties, vérifiables à
la main. Elle fournit à `04_codage.py` des preuves textuelles, et lui
sert de garde-fou : un codage qui affirme une mécanique dont aucun
marqueur n'apparaît mérite d'être relu.

Le lexique est versionné dans prompts/marqueurs.json et modifiable sans
toucher au code — c'est l'instrument de mesure de l'étude, il doit
pouvoir être discuté et amendé.

Reprise : un chart déjà traité est sauté ; --force retraite tout. Le
script est quasi instantané sur les 264 charts.
"""

import argparse
import json
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

# --- Chemins du projet ---
RACINE = Path(__file__).resolve().parents[1]
DOSSIER_OCR = RACINE / "data" / "interim" / "ocr"
DOSSIER_SORTIE = RACINE / "data" / "interim" / "marqueurs"
FICHIER_LEXIQUE = RACINE / "prompts" / "marqueurs.json"


def charger_lexique():
    """Lit le lexique et compile ses expressions régulières.

    Les clés commençant par « _ » sont des commentaires destinés au
    lecteur du fichier, pas des registres.
    """
    brut = json.loads(FICHIER_LEXIQUE.read_text(encoding="utf-8"))
    lexique = {}
    for registre, contenu in brut.items():
        if registre.startswith("_"):
            continue
        motifs = [re.compile(m, re.IGNORECASE) for m in contenu["motifs"]]
        lexique[registre] = {"definition": contenu.get("definition", ""),
                             "motifs": motifs}
    if not lexique:
        sys.exit(f"Lexique vide : {FICHIER_LEXIQUE}")
    return lexique


def analyser(donnees_ocr, lexique, extraits_max):
    """Compte les marqueurs d'un chart et retient des extraits probants."""
    lignes = [l["texte"] for l in donnees_ocr.get("lignes", []) if l.get("texte")]
    texte = "\n".join(lignes)

    registres = {}
    for nom, contenu in lexique.items():
        occurrences, extraits = 0, []
        for motif in contenu["motifs"]:
            for ligne in lignes:
                trouves = motif.findall(ligne)
                if not trouves:
                    continue
                occurrences += len(trouves)
                # L'extrait est la ligne entière : c'est elle qui permet
                # de juger si le marqueur est pertinent ou fortuit.
                if len(extraits) < extraits_max and ligne not in extraits:
                    extraits.append(ligne.strip()[:120])
        registres[nom] = {"occurrences": occurrences, "extraits": extraits}

    actifs = [nom for nom, v in registres.items() if v["occurrences"] > 0]
    return {
        "fichier": donnees_ocr.get("fichier"),
        "date": datetime.now(timezone.utc).isoformat(),
        "nb_lignes_texte": len(lignes),
        "nb_caracteres": len(texte),
        "registres_actifs": actifs,
        "score_total": sum(v["occurrences"] for v in registres.values()),
        "registres": registres,
    }


def principal():
    parseur = argparse.ArgumentParser(
        description="Phase 3 : marqueurs lexicaux de gamification (déterministe).")
    parseur.add_argument("--fichier", nargs="+", default=None,
                         help="ne traiter que ces charts (noms d'images ou de JSON)")
    parseur.add_argument("--extraits-max", type=int, default=4,
                         help="extraits conservés par registre, pour vérification "
                              "manuelle (défaut : %(default)s)")
    parseur.add_argument("--force", action="store_true",
                         help="retraite aussi les charts déjà analysés")
    parseur.add_argument("--resume", action="store_true",
                         help="affiche en fin de run la synthèse sur tout le corpus")
    args = parseur.parse_args()

    if not DOSSIER_OCR.exists():
        sys.exit(f"Aucun OCR dans {DOSSIER_OCR} : lancer d'abord src/01_ocr.py")
    DOSSIER_SORTIE.mkdir(parents=True, exist_ok=True)
    lexique = charger_lexique()

    fichiers = sorted(DOSSIER_OCR.glob("*.json"))
    if args.fichier:
        voulus = {Path(f).stem for f in args.fichier}
        fichiers = [f for f in fichiers if f.stem in voulus]
        introuvables = voulus - {f.stem for f in fichiers}
        if introuvables:
            sys.exit(f"Sans OCR : {sorted(introuvables)}")
    if not fichiers:
        sys.exit(f"Aucun OCR à analyser dans {DOSSIER_OCR}")

    bilan = {"ok": 0, "saut": 0}
    for chemin in fichiers:
        sortie = DOSSIER_SORTIE / chemin.name
        if sortie.exists() and not args.force:
            bilan["saut"] += 1
            continue
        resultat = analyser(json.loads(chemin.read_text(encoding="utf-8")),
                            lexique, args.extraits_max)
        sortie.write_text(json.dumps(resultat, ensure_ascii=False, indent=2),
                          encoding="utf-8")
        bilan["ok"] += 1

    print(f"Terminé : {bilan['ok']} charts analysés, {bilan['saut']} déjà faits.")

    if args.resume:
        tous = [json.loads(p.read_text(encoding="utf-8"))
                for p in sorted(DOSSIER_SORTIE.glob("*.json"))]
        compte = Counter(r for c in tous for r in c["registres_actifs"])
        print(f"\n=== Synthèse sur {len(tous)} charts ===")
        for registre in lexique:
            n = compte.get(registre, 0)
            print(f"  {registre:<20} {n:>4} charts ({n/len(tous):>4.0%})  "
                  f"— {lexique[registre]['definition']}")


if __name__ == "__main__":
    principal()
