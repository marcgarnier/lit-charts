# CLAUDE.md

## Le projet

`lit-charts` est une étude en sciences de l'information et de la communication portant sur les **« charts » de lecture de 4chan /lit/** : ces images-guides (« start with the Greeks », « so you want to read… ») qui prescrivent des parcours de lecture. Elles sont analysées comme des **dispositifs gamifiés** — progression par niveaux, points d'entrée, embranchements, badges implicites, difficulté croissante — et non comme de simples listes bibliographiques.

Le livrable central est un **pipeline computationnel reproductible** qui va du corpus brut à l'interprétation, en 6 phases.

## Les 6 phases du pipeline

1. **Collecte** — constitution du corpus de charts (archives de /lit/, wikis, miroirs) avec métadonnées de provenance (source, date, fil d'origine).
2. **Extraction** — en trois temps, chaque outil sur la question qu'il sait traiter (voir « Répartition des tâches » plus bas) :
   - **2a OCR** (`01_ocr.py`) : lecture du texte. Deux moteurs — `vision` (macOS, ~20 min pour le corpus) par défaut, `surya` (open source, ~13 h) pour contrôle.
   - **2c Classement visuel** (`03_vlm.py`, qwen2.5vl) : uniquement le type de mise en page et la présence de liens dessinés.
   - **2b Géométrie** (`02_blocs.py`, sans modèle) : regroupement des lignes en blocs, repérage des intitulés de sections, rattachement des œuvres à leur niveau, séparation auteur/titre.

   **Ordre d'exécution : 2a → 2c → 2b.** La numérotation des fichiers reflète l'ordre historique d'écriture, pas l'ordre d'appel. `02_blocs.py` a besoin du `layout_type` de `03_vlm.py` pour choisir son régime : distinguer une grille d'une carte est une question visuelle, et la géométrie s'y est montrée impuissante (coefficient de variation des écarts de colonnes, dispersion des abscisses, couverture verticale — tous mesurés, tous ambigus). Sans classement visuel disponible, `02_blocs.py` retombe sur une heuristique géométrique, moins fiable.
3. **Codage des mécaniques** (`04_codage.py`, llama3.1) — annotation de chaque chart selon une grille de mécaniques de gamification (progression, prérequis, niveaux de difficulté, embranchements, récompenses, injonctions, ton). Grille dans `prompts/codage.txt`.
4. **Typologie par clustering** — regroupement non supervisé des charts pour dégager une typologie empirique des formes de gamification. La matrice d'entrée est `data/processed/traits.csv` (`07_traits.py`) : 19 variables tirées du seul OCR, aucune étiquette imposée a priori.

## Ce qui est dans le pipeline, et ce qui le valide

Distinction à maintenir dans toute publication, sous peine de fausser la revendication de reproductibilité.

**Dans le pipeline** — local, open source, rejouable : OCR (`01_ocr.py`), géométrie (`02_blocs.py`), marqueurs lexicaux (`06_marqueurs.py`), traits (`07_traits.py`), tableaux (`05_tables.py`). Le classement visuel local (`03_vlm.py`) en fait partie techniquement, mais voir la réserve ci-dessous.

**Hors pipeline, validation externe** : le codage des formes des 264 charts, dans `data/interim/codage_manuel_formes.csv`. **Il a été produit par un modèle vision-langage distant (Claude)**, qui a examiné les images une à une, et non par un humain ni par le pipeline local. Il est donc ni local ni open source. Il sert de jeu de référence pour juger les groupes issus de la phase 4 — au même titre que les catégories du wiki, et comme elles, extérieur au dispositif qu'il valide. Toute publication doit le déclarer tel quel ; l'attribuer au modèle local serait démontrablement faux (voir ci-dessous). L'idéal serait qu'un échantillon soit revérifié par l'auteur, ce qui en ferait un codage assisté validé.

**Réserve mesurée sur `03_vlm.py`** (`08_accord.py`, rapport dans `results/`) : confronté au codage de référence sur 36 charts, le modèle local obtient un alpha de Krippendorff de **0,078 sur `layout_type`** — sous tout seuil d'exploitabilité, à peine mieux qu'un annotateur qui répondrait toujours la même étiquette. Il répond « sectioned_grid » 27 fois sur 36. **`layout_type` produit par le modèle local ne doit pas entrer dans une analyse.** En revanche `has_arrows` atteint **0,842**, au-dessus du seuil de fiabilité : cette variable est exploitable, et capte ce que le texte ne dit pas — un chart peut imposer un ordre graphiquement sans jamais l'écrire.
5. **Réseaux d'auteurs** — graphes de cooccurrence des auteurs/œuvres entre charts : centralité du canon, communautés, positions périphériques.
6. **Interprétation** — analyse communicationnelle des résultats, figures et tableaux finaux dans `results/`.

Chaque phase lit les sorties de la précédente : `data/raw/` → `data/interim/` → `data/processed/` → `results/`.

## Répartition des tâches entre outils

Règle directrice, établie par mesure et non par principe : **ne jamais demander à un modèle ce qu'un calcul déterministe peut établir, ni à un modèle de vision ce qui relève du texte.**

| Question | Outil | Pourquoi |
|---|---|---|
| Que dit le texte du chart ? | OCR (Vision par défaut, Surya en contrôle) | Un VLM local sur image réduite ne lit plus rien et invente. Vision est 75× plus rapide que Surya à qualité égale ; Surya, libre et portable, sert à rejouer un échantillon. |
| Quelles lignes forment un bloc, quel intitulé les gouverne ? | Géométrie pure (Python) | Les coordonnées de l'OCR contiennent déjà la réponse : instantané, déterministe, rien à halluciner. |
| Quelle est la forme du chart, y a-t-il des flèches ? | VLM (qwen2.5vl) | Seule question réellement visuelle. Posée seule, elle est traitée juste et vite. |
| Quelles mécaniques de gamification ? | LLM de texte (llama3.1) | Après OCR + géométrie il n'y a plus d'image : c'est une tâche de lecture, où un 8B de texte surpasse largement un 3B de vision. |

Mesures qui ont conduit à cette répartition (carte de philosophie, 2048×1437) : le VLM chargé de tout extrait 10 sections prises pour des livres, invente une chaîne de flèches inexistante, en 11 minutes. Restreint à la forme, il répond « map, avec liens » — exact — en 1 minute. La géométrie retrouve les 14 grappes et leurs 185 œuvres en moins d'une seconde.

Corollaire pratique : avant d'ajouter un appel de modèle, se demander si la donnée n'est pas déjà déductible des sorties précédentes.

## Contraintes non négociables

- **Local de bout en bout** : aucune API distante, aucune clé, aucun service cloud, aucun coût à l'usage. Le pipeline complet tourne sur une machine personnelle.
- **Libre, avec une exception assumée et contrôlable** : tout est open source (Surya, Ollama, qwen2.5vl, llama3.1) *sauf* le moteur OCR par défaut, qui est le framework Vision de macOS — local et gratuit, mais propriétaire et limité à macOS. Il est retenu pour un écart de performance qui change la nature du travail : 20 minutes contre 13 heures sur le corpus, à qualité mesurée équivalente. La contrepartie est explicite : `01_ocr.py --moteur surya` rejoue la même étape en open source sur n'importe quel système, et doit être passé sur un échantillon pour que la méthodologie puisse attester que les résultats ne dépendent pas d'un composant fermé. Le moteur employé est inscrit dans chaque fichier produit.
- **Code commenté en français** : tous les commentaires, docstrings et messages de log sont rédigés en français. Les noms de variables/fonctions peuvent rester en anglais si c'est plus idiomatique.
- **Reprise sans recalcul** : chaque script doit pouvoir être **relancé sans tout recalculer**. Concrètement : vérifier si la sortie existe déjà et la sauter (cache sur disque, traitement incrémental par fichier), ne jamais écraser silencieusement un résultat coûteux, prévoir un flag `--force` pour forcer le recalcul.

## Environnement et organisation

- Environnement conda `lit-charts` (Python 3.11, canal conda-forge) : `conda activate lit-charts`. Dépendances dans `requirements.txt` (pip).
- `data/raw/` est immuable et non versionné ; tout traitement écrit dans `data/interim/` ou `data/processed/`. Les images et données ne sont jamais commitées (voir `.gitignore`).
- `src/` : code réutilisable, organisé par phase. `notebooks/` : exploration seulement, la logique validée migre vers `src/`. `prompts/` : prompts VLM versionnés, un fichier par usage. `results/` : figures et tableaux finaux.
