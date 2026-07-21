# lit-charts

Projet d'analyse de données autour des graphiques de littérature (lit charts).

## Prérequis

- [Miniconda ou Anaconda](https://docs.conda.io/)

## Installation

```bash
conda activate lit-charts   # environnement Python 3.11 (créé via conda-forge)
pip install -r requirements.txt
```

Pour recréer l'environnement de zéro :

```bash
conda create -n lit-charts python=3.11 -c conda-forge --override-channels
```

## Structure du projet

```
lit-charts/
├── data/
│   ├── raw/         # données brutes, immuables (non versionnées)
│   ├── interim/     # données intermédiaires (non versionnées)
│   └── processed/   # jeux de données finaux (non versionnés)
├── notebooks/       # notebooks Jupyter d'exploration et d'analyse
├── src/             # code source Python réutilisable
├── prompts/         # prompts utilisés (LLM, génération, etc.)
├── results/         # figures, tableaux et sorties d'analyse
├── requirements.txt # dépendances pip
└── README.md
```

## Conventions

- Les données brutes dans `data/raw/` ne sont jamais modifiées ni versionnées.
- Tout traitement part de `data/raw/` et écrit dans `data/interim/` ou `data/processed/`.
- Le code partagé entre notebooks vit dans `src/`.
