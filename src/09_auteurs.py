#!/usr/bin/env python3
"""Préparation de la phase 5 — Nettoyage et normalisation des auteurs.

Lit data/processed/oeuvres.csv, filtre les faux auteurs, rapproche les
formes qui désignent la même personne, et écrit :

  data/processed/auteurs.csv        une ligne par (chart, auteur normalisé)
  results/auteurs_rapport.txt       ce qui a été écarté, fusionné, conservé

POURQUOI CETTE ÉTAPE. Le champ « auteur » vient d'une règle simple —
le motif « Auteur: Titre » — appliquée au texte de l'OCR. Elle est
efficace mais produit deux sortes de bruit, l'un et l'autre fatals à une
analyse de réseau :

  - des FAUX AUTEURS : « History », « ECONOMICS », « COMPLETE WORKS »
    quand le chart écrit « History: A Very Short Introduction ». Ils
    créent des nœuds qui n'existent pas, et comme ces mots reviennent
    dans des charts très différents, ils apparaissent faussement comme
    les auteurs les plus transversaux du corpus.

  - des FORMES ÉCLATÉES : « Kafka », « Franz Kafka », « KAFKA »
    désignent une seule personne mais comptent pour trois nœuds, ce qui
    divise mécaniquement leur centralité.

NORMALISATION. Deux noms sont rapprochés s'ils partagent le même
patronyme, pris comme dernier mot du nom, sans accents ni casse. La
forme retenue est la plus fréquente dans le corpus. Un rapprochement
supplémentaire, par similarité de chaînes, réunit les variantes
orthographiques et les coquilles d'OCR (« Dostoevsky » / « Dostoyevsky »).

LIMITE À DÉCLARER. Le patronyme seul ne distingue pas deux auteurs
homonymes : Cormac et Mary McCarthy sont fusionnés. Sur ce corpus, où
les charts nomment rarement les prénoms, c'est le compromis le moins
mauvais — mais il doit être mentionné, et les cas notables vérifiés à la
main. Le rapport liste les fusions les plus lourdes pour cela.

Le fichier d'exclusions (prompts/auteurs_exclusions.txt) est modifiable
sans toucher au code : c'est un instrument de l'étude, il doit pouvoir
être discuté et amendé.
"""

import argparse
import csv
import difflib
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

# --- Chemins du projet ---
RACINE = Path(__file__).resolve().parents[1]
OEUVRES = RACINE / "data" / "processed" / "oeuvres.csv"
EXCLUSIONS = RACINE / "prompts" / "auteurs_exclusions.txt"
SORTIE = RACINE / "data" / "processed" / "auteurs.csv"
RAPPORT = RACINE / "results" / "auteurs_rapport.txt"

COLONNES = ["fichier", "categorie", "layout_type", "auteur", "auteur_brut",
            "patronyme", "titre"]


def sans_accents(texte):
    """Retire les diacritiques, pour comparer « Céline » et « Celine »."""
    return "".join(c for c in unicodedata.normalize("NFD", texte)
                   if unicodedata.category(c) != "Mn")


def charger_exclusions():
    """Formes à écarter, en minuscules ; {} si le fichier est absent."""
    if not EXCLUSIONS.exists():
        return set()
    lignes = EXCLUSIONS.read_text(encoding="utf-8").splitlines()
    return {l.strip().lower() for l in lignes
            if l.strip() and not l.startswith("#")}


# Mots grammaticaux anglais : leur présence signe un fragment de titre,
# pas un nom de personne. « Way of », « IN THE », « Now Ted Tones Wrong
# And » figuraient ainsi parmi les « auteurs » les plus présents du
# corpus avant ce filtre.
MOTS_GRAMMATICAUX = {
    "of", "the", "in", "and", "to", "for", "with", "on", "from", "at", "by",
    "or", "as", "but", "if", "not", "all", "more", "that", "this", "these",
    "those", "his", "her", "their", "its", "you", "your", "who", "what",
    "how", "why", "when", "where", "is", "are", "was", "were", "be", "been",
    "an", "a", "into", "about", "after", "before", "than", "then", "also",
}

# Particules nobiliaires : admises DANS un nom, jamais seules ni en fin.
PARTICULES = {"de", "du", "des", "van", "von", "der", "den", "di", "da",
              "del", "della", "la", "le", "dos", "bin", "ibn", "al"}


