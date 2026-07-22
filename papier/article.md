# « That's kino anon » : les charts de /lit/ comme dispositifs gamifiés. D'une lecture qualitative à une mesure computationnelle du corpus

**Marc Garnier**

Version étendue du travail présenté au séminaire COM 885. Juillet 2026.

Code, données dérivées et carnet d'analyse : <https://github.com/marcgarnier/lit-charts>

---

## Résumé

Ce travail étudie les *charts* de lecture du board /lit/ de 4chan — des images qui recommandent des corpus d'auteurs — en tant que dispositifs gamifiés de diffusion de radicalités littéraires. Une première enquête qualitative, conduite sur un échantillon d'une dizaine de charts issus d'une base de 262, avait dégagé quatre mécaniques de gamification (progression, récompense symbolique, simplification cognitive, identification communautaire) et trois structures de cadrage (guides initiatiques, canons culturels, cartographies ludiques). La présente version soumet ces catégories à l'épreuve d'une mesure exhaustive : un pipeline computationnel local et reproductible — OCR par bandes, reconstruction géométrique de la mise en page, relevé lexical de neuf registres de gamification, codage de la forme des 264 images, classification non supervisée, réseau de cooccurrence des auteurs — traite l'intégralité du corpus sur une machine personnelle sans recours à aucune API distante. Les résultats précisent la thèse initiale plus qu'ils ne la confirment. Les trois quarts des charts (74,6 %) sont des catalogues qui juxtaposent sans prescrire de parcours ; la gamification s'avère d'abord discursive (26,1 % des charts prescrivent un ordre, 23,9 % recourent à l'impératif) quand son décorum vidéoludique est rare (paliers nommés : 3,8 % ; hiérarchie de valeur : 1,9 %) ; le travail prescriptif se distribue entre l'agencement visuel et l'énonciation, qui se compensent. La classification émergente ne retient que deux familles — catalogues muets et guides prescriptifs — et ne recoupe ni la forme visuelle ni le thème (indices de Rand ajustés de 0,09 et 0,02) : la troisième structure théorisée ne se sépare pas empiriquement. Enfin, le canon mis en circulation fonctionne comme un bloc solidaire (densité de cooccurrence de 56,5 % sur le noyau de 124 auteurs) sans qu'aucun nom ne soit obligatoire. La radicalité diffuse moins par l'initiation balisée que par la reconduction d'une liste : la conformité précède l'initiation. L'article documente également deux résultats négatifs de méthode, dont le rejet mesuré (α de Krippendorff = 0,078) de la classification automatique des formes par modèle vision-langage local, et propose une contribution méthodologique : un protocole reproductible et frugal pour l'analyse computationnelle de corpus visuels en sciences de l'information et de la communication.

**Mots-clés :** 4chan, gamification, contre-sphère publique, cadrage, canon littéraire, méthodes computationnelles, analyse de contenu, reproductibilité

## Abstract

This paper studies the reading *charts* of 4chan's /lit/ board — images recommending corpora of authors — as gamified devices for the diffusion of literary radicalism. An initial qualitative inquiry over a sample drawn from a base of 262 charts identified four gamified mechanics and three framing structures. The present version puts these categories to the test of exhaustive measurement: a local, reproducible computational pipeline — band-tiled OCR, geometric layout reconstruction, lexical screening of nine gamification registers, form coding of all 264 images, unsupervised clustering, and an author co-occurrence network — processes the whole corpus on a personal machine with no remote API. Results refine rather than confirm the initial thesis. Three quarters of the charts (74.6%) are catalogues that juxtapose without prescribing a route; gamification proves discursive first (26.1% of charts prescribe an order, 23.9% address the reader in the imperative) while its video-game decorum is rare (named tiers: 3.8%; value hierarchy: 1.9%); prescriptive work is distributed between layout and utterance, which compensate for each other. Emergent clustering retains only two families — mute catalogues and prescriptive guides — and matches neither visual form nor topic (adjusted Rand indices of 0.09 and 0.02): the third theorised structure does not separate empirically. Finally, the circulated canon behaves as a solidary block (56.5% co-occurrence density over the 124-author core) with no single obligatory name: radicalism spreads less through waymarked initiation than through the reproduction of a list — conformity precedes initiation. The paper also documents two negative methodological results, including the measured rejection (Krippendorff's α = 0.078) of automatic form classification by a local vision-language model, and offers a methodological contribution: a reproducible, frugal protocol for the computational analysis of visual corpora in communication studies.

**Keywords:** 4chan, gamification, counter-public sphere, framing, literary canon, computational methods, content analysis, reproducibility

---

## 1. Introduction

La montée des forums de discussion en ligne comme 4chan a profondément transformé l'espace public et la communication politique. Le board Literature de ce forum (/lit/), dédié en principe à la littérature, aux livres et aux humanités, illustre cette mutation : il devient un lieu où la culture sert de support à la diffusion d'idéologies et de visions du monde, parfois radicales. À travers des visuels appelés *charts* de lecture, les usagers y recommandent des corpus d'auteurs organisés selon des logiques de progression et de hiérarchie que l'on peut qualifier de « gamifiées ».

La communication politique contemporaine s'inscrit dans un contexte de sphères publiques fragmentées (Bennett & Pfetsch, 2018) : les interactions ne se construisent plus autour d'un espace commun mais dans une multiplicité d'arènes discursives, souvent en ligne. Cette configuration déstabilise le modèle habermassien d'un espace public reposant sur l'échange rationnel entre citoyens égaux (Habermas, 1978). Sur 4chan, les interactions sont anonymes, affectives et hautement symboliques ; de ce chaos naissent de nouvelles formes de légitimité et de circulation de l'information. À la suite de Fraser (2001), on peut faire l'hypothèse que /lit/ fonctionne comme une contre-sphère publique numérique, où culture littéraire et culture internet se mêlent pour devenir des vecteurs de diffusion de radicalités politiques — un espace où, comme le note De Zeeuw (2024) à propos des pseudo-sphères publiques, rien n'est tout à fait sérieux ni tout à fait jeu.

Le travail initial (Garnier, 2026) analysait qualitativement une dizaine de charts sélectionnés dans une base de 262. Il concluait à l'existence de quatre mécaniques gamifiées récurrentes et de trois structures de cadrage, et soutenait que la diffusion de radicalités tient moins à un militantisme avéré qu'à une économie des symboles valorisant l'appartenance subculturelle. Ces résultats reposaient toutefois sur un échantillon restreint, lu à la main. La présente version pose la question qui en découle : **que reste-t-il de ces catégories quand on mesure l'intégralité du corpus ?**

Pour y répondre, nous avons construit un pipeline computationnel entièrement local et reproductible qui traite les 264 images du corpus : extraction du texte, reconstruction de la structure visuelle, relevé systématique du vocabulaire de la gamification, codage de la forme de chaque chart, classification non supervisée et analyse de réseau des auteurs cités. La démarche assume un double objectif, empirique et méthodologique. Empirique : produire des résultats sur corpus entier, là où l'analyse qualitative ne pouvait que suggérer des tendances. Méthodologique : documenter — y compris dans ses échecs mesurés — ce qu'une instrumentation computationnelle légère, sans budget ni infrastructure, peut apporter à l'analyse de contenu de corpus *visuels* en sciences de l'information et de la communication (SIC), champ où l'outillage reste largement conçu pour le texte (Baden et al., 2022). Nous soutenons qu'un tel protocole a valeur de contribution en soi : l'article détaille donc chaque décision, chiffre chaque étape, et ancre chaque affirmation dans le code publié.

L'article procède ainsi. La section 2 rappelle le cadre théorique. La section 3, cœur technique de ce travail, décrit le corpus puis les six phases du pipeline, en justifiant chaque choix et en rapportant volumétries, temps de calcul et échecs. La section 4 détaille les résultats. Les sections 5 à 7 discutent, bornent et concluent. Une annexe technique (annexe A) consigne l'infrastructure, l'ordre d'exécution et les garanties de reproductibilité.

## 2. Cadre théorique

### 2.1 /lit/ comme contre-sphère publique

