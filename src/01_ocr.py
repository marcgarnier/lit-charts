#!/usr/bin/env python3
"""Phase 2a — OCR des charts.

Parcourt toutes les images de data/raw/images/, y lit les lignes de
texte et sauvegarde un JSON par chart dans data/interim/ocr/ : chaque
ligne avec son texte, sa boîte englobante et son score de confiance.
Les coordonnées sont exprimées dans le repère de l'image d'origine :
elles permettent à la phase 2b de reconstituer les blocs par géométrie.

DEUX MOTEURS, choisis par --moteur :

  vision (défaut) — l'OCR intégré à macOS (framework Vision), accéléré
    matériellement. L'image est découpée en bandes horizontales avant
    lecture : appliqué à l'image entière, Vision rate le petit texte des
    grands charts (2 titres sur 9 relevés sur « Top 100 »), alors qu'en
    bandes il les retrouve tous. Comme il traite une bande en une
    fraction de seconde, ce découpage ne coûte rien.

  surya — le moteur open source (https://github.com/datalab-to/surya),
    en PyTorch pur. Nettement plus lent, mais libre et rejouable sur
    n'importe quel système. Il sert de contrôle : rejouer un échantillon
    avec --moteur surya permet d'attester que les résultats ne tiennent
    pas à un composant propriétaire.

Écart mesuré sur le corpus, à qualité équivalente (mêmes 14 grappes
retrouvées sur la carte de philosophie, mêmes 9 titres et 8 auteurs sur
la grille) : 1,3 s contre 237 s, et 4,7 s contre 354 s. Soit environ
20 minutes contre 13 heures pour les 264 charts.

Le moteur employé est inscrit dans chaque JSON produit (champ
« moteur »), pour qu'un corpus mélangeant les deux reste traçable.

Version de Surya : ce script cible la lignée 0.16.x. Les versions >=
0.20 ont basculé sur un OCR « pleine page » qui exige le binaire externe
llama.cpp ou un GPU NVIDIA — inutilisable ici.

Reprise : une image dont le JSON existe déjà est sautée ; --force
retraite tout.
"""

import argparse
import html as module_html
import io
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image

# --- Chemins du projet ---
RACINE = Path(__file__).resolve().parents[1]
DOSSIER_IMAGES = RACINE / "data" / "raw" / "images"
DOSSIER_SORTIE = RACINE / "data" / "interim" / "ocr"

EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}

# Certaines images du corpus sont énormes (plus de 5000 px de côté) :
# Pillow refuse par défaut au-delà d'un seuil anti-« decompression bomb ».
# Le corpus est local et connu, on relève la limite.
Image.MAX_IMAGE_PIXELS = None


def nettoyer(texte):
    """Retire le balisage émis par Surya (<b>, <i>, <br>, entités HTML).

    Surya restitue la mise en forme repérée sur l'image : un titre en
    gras ressort en « <b>Blood Meridian</b> ». Utile à conserver, mais
    inexploitable tel quel pour apparier des titres et des auteurs en
    phases 4 et 5 — d'où ce champ « texte » normalisé, le balisage
    d'origine restant disponible dans « texte_balise ».
    """
    if not texte:
        return ""
    texte = re.sub(r"<br\s*/?>", " ", texte)
    texte = re.sub(r"<[^>]+>", "", texte)
    return module_html.unescape(texte).strip()


def _vision_sur_image(image):
    """Lit une image PIL avec le framework Vision de macOS.

    Renvoie une liste de (texte, bbox en pixels de l'image passée,
    confiance). Import différé : ces modules n'existent que sur macOS,
    et le moteur surya doit rester utilisable ailleurs.
    """
    import Quartz
    import Vision
    from Foundation import NSData

    tampon = io.BytesIO()
    image.save(tampon, format="PNG")
    octets = tampon.getvalue()
    donnees = NSData.dataWithBytes_length_(octets, len(octets))
    source = Quartz.CGImageSourceCreateWithData(donnees, None)
    cgimage = Quartz.CGImageSourceCreateImageAtIndex(source, 0, None)

    requete = Vision.VNRecognizeTextRequest.alloc().init()
    requete.setRecognitionLevel_(0)          # 0 = precise (1 = fast)
    requete.setUsesLanguageCorrection_(True)
    gestionnaire = Vision.VNImageRequestHandler.alloc().initWithCGImage_options_(
        cgimage, None)
    gestionnaire.performRequests_error_([requete], None)

    largeur, hauteur = image.size
    resultats = []
    for observation in (requete.results() or []):
        candidat = observation.topCandidates_(1)
        if not candidat:
            continue
        candidat = candidat[0]
        # Vision travaille en coordonnées normalisées (0-1) avec
        # l'origine en BAS à gauche ; on repasse en pixels avec
        # l'origine en haut à gauche, comme le reste du pipeline.
        cadre = observation.boundingBox()
        x0 = cadre.origin.x * largeur
        x1 = (cadre.origin.x + cadre.size.width) * largeur
        y0 = (1.0 - cadre.origin.y - cadre.size.height) * hauteur
        y1 = (1.0 - cadre.origin.y) * hauteur
        resultats.append((candidat.string(), [x0, y0, x1, y1],
                          float(candidat.confidence())))
    return resultats