def nettoyer(brut, exclusions):
    """Renvoie un nom d'auteur plausible, ou None.

    Les filtres écartent, dans l'ordre : les chaînes trop courtes ou trop
    longues, les formes listées en exclusion, celles sans lettre, celles
    à forte densité de chiffres, les suites en capitales de plus de deux
    mots (signature du texte décoratif des couvertures), les noms de plus
    de quatre mots, ceux sans aucune majuscule, et enfin ceux contenant
    un mot grammatical — le filtre décisif, celui qui distingue un nom de
    personne d'un fragment de titre.
    """
    nom = (brut or "").strip().strip(".,;:-—–\"'()[]{}")
    nom = re.sub(r"\s+", " ", nom)
    if not (3 <= len(nom) <= 40):
        return None
    if nom.lower() in exclusions:
        return None
    if not re.search(r"[A-Za-zÀ-ÿ]", nom):
        return None
    if sum(c.isdigit() for c in nom) > len(nom) / 4:
        return None
    if nom.isupper() and len(nom.split()) > 2:
        return None

    mots = nom.split()
    if len(mots) > 4:
        return None
    if not any(m[:1].isupper() for m in mots):
        return None
    for indice, mot in enumerate(mots):
        nu = re.sub(r"[^A-Za-zÀ-ÿ]", "", mot).lower()
        if not nu:
            continue
        if nu in PARTICULES and 0 < indice < len(mots) - 1:
            continue          # « Simone de Beauvoir », « Vincent van Gogh »
        if nu in MOTS_GRAMMATICAUX:
            return None
    return nom


def patronyme(nom):
    """Clé de rapprochement : dernier mot, sans accents ni casse.

    « Franz Kafka » et « Kafka » donnent tous deux « kafka ». Les
    particules sont recollées au mot suivant (« de Beauvoir » -> le
    dernier mot reste « beauvoir »), ce qui suffit ici.
    """
    mots = [m for m in re.split(r"[\s,]+", nom) if m]
    if not mots:
        return None
    dernier = sans_accents(mots[-1]).lower()
    dernier = re.sub(r"[^a-z]", "", dernier)
    return dernier or None


def fusionner_variantes(effectifs, seuil, longueur_min):
    """Rapproche les patronymes très proches (coquilles d'OCR).

    Chaque clé rare est comparée aux clés plus fréquentes ; au-delà du
    seuil de similarité, elle est rattachée à la plus fréquente. On ne
    compare que des clés assez longues : sur trois ou quatre lettres, la
    similarité rapprocherait des noms sans rapport.
    """
    cles = sorted(effectifs, key=lambda c: -effectifs[c])
    fusion = {}
    for i, rare in enumerate(cles):
        if len(rare) < longueur_min:
            continue
        for frequent in cles[:i]:
            if len(frequent) < longueur_min:
                continue
            if fusion.get(frequent):        # ne pas chaîner les fusions
                continue
            # Un simple « s » d'écart ne suffit pas : « William » et
            # « Williams » sont deux patronymes distincts, et sur des
            # noms communs restés dans le champ, la similarité
            # rapprocherait un singulier de son pluriel.
            if {rare, frequent} == {frequent.rstrip("s"), frequent} or \
               rare.rstrip("s") == frequent.rstrip("s"):
                continue
            if difflib.SequenceMatcher(None, rare, frequent).ratio() >= seuil:
                fusion[rare] = frequent
                break
    return fusion