Fraser (2001) montre que les groupes marginaux créent leurs propres espaces discursifs : des « arènes discursives parallèles dans lesquelles les membres des groupes sociaux subordonnés élaborent et diffusent des contre-discours, afin de formuler leur propre interprétation de leurs identités, leurs intérêts et leurs besoins » (p. 138). /lit/ en offre une illustration contemporaine : un espace discursif autonome où des discours alternatifs se construisent à partir d'objets culturels plutôt qu'autour de leaders ou de manifestes. Bennett et Pfetsch (2018) décrivent quant à eux un environnement de sphères publiques fragmentées où la cohésion du débat laisse place à des « micro-publics » autonomes, chacun développant ses logiques discursives propres — dispersion que Dahlgren (2005) et Waisbord (2016) documentent également. La structure anonyme de 4chan, sa culture du remix et la circulation interne de visuels favorisent précisément la constitution d'un micro-public intellectuel, dont l'interface même — qui exige une phase d'adaptation ou de *lurking* — trace les frontières.

Cette contre-sphère est aussi une culture de la transgression. Nagle (2017) a montré comment l'esthétique du détournement propre à 4chan a constitué le cœur culturel de la nouvelle droite en ligne, normalisant des discours réactionnaires derrière le masque du cynisme et du jeu mémétique ; Phillips (2015) situe ce trolling dans son rapport constitutif à la culture dominante. Sur /lit/, culture savante, rhétorique et idéologie se confondent dans une forme hybride de communication politique.

### 2.2 Gamification et cadrage

Les charts reposent sur un principe de gamification : l'application d'éléments de design du jeu à des contextes non ludiques afin d'encourager l'engagement (Deterding et al., 2011). Raessens (2014) parle d'une « ludification de la culture » qui transforme les modes de socialisation et de production symbolique à l'ère numérique ; les médias sociaux offrent aux usagers « the possibility to playfully express who they think they are » (p. 98). Dans le cas des charts, la lecture — activité traditionnellement individuelle et réflexive — est reconfigurée en parcours ludique : on « grimpe » des niveaux d'érudition, on « débloque » des auteurs, on « complète » un itinéraire intellectuel.

Les charts opèrent enfin comme des dispositifs de cadrage au sens d'Entman (2004) : ils délimitent ce qu'il faut lire, penser et croire, la hiérarchie visuelle se substituant à la délibération. Comme le rappellent Gerstlé et Piar (2020, p. 82) citant Nelson, Oxley et Clawson (1997), les cadres « peuvent n'apporter aucune information nouvelle, mais leur influence sur nos opinions peut être décisive pour leur contribution à la hiérarchisation de considérations alternatives ». Et si l'on suit McLuhan (1964), le message idéologique ne réside pas seulement dans les œuvres recommandées mais dans la forme même de la recommandation — intuition que la présente étude prend au pied de la lettre, puisqu'elle consiste à mesurer cette forme.

