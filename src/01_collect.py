#!/usr/bin/env python3
"""Phase 1 — Collecte du corpus de charts.

Interroge deux sources publiques :
  1. l'API JSON officielle de 4chan (board /lit/ en direct) ;
  2. l'API de recherche FoolFuuka d'une archive (Desuarchive par
     défaut — voir l'avertissement près de ARCHIVE_URL_DEFAUT : cette
     archive ne couvre pas /lit/, seuls les résultats effectivement
     issus de /lit/ sont conservés).

Pour chaque mot-clé recherché, le script repère les posts pertinents,
télécharge les images attachées dans data/raw/images/ et consigne les
métadonnées (fil d'origine, date, nombre de réponses, texte du post)
dans data/interim/posts.csv.

Reprise : le CSV sert de journal. Au démarrage, les posts déjà traités
sont relus et sautés ; les images déjà présentes sur disque ne sont pas
retéléchargées. On peut donc interrompre le script (Ctrl-C) et le
relancer sans perte. Le flag --force ignore ce mécanisme.

Politesse : une temporisation (--delai, 2 s par défaut) est appliquée
avant chaque requête HTTP, et le script s'identifie via un User-Agent
explicite. L'API 4chan impose au maximum 1 requête par seconde.
"""

import argparse
import csv
import html
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

# --- Chemins du projet (relatifs à la racine du dépôt) ---
RACINE = Path(__file__).resolve().parents[1]
DOSSIER_IMAGES = RACINE / "data" / "raw" / "images"
CSV_POSTS = RACINE / "data" / "interim" / "posts.csv"

# --- Constantes des deux APIs ---
API_4CHAN_CATALOGUE = "https://a.4cdn.org/lit/catalog.json"
API_4CHAN_FIL = "https://a.4cdn.org/lit/thread/{no}.json"
IMG_4CHAN = "https://i.4cdn.org/lit/{tim}{ext}"
# Archive FoolFuuka interrogée (modifiable via --archive-url).
# ATTENTION : Desuarchive n'archive PAS /lit/ (constaté en juillet 2026 :
# sa recherche ignore alors le filtre de board et renvoie des posts
# d'autres boards). Le filtre strict ci-dessous protège le corpus ; pour
# collecter réellement les archives de /lit/, fournir une autre archive
# FoolFuuka via --archive-url (archived.moe couvre /lit/ mais bloque les
# scripts derrière Cloudflare ; warosu.org n'a pas d'API JSON).
ARCHIVE_URL_DEFAUT = "https://desuarchive.org"

MOTS_CLES_DEFAUT = ["chart", "reading list", "start with the greeks"]

# En-tête du CSV de sortie ; « source » vaut "4chan" ou "desuarchive".
COLONNES = [
    "source", "mot_cle", "num_fil", "num_post", "date",
    "nb_reponses", "texte", "fichier_image", "url_image",
]

# User-Agent explicite : les archives FoolFuuka rejettent les clients
# anonymes, et c'est la moindre des politesses pour du scraping.
USER_AGENT = "lit-charts-recherche/0.1 (etude universitaire ; contact : garniermarc.pro@gmail.com)"


def nettoyer_html(texte):
    """Convertit le HTML d'un post 4chan en texte brut lisible."""
    if not texte:
        return ""
    texte = texte.replace("<br>", "\n").replace("<br/>", "\n")
    texte = re.sub(r"<[^>]+>", "", texte)  # suppression des balises
    return html.unescape(texte).strip()


def date_iso(horodatage):
    """Convertit un horodatage Unix en date ISO 8601 (UTC)."""
    return datetime.fromtimestamp(int(horodatage), tz=timezone.utc).isoformat()