def principal():
    parseur = argparse.ArgumentParser(
        description="Nettoie et normalise les auteurs pour la phase 5.")
    parseur.add_argument("--seuil-similarite", type=float, default=0.90,
                         help="similarité minimale pour fusionner deux patronymes "
                              "(défaut : %(default)s)")
    parseur.add_argument("--longueur-min-fusion", type=int, default=6,
                         help="longueur minimale d'un patronyme pour être candidat "
                              "à la fusion floue (défaut : %(default)s)")
    parseur.add_argument("--min-charts", type=int, default=1,
                         help="ne conserver que les auteurs présents dans au moins "
                              "N charts (défaut : %(default)s)")
    args = parseur.parse_args()

    if not OEUVRES.exists():
        sys.exit(f"Absent : {OEUVRES} — lancer d'abord src/05_tables.py")
    exclusions = charger_exclusions()

    with open(OEUVRES, newline="", encoding="utf-8") as fichier:
        lignes = [l for l in fichier if not l.startswith("#")]
    oeuvres = list(csv.DictReader(lignes))

    # 1. Filtrage
    retenues, ecartees = [], Counter()
    for ligne in oeuvres:
        brut = ligne.get("auteur", "")
        if not brut.strip():
            continue
        nom = nettoyer(brut, exclusions)
        if nom is None:
            ecartees[brut.strip()[:40]] += 1
            continue
        cle = patronyme(nom)
        if cle is None:
            ecartees[brut.strip()[:40]] += 1
            continue
        retenues.append((ligne, nom, cle))

    if not retenues:
        sys.exit("Aucun auteur retenu après filtrage.")

    # 2. Rapprochement des variantes orthographiques
    effectifs = Counter(cle for _, _, cle in retenues)
    fusion = fusionner_variantes(effectifs, args.seuil_similarite,
                                 args.longueur_min_fusion)

    # 3. Forme canonique : la plus fréquente pour chaque patronyme
    formes = defaultdict(Counter)
    for _, nom, cle in retenues:
        formes[fusion.get(cle, cle)][nom] += 1
    # Forme canonique : la plus fréquente, mais on écarte les variantes
    # tout en capitales tant qu'une forme lisible existe — les capitales
    # viennent des couvertures, pas de la manière dont un auteur s'écrit.
    canonique = {}
    for cle, compteur in formes.items():
        lisibles = Counter({f: n for f, n in compteur.items() if not f.isupper()})
        canonique[cle] = (lisibles or compteur).most_common(1)[0][0]

    # 4. Table de sortie
    charts_par_auteur = defaultdict(set)
    sortie = []
    for ligne, nom, cle in retenues:
        final = fusion.get(cle, cle)
        auteur = canonique[final]
        charts_par_auteur[auteur].add(ligne["fichier"])
        sortie.append({
            "fichier": ligne["fichier"],
            "categorie": ligne.get("categorie", ""),
            "layout_type": ligne.get("layout_type", ""),
            "auteur": auteur,
            "auteur_brut": nom,
            "patronyme": final,
            "titre": ligne.get("titre", ""),
        })
    if args.min_charts > 1:
        gardes = {a for a, c in charts_par_auteur.items() if len(c) >= args.min_charts}
        sortie = [l for l in sortie if l["auteur"] in gardes]

    SORTIE.parent.mkdir(parents=True, exist_ok=True)
    with open(SORTIE, "w", newline="", encoding="utf-8") as fichier:
        writer = csv.DictWriter(fichier, fieldnames=COLONNES)
        writer.writeheader()
        writer.writerows(sortie)

    # 5. Rapport — ce qui a été fait doit rester vérifiable
    presence = Counter({a: len(c) for a, c in charts_par_auteur.items()})
    fusions_lourdes = sorted(
        ((rare, vers, effectifs[rare]) for rare, vers in fusion.items()),
        key=lambda t: -t[2])[:20]
    lignes_rapport = [
        "NETTOYAGE DES AUTEURS — rapport",
        "",
        f"mentions d'auteur en entrée      : {sum(1 for l in oeuvres if l.get('auteur','').strip())}",
        f"mentions écartées (faux auteurs) : {sum(ecartees.values())}",
        f"mentions conservées              : {len(sortie)}",
        f"auteurs distincts après fusion   : {len(presence)}",
        f"auteurs présents dans >= 5 charts: {sum(1 for v in presence.values() if v >= 5)}",
        "",
        "--- formes écartées les plus fréquentes (à vérifier, puis compléter",
        "    prompts/auteurs_exclusions.txt si ce sont bien de faux auteurs) ---",
    ]
    for forme, n in ecartees.most_common(25):
        lignes_rapport.append(f"    {n:>4} ×  {forme}")
    lignes_rapport += [
        "",
        "--- fusions de variantes les plus lourdes (à vérifier : une fusion",
        "    abusive réunirait deux auteurs distincts) ---",
    ]
    for rare, vers, n in fusions_lourdes:
        lignes_rapport.append(f"    {n:>4} ×  {rare}  ->  {vers}")
    lignes_rapport += ["", "--- 30 auteurs les plus présents ---"]
    for auteur, n in presence.most_common(30):
        lignes_rapport.append(f"    {n:>3} charts  {auteur}")

    texte = "\n".join(lignes_rapport)
    RAPPORT.parent.mkdir(parents=True, exist_ok=True)
    RAPPORT.write_text(texte, encoding="utf-8")

    print(f"{SORTIE} : {len(sortie)} lignes, {len(presence)} auteurs distincts.")
    print(f"  écartés : {sum(ecartees.values())} mentions ; "
          f"fusions de variantes : {len(fusion)}")
    print(f"  auteurs dans >= 5 charts : {sum(1 for v in presence.values() if v >= 5)}")
    print(f"[rapport détaillé dans {RAPPORT}]")


if __name__ == "__main__":
    principal()
