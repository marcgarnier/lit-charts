#!/usr/bin/env python3
"""Phase 2c — Classement visuel des charts par modèle vision-langage.

Envoie chaque image de data/raw/images/ à un VLM servi par Ollama en
local (qwen2.5vl par défaut) et sauvegarde un JSON par chart dans
data/interim/vlm/ : layout_type, has_arrows, colors.

PÉRIMÈTRE VOLONTAIREMENT ÉTROIT. Ce script ne demande PAS au modèle de
lire le chart ni d'en extraire les œuvres. Le texte vient de Surya
(phase 2a, lecture en pleine résolution) et le rattachement des œuvres
à leur section vient de la géométrie (phase 2b, déterministe). Il ne
reste ici que ce qu'aucune des deux ne peut établir : la FORME générale
du chart et la présence de liens dessinés.

Ce partage n'est pas une préférence de style, il est mesuré. Chargé
d'extraire aussi les titres, le même modèle mettait 11 minutes par image
et rendait un résultat inutilisable : sur « /lit/'s Top 100 Books », 5
livres hallucinés au lieu de 100, des rangs faux et des flèches
imaginaires sur une grille qui n'en comporte aucune. Réduit à la seule
question de forme, il répond juste (« map » avec liens sur la carte de
philosophie) en moins de 2 minutes.

Reprise : une image dont le JSON existe déjà est sautée ; --force
retraite tout. Les réponses illisibles sont consignées en
*.erreur.json pour diagnostic, sans interrompre le run.

Matériel : sur une machine à 8 Go de RAM, ne pas lancer en même temps
que la phase 2a — les deux modèles ne tiennent pas ensemble.
"""

import argparse
import base64
import io
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests
from PIL import Image

# --- Chemins du projet ---
RACINE = Path(__file__).resolve().parents[1]
DOSSIER_IMAGES = RACINE / "data" / "raw" / "images"
DOSSIER_SORTIE = RACINE / "data" / "interim" / "vlm"
FICHIER_PROMPT = RACINE / "prompts" / "vlm.txt"

EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}

# Valeurs admises pour layout_type (contrat du prompt). Une réponse hors
# de cette liste est conservée mais signalée : le corpus peut réserver
# des formes imprévues, autant les voir plutôt que les écraser.
TYPES_CONNUS = {"tier_list", "flowchart", "sectioned_grid", "grid", "list",
                "map", "wheel", "collage", "other"}

Image.MAX_IMAGE_PIXELS = None


def encoder_image(chemin, cote_max):
    """Charge une image, la réduit et la renvoie en base64.

    500 px suffisent amplement : à cette taille la forme d'ensemble
    (bandes, colonnes, grappes reliées) reste parfaitement lisible,
    alors que le texte ne l'est plus — ce qui n'a aucune importance
    puisqu'on ne demande pas au modèle de lire.
    """
    image = Image.open(chemin).convert("RGB")
    if max(image.size) > cote_max:
        image.thumbnail((cote_max, cote_max), Image.LANCZOS)
    tampon = io.BytesIO()
    image.save(tampon, format="JPEG", quality=85)
    return base64.b64encode(tampon.getvalue()).decode("ascii"), image.size


def interroger_vlm(url, modele, prompt, image_b64, timeout, contexte, jetons):
    """Appelle l'API generate d'Ollama et renvoie le texte brut."""
    reponse = requests.post(f"{url}/api/generate", timeout=timeout, json={
        "model": modele,
        "prompt": prompt,
        "images": [image_b64],
        "format": "json",       # Ollama contraint la sortie à du JSON valide
        "stream": False,
        # temperature 0 : classement, on veut du déterminisme.
        # num_predict borne la réponse : elle tient en quelques dizaines
        # de jetons, inutile de laisser le modèle divaguer.
        "options": {"temperature": 0, "num_ctx": contexte, "num_predict": jetons},
    })
    reponse.raise_for_status()
    return reponse.json()["response"]


def valider(brut):
    """Parse la réponse et vérifie le contrat minimal du prompt."""
    try:
        extraction = json.loads(brut)
    except json.JSONDecodeError as erreur:
        return None, f"JSON invalide : {erreur}"
    if not isinstance(extraction, dict):
        return None, "la réponse n'est pas un objet JSON"
    if "layout_type" not in extraction:
        return None, "clé « layout_type » absente"
    # has_arrows et colors sont souhaitables mais non bloquants : le
    # modèle les omet parfois, et un classement sans elles reste utile.
    extraction.setdefault("has_arrows", None)
    extraction.setdefault("colors", [])
    return extraction, None