class Collecteur:
    """Encapsule la session HTTP, la temporisation et le journal CSV."""

    def __init__(self, delai, force, archive_url):
        self.delai = delai
        self.force = force
        # Endpoints FoolFuuka de l'archive choisie.
        self.api_recherche = archive_url.rstrip("/") + "/_/api/chan/search/"
        self.api_fil = archive_url.rstrip("/") + "/_/api/chan/thread/"
        self.session = requests.Session()
        self.session.headers["User-Agent"] = USER_AGENT
        # Cache du nombre de réponses par fil Desuarchive, pour ne pas
        # requêter deux fois le même fil.
        self.cache_nb_reponses = {}
        self.deja_vus = self._charger_deja_vus()
        self.nb_nouveaux = 0

    # ----- Reprise -----

    def _charger_deja_vus(self):
        """Relit le CSV existant pour savoir quels posts sauter."""
        if self.force or not CSV_POSTS.exists():
            return set()
        with open(CSV_POSTS, newline="", encoding="utf-8") as f:
            vus = {(ligne["source"], ligne["num_post"]) for ligne in csv.DictReader(f)}
        print(f"[reprise] {len(vus)} posts déjà collectés, ils seront sautés.")
        return vus

    # ----- HTTP poli -----

    def _get(self, url, params=None):
        """GET avec temporisation systématique et petit backoff sur 429."""
        time.sleep(self.delai)
        for tentative in range(3):
            reponse = self.session.get(url, params=params, timeout=30)
            if reponse.status_code == 429:  # trop de requêtes : on patiente
                attente = 30 * (tentative + 1)
                print(f"  [attente] 429 reçu, pause de {attente} s…")
                time.sleep(attente)
                continue
            reponse.raise_for_status()
            return reponse
        raise RuntimeError(f"Trop de 429 successifs sur {url}")

    def _get_json(self, url, params=None):
        return self._get(url, params=params).json()

    # ----- Écriture des résultats -----

    def _telecharger_image(self, url, nom_fichier):
        """Télécharge une image si elle n'est pas déjà sur disque.

        Écrit d'abord dans un fichier .tmp renommé à la fin : une
        interruption ne laisse jamais d'image tronquée, et la reprise
        peut se fier à la seule présence du fichier final.
        """
        chemin = DOSSIER_IMAGES / nom_fichier
        if chemin.exists() and not self.force:
            return
        temporaire = chemin.with_suffix(chemin.suffix + ".tmp")
        reponse = self._get(url)
        temporaire.write_bytes(reponse.content)
        temporaire.rename(chemin)

    def _enregistrer(self, writer, fichier_csv, ligne):
        """Ajoute une ligne au CSV et vide le tampon (sûreté en cas d'arrêt)."""
        writer.writerow(ligne)
        fichier_csv.flush()
        self.deja_vus.add((ligne["source"], ligne["num_post"]))
        self.nb_nouveaux += 1

    # ----- Source 1 : 4chan en direct -----

    def collecter_4chan(self, mots_cles, writer, fichier_csv):
        """Parcourt le catalogue de /lit/ à la recherche des mots-clés.

        L'API 4chan n'a pas de recherche : on filtre le catalogue sur le
        sujet et le texte de l'OP. Dans un fil retenu, toutes les images
        sont collectées (les charts sont souvent postés en réponse, sans
        reprendre le mot-clé).
        """
        print("=== Source : 4chan /lit/ (catalogue en direct) ===")
        catalogue = self._get_json(API_4CHAN_CATALOGUE)
        for page in catalogue:
            for fil in page["threads"]:
                texte_op = nettoyer_html(fil.get("sub", "") + " " + fil.get("com", "")).lower()
                correspondances = [mc for mc in mots_cles if mc in texte_op]
                if not correspondances:
                    continue
                self._collecter_fil_4chan(fil, correspondances[0], writer, fichier_csv)

    def _collecter_fil_4chan(self, fil, mot_cle, writer, fichier_csv):
        """Télécharge toutes les images d'un fil 4chan retenu."""
        num_fil = fil["no"]
        nb_reponses = fil.get("replies", "")
        print(f"[4chan] fil {num_fil} (mot-clé « {mot_cle} », {nb_reponses} réponses)")
        detail = self._get_json(API_4CHAN_FIL.format(no=num_fil))
        for post in detail["posts"]:
            if "tim" not in post:  # post sans image : rien à collecter
                continue
            if ("4chan", str(post["no"])) in self.deja_vus:
                continue
            nom_fichier = f"4chan_{num_fil}_{post['tim']}{post['ext']}"
            url_image = IMG_4CHAN.format(tim=post["tim"], ext=post["ext"])
            self._telecharger_image(url_image, nom_fichier)
            self._enregistrer(writer, fichier_csv, {
                "source": "4chan",
                "mot_cle": mot_cle,
                "num_fil": num_fil,
                "num_post": post["no"],
                "date": date_iso(post["time"]),
                "nb_reponses": nb_reponses,
                "texte": nettoyer_html(post.get("com", "")),
                "fichier_image": nom_fichier,
                "url_image": url_image,
            })

    # ----- Source 2 : Desuarchive (FoolFuuka) -----

    def collecter_archive(self, mots_cles, pages_max, writer, fichier_csv):
        """Recherche plein texte dans l'archive FoolFuuka, mot-clé par mot-clé.

        Garde-fou : si l'archive ne couvre pas /lit/, FoolFuuka ignore
        silencieusement le paramètre « board » et renvoie des posts
        d'autres boards. On vérifie donc le board de chaque résultat et
        on écarte tout ce qui ne vient pas de /lit/.
        """
        print(f"=== Source : archive FoolFuuka ({self.api_recherche}) ===")
        for mot_cle in mots_cles:
            for page in range(1, pages_max + 1):
                print(f"[archive] mot-clé « {mot_cle} », page {page}")
                donnees = self._get_json(self.api_recherche, params={
                    "board": "lit", "text": mot_cle, "page": page,
                })
                if "error" in donnees:  # plus de résultats (ou requête refusée)
                    print(f"  [archive] fin : {donnees['error']}")
                    break
                posts = donnees.get("0", {}).get("posts", [])
                if not posts:
                    break
                hors_board = [p for p in posts
                              if p.get("board", {}).get("shortname") != "lit"]
                if hors_board:
                    print(f"  [archive] AVERTISSEMENT : {len(hors_board)}/{len(posts)} "
                          f"résultats hors /lit/ écartés — cette archive ne couvre "
                          f"probablement pas /lit/ (essayer --archive-url).")
                for post in posts:
                    if post.get("board", {}).get("shortname") == "lit":
                        self._collecter_post_archive(post, mot_cle, writer, fichier_csv)

    def _nb_reponses_archive(self, num_fil):
        """Nombre de réponses d'un fil archivé (requête mise en cache).

        L'API de recherche ne renvoie pas cette information : on
        interroge le fil une seule fois, et en cas d'échec on laisse la
        colonne vide plutôt que d'interrompre la collecte.
        """
        if num_fil in self.cache_nb_reponses:
            return self.cache_nb_reponses[num_fil]
        try:
            donnees = self._get_json(self.api_fil, params={"board": "lit", "num": num_fil})
            fil = donnees.get(str(num_fil), {})
            nb = fil.get("op", {}).get("nreplies") or len(fil.get("posts", {}))
        except Exception as erreur:
            print(f"  [archive] fil {num_fil} : réponses inconnues ({erreur})")
            nb = ""
        self.cache_nb_reponses[num_fil] = nb
        return nb

    def _collecter_post_archive(self, post, mot_cle, writer, fichier_csv):
        """Traite un résultat de recherche FoolFuuka (un post archivé)."""
        media = post.get("media") or {}
        url_image = media.get("media_link") or media.get("remote_media_link")
        if not url_image:  # post sans image, ou média purgé de l'archive
            return
        if ("archive", str(post["num"])) in self.deja_vus:
            return
        nom_serveur = media.get("media") or Path(url_image).name
        nom_fichier = f"archive_{post['thread_num']}_{nom_serveur}"
        self._telecharger_image(url_image, nom_fichier)
        self._enregistrer(writer, fichier_csv, {
            "source": "archive",
            "mot_cle": mot_cle,
            "num_fil": post["thread_num"],
            "num_post": post["num"],
            "date": date_iso(post["timestamp"]),
            "nb_reponses": self._nb_reponses_archive(post["thread_num"]),
            "texte": nettoyer_html(post.get("comment") or ""),
            "fichier_image": nom_fichier,
            "url_image": url_image,
        })


