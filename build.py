#!/usr/bin/env python3
"""Génère les pages du référentiel à partir de data/perimetre.json.

Usage : python3 build.py
Aucune dépendance. Le JSON est la source ; ce script ne fabrique jamais de valeur.
"""

import html
import json
import pathlib

RACINE = pathlib.Path(__file__).parent
PUBLIC = RACINE / "public"  # seul ce dossier est servi ; le reste du depot ne l'est pas
DATA = json.loads((PUBLIC / "data" / "perimetre.json").read_text(encoding="utf-8"))

TETE = """<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{titre}</title>
<meta name="description" content="{desc}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap">
<link rel="stylesheet" href="/style.css">
</head>
<body>
<main class="wrap">
"""

PIED = """
  <footer>
    <p>{editeur} · {version}, {date} · {licence}</p>
    <p><a href="/">behindthescale.io</a> · <a href="/data/perimetre.json">les données de cette page</a></p>
  </footer>

</main>
</body>
</html>
"""


def classe_etat(etat):
    """Rend la classe CSS d'un état, sans jamais réinterpréter sa valeur."""
    tete = etat[0] if etat else "?"
    return {"S": "st-S", "F": "st-F", "Ø": "st-O"}.get(tete, "st-O")


def libelle_etat(etat):
    tete = etat[0] if etat else "?"
    base = {"S": "source solide", "F": "source faible", "Ø": "zone blanche"}.get(tete, etat)
    return base + (" *" if len(etat) > 1 else "")


def page_index():
    d = DATA
    r = d["repartition"]
    out = [TETE.format(
        titre=html.escape(d["titre"]),
        desc=html.escape(f'{d["total"]} questions entre une audience et une première vente '
                         f'encaissée. {r["vide"]} n\'ont aucune source connue.'),
    )]

    out.append(f'''  <p class="brand">{html.escape(d["editeur"])}</p>
  <h1>{html.escape(d["titre"])}</h1>
  <p class="lede">{d["total"]} questions entre une audience et une première vente encaissée.
    <strong>{r["vide"]} d'entre elles n'ont aucune source connue.</strong></p>
  <p class="note">{html.escape(d["sous_titre"])}. Périmètre fermé : une question qui n'est pas
    dans ces neuf étapes ne sera pas traitée.</p>

  <div class="legend">
    <span class="st-S">{r["solide"]} source solide</span>
    <span class="st-F">{r["faible"]} source faible ou intéressée</span>
    <span class="st-O">{r["vide"]} zone blanche</span>
  </div>

  <div class="warn">
    <strong>Ce que cette page ne sait pas encore.</strong>
    {html.escape(d["avertissement"])}
    Un astérisque signale un état nuancé : source partielle, adjacente, ou contredite.
  </div>
''')

    for e in d["etapes"]:
        out.append(f'''
  <section class="step">
    <h3>{e["n"]} · {html.escape(e["titre"])}</h3>
    <p class="count">{len(e["reperes"])} repères</p>
    <div class="rows">''')
        for rep in e["reperes"]:
            q = html.escape(rep["question"])
            out.append(f'''
      <div class="row">
        <span class="id">{rep["id"]}</span>
        <span class="q">{q}</span>
        <span class="st {classe_etat(rep["etat"])}">{libelle_etat(rep["etat"])}</span>
      </div>''')
        out.append('''
    </div>
  </section>''')

    out.append(f'''
  <h2>Comment lire ces états</h2>
  <p><strong>Source solide</strong> : une source indépendante ou normative semble exister, avec un
    échantillon et une date, ou un texte de droit. <strong>Source faible</strong> : seules des
    sources intéressées ont été trouvées, c'est-à-dire publiées par quelqu'un qui vend un produit
    dont la demande augmente si le chiffre est cru vrai. <strong>Zone blanche</strong> : rien n'a
    été trouvé.</p>
  <p>Une zone blanche n'est pas un manque de ce référentiel, c'est un résultat sur l'état du
    domaine. Elle vaut ce que vaut la liste des sources examinées et écartées, qui sera publiée
    avec chaque repère.</p>
''')

    out.append(PIED.format(editeur=html.escape(d["editeur"]), version=d["version"],
                           date=d["date"], licence=d["licence"]))
    return "".join(out)


def main():
    cible = PUBLIC / "ressources" / "index.html"
    cible.parent.mkdir(exist_ok=True)
    cible.write_text(page_index(), encoding="utf-8")

    total = sum(len(e["reperes"]) for e in DATA["etapes"])
    assert total == DATA["total"], f"incohérence : {total} repères pour un total annoncé de {DATA['total']}"
    print(f"écrit : {cible} ({total} repères, {DATA['repartition']['vide']} zones blanches)")


if __name__ == "__main__":
    main()