Le travail initial en dégageait quatre mécaniques — progression, récompense symbolique, simplification cognitive, identification communautaire — et trois structures de cadrage : les guides initiatiques (apprentissage gradué), les canons culturels (bibliothèques idéologiques fermées) et les cartographies ludiques (arbres de décision à la manière des RPG, où la liberté apparente du joueur dissimule une orientation cadrée à l'avance). Ce sont ces catégories que la mesure met à l'épreuve.

## 3. Corpus et méthode

### 3.1 Corpus et constitution

Le corpus est constitué des 264 images rassemblées par le wiki communautaire des charts de /lit/, soit la base de 262 charts réunie pour le travail initial, complétée de deux doublons de classement (une même image rangée dans deux catégories thématiques du wiki, que nous conservons pour ne pas perdre l'information de rangement multiple). Le wiki organise ces images en onze catégories thématiques (Beginnings, General, Philosophy, Countries, Speculative Fiction, Religion, Ideologies, Pills, Science, Meme Charts, Other Boards). Ce classement indigène est conservé comme point de comparaison externe — jamais comme variable d'analyse, ce qui serait circulaire (voir § 3.8).

Les images sont matériellement très hétérogènes : de 0,3 à 43,1 mégapixels, médiane 4,1. Cette hétérogénéité a des conséquences méthodologiques directes. Les grands charts (jusqu'à 7 600 px de côté) portent un texte proportionnellement minuscule, ce qui met en échec l'OCR appliqué à l'image entière (§ 3.4) ; les seuils géométriques doivent être exprimés en unités relatives à chaque image plutôt qu'en pixels absolus (§ 3.6) ; et la charge mémoire des modèles vision-langage sur ces images sature une machine à 8 Go (§ 3.5). L'architecture du pipeline est en grande partie une réponse à cette contrainte.

Deux limites de constitution doivent être posées d'emblée. D'une part, le corpus provient du wiki et non des fils de discussion : il ne comporte aucune métadonnée de circulation (dates de publication, nombre de reposts), et les analyses de recirculation (§ 4.6) reposent donc sur le contenu des charts, non sur leur diffusion observée. D'autre part, le wiki opère sa propre curation ; le corpus représente les charts jugés dignes d'archivage par la communauté, non l'ensemble des charts ayant circulé. Un module de collecte directe (`src/01_collect.py`, interrogeant l'API JSON publique de 4chan et une archive FoolFuuka) a été développé, mais l'archive historique de /lit/ n'exposant pas d'API exploitable, la collecte de fils reste une extension et non une source du présent corpus.

### 3.2 Contrainte d'exécution locale et principes de reproductibilité

L'ensemble du traitement s'exécute localement, sans API distante ni coût à l'usage, sur une machine personnelle ordinaire (Apple M1, 8 Go de mémoire unifiée ; voir annexe A). Cette contrainte n'est pas un simple parti pris économique : elle garantit qu'un tiers peut rejouer l'analyse intégralement, sans dépendre d'un service susceptible de changer, d'être facturé ou d'être retiré ; elle protège des dérives de coût qui rendent les LLM propriétaires prohibitifs aux grandes échelles de corpus (Alizadeh et al., 2024) ; et elle a imposé des choix d'architecture qui constituent en eux-mêmes des résultats de méthode, développés ci-dessous.

Trois principes de reproductibilité gouvernent l'implémentation. **(i) Relançabilité sans recalcul** : chaque script vérifie l'existence de ses sorties et saute ce qui est déjà fait, un indicateur `--force` permettant de retraiter ; on peut donc interrompre et reprendre un traitement long (l'OCR, le classement visuel) sans perte. **(ii) Déterminisme** : toutes les graines aléatoires sont fixées (k-moyennes, disposition du graphe), et les étapes non stochastiques — géométrie, relevé lexical, nettoyage des auteurs — produisent le même résultat à chaque exécution. **(iii) Traçabilité** : le moteur d'OCR employé est inscrit dans chaque fichier produit ; chaque détection lexicale conserve la ligne qui la justifie ; les rapports de nettoyage des auteurs et d'accord inter-codeurs sont versionnés avec le code. L'ensemble — code commenté en français, lexiques, carnet d'analyse exécuté, rapports — est publié (Garnier, 2026b).

### 3.3 Vue d'ensemble du pipeline

Le pipeline comprend six phases, dont la deuxième se décompose en trois sous-étapes exécutées dans un ordre précis. Le tableau 1 en donne la carte, avec le fichier de code correspondant et la nature de chaque étape.

**Tableau 1.** Phases du pipeline et fichiers du dépôt

| Phase | Fichier | Nature | Sortie principale |
|---|---|---|---|
| 1. Collecte / constitution | `01_collect.py` | API + inventaire | corpus, `inventaire_images.csv` |
| 2a. OCR | `01_ocr.py` | modèle (Vision / Surya) | texte + coordonnées |
| 2c. Classement visuel | `03_vlm.py` | VLM local (Qwen2.5-VL) | `layout_type`, `has_arrows` |
| 2b. Géométrie | `02_blocs.py` | déterministe, sans modèle | blocs, sections, auteur/titre |
| 3. Marqueurs lexicaux | `06_marqueurs.py` | expressions régulières | 9 registres + preuves |
| 4. Traits | `07_traits.py` | calcul déterministe | `traits.csv` (19 variables) |
| 5. Typologie | notebook | k-moyennes + ARI | clusters, validation |
| 6. Réseau des auteurs | `09_auteurs.py` | nettoyage + graphe | `auteurs.csv`, réseau |
| Validation | `08_accord.py` | α de Krippendorff | `accord_inter_codeurs.txt` |
| Consolidation | `05_tables.py` | jointures | `charts.csv`, `oeuvres.csv` |

L'ordre logique d'exécution de la phase 2 est **2a → 2c → 2b** : la géométrie (2b) consomme le `layout_type` produit par le classement visuel (2c) pour choisir son régime de reconstruction (§ 3.6). La numérotation des fichiers reflète l'ordre historique d'écriture, non l'ordre d'appel — précision consignée dans la documentation du dépôt (`CLAUDE.md`) pour éviter toute méprise.

Une règle directrice, dégagée par l'expérience et non posée a priori, a guidé la répartition des tâches : *ne jamais demander à un modèle ce qu'un calcul déterministe peut établir, ni à un modèle de vision ce qui relève du texte*. Chaque violation de cette règle, testée, a échoué de façon mesurable ; les sections suivantes en rendent compte.

### 3.4 Phase 2a — Extraction du texte par OCR

**Pourquoi.** Une image est, pour un ordinateur, une grille de pixels : aucune des analyses ultérieures (comptage, comparaison, réseau) n'est possible sans convertir le texte des charts en caractères assortis de leurs coordonnées. L'OCR est donc la première conversion, celle dont tout dépend, et la plus coûteuse en temps.

**Le problème du texte minuscule.** Appliqué à l'image entière, un OCR perd le petit texte des grands charts : réduit à la résolution qu'un moteur ingère, un titre de vignette de 20 px devient illisible. Nous découpons donc chaque image en **bandes horizontales** lues à pleine résolution, puis fusionnons les résultats en écartant les doublons de recouvrement (même texte à quelques pixels près). L'apport de ce découpage est net et mesuré : sur un chart de référence en grille (« /lit/'s Top 100 Books »), l'OCR plein format ne relevait que **2 titres sur 9** contrôlés, contre **9 sur 9** après découpage en bandes.

**Deux moteurs.** Le moteur par défaut est celui du système d'exploitation — le framework Vision d'Apple (Apple, 2024) —, accéléré matériellement et immédiatement disponible. Un moteur libre, Surya (Paruchuri, 2025, version 0.16.7), est intégré comme **contrôle** : il reproduit les mêmes extractions sur nos vérités terrain — 14 sections sur 14 et 185 œuvres sur une carte de philosophie, 9 titres sur 9 et 8 auteurs sur 8 sur la grille « Top 100 » — mais à un coût temporel environ **75 fois supérieur** (de l'ordre de 5 minutes par chart contre quelques secondes). Le contrôle importe : il atteste que les résultats ne dépendent pas d'un composant propriétaire, et permet de rejouer l'étape sur un système non-Apple. Le champ « moteur » inscrit dans chaque JSON de sortie assure la traçabilité d'un corpus qui mélangerait les deux.

**Volumétrie et temps.** Avec Vision, les 264 images sont traitées en **10,9 minutes** (moyenne 2,5 s par chart, maximum 15,5 s sur le chart le plus dense), sans erreur. Le temps suit le nombre de lignes de texte, non la taille de l'image : un chart de 37 lignes est lu en 0,4 s, quelle que soit sa résolution. L'extraction produit **34 581 segments d'œuvres** (lignes de texte non vides), chacun accompagné de sa boîte englobante et d'un score de confiance. Le balisage de mise en forme éventuellement restitué par le moteur (gras, italique) est conservé dans un champ séparé, un champ normalisé servant aux appariements ultérieurs. Les coordonnées sont ramenées au repère de l'image d'origine, condition d'un croisement correct avec la géométrie.

### 3.5 Phase 2c — Classement visuel par modèle vision-langage

**Pourquoi.** Une seule question, après l'OCR, relève encore de la vision et non du texte : la *forme* d'ensemble du chart (grille, organigramme, tier list, carte…) et la présence de liens dessinés. Nous la confions à un modèle vision-langage (VLM).

**Implémentation.** Le modèle est Qwen2.5-VL 3B (Bai et al., 2025), servi localement par Ollama (Ollama, 2025). Le prompt (`prompts/vlm.txt`) lui interdit explicitement de lire ou de transcrire le texte — assuré par ailleurs par l'OCR — et le restreint à la forme et aux flèches ; la sortie est contrainte en JSON, à température nulle. L'image est réduite à 500 px de côté avant envoi : à cette taille la forme d'ensemble reste parfaitement lisible alors que le texte ne l'est plus, ce qui divise par sept le temps d'inférence sans changer la réponse de forme.

**Un échec mesuré, et son enseignement.** L'histoire de cette étape est instructive. Une première version demandait au VLM d'extraire *aussi* les titres et la structure. Le résultat était inexploitable : sur « /lit/'s Top 100 Books », le modèle rendait **5 livres au lieu de 100**, avec des rangs faux et des flèches imaginaires sur une grille qui n'en comporte aucune ; l'inférence prenait **onze minutes par image** en saturation mémoire. Réduit à la seule question de forme, le même modèle répond juste (« carte, avec liens » sur la carte de philosophie) et vite. Mais même sur cette tâche restreinte, la classification multi-classes de la mise en page s'est révélée non fiable à la mesure (§ 3.10) : α de Krippendorff = 0,078. Seule la variable binaire « présence de flèches » atteint une fiabilité exploitable (α = 0,842) et est conservée. Le contraste — un petit modèle local traite correctement une question perceptive binaire et échoue sur une catégorisation abstraite à sept modalités — est en lui-même un résultat, discuté en § 5.3. Le classement visuel n'a été calculé que sur les 36 charts nécessaires à cette mesure d'accord ; sur le reste du corpus, la géométrie choisit son régime par une heuristique de secours (§ 3.6).

### 3.6 Phase 2b — Reconstruction géométrique de la structure

**Pourquoi sans modèle.** « Quelles lignes appartiennent au même bloc, et quel intitulé les gouverne » est une question de géométrie : les coordonnées produites par l'OCR contiennent déjà la réponse. Confiée à un VLM local, la même tâche demandait onze minutes par image et confondait les intitulés de sections avec les livres. Traitée géométriquement, elle prend moins d'une seconde par chart, ne peut rien halluciner, et donne exactement le même résultat à chaque exécution — condition de reproductibilité que l'étude s'impose.

**Algorithme.** Les lignes sont regroupées de haut en bas par accrétion : deux lignes appartiennent au même bloc si leurs plages horizontales se **chevauchent** réellement et si leur écart vertical n'excède pas un seuil. Le chevauchement strict est essentiel — sur une grille, les titres d'une même rangée partagent la hauteur, et un simple critère de proximité fusionnerait des colonnes voisines. Les seuils sont exprimés en **multiples de la hauteur de ligne médiane** du chart considéré, ce qui les rend robustes à l'hétérogénéité des formats sans réglage manuel : le facteur vertical retenu est de 1,2 hauteur de ligne (calibré de sorte qu'au-delà de ~2 des sections superposées fusionnent, et qu'en deçà les listes se fragmentent). L'intitulé d'un bloc est identifié par ordre de fiabilité décroissante : d'abord le gras repéré par l'OCR ; à défaut, l'absence de deux-points sur une ligne isolée alors que le corps du bloc en est truffé (les œuvres s'écrivant « Auteur : Titre », les intitulés jamais) ; en dernier ressort, une hauteur de police nettement supérieure.

**Deux régimes.** Le corpus mêle deux organisations que la même procédure ne peut traiter : les charts « en texte » (listes, sections) et les charts « à couvertures » (grilles régulières de vignettes). Le régime est choisi d'après le `layout_type` fourni par la phase 2c quand il est disponible. Distinguer une grille d'une carte est en effet une question visuelle, et la géométrie s'y est montrée impuissante : nous avons successivement testé la régularité des écarts de colonnes, la dispersion des abscisses et la couverture verticale — toutes mesurées, toutes ambiguës (une carte dont les grappes s'alignent présente la même signature qu'une grille). En l'absence de classement visuel, une **heuristique géométrique de secours** tranche : une grille se signale par des bandes horizontales de population régulière et des colonnes équidistantes (coefficient de variation des écarts inférieur à 0,20, mesuré à 0,10 sur la grille « Top 100 » contre 0,31 sur la carte de philosophie). Sur les tier lists à couvertures, un détecteur d'intitulés isolés récupère les paliers nommés (« God-Tier », « Entry-level Tier »), qui portent l'essentiel de la gamification et priment sur l'exactitude de la liste d'œuvres — de toute façon non récupérable là où les livres ne figurent que par leur couverture.

**Sortie.** Chaque chart est décrit par ses blocs, chaque bloc par son intitulé (le *tier*) et ses nœuds au format `{titre, auteur, tier}`. Sur la carte de philosophie de référence, la procédure retrouve les 14 grappes et leurs 185 œuvres ; sur la grille « Top 100 », elle apparie exactement 100 nœuds (« Infinite Jest / Wallace », « The Brothers Karamazov / Dostoevsky »…). Les productions sont consolidées avec l'inventaire du wiki en deux tables (`05_tables.py`) : `charts.csv` (une ligne par chart) et `oeuvres.csv` (une ligne par couple chart-œuvre, format long supportant aussi bien le comptage que la projection en graphe).

### 3.7 Phase 3 — Relevé lexical des marqueurs de gamification

**Pourquoi lexical et déterministe.** La nature du dispositif — ce qui fait qu'un chart *fonctionne* comme un jeu — se lit d'abord dans les mots. Un chart qui écrit « God-Tier », « start with the Greeks » ou « do not skip » se déclare comme prescriptif, indépendamment de sa mise en page, et y compris lorsque ses œuvres ne sont pas extractibles (charts à couvertures muettes). Nous relevons donc, dans le texte intégral de chaque chart, neuf registres par expressions régulières : progression, injonction, point d'entrée, prérequis, difficulté graduée, optionnel, récompense, paliers nommés, hiérarchie de valeur.

**Un instrument versionné et vérifiable.** Le lexique est un fichier autonome (`prompts/marqueurs.json`), modifiable et discutable indépendamment du code : c'est l'instrument de mesure de l'étude, il doit pouvoir être amendé et rejoué. Chaque registre y est défini par un ensemble de motifs, insensibles à la casse. Surtout, **chaque détection conserve la ligne qui la justifie**, ce qui rend le relevé vérifiable à la main et expose ses erreurs. Cette vérification n'est pas décorative : sur un chart consacré à Dante, les 27 « injonctions » détectées se sont révélées être des **vers cités de la *Commedia*** (« Dante, do not weep yet ») et non le chart s'adressant à son lecteur — erreur identifiable précisément parce que la preuve est conservée. À l'inverse, sur un chart « Greek 3 », les détections sont du pur matériau : « Start with the Greeks », « Then all of Plato in order of writing », « start with Herodotus, then Thucydides ».

**Une voie alternative écartée.** Un codage des mécaniques par LLM de texte local (Llama 3.1 8B, Grattafiori et al., 2024, servi par Ollama) a été implémenté (`04_codage.py`) : une fois l'OCR et la géométrie passés, le chart est devenu du texte structuré, et le coder relève de la lecture, non de la vision — un modèle de texte 8B y raisonne mieux qu'un modèle de vision 3B, et bien plus vite (45 s contre 11 min sur la carte de philosophie). Ce module reste dans le dépôt comme extension possible, mais il n'a pas été retenu pour les résultats de cet article : le relevé lexical déterministe lui a été préféré parce qu'il est reproductible au caractère près, vérifiable ligne à ligne, et sans dépendance à la variabilité d'un modèle génératif. Le confronter au relevé lexical constituerait un contrôle utile, laissé à un travail ultérieur.

### 3.8 Phases 4 et 5 — Traits mesurables et typologie émergente

**De la structure aux variables.** Faire émerger une typologie suppose de décrire chaque chart par des variables comparables. `07_traits.py` calcule, pour les 264 charts, **19 variables** entièrement issues des sorties précédentes (`traits.csv`) : dix variables de forme dérivées de l'OCR — proportions de l'image, densité de texte, couverture verticale, part de bandes horizontales peuplées, régularité des colonnes, dispersion des hauteurs de ligne (indice d'une hiérarchie typographique), longueur moyenne et part de lignes courtes, confiance médiane de l'OCR — et les neuf registres lexicaux. Le choix de *traits* plutôt que d'un *label* de forme est délibéré : demander à un modèle « quel type de chart est-ce ? » impose une taxonomie décidée a priori (celle qui, du reste, s'est révélée non fiable en § 3.10), alors que la phase de typologie doit faire l'inverse — dégager les regroupements empiriquement. Deux colonnes de contrôle (la forme codée, la catégorie du wiki) figurent dans la table mais **n'entrent jamais** dans le calcul des groupes.

**Classification.** Les variables de comptage (nombre de lignes, registres lexicaux) sont passées au logarithme pour amortir leur forte asymétrie, puis l'ensemble est standardisé. Une classification par k-moyennes (MacQueen, 1967 ; implémentation scikit-learn, Pedregosa et al., 2011, `n_init = 10`, graine fixée) est appliquée. Le nombre de groupes est choisi au **critère de silhouette** (Rousseeuw, 1987) : le tableau 2 montre un optimum net à *k* = 2 (silhouette 0,309, contre 0,12 environ pour tout *k* ≥ 3).

**Tableau 2.** Score de silhouette selon le nombre de groupes

| *k* | 2 | 3 | 4 | 5 | 6 |
|---|---:|---:|---:|---:|---:|
| Silhouette | **0,309** | 0,122 | 0,119 | 0,129 | 0,118 |

**Validation externe.** La partition obtenue est confrontée, par l'indice de Rand ajusté (ARI ; Hubert & Arabie, 1985), à trois classements indépendants : la forme codée des charts, les catégories thématiques du wiki, et la typologie théorique en trois types (approchée depuis les formes : guides initiatiques ≈ organigrammes et tier lists, canons ≈ grilles et listes, cartographies ≈ cartes et collages). Un ARI proche de 0 signifie que la partition ne recoupe pas le classement comparé ; proche de 1, qu'elle le redécouvre. C'est le test central de la phase : la typologie par les *mécaniques* est-elle réductible à la forme visuelle ou au sujet ?

### 3.9 Phase 6 — Réseau des auteurs

**Extraction et bruit.** Les mentions d'auteur proviennent du motif « Auteur : Titre » appliqué au texte OCR : 8 470 mentions, soit 24,5 % des 34 581 segments — les charts figurant les livres par leur seule couverture ne livrent aucun nom, ce qui borne le réseau à ce qui est *textuellement* énoncé. Ce motif produit deux sortes de bruit, l'un et l'autre fatals à une analyse de réseau. Les **faux auteurs**, d'abord : lorsqu'un chart écrit « History: A Very Short Introduction » ou « ECONOMICS: readings », la règle fabrique un nœud inexistant, et comme ces mots reviennent dans des charts très divers, ils apparaissent faussement comme les auteurs les plus transversaux du corpus. Les **formes éclatées**, ensuite : « Kafka », « Franz Kafka » et « KAFKA » désignent une personne mais comptent pour trois nœuds, divisant mécaniquement leur centralité.

**Nettoyage et normalisation** (`09_auteurs.py`). Le filtre des faux auteurs combine plusieurs critères, dont le plus discriminant s'est révélé être la **présence d'un mot grammatical anglais** dans la chaîne : un fragment de titre en contient presque toujours un (« Way of », « in the »), un nom de personne jamais. Les particules nobiliaires (« de », « van »…) sont préservées lorsqu'elles sont enchâssées, pour ne pas casser « Simone de Beauvoir ». Les variantes sont ensuite rapprochées par **patronyme** (dernier mot, sans accents ni casse) et par **similarité de chaînes** pour les coquilles d'OCR (« Dostoyevsky » → « Dostoevsky », « Mellville » → « Melville », « Fizgerald » → « Fitzgerald »), un garde-fou empêchant la fusion des paires singulier/pluriel (« William » ≠ « Williams »). Un lexique d'exclusions versionné (`prompts/auteurs_exclusions.txt`) recueille les faux auteurs résiduels repérés à l'œil. Le résultat : **5 518 mentions** pour **3 006 auteurs distincts**, chaque forme écartée et chaque fusion étant consignées dans un rapport inspectable (`results/auteurs_rapport.txt`).

**Graphe.** Deux auteurs sont liés s'ils figurent sur un même chart. Le graphe de cooccurrence est construit avec NetworkX (Hagberg et al., 2008) sur le **noyau** des auteurs présents dans au moins cinq charts, seuil qui écarte la traîne des mentions uniques (§ 4.5) pour concentrer l'analyse sur le canon effectivement partagé.

### 3.10 Fiabilité, validation et transparence

**Provenance du codage des formes.** Le codage de la forme des 264 charts (§ 3.8, colonne de contrôle de la typologie) n'a été réalisé ni par un humain ni par le pipeline local : il a été produit par un modèle vision-langage distant (Claude Opus 4.8, Anthropic), qui a examiné chaque image sur planches contact, avec vérifications ponctuelles en pleine résolution, selon une taxonomie construite inductivement en sept modalités (grille simple, grille à sections nommées, organigramme, tier list, liste de texte, collage, carte). Deux modalités — la grille à sections, la distinction tier list / grille à sections selon que l'intitulé exprime un rang ou un thème — ont dû être ajoutées en cours de codage, la taxonomie initiale ne rendant pas compte du corpus. Ce codage a le statut d'une **validation externe** : il sert à juger les partitions émergentes, au même titre que les catégories du wiki, et reste extérieur au pipeline local reproductible. Sa provenance est déclarée en tête du fichier de données lui-même (`data/interim/codage_manuel_formes.csv`). L'idéal méthodologique — un recodage d'échantillon par l'auteur permettant de rapporter un accord humain-machine — est une extension prévue.

**Mesure d'accord et rejet.** Une classification des formes par le VLM local (§ 3.5) a été testée puis rejetée sur mesure d'accord inter-codeurs (`08_accord.py`). Sur les 36 charts classés par les deux annotateurs, l'α de Krippendorff (Krippendorff, 2018 ; sur le choix de cet indice plutôt que le kappa de Cohen, voir Artstein & Poesio, 2008) s'établit à **0,078** pour le type de mise en page. L'alpha rapporte le désaccord observé au désaccord attendu si les étiquettes étaient distribuées au hasard selon les fréquences de chaque codeur ; il vaut 1 pour l'accord parfait, 0 pour un accord équivalent au hasard, et devient négatif en deçà. Krippendorff recommande α ≥ 0,800 pour conclure, 0,667 pour des conclusions provisoires. La valeur de 0,078 est donc sous tout seuil d'exploitabilité, à peine au-dessus d'un annotateur constant qui répondrait la même modalité pour chaque image (accord brut de 33 % sans regarder les images ; le modèle local atteint 39 %). Le contraste est diagnostique : le modèle répond « grille à sections » 27 fois sur 36, ne discriminant presque pas. Interrogé sur la seule présence de flèches, il atteint α = **0,842**, au-dessus du seuil de fiabilité : cette unique variable binaire est conservée, les autres écartées de toute analyse. La démonstration — un petit modèle local traite une question perceptive binaire mais échoue sur une catégorisation abstraite — vaut mieux qu'une variable non examinée.

**Transparence.** L'usage de modèles de langage dans la construction du pipeline et l'assistance à la rédaction est déclaré en fin d'article (« Déclaration de transparence »). Aucune revue ni SocArXiv ne l'exige au dépôt, mais la déclaration figure et documente précisément qui a fait quoi.

## 4. Résultats

### 4.1 Les charts sont d'abord des catalogues

Le tableau 3 et la figure 1 donnent la distribution des formes sur les 264 charts.

**Tableau 3.** Formes des charts (codage sur image, n = 264)

| Forme | n | % |
|---|---:|---:|
| Grille simple | 110 | 41,7 |
| Grille à sections nommées | 76 | 28,8 |
| Organigramme | 29 | 11,0 |
| Tier list | 24 | 9,1 |
| Liste de texte | 11 | 4,2 |
| Collage | 11 | 4,2 |
| Carte | 3 | 1,1 |

Les formes-catalogues — grilles avec ou sans sections, collages — représentent **74,6 %** du corpus ; les formes structurellement prescriptives (organigrammes et tier lists) en représentent **20,1 %**, et 12,9 % des charts seulement comportent des flèches dessinées. Contre l'imaginaire du « start with the Greeks », la forme dominante du chart n'est pas le parcours balisé mais le classement.

### 4.2 Une gamification discursive avant d'être vidéoludique

Aucun des neuf registres lexicaux n'est majoritaire (tableau 4, figure 2). Les plus répandus sont discursifs : un quart des charts prescrit un ordre de lecture (26,1 %) ou s'adresse au lecteur à l'impératif (23,9 %). Les registres qui miment le plus explicitement le jeu vidéo — paliers nommés (« Tier », « Level ») : 3,8 % ; hiérarchie de valeur (« God-Tier », « patrician », « pleb ») : 1,9 % — sont rares.

**Tableau 4.** Taux de présence des marqueurs lexicaux de gamification (n = 264)

| Registre | Charts | % |
|---|---:|---:|
| Progression (ordre prescrit) | 69 | 26,1 |
| Injonction (adresse impérative) | 63 | 23,9 |
| Point d'entrée | 44 | 16,7 |
| Prérequis | 36 | 13,6 |
| Difficulté graduée | 32 | 12,1 |
| Optionnel / bonus | 17 | 6,4 |
| Récompense promise | 16 | 6,1 |
| Paliers nommés | 10 | 3,8 |
| Hiérarchie de valeur | 5 | 1,9 |

La gamification des charts de /lit/ est donc d'abord une affaire de langage prescriptif, non de décorum vidéoludique — nuance importante par rapport à la lecture initiale, qui accordait aux signes visuels du jeu (niveaux, badges, achievements) une place que la mesure ne leur retrouve pas à l'échelle du corpus.

### 4.3 Le travail prescriptif est distribué entre forme et langage

Le croisement des formes et des registres (figure 3) constitue le résultat central. Le tableau 5 en donne les valeurs saillantes. Les organigrammes prescrivent doublement : 66 % désignent un point d'entrée, 62 % emploient l'impératif. Les tier lists commandent peu (12 % d'injonctions) mais gradent : elles concentrent l'essentiel des paliers nommés (25 %) et de la hiérarchie de valeur (12 %). Surtout, les **listes de texte** — la forme visuellement la plus pauvre — compensent entièrement par le langage : 73 % d'injonctions et le score lexical moyen le plus élevé du corpus (9,0 marqueurs par chart, contre 0,9 pour les grilles simples, dont la médiane est nulle).

**Tableau 5.** Part des charts portant chaque registre, par forme (extraits, %)

| Forme (n) | Progression | Injonction | Point d'entrée | Paliers nommés |
|---|---:|---:|---:|---:|
| Grille simple (110) | 24 | 17 | 3 | 2 |
| Grille à sections (76) | 32 | 18 | 12 | 3 |
| Organigramme (29) | 31 | 62 | 66 | 0 |
| Tier list (24) | 17 | 12 | 38 | 25 |
| Liste de texte (11) | 55 | 73 | 27 | 0 |

La gamification n'apparaît donc pas comme une propriété du chart mais comme une **fonction distribuée** entre l'agencement visuel et l'énonciation : chaque forme choisit son canal, et les deux se compensent. Un chart peut être une grille parfaitement muette ou un texte survolté d'impératifs ; le dispositif prescriptif est le même, porté par des moyens différents. Ce résultat prolonge directement l'intuition de McLuhan (1964) mobilisée dans le travail initial, en la précisant : le médium est bien le message, mais le « médium » du chart est double — mise en page *et* registre de parole. Il éclaire aussi une observation qualitative du travail initial, selon laquelle certains charts « minimalistes » proposent un corpus sans thématique : la mesure montre que ces charts muets ne sont pas des exceptions mais la norme statistique, et que la prescription, lorsqu'elle a lieu, migre vers le texte.

### 4.4 Deux familles émergentes, pas trois

La classification non supervisée (§ 3.8) retient deux groupes : **222 charts** que l'on peut décrire comme des *catalogues muets* et **42** comme des *guides bavards et prescriptifs* (figure 4). La partition ne recoupe ni le codage des formes (ARI = 0,09), ni les catégories thématiques du wiki (ARI = 0,02), ni la typologie théorique en trois types (ARI = 0,12). Elle isole donc une dimension propre — le **régime d'énonciation** — irréductible à l'apparence comme au sujet. Autrement dit, la variable qui structure le mieux le corpus n'est pas ce dont un chart parle (le thème), ni sa silhouette (la forme visuelle), mais l'intensité avec laquelle il s'adresse à son lecteur.

Confrontés aux trois structures de cadrage du travail initial, ces résultats sont contrastés. Les *canons culturels* sortent renforcés : décrits comme « une grande partie de l'échantillon », ils sont 74,6 % du corpus. Les *guides initiatiques* existent bien (53 charts, si l'on additionne organigrammes et tier lists) et structurent le second groupe émergent. Mais les *cartographies ludiques* — frappantes à l'unité, et réelles : le corpus compte des arbres de décision explicites tels que « What China Miéville book should I read? » ou « Which Quran should I get? » — ne forment pas une famille statistique séparable : 14 charts au plus en relèvent (cartes et collages), et aucune partition ne les distingue. La distinction qui survit à la mesure est binaire : **guider ou cataloguer**.

### 4.5 Le canon comme bloc solidaire

Sur les 3 006 auteurs distincts identifiés, **77,7 %** (2 337) n'apparaissent que sur un seul chart : la reconnaissance est une pointe très fine sur une traîne immense, et seuls 124 auteurs atteignent le seuil de cinq charts. Le noyau ainsi défini présente une **densité de cooccurrence de 56,5 %** (figure 5) : plus d'une paire possible sur deux cooccurre effectivement. Les paires les plus fréquentes — Dostoïevski–Joyce (13 charts communs), Joyce–Kafka, Joyce–Nabokov, Kafka–Nabokov, Mann–Nabokov (12 chacune) — dessinent un canon moderniste qui voyage en bloc : citer l'un revient presque mécaniquement à citer les autres.

Le palmarès de présence est cohérent avec l'image que /lit/ donne de lui-même : Kafka et McCarthy (18 charts chacun), Dostoïevski et Platon (17), Herbert, Hesse, Nietzsche, Orwell et Shakespeare (16) — difficulté moderniste, pessimisme russe, un philosophe antique, et un unique auteur de genre (Frank Herbert) toléré. Un plafond mérite attention : **aucun auteur n'atteint 7 % du corpus**. La reconnaissance est concentrée dans un cercle très étroit, mais aucun nom n'y est obligatoire — un consensus sans dogme.

Pour la thèse de l'étude, ce résultat déplace l'accent : le chart ne recommande pas des livres, il **reconduit une liste solidaire**. C'est précisément le fonctionnement d'un dispositif de conformité : l'appartenance ne s'y prouve pas par l'adhésion à un texte-clé mais par la maîtrise d'un répertoire.

### 4.6 La recirculation passe par les listes

Faute de données de diffusion (§ 3.1), la recirculation ne peut être approchée que par le contenu. Le recouvrement des ensembles d'auteurs entre charts (indice de Jaccard) fait apparaître, outre deux doublons stricts (le même fichier rangé deux fois par le wiki, identité de contenu confirmée par empreinte), une famille dominante : les palmarès annuels « Top 100 » (2014-2022), dont chaque édition partage jusqu'à 59 % de ses auteurs avec les autres. La communauté ne reposte pas des images : elle réédite des **listes** — le chart change d'habillage, le canon reste. Cette mesure est un plancher, non un classement exhaustif : les charts à couvertures muettes en sont structurellement absents.

## 5. Discussion

### 5.1 La conformité précède l'initiation

Le travail initial concluait que la diffusion de radicalités tient « moins à un militantisme avéré qu'à une économie des symboles et de la provocation, valorisant l'appartenance subculturelle ». La mesure confirme cette économie des symboles mais en précise le mécanisme, et le déplace. Le dispositif dominant n'est pas le parcours initiatique — minoritaire dans les formes (20,1 %) comme dans les mots (26,1 % de progression) — mais le **catalogue** : la juxtaposition d'un répertoire fermé, solidaire (densité de 56,5 %) et réédité à l'identique (§ 4.6). L'initiation existe, portée par une minorité de guides intensément prescriptifs ; mais la voie principale de la diffusion est la reconduction d'une liste dont la maîtrise vaut appartenance. En termes de cadrage (Entman, 2004), l'essentiel du travail des charts n'est pas de hiérarchiser des considérations par un chemin, mais de délimiter silencieusement ce qui existe : le cadre opère par la sélection plus que par la séquence.

Ce déplacement éclaire la fonction de contre-sphère (Fraser, 2001). Ce que /lit/ élabore et diffuse n'est pas d'abord un itinéraire de radicalisation mais un canon alternatif — un « ce qu'il faut avoir lu » qui se substitue aux instances de consécration légitimes. La radicalité y est disponible plutôt qu'imposée : elle loge dans les marges du répertoire (les corpus réactionnaires, traditionalistes ou conspirationnistes voisinent avec Kafka et Platon dans le même format, le même wiki, la même grammaire visuelle), et c'est cette banalisation formelle — plus que tout parcours balisé — qui l'« expose sans imposer ».

### 5.2 Une gamification de langage

La rareté du décorum vidéoludique (3,8 % de paliers nommés) invite à requalifier la gamification observée. Au sens strict de Deterding et al. (2011) — des éléments de *design* de jeu —, seule une minorité de charts est pleinement gamifiée. Mais si l'on suit Raessens (2014) sur la ludification comme mode d'engagement et d'expression identitaire, la mesure révèle une gamification plus diffuse et plus intéressante : elle passe par le *registre d'énonciation* (l'injonction, le point d'entrée, la promesse d'un état futur du lecteur) et se distribue entre la forme et la parole selon les moyens de chaque format. La partition émergente en deux régimes — catalogues muets, guides bavards — suggère que la frontière pertinente n'est pas entre charts « gamifiés » et « non gamifiés », mais entre deux manières d'exercer la prescription : par l'ordre du visible ou par l'adresse au lecteur.

### 5.3 Apports et leçons de méthode

Ce travail vaut aussi comme protocole. Trois leçons nous semblent généralisables au traitement computationnel de corpus visuels en SIC.

D'abord, la **complémentarité stricte des instruments**. L'OCR lit, la géométrie structure, le lexique qualifie, un VLM ne tranche que la forme d'ensemble : chaque tâche confiée à l'outil d'à côté a échoué de façon mesurable — le VLM sommé de tout extraire hallucinait 95 livres sur 100, la géométrie sommée de distinguer une grille d'une carte restait ambiguë. La règle « ne demander à un modèle que ce qu'aucun calcul ne peut établir » n'est pas une préférence esthétique : c'est ce qui, ici, sépare un résultat exploitable d'un artefact.

Ensuite, la **valeur des résultats négatifs rapportés**. Le rejet chiffré de la classification automatique des formes (α = 0,078) et la non-séparabilité du troisième type théorique (ARI = 0,12) ne sont pas des accidents à taire mais ce qui rend crédibles les résultats positifs voisins. Une littérature récente insiste sur la fragilité et l'imprévisibilité des sorties de LLM selon le *prompt* (Atreja et al., 2024) ; mesurer systématiquement l'accord, y compris quand il conduit à écarter un outil, est la seule parade honnête.

Enfin, la **frugalité**. L'ensemble du pipeline tourne sur une machine personnelle d'entrée de gamme (Apple M1, 8 Go), en des temps compatibles avec le travail d'un chercheur seul — l'OCR du corpus entier prend onze minutes, la géométrie et le relevé lexical quelques secondes, la typologie et le réseau sont instantanés. L'instrumentation computationnelle de l'analyse de contenu visuel n'exige ni infrastructure ni budget, mais une répartition rigoureuse des tâches entre calcul déterministe et modèles, et une contrainte d'exécution locale qui, loin d'être une limite, est la condition de la reproductibilité (annexe A).

## 6. Limites

Cinq limites bornent la portée des résultats. **(1) Couverture des auteurs** : 24,5 % des segments extraits portent un auteur identifiable ; les charts figurant les livres par leur seule couverture sont sous-représentés dans le réseau, qui décrit le canon *textuellement* énoncé. **(2) Provenance du codage des formes** : réalisé par un modèle vision-langage distant, il a valeur de validation externe déclarée, non de vérité terrain humaine ; un recodage d'échantillon par l'auteur reste à conduire pour rapporter un accord humain-machine. **(3) Absence de données de circulation** : le corpus provient du wiki, la recirculation n'est approchée que par le contenu, et le corpus lui-même reflète la curation du wiki plutôt que l'ensemble des charts ayant circulé. **(4) Dépendance au volume de texte** : les scores lexicaux croissent mécaniquement avec la quantité de texte d'un chart ; les comparaisons inter-formes portent sur des taux de présence, mais toute exploitation fine des intensités exigerait une normalisation. **(5) Taxonomie et effectifs faibles** : les catégories « carte » (3) et « collage » (11) sont trop peu peuplées pour un traitement statistique séparé, et la taxonomie des formes a dû être révisée en cours de codage, ce qui signale son caractère inductif et perfectible.

À quoi s'ajoute une limite d'interprétation, la plus importante : la mesure porte sur les **dispositifs, non sur leur réception**. Rien ici ne documente ce que les lecteurs de /lit/ *font* des charts — l'enquête de réception reste entière.

## 7. Conclusion

Repartant d'une analyse qualitative qui voyait dans les charts de /lit/ des dispositifs gamifiés de diffusion de radicalités littéraires, cette étude a soumis ses catégories à la mesure du corpus entier, au moyen d'un pipeline computationnel local, frugal et reproductible. Le verdict est nuancé et, croyons-nous, plus intéressant que la confirmation : les charts classent bien plus qu'ils ne guident ; leur gamification est discursive avant d'être vidéoludique et se distribue entre la forme et la parole ; deux de leurs trois types théoriques survivent à la mesure, le troisième non ; et le canon qu'ils mettent en circulation fonctionne comme un bloc solidaire sans nom obligatoire. La radicalité s'y diffuse moins par l'initiation balisée que par la reconduction d'une liste — la conformité précède l'initiation.

À ce résultat de fond s'ajoute une contribution de méthode : la démonstration qu'un corpus visuel en SIC peut être traité de bout en bout, honnêtement et de façon reproductible, sur une machine ordinaire, à condition de répartir strictement les tâches entre calcul déterministe et modèles, et de mesurer — puis de publier — jusqu'aux échecs.

Deux prolongements s'imposent. Le premier est temporel : la série des palmarès annuels (2014-2022) présente dans le corpus permettrait de suivre le déplacement du canon dans le temps, et l'intensification éventuelle de la gamification. Le second rejoint l'ouverture du travail initial : analyser la structure propre de 4chan — code, interface, affordances — pour comprendre comment la plateforme conditionne les objets qui y naissent. L'étude de la réception des charts, enfin, reste le chaînon manquant entre dispositifs mesurés et effets supposés.

## Déclaration de transparence

Le pipeline d'analyse, le codage des formes et l'assistance à la rédaction du présent article ont mobilisé des modèles de langage. Claude Opus 4.8 (Anthropic) a servi à construire le pipeline, à coder visuellement les 264 formes (validation externe déclarée en § 3.10) et à assister la rédaction, sous la direction et la validation de l'auteur, qui assume l'intégralité des choix théoriques, méthodologiques et interprétatifs. Qwen2.5-VL 3B et Llama 3.1 8B, exécutés localement, sont des composants testés du pipeline : le premier n'a été conservé que pour la détection binaire de liens graphiques (α = 0,842), le second implémenté mais non retenu pour les résultats. L'intégralité du code, des lexiques, des rapports de fiabilité et du carnet d'analyse est disponible : <https://github.com/marcgarnier/lit-charts>. Les images du corpus, artefacts d'usagers anonymes collectés à des fins d'analyse académique, ne sont pas redistribuées.

## Références

Alizadeh, M., Kubli, M., Samei, Z., Dehghani, S., Zahedivafa, M., Bermeo, J. D., Korobeynikova, M., & Gilardi, F. (2024). Open-source LLMs for text annotation: A practical guide for model setting and fine-tuning. *Journal of Computational Social Science, 8*(1), Article 17. https://doi.org/10.1007/s42001-024-00345-9

Apple. (2024). *Vision framework* [Logiciel]. Apple Inc. https://developer.apple.com/documentation/vision

Artstein, R., & Poesio, M. (2008). Inter-coder agreement for computational linguistics. *Computational Linguistics, 34*(4), 555–596. https://doi.org/10.1162/coli.07-034-R2

Atreja, S., Ashkinaze, J., Li, L., Mendelsohn, J., & Hemphill, L. (2024). *Prompt design matters for computational social science tasks but in unpredictable ways*. arXiv. https://doi.org/10.48550/arXiv.2406.11980

Baden, C., Pipal, C., Schoonvelde, M., & van der Velden, M. A. C. G. (2022). Three gaps in computational text analysis methods for social sciences: A research agenda. *Communication Methods and Measures, 16*(1), 1–18. https://doi.org/10.1080/19312458.2021.2015574

Bai, S., Chen, K., Liu, X., Wang, J., Ge, W., Song, S., Dang, K., Wang, P., Wang, S., Tang, J., Zhong, H., Zhu, Y., Yang, M., Li, Z., Wan, J., Wang, P., Ding, W., Fu, Z., Xu, Y., … Lin, J. (2025). *Qwen2.5-VL technical report*. arXiv. https://doi.org/10.48550/arXiv.2502.13923

Bennett, W. L., & Pfetsch, B. (2018). Rethinking political communication in a time of disrupted public spheres. *Journal of Communication, 68*(2), 243–253. https://doi.org/10.1093/joc/jqx017

Dahlgren, P. (2000). L'espace public et l'internet : structure, espace et communication. *Réseaux, 18*(100), 157–186.

Dahlgren, P. (2005). The Internet, public spheres, and political communication: Dispersion and deliberation. *Political Communication, 22*(2), 147–162. https://doi.org/10.1080/10584600590933160

De Zeeuw, D. (2024). Post-truth conspiracism and the pseudo-public sphere. *Frontiers in Communication, 9*, Article 1384363. https://doi.org/10.3389/fcomm.2024.1384363

Deterding, S., Dixon, D., Khaled, R., & Nacke, L. E. (2011). From game design elements to gamefulness: Defining "gamification". Dans *Proceedings of the 15th International Academic MindTrek Conference: Envisioning Future Media Environments* (p. 9–15). ACM. https://doi.org/10.1145/2181037.2181040

Entman, R. M. (2004). *Projections of power: Framing news, public opinion, and U.S. foreign policy*. University of Chicago Press.

Fraser, N. (2001). Repenser la sphère publique : une contribution à la critique de la démocratie telle qu'elle existe réellement. *Hermès, 31*, 125–156.

Garnier, M. (2026). *« That's kino anon » : les charts de /lit/ comme dispositifs gamifiés de diffusion de radicalités littéraires* [Travail de séminaire, COM 885]. Université de Sherbrooke.

Garnier, M. (2026b). *lit-charts : pipeline computationnel pour l'analyse des charts de lecture de /lit/* [Code source]. GitHub. https://github.com/marcgarnier/lit-charts

Gerstlé, J., & Piar, C. (2020). Les effets persuasifs de la communication et de l'information. Dans J. Gerstlé & C. Piar, *La communication politique* (4e éd., p. 69–103). Armand Colin.

Grattafiori, A., Dubey, A., Jauhri, A., Pandey, A., Kadian, A., Al-Dahle, A., Letman, A., Mathur, A., Schelten, A., Vaughan, A., … Ma, Z. (2024). *The Llama 3 herd of models*. arXiv. https://doi.org/10.48550/arXiv.2407.21783

Habermas, J. (1978). *L'espace public : archéologie de la publicité comme dimension constitutive de la société bourgeoise*. Payot.

Hagberg, A. A., Schult, D. A., & Swart, P. J. (2008). Exploring network structure, dynamics, and function using NetworkX. Dans G. Varoquaux, T. Vaught, & J. Millman (Éds.), *Proceedings of the 7th Python in Science Conference (SciPy 2008)* (p. 11–15).

Hameleers, M., Powell, T. E., Van Der Meer, T. G. L. A., & Bos, L. (2020). A picture paints a thousand lies? The effects and mechanisms of multimodal disinformation and rebuttals disseminated via social media. *Political Communication, 37*(2), 281–301. https://doi.org/10.1080/10584609.2019.1674979

Harris, C. R., Millman, K. J., van der Walt, S. J., Gommers, R., Virtanen, P., Cournapeau, D., Wieser, E., Taylor, J., Berg, S., Smith, N. J., Kern, R., Picus, M., Hoyer, S., van Kerkwijk, M. H., Brett, M., Haldane, A., del Río, J. F., Wiebe, M., Peterson, P., … Oliphant, T. E. (2020). Array programming with NumPy. *Nature, 585*(7825), 357–362. https://doi.org/10.1038/s41586-020-2649-2

Hubert, L., & Arabie, P. (1985). Comparing partitions. *Journal of Classification, 2*(1), 193–218. https://doi.org/10.1007/BF01908075

Hunter, J. D. (2007). Matplotlib: A 2D graphics environment. *Computing in Science & Engineering, 9*(3), 90–95. https://doi.org/10.1109/MCSE.2007.55

Krippendorff, K. (2018). *Content analysis: An introduction to its methodology* (4e éd.). Sage.

MacQueen, J. (1967). Some methods for classification and analysis of multivariate observations. Dans L. M. Le Cam & J. Neyman (Éds.), *Proceedings of the Fifth Berkeley Symposium on Mathematical Statistics and Probability* (vol. 1, p. 281–297). University of California Press.

McKinney, W. (2010). Data structures for statistical computing in Python. Dans S. van der Walt & J. Millman (Éds.), *Proceedings of the 9th Python in Science Conference (SciPy 2010)* (p. 56–61). https://doi.org/10.25080/Majora-92bf1922-00a

McLuhan, M. (1964). *Understanding media: The extensions of man*. McGraw-Hill.

Nagle, A. (2017). *Kill all normies: Online culture wars from 4chan and Tumblr to Trump and the alt-right*. Zero Books.

Nelson, T. E., Oxley, Z. M., & Clawson, R. A. (1997). Toward a psychology of framing effects. *Political Behavior, 19*(3), 221–246. https://doi.org/10.1023/A:1024834831093

Ollama. (2025). *Ollama* [Logiciel]. https://ollama.com

Paruchuri, V. (2025). *Surya* (version 0.16.7) [Logiciel]. GitHub. https://github.com/datalab-to/surya

Pedregosa, F., Varoquaux, G., Gramfort, A., Michel, V., Thirion, B., Grisel, O., Blondel, M., Prettenhofer, P., Weiss, R., Dubourg, V., Vanderplas, J., Passos, A., Cournapeau, D., Brucher, M., Perrot, M., & Duchesnay, É. (2011). Scikit-learn: Machine learning in Python. *Journal of Machine Learning Research, 12*, 2825–2830.

Phillips, W. (2015). *This is why we can't have nice things: Mapping the relationship between online trolling and mainstream culture*. MIT Press.

Raessens, J. (2014). The ludification of culture. Dans M. Fuchs, S. Fizek, P. Ruffino, & N. Schrape (Éds.), *Rethinking gamification* (p. 91–114). meson press.

Rousseeuw, P. J. (1987). Silhouettes: A graphical aid to the interpretation and validation of cluster analysis. *Journal of Computational and Applied Mathematics, 20*, 53–65. https://doi.org/10.1016/0377-0427(87)90125-7

Waisbord, S. (2016). The elective affinity between post-truth communication and populist politics. *Communication Research and Practice, 2*(1), 1–7. https://doi.org/10.1080/22041451.2018.1428928

---

## Annexe A. Infrastructure, exécution et reproductibilité

### A.1 Environnement matériel et logiciel

Toutes les mesures ont été produites sur un **Apple M1 (puce Apple Silicon, 8 Go de mémoire unifiée)**, sous macOS. Aucun GPU dédié ni service distant n'est requis. L'environnement Python est géré par conda (Python 3.11, canal conda-forge). Les dépendances principales, avec leur rôle : Pillow (manipulation d'images) ; les liaisons PyObjC vers le framework Vision d'Apple (OCR par défaut) ; Surya 0.16.7 avec `transformers` 4.x (OCR de contrôle open source) ; Ollama servant Qwen2.5-VL 3B et Llama 3.1 8B (modèles locaux) ; NumPy (Harris et al., 2020), pandas (McKinney, 2010), scikit-learn (Pedregosa et al., 2011), NetworkX (Hagberg et al., 2008) et Matplotlib (Hunter, 2007) pour l'analyse et les figures. Les versions exactes sont figées dans `requirements.txt`.

### A.2 Ordre d'exécution

```
01_ocr.py  →  03_vlm.py (36 charts, mesure d'accord)  →  02_blocs.py
   →  06_marqueurs.py  →  05_tables.py  →  07_traits.py
   →  08_accord.py  →  09_auteurs.py  →  notebooks/resultats.ipynb
```

Chaque script est relançable sans recalcul (sorties existantes sautées, `--force` pour retraiter). Le carnet `notebooks/resultats.ipynb`, exécuté et versionné avec ses sorties, produit l'ensemble des figures et des chiffres du présent article ; `src/10_figures_site.py` en dérive les figures aux couleurs de la page de présentation du projet.

### A.3 Volumétrie et temps (récapitulatif)

**Tableau A.1.** Volumétrie et temps de calcul par étape (corpus de 264 charts)

| Étape | Sortie | Temps |
|---|---|---|
| OCR (Vision) | 34 581 segments d'œuvres | 10,9 min (2,5 s/chart) |
| OCR (Surya, contrôle) | idem, vérités terrain | ≈ 5 min/chart |
| Classement visuel (VLM) | 36 charts classés | ≈ 19 s/chart (à froid) |
| Géométrie | blocs, sections, nœuds | < 1 s/chart |
| Marqueurs lexicaux | 9 registres + preuves | quasi instantané |
| Traits | matrice 264 × 19 | quasi instantané |
| Nettoyage auteurs | 8 470 → 5 518 mentions | quasi instantané |
| Typologie, réseau | clusters, graphe | quelques secondes |

### A.4 Garanties de reproductibilité

Graines aléatoires fixées (k-moyennes `random_state = 42`, disposition du graphe `seed = 42`). Étapes déterministes (OCR, géométrie, lexique, nettoyage) invariantes d'une exécution à l'autre. Traçabilité : moteur d'OCR inscrit dans chaque sortie ; preuve conservée pour chaque détection lexicale ; provenance du codage des formes en tête du fichier de données ; rapports de nettoyage (`results/auteurs_rapport.txt`) et d'accord (`results/accord_inter_codeurs.txt`) versionnés. Le dépôt ne redistribue pas les images du corpus ni les sorties volumineuses ; il versionne le code, les lexiques (`prompts/`), le codage des formes, l'inventaire, les rapports et le carnet exécuté.

## Annexe B. Figures

Les figures sont produites par `notebooks/resultats.ipynb` ; graines fixées, exécution reproductible.

**Figure 1.** Formes des 264 charts (codage sur image).
![Figure 1](figures/fig01_formes.png)

**Figure 2.** Taux de présence de chaque marqueur lexical de gamification.
![Figure 2](figures/fig02_mecaniques.png)

**Figure 3.** Part des charts portant chaque mécanique, par forme (%).
![Figure 3](figures/fig03_forme_x_mecanique.png)

**Figure 4.** Taille et composition des deux groupes émergents.
![Figure 4](figures/fig05_clusters_composition.png)

**Figure 5.** Ossature du réseau de cooccurrence du noyau (liens ≥ 5 charts communs).
![Figure 5](figures/fig08_reseau.png)
