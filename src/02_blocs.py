#!/usr/bin/env python3
"""Phase 2b — Reconstruction géométrique des blocs et des niveaux.

Lit les JSON d'OCR de data/interim/ocr/ et en déduit, sans aucun modèle,
la structure interne de chaque chart : quelles lignes forment un même
bloc (section, colonne, vignette), quel intitulé gouverne ce bloc, et
quelles œuvres lui sont rattachées. Écrit un JSON par chart dans
data/interim/blocs/ avec les nœuds au format (titre, auteur, tier).

POURQUOI SANS MODÈLE. « Quelles lignes appartiennent au même bloc » est
une question de géométrie : les coordonnées produites par l'OCR
contiennent déjà la réponse. Confié à un VLM local, ce travail prenait
11 minutes par image et confondait les intitulés de sections avec les
livres ; ici il prend moins d'une seconde, ne peut rien halluciner, et
donne exactement le même résultat à chaque exécution — ce que la
reproductibilité du protocole exige.

RÈGLE DE REGROUPEMENT. Deux lignes appartiennent au même bloc si leurs
plages horizontales se CHEVAUCHENT et si elles sont verticalement
proches (quelques hauteurs de ligne). Le chevauchement strict est
essentiel : sur un chart en grille, les titres de toute une rangée
partagent la même hauteur, et un simple critère de proximité
fusionnerait des colonnes voisines.

Les seuils sont exprimés en multiples de la hauteur de ligne médiane du
chart, pour s'adapter aux images de 780 à 7600 px sans réglage manuel.

Reprise : un chart dont le JSON existe déjà est sauté ; --force
retraite tout. Le script est instantané, le relancer ne coûte rien.
"""

import argparse
import html as module_html
import json
import re
import statistics
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

# --- Chemins du projet ---
RACINE = Path(__file__).resolve().parents[1]
DOSSIER_OCR = RACINE / "data" / "interim" / "ocr"
DOSSIER_VLM = RACINE / "data" / "interim" / "vlm"
DOSSIER_SORTIE = RACINE / "data" / "interim" / "blocs"

# Mises en page traitées en rangées plutôt qu'en blocs.
LAYOUTS_GRILLE = {"grid", "collage"}

# Motif « Auteur : Œuvre », très courant sur les charts de /lit/.
# Le deux-points doit être suivi d'un espace et précédé d'un libellé
# court, pour ne pas couper un titre qui contient lui-même un
# deux-points (« Ecce Homo: How One Becomes What One Is »).
MOTIF_AUTEUR = re.compile(r"^(?P<auteur>[^:]{2,40}?)\s*:\s+(?P<titre>.+)$")


def nettoyer(texte):
    """Retire le balisage émis par Surya (<b>, <i>, <br>) et les entités."""
    if not texte:
        return ""
    texte = re.sub(r"<br\s*/?>", " ", texte)
    texte = re.sub(r"<[^>]+>", "", texte)
    return module_html.unescape(texte).strip()


def est_en_gras(ligne):
    """Vrai si l'OCR a repéré la ligne en gras.

    Les charts du corpus mettent leurs intitulés de section en gras
    (« <b>Optional Christian Works</b> ») : c'est un indice structurel
    gratuit, plus fiable qu'une comparaison de tailles de police.
    Le champ « texte_balise » n'existe que dans les OCR produits après
    l'ajout de la normalisation ; on retombe sur « texte » sinon.
    """
    brut = ligne.get("texte_balise") or ligne.get("texte") or ""
    return "<b>" in brut or "<strong>" in brut


def regrouper(lignes, facteur_vertical):
    """Regroupe les lignes en blocs par chevauchement horizontal.

    Renvoie une liste de blocs, chacun trié dans l'ordre de lecture.
    """
    if not lignes:
        return []
    hauteur = statistics.median(l["bbox"][3] - l["bbox"][1] for l in lignes) or 1
    seuil_vertical = hauteur * facteur_vertical

    # Traiter de haut en bas : un bloc se construit par accrétion des
    # lignes qui le suivent immédiatement.
    lignes = sorted(lignes, key=lambda l: (l["bbox"][1], l["bbox"][0]))
    blocs = []
    for ligne in lignes:
        x0, y0, x1, y1 = ligne["bbox"]
        accueil = None
        for bloc in blocs:
            bx0, by0, bx1, by1 = bloc["bbox"]
            # Chevauchement horizontal réel (pas seulement voisinage)…
            if x0 >= bx1 or x1 <= bx0:
                continue
            # …et continuité verticale avec le bas du bloc.
            if y0 - by1 > seuil_vertical:
                continue
            # À chevauchement égal, on préfère le bloc le plus proche.
            if accueil is None or by1 > accueil["bbox"][3]:
                accueil = bloc
        if accueil is None:
            blocs.append({"lignes": [ligne], "bbox": [x0, y0, x1, y1]})
        else:
            accueil["lignes"].append(ligne)
            ax0, ay0, ax1, ay1 = accueil["bbox"]
            accueil["bbox"] = [min(ax0, x0), min(ay0, y0), max(ax1, x1), max(ay1, y1)]

    for bloc in blocs:
        bloc["lignes"].sort(key=lambda l: (l["bbox"][1], l["bbox"][0]))
    blocs.sort(key=lambda b: (b["bbox"][1], b["bbox"][0]))
    return blocs, hauteur


