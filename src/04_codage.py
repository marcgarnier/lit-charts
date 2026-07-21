#!/usr/bin/env python3
"""Phase 3 — Codage des mécaniques de gamification par LLM de texte.

Croise, pour chaque chart, la structure reconstruite en phase 2b
(data/interim/blocs/) et le type de mise en page relevé en phase 2c
(data/interim/vlm/), en fait une description textuelle compacte, et la
soumet à un LLM de TEXTE servi par Ollama en local (llama3.1 par
défaut) avec la grille de codage de prompts/codage.txt. Écrit un JSON
par chart dans data/interim/codage/.

POURQUOI UN MODÈLE DE TEXTE ET NON DE VISION. Une fois l'OCR et la
géométrie passés, il ne reste plus d'image : le chart est devenu du
texte structuré, et le coder est une tâche de lecture, pas de vision.
Mesuré sur la carte de philosophie : 45 s avec llama3.1 (8B) contre
11 min avec qwen2.5vl (3B) — et le modèle de texte, à taille bien
supérieure, raisonne nettement mieux sur les intitulés de sections.

Le chart est rendu en quelques centaines de jetons seulement : les
sections avec leur position et leurs premières œuvres suffisent à juger
d'une progression ou d'un embranchement, inutile de déverser les 500
entrées d'un chart encyclopédique dans le contexte.

Reprise : un chart dont le JSON existe déjà est sauté ; --force
retraite tout. Les réponses illisibles sont consignées en
*.erreur.json sans interrompre le run.
"""

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

# --- Chemins du projet ---
RACINE = Path(__file__).resolve().parents[1]
DOSSIER_BLOCS = RACINE / "data" / "interim" / "blocs"
DOSSIER_VLM = RACINE / "data" / "interim" / "vlm"
DOSSIER_SORTIE = RACINE / "data" / "interim" / "codage"
FICHIER_PROMPT = RACINE / "prompts" / "codage.txt"

# Clés attendues dans la réponse (contrat du prompt).
CLES_ATTENDUES = {"mecaniques", "ordinal_labels", "point_entree", "ton",
                  "justification"}
MECANIQUES_ATTENDUES = {"progression", "prerequis", "niveaux_de_difficulte",
                        "embranchements", "recompenses", "injonction"}


def decrire_chart(blocs, vlm, max_oeuvres):
    """Rend un chart sous forme de texte compact pour le LLM.

    On donne la position de chaque section : elle porte la lecture
    spatiale (de haut en bas, de gauche à droite) sur laquelle repose
    tout jugement de progression.
    """
    lignes = [f"CHART: {blocs.get('fichier')}"]
    if vlm:
        extraction = vlm.get("extraction", {})
        lignes.append(f"VISUAL LAYOUT: {extraction.get('layout_type')} "
                      f"(arrows drawn: {extraction.get('has_arrows')}, "
                      f"colors: {', '.join(extraction.get('colors') or []) or 'n/a'})")
    taille = blocs.get("taille_origine") or [0, 0]
    lignes.append(f"IMAGE SIZE: {taille[0]}x{taille[1]} px")
    lignes.append(f"SECTIONS: {blocs.get('nb_blocs')} blocks, "
                  f"{blocs.get('nb_noeuds')} works total")

    for bloc in blocs.get("blocs", []):
        x, y = int(bloc["bbox"][0]), int(bloc["bbox"][1])
        intitule = bloc["tier"] or "(no heading)"
        noeuds = bloc.get("noeuds", [])
        lignes.append(f"\nSECTION at ({x},{y}) — {intitule}  [{len(noeuds)} works]")
        for noeud in noeuds[:max_oeuvres]:
            auteur = f"{noeud['auteur']}: " if noeud.get("auteur") else ""
            lignes.append(f"  - {auteur}{noeud['titre']}")
        if len(noeuds) > max_oeuvres:
            lignes.append(f"  ... (+{len(noeuds) - max_oeuvres} more)")
    return "\n".join(lignes)


def interroger(url, modele, prompt, timeout, contexte):
    """Appelle l'API generate d'Ollama et renvoie le texte brut."""
    reponse = requests.post(f"{url}/api/generate", timeout=timeout, json={
        "model": modele,
        "prompt": prompt,
        "format": "json",       # Ollama contraint la sortie à du JSON valide
        "stream": False,
        # temperature 0 : un codage doit être reproductible d'un run à
        # l'autre, c'est la condition pour que les résultats soient
        # vérifiables.
        "options": {"temperature": 0, "num_ctx": contexte},
    })
    reponse.raise_for_status()
    return reponse.json()["response"]


def valider(brut):
    """Parse la réponse et vérifie le contrat de la grille de codage."""
    try:
        codage = json.loads(brut)
    except json.JSONDecodeError as erreur:
        return None, f"JSON invalide : {erreur}"
    if not isinstance(codage, dict):
        return None, "la réponse n'est pas un objet JSON"
    manquantes = CLES_ATTENDUES - codage.keys()
    if manquantes:
        return None, f"clés manquantes : {sorted(manquantes)}"
    if not isinstance(codage.get("mecaniques"), dict):
        return None, "« mecaniques » n'est pas un objet"
    # Une mécanique non citée vaut « non observée » : on complète plutôt
    # que de rejeter, pour ne pas perdre un codage par ailleurs correct.
    for cle in MECANIQUES_ATTENDUES:
        codage["mecaniques"].setdefault(cle, False)
    return codage, None


