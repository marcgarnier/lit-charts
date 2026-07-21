# lit-charts

Pipeline computationnel pour l'étude des **charts de lecture de 4chan /lit/** comme dispositifs gamifiés — code, lexiques, carnet d'analyse et article.

Étude en sciences de l'information et de la communication : les 264 charts du wiki de /lit/ sont traités de bout en bout (OCR, reconstruction de la mise en page, relevé lexical de la gamification, typologie émergente, réseau des auteurs), **entièrement en local**, sans API distante ni coût à l'usage.

- **Article** : [papier/article.md](papier/article.md)
- **Carnet de résultats** (exécuté, figures incluses) : [notebooks/resultats.ipynb](notebooks/resultats.ipynb)
- **Page de présentation** : <https://marcgarnier.github.io/website/kino.html>

## Résultats en bref

| Résultat | Mesure |
|---|---|
| Les charts sont d'abord des catalogues | 74,6 % de grilles/collages ; 20,1 % de formes prescriptives ; 12,9 % avec flèches |
| La gamification est discursive avant d'être vidéoludique | ordre prescrit 26 %, impératif 24 % — paliers nommés 4 %, « God-Tier » 2 % |
| Le travail prescriptif se distribue forme/langage | listes de texte : 73 % d'injonctions ; grilles : score lexical médian nul |
| Deux familles émergentes, pas trois | k-moyennes : 222 catalogues muets / 42 guides prescriptifs ; ARI 0,09 (formes), 0,02 (thèmes) |
| Le canon voyage en bloc | noyau de 124 auteurs, densité de cooccurrence 56,5 % ; aucun auteur ≥ 7 % du corpus |
| Résultat négatif assumé | classification des formes par VLM local rejetée : α de Krippendorff 0,078 (flèches : 0,842, conservée) |

## Le pipeline

```
data/raw/images/          264 images (non versionnées)
        │
  01_ocr.py               OCR par bandes, pleine résolution
        │                 moteurs : vision (macOS, défaut) | surya (libre, contrôle)
  03_vlm.py               classement visuel local (seul has_arrows est fiable)
        │
  02_blocs.py             blocs, sections, auteur/titre — géométrie pure, sans modèle
  06_marqueurs.py         9 registres lexicaux de gamification (prompts/marqueurs.json)
  09_auteurs.py           nettoyage + normalisation des auteurs (rapport versionné)
        │
  05_tables.py            charts.csv · oeuvres.csv
  07_traits.py            traits.csv — matrice de la typologie (19 variables)
  08_accord.py            α de Krippendorff (results/accord_inter_codeurs.txt)
  10_figures_site.py      figures aux couleurs du site
        │
  notebooks/resultats.ipynb   analyses, figures, clustering, réseau
```

Chaque script est **relançable sans recalcul** (les sorties existantes sont sautées, `--force` pour retraiter), commenté en français, et consigne ce qu'il fait. Les décisions de méthode — y compris les échecs mesurés — sont documentées dans [CLAUDE.md](CLAUDE.md).

## Installation

```bash
conda create -n lit-charts python=3.11 -c conda-forge --override-channels
conda activate lit-charts
pip install -r requirements.txt
# phases locales à modèles : installer Ollama (https://ollama.com) puis
ollama pull qwen2.5vl:3b && ollama pull llama3.1
```

Les images du corpus ne sont pas redistribuées (artefacts d'usagers anonymes, reproduits dans l'étude à seule fin d'analyse) : placer les vôtres dans `data/raw/images/` puis dérouler le pipeline dans l'ordre ci-dessus.

## Données versionnées

Le dépôt ne contient ni images ni sorties volumineuses (voir `.gitignore`). Sont versionnés : le code, les lexiques (`prompts/`), le codage des formes des 264 charts (`data/interim/codage_manuel_formes.csv`, provenance déclarée en tête de fichier), l'inventaire du corpus, les rapports de fiabilité (`results/*.txt`) et le carnet exécuté.

## Citation

> Garnier, M. (2026). *« That's kino anon » : les charts de /lit/ comme dispositifs gamifiés. D'une lecture qualitative à une mesure computationnelle du corpus.* https://github.com/marcgarnier/lit-charts

## Licence

Code et lexiques sous licence MIT (voir [LICENSE](LICENSE)). L'article (`papier/`) est © Marc Garnier.