def nombre_de_bandes(hauteur, hauteur_bande):
    """Nombre de bandes horizontales pour découper une image.

    Vision perd le petit texte quand l'image est haute : on vise des
    bandes d'environ `hauteur_bande` pixels, ce qui ramène chaque
    morceau à une échelle où le texte reste lisible.
    """
    if hauteur_bande <= 0:
        return 1
    return max(1, round(hauteur / hauteur_bande))


def ocr_vision(chemin, hauteur_bande, recouvrement_relatif=0.125):
    """Océrise une image en bandes avec Vision, et fusionne les résultats.

    Les bandes se recouvrent légèrement pour ne pas couper une ligne
    posée à la frontière ; les doublons ainsi créés sont ensuite écartés
    (même texte, même endroit).
    """
    image = Image.open(chemin).convert("RGB")
    largeur, hauteur = image.size
    total = nombre_de_bandes(hauteur, hauteur_bande)
    pas = hauteur / total
    marge = int(pas * recouvrement_relatif)

    debut = time.time()
    brutes = []
    for indice in range(total):
        haut = max(0, int(indice * pas) - marge)
        bas = min(hauteur, int((indice + 1) * pas) + marge)
        bande = image.crop((0, haut, largeur, bas))
        for texte, bbox, confiance in _vision_sur_image(bande):
            # Repasser du repère de la bande à celui de l'image entière.
            brutes.append((texte, [bbox[0], bbox[1] + haut,
                                   bbox[2], bbox[3] + haut], confiance))

    lignes = []
    vus = []
    for texte, bbox, confiance in brutes:
        propre = nettoyer(texte)
        if not propre:
            continue
        # Doublon de recouvrement : même texte à quelques pixels près.
        if any(t == propre and abs(b[1] - bbox[1]) < 12 and abs(b[0] - bbox[0]) < 12
               for t, b in vus):
            continue
        vus.append((propre, bbox))
        lignes.append({
            "texte": propre,
            "texte_balise": texte,
            "bbox": [round(v, 1) for v in bbox],
            "confiance": round(confiance, 4),
        })

    # Ordre de lecture : de haut en bas, puis de gauche à droite.
    lignes.sort(key=lambda l: (l["bbox"][1], l["bbox"][0]))
    return {
        "fichier": Path(chemin).name,
        "moteur": "vision",
        "date": datetime.now(timezone.utc).isoformat(),
        "duree_s": round(time.time() - debut, 1),
        "taille_origine": [largeur, hauteur],
        "nb_bandes": total,
        "nb_lignes": len(lignes),
        "lignes": lignes,
    }


def charger_predicteurs():
    """Instancie les prédicteurs Surya (import différé : lourd à charger).

    L'import est fait ici et non en tête de fichier pour que --help
    reste instantané et que les erreurs d'installation soient claires.
    """
    from surya.detection import DetectionPredictor
    from surya.foundation import FoundationPredictor
    from surya.recognition import RecognitionPredictor

    return RecognitionPredictor(FoundationPredictor()), DetectionPredictor()


def ocr_image(chemin, reconnaissance, detection, cote_detection, lot):
    """Passe une image dans Surya et renvoie le dictionnaire à sérialiser.

    Les coordonnées renvoyées sont TOUJOURS dans le repère de l'image
    d'origine, quelle que soit la résolution de détection employée.
    """
    pleine = Image.open(chemin).convert("RGB")
    taille_origine = pleine.size

    # Image de DÉTECTION des lignes. Attention : détecter sur une image
    # trop réduite produit des cadres trop courts, qui tronquent la fin
    # des titres à la lecture (« Blood Meridi » au lieu de « Blood
    # Meridian »). D'où une détection en pleine résolution par défaut.
    detectee = pleine
    if cote_detection and max(pleine.size) > cote_detection:
        detectee = pleine.copy()
        detectee.thumbnail((cote_detection, cote_detection), Image.LANCZOS)

    debut = time.time()
    # La LECTURE se fait dans l'image pleine résolution (highres_images).
    resultat = reconnaissance(
        [detectee],
        det_predictor=detection,
        highres_images=[pleine],
        recognition_batch_size=lot,
        sort_lines=True,   # lignes triées dans l'ordre de lecture
    )[0]

    # Surya rend les bbox dans le repère de l'image de DÉTECTION : on les
    # ramène dans celui de l'image d'origine pour que les coordonnées
    # soient exploitables telles quelles en phase 2b.
    echelle_x = taille_origine[0] / detectee.size[0]
    echelle_y = taille_origine[1] / detectee.size[1]

    lignes = [
        {
            "texte": nettoyer(ligne.text),
            "texte_balise": ligne.text,
            "bbox": [
                round(ligne.bbox[0] * echelle_x, 1), round(ligne.bbox[1] * echelle_y, 1),
                round(ligne.bbox[2] * echelle_x, 1), round(ligne.bbox[3] * echelle_y, 1),
            ],
            "confiance": round(ligne.confidence, 4) if ligne.confidence is not None else None,
        }
        for ligne in resultat.text_lines
        if nettoyer(ligne.text)
    ]
    return {
        "fichier": chemin.name,
        "moteur": "surya",
        "date": datetime.now(timezone.utc).isoformat(),
        "duree_s": round(time.time() - debut, 1),
        "taille_origine": list(taille_origine),
        "taille_detection": list(detectee.size),
        "nb_lignes": len(lignes),
        "lignes": lignes,
    }


