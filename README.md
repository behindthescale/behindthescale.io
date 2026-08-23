# behindthescale.io

Le site de Behind The Scale et ses ressources publiques.

## Ce que contient ce dépôt

| Chemin | Rôle |
|---|---|
| `public/` | **Le seul dossier publié.** Tout ce qui est en dehors n'est pas servi |
| `public/index.html` | La racine du domaine |
| `public/ressources/` | Le référentiel, généré par `build.py` |
| `public/data/perimetre.json` | Les données du périmètre, source de la génération |
| `build.py` | Le générateur. Aucune dépendance, `python3 build.py` |
| `wrangler.jsonc` | La configuration de publication. Aucun code exécuté côté serveur |

## Le principe

`public/data/` est la source, `build.py` fabrique les pages, et rien ne s'écrit à la main dans
`public/ressources/`. Un chiffre qui n'est pas dans les données ne peut pas apparaître sur une page.

## Ce que ce dépôt ne contient jamais

Aucun élément de la base de connaissances privée de Behind The Scale : ni document, ni tableau, ni
extrait, ni nom de module. Elle sert de grille de lecture, elle ne se publie pas.

Aucun nom de créateur susceptible d'être démarché.

## Licence

Le contenu et les données sont sous [CC BY 4.0](LICENSE) : réutilisables, y compris
commercialement, à condition de citer la source.