def traiter_image(chemin, args, consigne):
    """Traite une image ; renvoie 'ok', 'erreur' ou 'saut'."""
    sortie = DOSSIER_SORTIE / (chemin.stem + ".json")
    sortie_erreur = DOSSIER_SORTIE / (chemin.stem + ".erreur.json")
    if sortie.exists() and not args.force:
        return "saut"

    debut = time.time()
    image_b64, taille = encoder_image(chemin, args.cote_max)
    try:
        brut = interroger_vlm(args.url, args.modele, consigne, image_b64,
                              args.timeout, args.contexte, args.jetons)
    except requests.RequestException as erreur:
        print(f"  [erreur] {chemin.name} : appel Ollama échoué ({erreur})", flush=True)
        return "erreur"

    extraction, probleme = valider(brut)
    duree = round(time.time() - debut, 1)
    enveloppe = {
        "fichier": chemin.name,
        "modele": args.modele,
        "date": datetime.now(timezone.utc).isoformat(),
        "duree_s": duree,
        "taille_envoyee": list(taille),
    }

    if probleme is not None:
        enveloppe.update({"probleme": probleme, "reponse_brute": brut})
        sortie_erreur.write_text(json.dumps(enveloppe, ensure_ascii=False, indent=2),
                                 encoding="utf-8")
        print(f"  [erreur] {chemin.name} : {probleme}", flush=True)
        return "erreur"

    enveloppe["extraction"] = extraction
    sortie.write_text(json.dumps(enveloppe, ensure_ascii=False, indent=2),
                      encoding="utf-8")
    sortie_erreur.unlink(missing_ok=True)  # ancien échec devenu obsolète

    type_lu = extraction.get("layout_type")
    alerte = "" if type_lu in TYPES_CONNUS else "  [type inattendu]"
    print(f"  [ok] {chemin.name} : {type_lu}, flèches={extraction.get('has_arrows')}, "
          f"{duree} s{alerte}", flush=True)
    return "ok"


def principal():
    parseur = argparse.ArgumentParser(
        description="Phase 2c : classement visuel des charts par VLM (Ollama).")
    parseur.add_argument("--modele", default="qwen2.5vl:3b",
                         help="modèle Ollama à utiliser (défaut : %(default)s)")
    parseur.add_argument("--url", default="http://localhost:11434",
                         help="URL du serveur Ollama (défaut : %(default)s)")
    parseur.add_argument("--limite", type=int, default=None,
                         help="ne traiter que N images (pour tester)")
    parseur.add_argument("--fichier", nargs="+", default=None,
                         help="ne traiter que ces images (noms de fichiers)")
    parseur.add_argument("--cote-max", type=int, default=500,
                         help="côté max en pixels avant envoi ; 500 suffit à lire la "
                              "forme et va 7 fois plus vite que 900 (défaut : %(default)s)")
    parseur.add_argument("--contexte", type=int, default=2048,
                         help="taille du contexte Ollama en jetons (défaut : %(default)s)")
    parseur.add_argument("--jetons", type=int, default=120,
                         help="longueur max de la réponse en jetons (défaut : %(default)s)")
    parseur.add_argument("--timeout", type=float, default=600,
                         help="délai max par image en secondes (défaut : %(default)s)")
    parseur.add_argument("--force", action="store_true",
                         help="retraite aussi les images déjà classées")
    args = parseur.parse_args()

    DOSSIER_SORTIE.mkdir(parents=True, exist_ok=True)
    consigne = FICHIER_PROMPT.read_text(encoding="utf-8")

    images = sorted(p for p in DOSSIER_IMAGES.iterdir()
                    if p.suffix.lower() in EXTENSIONS)
    if not images:
        sys.exit(f"Aucune image dans {DOSSIER_IMAGES}")
    if args.fichier:
        voulus = set(args.fichier)
        images = [p for p in images if p.name in voulus]
        introuvables = voulus - {p.name for p in images}
        if introuvables:
            sys.exit(f"Introuvable(s) : {sorted(introuvables)}")
    if args.limite:
        images = images[:args.limite]

    print(f"{len(images)} images à classer avec {args.modele}", flush=True)
    bilan = {"ok": 0, "erreur": 0, "saut": 0}
    try:
        for chemin in images:
            bilan[traiter_image(chemin, args, consigne)] += 1
    except KeyboardInterrupt:
        print("\n[interruption] relancer le script reprendra où il s'est arrêté.")
        sys.exit(130)

    print(f"Terminé : {bilan['ok']} classées, {bilan['erreur']} en erreur, "
          f"{bilan['saut']} déjà faites.")


if __name__ == "__main__":
    principal()