def analyser_bloc(bloc, hauteur_mediane):
    """Extrait l'intitulé (tier) et les nœuds d'un bloc.

    Deux formes de blocs coexistent dans le corpus :

    - le bloc de SECTION : un intitulé (en gras, ou nettement plus haut
      que le corps du bloc) suivi d'une liste d'œuvres. L'intitulé
      devient le « tier » de toutes les œuvres du bloc.
    - la VIGNETTE de grille : deux ou trois lignes sans intitulé, où la
      première est le titre et la suivante l'auteur. Pas de tier.
    """
    lignes = bloc["lignes"]
    textes = [nettoyer(l["texte"]) for l in lignes]

    # Repérage de l'intitulé, par ordre de fiabilité décroissante.
    indice_titre = None

    # 1. Le gras, quand l'OCR l'a repéré : signal explicite.
    for i, ligne in enumerate(lignes):
        if est_en_gras(ligne):
            indice_titre = i
            break

    # 2. Sinon, sur la première ligne d'un bloc d'au moins trois lignes :
    #    l'absence de deux-points alors que le corps du bloc en est
    #    truffé. Les charts écrivent leurs œuvres « Auteur: Titre » et
    #    leurs intitulés sans ponctuation — discriminant très net, et
    #    plus sûr que la taille de police (mesurée à seulement 15 %
    #    d'écart sur la carte de philosophie, soit sous tout seuil de
    #    hauteur raisonnable).
    if indice_titre is None and len(lignes) >= 3:
        corps_avec_deux_points = sum(1 for t in textes[1:] if ": " in t)
        if ": " not in textes[0] and corps_avec_deux_points >= len(textes[1:]) * 0.6:
            indice_titre = 0

    # 3. À défaut, une première ligne nettement plus haute que le corps.
    if indice_titre is None and len(lignes) >= 3:
        hauteurs = [l["bbox"][3] - l["bbox"][1] for l in lignes]
        if hauteurs[0] > statistics.median(hauteurs[1:]) * 1.25:
            indice_titre = 0

    if indice_titre is not None:
        tier = textes[indice_titre]
        corps = [t for i, t in enumerate(textes) if i != indice_titre]
    else:
        tier = None
        corps = textes

    noeuds = []
    if tier is None and 2 <= len(corps) <= 3 and not any(":" in t for t in corps):
        # Vignette de grille : titre puis auteur.
        noeuds.append({"titre": corps[0], "auteur": corps[1], "tier": None})
    else:
        for texte in corps:
            correspondance = MOTIF_AUTEUR.match(texte)
            if correspondance:
                noeuds.append({
                    "titre": correspondance.group("titre").strip(),
                    "auteur": correspondance.group("auteur").strip(),
                    "tier": tier,
                })
            else:
                noeuds.append({"titre": texte, "auteur": None, "tier": tier})

    return {
        "tier": tier,
        "bbox": [round(v, 1) for v in bloc["bbox"]],
        "nb_lignes": len(lignes),
        "noeuds": noeuds,
    }


def lire_layout(nom_json):
    """Type de mise en page relevé en phase 2c, ou None s'il manque."""
    chemin = DOSSIER_VLM / nom_json
    if not chemin.exists():
        return None
    donnees = json.loads(chemin.read_text(encoding="utf-8"))
    return (donnees.get("extraction") or {}).get("layout_type")


