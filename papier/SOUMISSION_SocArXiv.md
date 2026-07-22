# Soumettre le préprint sur SocArXiv — mode d'emploi

Le PDF prêt à déposer : **`Garnier_2026_lit-charts_SocArXiv.pdf`** (ce dossier).
Régénérable à tout moment : `python papier/build_pdf.py`.

## Pourquoi c'est vous qui déposez, pas le pipeline

SocArXiv passe par **OSF** (Open Science Framework, <https://osf.io/preprints/socarxiv>).
Déposer un préprint suppose de se connecter à votre compte OSF, d'accepter des
conditions et de rendre public un document horodaté qui reçoit un DOI et est
indexé. C'est une action personnelle, engageante et irréversible : elle doit
être faite par vous, depuis votre compte. Les champs ci-dessous sont prêts à
copier-coller.

## Étapes

1. Compte OSF (gratuit) : <https://osf.io> → *Sign up* (ou connexion institutionnelle Université Laval).
2. <https://osf.io/preprints/socarxiv> → **Add a preprint** → *Create a new preprint*.
3. **Upload** : déposer le PDF ci-dessus.
4. Renseigner les métadonnées (section suivante).
5. Relire l'aperçu, puis **Submit**. La modération SocArXiv est légère (vérification de pertinence disciplinaire), la mise en ligne prend en général de quelques heures à un jour.

## Métadonnées à saisir

**Title**
```
« That's kino anon » : les charts de /lit/ comme dispositifs gamifiés. D'une lecture qualitative à une mesure computationnelle du corpus
```

**Authors** : Marc Garnier (Université Laval). Ajouter l'ORCID si vous en avez un.

**Abstract** (coller le résumé français, ou l'anglais selon la langue déclarée — SocArXiv accepte les deux ; l'anglais élargit l'audience) :
> This paper studies the reading charts of 4chan's /lit/ board — images recommending corpora of authors — as gamified devices for the diffusion of literary radicalism. An initial qualitative inquiry over a sample drawn from a base of 262 charts identified four gamified mechanics and three framing structures. The present version puts these categories to the test of exhaustive measurement: a local, reproducible computational pipeline — OCR, geometric layout reconstruction, lexical screening of nine gamification registers, form coding of all 264 images, unsupervised clustering, and an author co-occurrence network — processes the whole corpus. Results refine rather than confirm the initial thesis. Three quarters of the charts (74.6%) are catalogues that juxtapose without prescribing a route; gamification proves discursive first (26.1% of charts prescribe an order, 23.9% address the reader in the imperative) while its video-game decorum is rare (named tiers: 3.8%; value hierarchy: 1.9%); prescriptive work is distributed between layout and utterance. Emergent clustering retains only two families and matches neither visual form nor topic (adjusted Rand indices of 0.09 and 0.02). The circulated canon behaves as a solidary block (56.5% co-occurrence density over the 124-author core) with no single obligatory name: radicalism spreads less through waymarked initiation than through the reproduction of a list. The paper also documents two negative methodological results, including the measured rejection (Krippendorff's α = 0.078) of automatic form classification by a local vision-language model.

**Keywords**
```
4chan; gamification; counter-public sphere; framing; literary canon; computational methods; content analysis
```

**Discipline / Subject** (arborescence bepress d'OSF) :
- *Social and Behavioral Sciences → Communication*
- ajouter si proposé : *Critical and Cultural Studies*, *Social Media*

**License** : `CC-BY 4.0` recommandée (préprint ouvert, réutilisation avec attribution). À défaut, `CC-BY-NC-ND 4.0` pour restreindre les usages commerciaux et les dérivés.

**Supplements / lien de données** — dans le champ prévu, ou en note :
```
Code, lexiques et carnet d'analyse reproductible : https://github.com/marcgarnier/lit-charts
```

**Conflict of interest** : aucun. **Funding** : à renseigner si applicable (sinon « None »).

## Points de vigilance avant de cliquer *Submit*

- **Déclaration d'usage des LLM** : elle figure déjà dans l'article (section « Déclaration de transparence »). Aucune revue ni SocArXiv ne l'exige au dépôt, mais elle est là et vous protège.
- **Corpus d'images** : le PDF ne reproduit que trois exemples de charts à titre d'analyse ; les 264 images ne sont pas redistribuées (artefacts d'usagers anonymes). Rien à joindre.
- **Version** : SocArXiv gère les versions. Vous pourrez déposer une v2 (le modèle que vous m'avez montré est un `_v2`) sans changer le DOI de base.
- **Anonymat** : le fichier initial était anonymisé (« _anon »). Ce préprint est signé — c'est le propre d'un préprint. Vérifiez que c'est bien voulu à ce stade.