def principal():
    parseur = argparse.ArgumentParser(description="Phase 1 : collecte des charts de /lit/.")
    parseur.add_argument("--mots-cles", nargs="+", default=MOTS_CLES_DEFAUT,
                         help="mots-clés recherchés (défaut : %(default)s)")
    parseur.add_argument("--delai", type=float, default=2.0,
                         help="pause en secondes avant chaque requête (défaut : %(default)s)")
    parseur.add_argument("--pages-max", type=int, default=10,
                         help="pages de résultats Desuarchive par mot-clé (défaut : %(default)s)")
    parseur.add_argument("--archive-url", default=ARCHIVE_URL_DEFAUT,
                         help="archive FoolFuuka à interroger (défaut : %(default)s ; "
                              "voir l'avertissement en tête de fichier sur /lit/)")
    parseur.add_argument("--force", action="store_true",
                         help="retraite tout, y compris les posts et images déjà collectés")
    arguments = parseur.parse_args()

    DOSSIER_IMAGES.mkdir(parents=True, exist_ok=True)
    CSV_POSTS.parent.mkdir(parents=True, exist_ok=True)

    collecteur = Collecteur(delai=arguments.delai, force=arguments.force,
                            archive_url=arguments.archive_url)
    mots_cles = [mc.lower() for mc in arguments.mots_cles]

    # Le CSV est ouvert en ajout : les lignes des exécutions précédentes
    # sont conservées (c'est le journal qui permet la reprise).
    nouveau = arguments.force or not CSV_POSTS.exists()
    mode = "w" if nouveau else "a"
    with open(CSV_POSTS, mode, newline="", encoding="utf-8") as fichier_csv:
        writer = csv.DictWriter(fichier_csv, fieldnames=COLONNES)
        if nouveau:
            writer.writeheader()
        try:
            collecteur.collecter_4chan(mots_cles, writer, fichier_csv)
            collecteur.collecter_archive(mots_cles, arguments.pages_max, writer, fichier_csv)
        except KeyboardInterrupt:
            print("\n[interruption] collecte arrêtée ; relancer le script reprendra où il s'est arrêté.")
            sys.exit(130)

    print(f"Terminé : {collecteur.nb_nouveaux} nouveaux posts ajoutés à {CSV_POSTS}.")


if __name__ == "__main__":
    principal()
