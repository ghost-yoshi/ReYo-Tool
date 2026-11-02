# ReYo

Outil qui transforme une fiche de TP en compte rendu propre et bien mis en forme.

L'IA n'est **pas** au centre du projet : elle est externe et optionnelle. L'étudiant garde la main sur le contenu, l'outil s'occupe de la structure, des captures et de la mise en page.

> Statut : MVP en cours de construction.

## Principe

ReYo ne lit pas les fiches lui-même. Il génère un **prompt**. L'utilisateur colle ce prompt et sa fiche dans l'IA de son choix, puis rapporte le **JSON** obtenu. ReYo valide ce JSON et produit le document final.

Deux JSON distincts, reconnus par leur champ `kind` :

- `structure` : l'arbre des parties, consignes et questions de la fiche.
- `reponses` : les réponses, rattachées aux nœuds par leur `id` (optionnel).

## Workflow

1. L'utilisateur demande le **prompt A** (structure).
2. Il l'envoie avec la fiche à son IA et colle le JSON `structure` dans ReYo.
3. ReYo **valide** le JSON (erreurs lisibles, prompt de réparation si besoin).
4. Les réponses viennent de l'utilisateur, ou d'un JSON `reponses` généré via le **prompt B** (optionnel).
5. Si un nœud demande une capture, l'outil le signale et l'utilisateur envoie l'image.
6. ReYo applique un **thème** et exporte le document (DOCX/PDF).

## Règles de conception

- Le cœur est une **bibliothèque pure** : les fonctions prennent des données et en renvoient, sans lire de fichier ni afficher quoi que ce soit. Seul `cli.py` touche au disque.
- Tout contenu venant d'une IA est traité comme **non fiable** : on valide, on échappe avant l'export.
- Toute réponse venant d'une IA est marquée `source: "ia"` et reste un **brouillon à relire**.
- Les identifiants de nœuds sont des **chemins** (`P4.4.3`), jamais le seul numéro affiché.
- Le JSON porte un `schema_version`.

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

Vérification : `python -c "import reyo"` ne doit afficher aucune erreur.

## Structure du dépôt

```
.
├── pyproject.toml
├── README.md
├── docs/
│   └── contracts/        un fichier par module
├── src/reyo/
│   ├── cli.py            point d'entrée (seul module qui touche au disque)
│   ├── __main__.py       python -m reyo
│   ├── schema/           modèles de données
│   ├── validation/       validation et contrôles croisés
│   ├── prompts/          génération des prompts A et B
│   ├── captures/         rattachement des images aux nœuds
│   └── render/           assemblage et export du document
└── tests/
    └── fixtures/         JSON d'exemple (fiches réelles)
```

## Modules et contrats

Chaque module reçoit des données, en renvoie d'autres, et ne connaît pas les autres. Le contrat détaillé de chacun est dans `docs/contracts/`.

| Module | Reçoit | Renvoie | Responsable |
|---|---|---|---|
| `schema` | — | modèles `Structure`, `Noeud`, `Reponse`, `Capture` | lead |
| `validation` | texte JSON | structure valide **ou** liste d'erreurs lisibles | lead |
| `prompts` | options (mode, contexte) | texte du prompt | lead |
| `captures` | image + `id` de nœud | `Capture` rattachée | à répartir |
| `render` | structure + réponses + captures + thème | document (octets) | à répartir |

Un nouveau contrat se crée à partir de `docs/contracts/captures.md`, qui sert d'exemple.

## Contribuer

1. Une issue par tâche, avec un critère de fin clair.
2. Une branche par tâche : `git switch -c feature/nom-de-la-tache`.
3. Une PR vers `main`, relue avant fusion. `main` est protégée.
4. Tout module livré s'accompagne de tests (`pytest`) qui s'appuient sur `tests/fixtures/`.

## Licence

je definirai plus tard mdrr