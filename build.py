#!/usr/bin/env python3
"""Génère les pages du référentiel à partir de data/perimetre.json.

Usage : python3 build.py
Aucune dépendance. Le JSON est la source ; ce script ne fabrique jamais de valeur.
"""

import html
import json
import pathlib

import controles

RACINE = pathlib.Path(__file__).parent
PUBLIC = RACINE / "public"  # seul ce dossier est servi ; le reste du depot ne l'est pas
DATA = json.loads((PUBLIC / "data" / "perimetre.json").read_text(encoding="utf-8"))
PUBLIES = {f.stem.upper() for f in (PUBLIC / "data" / "reperes").glob("*.json")}

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
            if rep["id"] in PUBLIES:
                q = f'<a href="/ressources/{rep["id"].lower()}/">{q}</a>'
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


def ancrer(texte, chiffres):
    """Remplace les ancres {{c:id}} par la valeur declaree, et la rend reperable a l'oeil.

    Aucune valeur n'est ecrite a la main dans un texte : c'est ce que verifie C3.
    """
    def remplacer(m):
        c = chiffres[m.group(1)]
        titre = html.escape(f'{c["libelle"]} · {c["unite"]}')
        return f'<span class="v" title="{titre}">{html.escape(str(c["valeur"]))}</span>'
    return controles.ANCRE.sub(remplacer, html.escape(texte))


def pastilles(source):
    """La barre de tracabilite : ce que la source publie, pas ce qu'elle vaut."""
    tests = [
        ("échantillon publié", bool(source.get("n"))),
        ("date de terrain", bool(source.get("terrain"))),
        ("méthode consultable", bool(source.get("methode_consultable"))),
        ("accès ouvert", bool(source.get("acces_ouvert"))),
        ("éditeur sans intérêt", source.get("interet") == 0),
    ]
    return "".join(
        f'<span class="pastille {"ok" if v else "ko"}">{"●" if v else "○"} {html.escape(t)}</span>'
        for t, v in tests
    )


def page_repere(r):
    chiffres = {c["id"]: c for c in r.get("chiffres", [])}
    src = r["sources"][0]
    d = DATA

    out = [TETE.format(
        titre=html.escape(r["question"]),
        desc=html.escape(f'{r["id"]} · {r["question"]} Chiffre sourcé, daté, '
                         f'avec le nom de qui a intérêt à ce qu\'il soit vrai.'),
    )]

    out.append(f'''  <p class="brand"><a href="/ressources/">Ressources</a> · {html.escape(r["etape"])}</p>
  <p class="repere-id">{r["id"]}</p>
  <h1>{html.escape(r["question"])}</h1>
  <div class="legend">
    <span>Lecture : {html.escape(r["cout_de_lecture"])}</span>
    <span class="{classe_etat("S" if r["etat"] == "mesure" else "Ø")}">
      {"mesure" if r["etat"] == "mesure" else html.escape(r["etat"])}</span>
    <span>Intérêt de la source : niveau {src["interet"]}</span>
  </div>

  <p class="reponse">{ancrer(r["reponse"], chiffres)}</p>

  <h2>La source</h2>
  <p><em>{html.escape(src["titre"])}</em>, {html.escape(src["auteurs"])}.
    {html.escape(src["reference"])}. <a href="{html.escape(src["url"])}">Lire la source</a>.</p>
  <p class="note">n = {html.escape(src["n"])} · terrain : {html.escape(src["terrain"])} ·
    {html.escape(src["methode_consultable"])}</p>
  <div class="barre">{pastilles(src)}</div>

  <h2>Qui a intérêt à ce que ce chiffre soit cru vrai</h2>
  <p>{html.escape(src["beneficiaire"])}</p>

  <h2>Ce que ce chiffre ne dit pas</h2>
  <p>{ancrer(r["limites"], chiffres)}</p>

  <h2>La lecture qui manque au champ</h2>
  <p>{ancrer(r["lecture_inversion"], chiffres)}</p>
  <p class="note">{ancrer(r["limite_inversion"], chiffres)}</p>

  <h2>Notre intérêt à nous</h2>
  <p>{ancrer(r["notre_interet"], chiffres)}</p>

  <h2>Les chiffres de cette page</h2>
  <div class="rows">''')

    for c in r.get("chiffres", []):
        out.append(f'''
      <div class="row">
        <span class="id">{html.escape(str(c["valeur"]))}</span>
        <span class="q">{html.escape(c["libelle"])}</span>
        <span class="st st-O">{html.escape(c["unite"])}</span>
      </div>''')

    out.append(f'''
  </div>

  <h2>À lire ensuite</h2>
  <div class="rows">''')
    for l in r["liens_sortants"]:
        etat = "publié" if l.get("publie") else "à venir"
        out.append(f'''
      <div class="row">
        <span class="id">{l["id"]}</span>
        <span class="q">{html.escape(l["question"])}</span>
        <span class="st st-O">{etat}</span>
      </div>''')
    out.append('''
  </div>
''')

    out.append(f'''
  <h2>Citer ce repère</h2>
  <p class="note mono">{html.escape(r["citation_suggeree"])}</p>
  <p class="note">Version {r["version"]}, consulté le {r["date_consultation"]} ·
    <a href="/data/reperes/{r["id"].lower()}.json">les données de ce repère</a></p>
''')

    out.append(PIED.format(editeur=html.escape(d["editeur"]), version=d["version"],
                           date=d["date"], licence=d["licence"]))
    return "".join(out)


def charger_reperes():
    dossier = PUBLIC / "data" / "reperes"
    if not dossier.exists():
        return []
    return [json.loads(f.read_text(encoding="utf-8")) for f in sorted(dossier.glob("*.json"))]


def main():
    reperes = charger_reperes()

    # Les controles d'abord : un seul qui echoue et rien n'est ecrit.
    alertes, deja_vues = [], set()
    for r in reperes:
        alertes += controles.controler(r, deja_vues)

    cible = PUBLIC / "ressources" / "index.html"
    cible.parent.mkdir(exist_ok=True)
    cible.write_text(page_index(), encoding="utf-8")

    total = sum(len(e["reperes"]) for e in DATA["etapes"])
    assert total == DATA["total"], f"incohérence : {total} repères pour un total annoncé de {DATA['total']}"
    print(f"écrit : {cible} ({total} repères, {DATA['repartition']['vide']} zones blanches)")

    for r in reperes:
        page = PUBLIC / "ressources" / r["id"].lower() / "index.html"
        page.parent.mkdir(parents=True, exist_ok=True)
        page.write_text(page_repere(r), encoding="utf-8")
        print(f"écrit : {page} ({len(r.get('chiffres', []))} chiffres déclarés, tous contrôlés)")

    for a in alertes:
        print(f"  ⚠ {a}")


if __name__ == "__main__":
    main()