def bandes_denses(lignes, hauteur, minimum):
    """Repère les bandes horizontales peuplées de plusieurs lignes.

    Les charts en grille alignent leurs légendes en rangées régulières :
    une bande de titres, une bande d'auteurs juste dessous, une bande de
    numéros de rang. Le texte décoratif des couvertures, lui, est
    dispersé. Compter les lignes par bande suffit donc à distinguer les
    deux — sans modèle et sans connaître la mise en page à l'avance.

    Renvoie une liste de bandes (y moyen, lignes triées par x).
    """
    groupes = {}
    for ligne in lignes:
        centre = (ligne["bbox"][1] + ligne["bbox"][3]) / 2
        groupes.setdefault(int(centre // hauteur), []).append(ligne)
    bandes = []
    for indice in sorted(groupes):
        contenu = groupes[indice]
        if len(contenu) >= minimum:
            contenu.sort(key=lambda l: l["bbox"][0])
            centres = [(l["bbox"][1] + l["bbox"][3]) / 2 for l in contenu]
            bandes.append({"y": sum(centres) / len(centres), "lignes": contenu})
    return bandes


def est_grille(bandes, population_min=5, irregularite_max=0.20):
    """Vrai si le chart présente la signature d'une grille régulière.

    Deux conditions cumulatives, l'une sur les rangées, l'autre sur les
    colonnes :

    1. au moins trois bandes horizontales de même population, d'au moins
       cinq entrées — une rangée de vignettes ;
    2. des colonnes RÉGULIÈREMENT espacées, mesuré par le coefficient de
       variation des écarts entre débuts de colonnes.

    La seconde condition est la discriminante. Mesuré sur le corpus :
    0,10 pour la grille « Top 100 » contre 0,31 pour la carte de
    philosophie, dont les grappes s'alignent parfois par hasard sur une
    même hauteur mais jamais à intervalles réguliers. Sans elle, une
    carte est prise pour une grille et perd 80 % de ses œuvres.
    """
    if len(bandes) < 3:
        return False
    populations = Counter(len(b["lignes"]) for b in bandes)
    modale, occurrences = populations.most_common(1)[0]
    if modale < population_min or occurrences < 3:
        return False

    ecarts = []
    for bande in bandes:
        if len(bande["lignes"]) != modale:
            continue
        xs = sorted(l["bbox"][0] for l in bande["lignes"])
        ecarts += [suivant - courant for courant, suivant in zip(xs, xs[1:])]
    if len(ecarts) < 3:
        return False
    moyenne = statistics.mean(ecarts)
    if moyenne <= 0:
        return False
    return statistics.pstdev(ecarts) / moyenne < irregularite_max


def intitules_isoles(lignes, hauteur, tolerance=0.30):
    """Repère les intitulés de section d'un chart à couvertures.

    Sur ces charts, les œuvres sont des couvertures alignées en rangées
    et les intitulés de niveau (« Entry-level Tier », « God-Tier »,
    « Core Texts ») sont des lignes de texte SEULES sur leur bande
    horizontale. C'est le critère décisif, et le seul qui vaille pour
    les deux mises en page rencontrées dans le corpus : intitulés collés
    à la marge gauche (« /lit/'s beginner's guide to Fantasy ») aussi
    bien que centrés (« Hermeticism Study Guide »).

    Trois filtres écartent ensuite le texte décoratif des couvertures,
    lui aussi parfois isolé : les titres tout en majuscules (« THE
    ODYSSEY »), ceux sans aucune minuscule, et ceux dont la hauteur
    s'écarte de la police d'intitulé du chart.

    Mesuré sur deux charts de référence : 18 intitulés retrouvés sur 18,
    pour 6 faux positifs. Le déséquilibre est voulu — un niveau
    surnuméraire se repère et s'écarte à la lecture, un niveau manquant
    fausse silencieusement le codage de la progression.
    """
    bandes = {}
    for ligne in lignes:
        centre = (ligne["bbox"][1] + ligne["bbox"][3]) / 2
        bandes.setdefault(int(centre // hauteur), []).append(ligne)

    candidats = []
    for _, contenu in sorted(bandes.items()):
        if len(contenu) != 1:      # une rangée de légendes, pas un intitulé
            continue
        ligne = contenu[0]
        texte = nettoyer(ligne["texte"])
        if len(texte) < 4:
            continue
        if texte.upper() == texte:                   # tout en capitales
            continue
        if not re.search(r"[a-z]", texte):
            continue
        if sum(c.isdigit() for c in texte) > len(texte) / 3:
            continue
        candidats.append((ligne["bbox"][1], texte,
                          ligne["bbox"][3] - ligne["bbox"][1]))

    if not candidats:
        return []
    reference = statistics.median([c[2] for c in candidats])
    return [(y, texte) for y, texte, h in candidats
            if reference and abs(h - reference) / reference <= tolerance]


def tier_au_dessus(y, intitules):
    """Intitulé de section gouvernant une rangée située à l'ordonnée y."""
    courant = None
    for y_titre, texte in intitules:
        if y_titre <= y:
            courant = texte
        else:
            break
    return courant


def extraire_grille(bandes, hauteur, ecart_max, intitules=()):
    """Apparie titres et auteurs d'un chart en grille, colonne par colonne.

    Deux bandes consécutives et proches forment un couple
    (titres, auteurs) ; l'appariement se fait par chevauchement
    horizontal, chaque vignette occupant sa colonne. Les bandes de
    numéros de rang sont écartées : elles ne portent pas d'œuvre.
    """
    # Ne retenir que les rangées PLEINES. Le texte décoratif des
    # couvertures forme parfois des bandes fortuites de 4 à 6 lignes,
    # qui produisent des entrées absurdes (« BROTHERS », « ALBERT
    # CAMUS ») ; les vraies rangées de légendes, elles, comptent une
    # entrée par colonne. Une tolérance de 20 % laisse passer une
    # dernière rangée incomplète.
    populations = Counter(len(b["lignes"]) for b in bandes)
    modale = populations.most_common(1)[0][0]
    pleines = [b for b in bandes if len(b["lignes"]) >= modale * 0.8]

    # Les rangées de numéros de rang ne portent aucune œuvre.
    utiles = [b for b in pleines
              if sum(1 for l in b["lignes"] if nettoyer(l["texte"]).isdigit())
              < len(b["lignes"]) * 0.6]

    noeuds, consommees = [], set()
    for i, bande in enumerate(utiles):
        if i in consommees:
            continue
        suivante = utiles[i + 1] if i + 1 < len(utiles) else None
        if (suivante is None or suivante["y"] - bande["y"] > hauteur * ecart_max
                or (i + 1) in consommees):
            continue
        consommees.add(i + 1)
        for ligne in bande["lignes"]:
            x0, x1 = ligne["bbox"][0], ligne["bbox"][2]
            auteur = None
            for candidate in suivante["lignes"]:
                cx0, cx1 = candidate["bbox"][0], candidate["bbox"][2]
                if cx0 < x1 and cx1 > x0:      # chevauchement de colonne
                    auteur = nettoyer(candidate["texte"])
                    break
            noeuds.append({"titre": nettoyer(ligne["texte"]),
                           "auteur": auteur,
                           "tier": tier_au_dessus(ligne["bbox"][1], intitules)})
    return noeuds


def traiter(chemin_ocr, facteur_vertical, min_bande, ecart_grille):
    """Construit la structure d'un chart à partir de son JSON d'OCR.

    Deux régimes, choisis automatiquement : appariement en rangées pour
    les charts en grille, regroupement en blocs pour tous les autres.
    """
    donnees = json.loads(chemin_ocr.read_text(encoding="utf-8"))
    lignes = [l for l in donnees.get("lignes", []) if nettoyer(l["texte"])]
    if not lignes:
        return {"fichier": donnees.get("fichier"),
                "date": datetime.now(timezone.utc).isoformat(),
                "taille_origine": donnees.get("taille_origine"),
                "regime": "vide", "nb_blocs": 0, "nb_noeuds": 0,
                "tiers": [], "blocs": []}

    hauteur = statistics.median(l["bbox"][3] - l["bbox"][1] for l in lignes) or 1
    bandes = bandes_denses(lignes, hauteur, min_bande)

    # Le régime est décidé par le type de mise en page relevé en phase
    # 2c quand il est disponible. C'est une question visuelle, et la
    # géométrie s'y est montrée impuissante : une carte dont les grappes
    # s'alignent en colonnes présente exactement la même signature
    # qu'une grille (coefficient de variation des écarts, dispersion des
    # colonnes, couverture verticale — tous mesurés, tous ambigus). Le
    # VLM, lui, tranche correctement sur les deux cas de référence.
    # L'heuristique géométrique reste en secours si la phase 2c n'a pas
    # encore tourné.
    layout = lire_layout(chemin_ocr.name)
    if layout is not None:
        grille = layout in LAYOUTS_GRILLE
        source_regime = f"vlm:{layout}"
    else:
        grille = est_grille(bandes)
        source_regime = "geometrie"

    if grille:
        # Les intitulés de niveau sont cherchés avant l'appariement :
        # sur une tier list à couvertures, ils portent l'essentiel de la
        # gamification (« God-Tier », « Shit-Tier ») et doivent être
        # rattachés à chaque œuvre de la rangée qu'ils gouvernent.
        # Les intitulés isolés portent la gamification (« God-Tier »,
        # « Entry-level Tier ») : ils priment sur l'exactitude de la
        # liste d'œuvres, qui n'est de toute façon pas récupérable sur
        # les charts où les livres ne figurent que par leur couverture.
        # Le prix est un peu de bruit sur les grilles sans niveaux (le
        # paragraphe d'introduction du « Top 100 » en produit quelques
        # uns) : un niveau surnuméraire se repère et s'écarte, un niveau
        # manquant fausserait silencieusement le codage.
        intitules = intitules_isoles(lignes, hauteur)
        noeuds = extraire_grille(bandes, hauteur, ecart_grille, intitules)
        par_tier = {}
        for noeud in noeuds:
            par_tier.setdefault(noeud["tier"], []).append(noeud)
        blocs = [{"tier": tier, "bbox": None, "nb_lignes": len(groupe),
                  "noeuds": groupe} for tier, groupe in par_tier.items()]
        regime = "grille"
    else:
        blocs_bruts, hauteur = regrouper(lignes, facteur_vertical)
        blocs = [analyser_bloc(b, hauteur) for b in blocs_bruts]
        noeuds = [n for b in blocs for n in b["noeuds"]]
        regime = "blocs"

    return {
        "fichier": donnees.get("fichier"),
        "date": datetime.now(timezone.utc).isoformat(),
        "taille_origine": donnees.get("taille_origine"),
        "hauteur_ligne_mediane": round(hauteur, 1),
        "regime": regime,
        "regime_source": source_regime,
        "nb_blocs": len(blocs),
        "nb_noeuds": len(noeuds),
        "tiers": [b["tier"] for b in blocs if b["tier"]],
        "intitules_isoles": [t for _, t in intitules_isoles(lignes, hauteur)],
        "blocs": blocs,
    }


def principal():
    parseur = argparse.ArgumentParser(
        description="Phase 2b : reconstruction géométrique des blocs et niveaux.")
    parseur.add_argument("--fichier", nargs="+", default=None,
                         help="ne traiter que ces charts (noms d'images ou de JSON)")
    parseur.add_argument("--facteur-vertical", type=float, default=1.2,
                         help="écart vertical max entre deux lignes d'un même bloc, "
                              "en hauteurs de ligne ; au-delà de 1,2 des sections "
                              "superposées fusionnent, en deçà les listes se "
                              "fragmentent (défaut : %(default)s)")
    parseur.add_argument("--min-bande", type=int, default=4,
                         help="lignes minimum pour qu'une bande horizontale compte "
                              "comme une rangée de grille (défaut : %(default)s)")
    parseur.add_argument("--ecart-grille", type=float, default=4.0,
                         help="écart vertical max entre la rangée des titres et celle "
                              "des auteurs, en hauteurs de ligne (défaut : %(default)s)")
    parseur.add_argument("--force", action="store_true",
                         help="retraite aussi les charts déjà analysés")
    args = parseur.parse_args()

    if not DOSSIER_OCR.exists():
        sys.exit(f"Aucun OCR dans {DOSSIER_OCR} : lancer d'abord src/01_ocr.py")
    DOSSIER_SORTIE.mkdir(parents=True, exist_ok=True)

    fichiers = sorted(DOSSIER_OCR.glob("*.json"))
    if not fichiers:
        sys.exit(f"Aucun OCR dans {DOSSIER_OCR} : lancer d'abord src/01_ocr.py")
    if args.fichier:
        voulus = {Path(f).stem for f in args.fichier}
        fichiers = [f for f in fichiers if f.stem in voulus]
        introuvables = voulus - {f.stem for f in fichiers}
        if introuvables:
            sys.exit(f"Sans OCR : {sorted(introuvables)}")

    bilan = {"ok": 0, "saut": 0}
    for chemin in fichiers:
        sortie = DOSSIER_SORTIE / chemin.name
        if sortie.exists() and not args.force:
            bilan["saut"] += 1
            continue
        resultat = traiter(chemin, args.facteur_vertical, args.min_bande,
                           args.ecart_grille)
        sortie.write_text(json.dumps(resultat, ensure_ascii=False, indent=2),
                          encoding="utf-8")
        print(f"  [ok] {resultat['fichier']} [{resultat['regime']}] : "
              f"{resultat['nb_blocs']} blocs, {resultat['nb_noeuds']} nœuds, "
              f"{len(resultat['tiers'])} niveaux")
        bilan["ok"] += 1

    print(f"Terminé : {bilan['ok']} charts analysés, {bilan['saut']} déjà faits.")


if __name__ == "__main__":
    principal()
