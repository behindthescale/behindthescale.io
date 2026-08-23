#!/usr/bin/env python3
"""Repartit les 97 questions du perimetre en neuf fichiers de chapitre.

    JOUE LE 23/08/2026, NE PAS REJOUER : il ecraserait les items rediges depuis.

Script de migration, joue une fois. Il ne fabrique aucune valeur : chaque
question garde son identifiant, son etat estime et son origine. Ce qui n'a pas
ete mesure sort en zone blanche, ce qui l'a ete attend d'etre redige a la main.
"""

import json
import pathlib
import unicodedata

RACINE = pathlib.Path(__file__).parent
PUBLIC = RACINE / "public"
DEST = PUBLIC / "data" / "chapitres"

SLUGS = {
    0: "le-seuil",
    1: "ce-que-je-vends",
    2: "savoir-avant-de-fabriquer",
    3: "le-prix",
    4: "l-annonce",
    5: "la-page-et-la-conversion",
    6: "encaisser",
    7: "le-cadre-legal-et-fiscal",
    8: "la-vente-tient-elle",
}


def sans_accent(s):
    return "".join(c for c in unicodedata.normalize("NFD", s)
                   if unicodedata.category(c) != "Mn")


def type_depuis_etat(etat):
    """Rien ne se publie tant que ce n'est pas redige, zone blanche comprise.

    Une zone blanche n'est pas un item vide : elle doit dire ce qu'il faudrait
    pour la combler et qui pourrait le mesurer. Tant que ces deux champs ne sont
    pas ecrits, elle reste a rediger comme les autres. L'etat estime est
    conserve pour ordonner le travail, il ne publie rien.
    """
    return "a_rediger"


def main():
    if any(DEST.glob("*.json")):
        raise SystemExit("migration deja jouee : les chapitres existent et portent du contenu redige")

    d = json.loads((PUBLIC / "data" / "perimetre.json").read_text(encoding="utf-8"))
    DEST.mkdir(parents=True, exist_ok=True)

    total = 0
    for e in d["etapes"]:
        n = e["n"]
        items = []
        for rep in e["reperes"]:
            t = type_depuis_etat(rep["etat"])
            item = {
                "id": rep["id"],
                "type": t,
                "titre": rep["question"],
                "etat_estime": rep["etat"],
                "verifie_le": None,
            }
            if rep.get("origine"):
                item["origine"] = rep["origine"]
            items.append(item)

        chapitre = {
            "n": n,
            "slug": SLUGS[n],
            "titre": e["titre"],
            "annonce": e.get("annonce") or "",
            "etat": "annonce",          # complet | en_cours | annonce
            "verifie_le": None,
            "intro": None,
            "items": items,
            "outils": [],
        }
        f = DEST / f"{n}-{SLUGS[n]}.json"
        f.write_text(json.dumps(chapitre, ensure_ascii=False, indent=2) + "\n",
                     encoding="utf-8")
        total += len(items)
        print(f"  {f.name:<34} {len(items):>2} items")

    assert total == d["total"], f"{total} items pour {d['total']} annonces"
    print(f"\n{total} items repartis, aucun perdu.")


if __name__ == "__main__":
    main()