def principal():
    parseur = argparse.ArgumentParser(description="Phase 2a : OCR des charts avec Surya.")
    parseur.add_argument("--limite", type=int, default=None,
                         help="ne traiter que N images (pour tester avant un run complet)")
    parseur.add_argument("--fichier", nargs="+", default=None,
                         help="ne traiter que ces images (noms de fichiers), pour tester "
                              "un cas précis")
    parseur.add_argument("--moteur", choices=["vision", "surya"], default="vision",
                         help="moteur d'OCR : « vision » (macOS, rapide) ou « surya » "
                              "(open source, lent, sert de contrôle) "
                              "(défaut : %(default)s)")
    parseur.add_argument("--hauteur-bande", type=int, default=1100,
                         help="hauteur visée des bandes découpées pour Vision, en "
                              "pixels ; 0 pour ne pas découper (défaut : %(default)s)")
    parseur.add_argument("--cote-detection", type=int, default=0,
                         help="côté max en pixels pour la détection des lignes, "
                              "0 = pleine résolution ; réduire tronque la fin des "
                              "titres, n'y toucher que si la mémoire sature "
                              "(défaut : %(default)s)")
    parseur.add_argument("--lot", type=int, default=16,
                         help="nombre de lignes lues par lot ; baisser si la mémoire "
                              "sature (défaut : %(default)s)")
    parseur.add_argument("--force", action="store_true",
                         help="retraite aussi les images déjà océrisées")
    args = parseur.parse_args()

    DOSSIER_SORTIE.mkdir(parents=True, exist_ok=True)
    images = sorted(p for p in DOSSIER_IMAGES.iterdir()
                    if p.suffix.lower() in EXTENSIONS)
    if not images:
        sys.exit(f"Aucune image dans {DOSSIER_IMAGES}")

    if args.fichier:
        voulus = set(args.fichier)
        images = [p for p in images if p.name in voulus]
        introuvables = voulus - {p.name for p in images}
        if introuvables:
            sys.exit(f"Introuvable(s) dans {DOSSIER_IMAGES} : {sorted(introuvables)}")

    # La reprise se décide AVANT de charger les modèles : si tout est
    # déjà fait, le script rend la main en une seconde.
    restantes = [p for p in images
                 if args.force or not (DOSSIER_SORTIE / (p.stem + ".json")).exists()]
    deja_faites = len(images) - len(restantes)
    if args.limite:
        restantes = restantes[:args.limite]
    if not restantes:
        print(f"Rien à faire : {deja_faites} images déjà océrisées.")
        return

    # Surya doit charger ses modèles (lourd) ; Vision est immédiatement
    # disponible, il n'y a rien à initialiser.
    if args.moteur == "surya":
        print(f"{len(restantes)} images à océriser ({deja_faites} déjà faites). "
              f"Chargement des modèles Surya…", flush=True)
        reconnaissance, detection = charger_predicteurs()
    else:
        print(f"{len(restantes)} images à océriser ({deja_faites} déjà faites) "
              f"avec le moteur Vision (macOS).", flush=True)
        reconnaissance = detection = None

    bilan = {"ok": 0, "erreur": 0}
    try:
        for chemin in restantes:
            try:
                if args.moteur == "vision":
                    resultat = ocr_vision(chemin, args.hauteur_bande)
                else:
                    resultat = ocr_image(chemin, reconnaissance, detection,
                                         args.cote_detection, args.lot)
            except Exception as erreur:
                # Une image corrompue ne doit pas faire perdre le run.
                print(f"  [erreur] {chemin.name} : {erreur}", flush=True)
                bilan["erreur"] += 1
                continue
            sortie = DOSSIER_SORTIE / (chemin.stem + ".json")
            sortie.write_text(json.dumps(resultat, ensure_ascii=False, indent=2),
                              encoding="utf-8")
            print(f"  [ok] {chemin.name} : {resultat['nb_lignes']} lignes, "
                  f"{resultat['duree_s']} s", flush=True)
            bilan["ok"] += 1
    except KeyboardInterrupt:
        print("\n[interruption] relancer le script reprendra où il s'est arrêté.")
        sys.exit(130)

    print(f"Terminé : {bilan['ok']} océrisées, {bilan['erreur']} en erreur, "
          f"{deja_faites} déjà faites.")


if __name__ == "__main__":
    principal()
