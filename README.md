# behindthescale.io

Le site de Behind The Scale et son référentiel public, **Derrière le chiffre**.

## Ce que contient ce dépôt

| Chemin | Rôle |
|---|---|
| `index.html` | La racine du domaine |
| `reperes/` | Le référentiel, généré par `build.py` |
| `data/perimetre.json` | Les données du périmètre, source de la génération |
| `build.py` | Le générateur. Aucune dépendance, `python3 build.py` |
| `style.css` | La feuille de style commune |

## Le principe

`data/` est la source, `build.py` fabrique les pages, et rien ne s'écrit à la main dans `reperes/`.
Un chiffre qui n'est pas dans les données ne peut pas apparaître sur une page.

## Ce que ce dépôt ne contient jamais

Aucun élément de la base de connaissances privée de Behind The Scale : ni document, ni tableau, ni
extrait, ni nom de module. Elle sert de grille de lecture, elle ne se publie pas.

Aucun nom de créateur susceptible d'être démarché.

## Licence

Le contenu et les données sont sous [CC BY 4.0](LICENSE) : réutilisables, y compris
commercialement, à condition de citer la source.