def traiter(chemin_blocs, args, consigne):
    """Code un chart ; renvoie 'ok', 'erreur' ou 'saut'."""
    sortie = DOSSIER_SORTIE / chemin_blocs.name
    sortie_erreur = DOSSIER_SORTIE / (chemin_blocs.stem + ".erreur.json")
    if sortie.exists() and not args.force:
        return "saut"

    blocs = json.loads(chemin_blocs.read_text(encoding="utf-8"))
    chemin_vlm = DOSSIER_VLM / chemin_blocs.name
    # Le classement visuel est un plus, pas un prérequis : sans lui le
    # codage reste possible, simplement moins informé.
    vlm = (json.loads(chemin_vlm.read_text(encoding="utf-8"))
           if chemin_vlm.exists() else None)

    description = decrire_chart(blocs, vlm, args.max_oeuvres)
    debut = time.time()
    try:
        brut = interroger(args.url, args.modele, f"{consigne}\n\n{description}",
                          args.timeout, args.contexte)
    except requests.RequestException as erreur:
        print(f"  [erreur] {chemin_blocs.stem} : appel Ollama échoué ({erreur})",
              flush=True)
        return "erreur"

    codage, probleme = valider(brut)
    duree = round(time.time() - debut, 1)
    enveloppe = {
        "fichier": blocs.get("fichier"),
        "modele": args.modele,
        "date": datetime.now(timezone.utc).isoformat(),
        "duree_s": duree,
        "layout_type": (vlm or {}).get("extraction", {}).get("layout_type"),
        "sans_vlm": vlm is None,
    }

    if probleme is not None:
        enveloppe.update({"probleme": probleme, "reponse_brute": brut})
        sortie_erreur.write_text(json.dumps(enveloppe, ensure_ascii=False, indent=2),
                                 encoding="utf-8")
        print(f"  [erreur] {chemin_blocs.stem} : {probleme}", flush=True)
        return "erreur"

    enveloppe["codage"] = codage
    sortie.write_text(json.dumps(enveloppe, ensure_ascii=False, indent=2),
                      encoding="utf-8")
    sortie_erreur.unlink(missing_ok=True)

    actives = [c for c, v in codage["mecaniques"].items() if v]
    print(f"  [ok] {blocs.get('fichier')} : {', '.join(actives) or 'aucune mécanique'} "
          f"| ton={codage.get('ton')} | {duree} s", flush=True)
    return "ok"


def principal():
    parseur = argparse.ArgumentParser(
        description="Phase 3 : codage des mécaniques de gamification (LLM de texte).")
    parseur.add_argument("--modele", default="llama3.1:latest",
                         help="modèle Ollama de TEXTE à utiliser (défaut : %(default)s)")
    parseur.add_argument("--url", default="http://localhost:11434",
                         help="URL du serveur Ollama (défaut : %(default)s)")
    parseur.add_argument("--limite", type=int, default=None,
                         help="ne traiter que N charts (pour tester)")
    parseur.add_argument("--fichier", nargs="+", default=None,
                         help="ne traiter que ces charts (noms d'images ou de JSON)")
    parseur.add_argument("--max-oeuvres", type=int, default=8,
                         help="œuvres citées par section dans le prompt "
                              "(défaut : %(default)s)")
    parseur.add_argument("--contexte", type=int, default=8192,
                         help="taille du contexte Ollama en jetons (défaut : %(default)s)")
    parseur.add_argument("--timeout", type=float, default=600,
                         help="délai max par chart en secondes (défaut : %(default)s)")
    parseur.add_argument("--force", action="store_true",
                         help="retraite aussi les charts déjà codés")
    args = parseur.parse_args()

    if not DOSSIER_BLOCS.exists():
        sys.exit(f"Aucune structure dans {DOSSIER_BLOCS} : lancer d'abord src/02_blocs.py")
    DOSSIER_SORTIE.mkdir(parents=True, exist_ok=True)
    consigne = FICHIER_PROMPT.read_text(encoding="utf-8")

    fichiers = sorted(DOSSIER_BLOCS.glob("*.json"))
    if not fichiers:
        sys.exit(f"Aucune structure dans {DOSSIER_BLOCS} : lancer d'abord src/02_blocs.py")
    if args.fichier:
        voulus = {Path(f).stem for f in args.fichier}
        fichiers = [f for f in fichiers if f.stem in voulus]
        introuvables = voulus - {f.stem for f in fichiers}
        if introuvables:
            sys.exit(f"Sans structure : {sorted(introuvables)}")
    if args.limite:
        fichiers = fichiers[:args.limite]

    print(f"{len(fichiers)} charts à coder avec {args.modele}", flush=True)
    bilan = {"ok": 0, "erreur": 0, "saut": 0}
    try:
        for chemin in fichiers:
            bilan[traiter(chemin, args, consigne)] += 1
    except KeyboardInterrupt:
        print("\n[interruption] relancer le script reprendra où il s'est arrêté.")
        sys.exit(130)

    print(f"Terminé : {bilan['ok']} codés, {bilan['erreur']} en erreur, "
          f"{bilan['saut']} déjà faits.")


if __name__ == "__main__":
    principal()
