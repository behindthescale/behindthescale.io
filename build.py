#!/usr/bin/env python3
"""Génère les pages du référentiel à partir de data/perimetre.json.

Usage : python3 build.py
Aucune dépendance. Le JSON est la source ; ce script ne fabrique jamais de valeur.
"""

import html
import json
import pathlib

import controles
import figures

RACINE = pathlib.Path(__file__).parent
PUBLIC = RACINE / "public"  # seul ce dossier est servi ; le reste du depot ne l'est pas
DATA = json.loads((PUBLIC / "data" / "perimetre.json").read_text(encoding="utf-8"))
PUBLIES = {f.stem.upper() for f in (PUBLIC / "data" / "reperes").glob("*.json")}
DECORTICAGES = PUBLIC / "data" / "decorticages"

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
<main class="wrap {classe}">
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


TETE_DOC = """<!doctype html>
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
<body class="doc">

<aside class="side">
  <a class="side-marque" href="/">Behind The Scale</a>
  <nav class="sommaire">
{sommaire}  </nav>
  <a class="side-cta" href="mailto:alois@behindthescale.io?subject=Behind%20The%20Scale">Travailler avec nous</a>
</aside>

<div class="doc-col">
  <a class="doc-dl" href="{telechargement}" download>Télécharger</a>
  <main class="doc-main">
"""

PIED_DOC = """
    <footer>
      <p>{editeur} · {licence}</p>
      <p><a href="/ressources/">Toutes les ressources</a> ·
         <a href="/data/decorticages/{ident}.json">les données de cette page</a></p>
    </footer>
  </main>
</div>
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
    """L'index : meme chassis que les decorticages, sinon l'ensemble se disloque."""
    d, r = DATA, DATA["repartition"]
    decorticages = charger_decorticages()

    som = ['    <p class="som-titre">Décorticages</p>\n']
    for dec in decorticages:
        som.append(f'    <a href="/ressources/{dec["id"]}/"><span class="som-n">→</span>'
                   f'{html.escape(dec["titre"])}</a>\n')
    som.append('    <p class="som-titre">La bibliothèque</p>\n')
    for e in d["etapes"]:
        som.append(f'    <a href="#e{e["n"]}"><span class="som-n">{e["n"]}</span>'
                   f'{html.escape(e["titre"])}</a>\n')

    out = [TETE_DOC.format(
        titre="Ressources",
        desc=html.escape("Des systèmes de créateurs, démontés décision par décision. "
                         "Chaque affirmation porte sa preuve et son verdict."),
        sommaire="".join(som),
        telechargement="/data/perimetre.json",
    )]

    out.append(f'''    <p class="doc-eyebrow">Behind The Scale</p>
    <h1>Ressources</h1>
    <p class="doc-lede">Des systèmes de créateurs, démontés décision par décision. Chaque
      affirmation porte sa preuve, sa date, et le verdict de ce que tu peux en copier.</p>
''')

    for dec in decorticages:
        n_cop = sum(1 for x in dec["decisions"] if x["verdict"] == "copiable")
        out.append(f'''
    <a class="carte" href="/ressources/{dec["id"]}/">
      <span class="carte-eyebrow">Décorticage · {html.escape(dec["cout_de_lecture"])}</span>
      <span class="carte-titre">{html.escape(dec["titre"])}</span>
      <span class="carte-sous">{html.escape(dec["sujet"])}</span>
      <span class="carte-pied">{len(dec["decisions"])} décisions relevées ·
        {n_cop} copiables telles quelles · observé le {dec["date_observation"]}</span>
    </a>''')

    out.append(f'''
    <section class="bloc">
      <p class="bloc-n">Sous les décorticages</p>
      <h2 class="bloc-titre">La bibliothèque</h2>
      <p class="bloc-fait">Une liste fermée de {d["total"]} questions qui vont d'une audience à une
        première vente encaissée. Elle sert de réserve de preuves : quand un décorticage avance un
        chiffre, il renvoie ici.</p>
      <p class="bloc-pourquoi"><strong>{r["vide"]} de ces questions n'ont aucune source connue</strong>,
        et c'est le résultat le plus utile de la liste. {html.escape(d["avertissement"])}</p>
      <p class="preuve">{r["solide"]} source solide · {r["faible"]} source faible ou intéressée ·
        {r["vide"]} zone blanche</p>
    </section>
''')

    for e in d["etapes"]:
        out.append(f'''
    <section class="bloc" id="e{e["n"]}">
      <p class="bloc-n">Étape {e["n"]} · {len(e["reperes"])} repères</p>
      <h2 class="bloc-titre">{html.escape(e["titre"])}</h2>
      <div class="rows">''')
        for rep in e["reperes"]:
            q = html.escape(rep["question"])
            if rep["id"] in PUBLIES:
                q = f'<a href="/ressources/{rep["id"].lower()}/">{q}</a>'
            out.append(f'''
        <div class="row"><span class="id">{rep["id"]}</span><span class="q">{q}</span>
          <span class="st {classe_etat(rep["etat"])}">{libelle_etat(rep["etat"])}</span></div>''')
        out.append('''
      </div>
    </section>''')

    out.append(PIED_DOC.format(editeur=html.escape(d["editeur"]),
                              licence=d["licence"], ident="jeff-nippard"))
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
        classe="etroit",
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

    for r in charger_decorticages():
        controles.controler_decorticage(r)
        dossier = PUBLIC / "ressources" / r["id"]
        dossier.mkdir(parents=True, exist_ok=True)
        (dossier / "index.html").write_text(page_decorticage(r), encoding="utf-8")
        (dossier / "chronologie-des-prix.svg").write_text(
            figures.svg_autonome(figures.chronologie_des_prix(figures.charger_catalogue(RACINE))),
            encoding="utf-8")
        print(f"écrit : {dossier}/index.html ({len(r['decisions'])} décisions, "
              f"{len(r['chiffres'])} chiffres, 3 figures)")

    for a in alertes:
        print(f"  ⚠ {a}")




# --- Le decorticage --------------------------------------------------------

LIBELLE_VERDICT = {
    "copiable": "Copiable tel quel",
    "conditionnel": "Copiable sous condition",
    "non_copiable": "À ne pas reproduire",
}


def page_decorticage(r):
    """Une colonne unique, un sommaire fixe, aucune alternance de largeur.

    Modele : eptwts.com, la reference donnee par Alois. Une seule figure y est
    admise, celle qui porte une donnee qu'aucune phrase ne remplace.
    """
    chiffres = {c["id"]: c for c in r.get("chiffres", [])}
    src = r["sources"][0]

    entrees = [(f'd{i}', f'{i:02d}', dec["titre"]) for i, dec in enumerate(r["decisions"], 1)]
    sommaire = ['    <p class="som-titre">Les décisions</p>\n']
    for ancre, n, titre in entrees:
        sommaire.append(f'    <a href="#{ancre}"><span class="som-n">{n}</span>'
                        f'{html.escape(titre)}</a>\n')
    sommaire.append('    <p class="som-titre">Et ensuite</p>\n')
    sommaire.append('    <a href="#invisible"><span class="som-n">·</span>Ce qui n’est pas visible</a>\n')
    sommaire.append('    <a href="#actions"><span class="som-n">·</span>Ce que tu fais cette semaine</a>\n')
    sommaire.append('    <a href="#methode"><span class="som-n">·</span>Comment ceci a été relevé</a>\n')

    out = [TETE_DOC.format(
        titre=html.escape(r["titre"]),
        desc=html.escape(r["sujet"]),
        sommaire="".join(sommaire),
        telechargement=f'/ressources/{r["id"]}/chronologie-des-prix.svg',
    )]

    out.append(f'''    <p class="doc-eyebrow">Décorticage · observé le {r["date_observation"]}</p>
    <h1>{html.escape(r["titre"])}</h1>
    <p class="doc-lede">{html.escape(r["sujet"])}</p>
    <p class="doc-resume">{ancrer(r["resume"], chiffres)}</p>
''')

    for i, dec in enumerate(r["decisions"], 1):
        pr = dec["preuve"]
        out.append(f'''
    <section class="bloc" id="d{i}">
      <p class="bloc-n">Décision {i:02d}</p>
      <h2 class="bloc-titre">{ancrer(dec["titre"], chiffres)}</h2>
      <p class="bloc-fait">{ancrer(dec["fait"], chiffres)}</p>
      <p class="bloc-pourquoi">{ancrer(dec["pourquoi"], chiffres)}</p>
      <p class="verdict v-{dec["verdict"]}"><span class="v-label">{LIBELLE_VERDICT[dec["verdict"]]}.</span>
        {ancrer(dec["verdict_texte"], chiffres)}</p>
      <p class="preuve">{html.escape(pr["quoi"])} ·
        <a href="{html.escape(pr["url"])}">source</a> · relevé le {pr["date"]}</p>
    </section>''')
        if dec["id"] == "d1":
            out.append("\n" + figures.chronologie_des_prix(figures.charger_catalogue(RACINE)))

    out.append(f'''
    <section class="bloc" id="invisible">
      <p class="bloc-n">La limite</p>
      <h2 class="bloc-titre">Ce qui n’est pas visible</h2>
      <p>{ancrer(r["invisible"], chiffres)}</p>
    </section>

    <section class="bloc" id="actions">
      <p class="bloc-n">À faire</p>
      <h2 class="bloc-titre">Ce que tu fais cette semaine</h2>''')
    for i, a in enumerate(r["actions"], 1):
        out.append(f'''
      <p class="action"><span class="action-n">{i}</span>{ancrer(a, chiffres)}</p>''')
    out.append('''
    </section>''')

    out.append(f'''
    <section class="bloc" id="methode">
      <p class="bloc-n">La méthode</p>
      <h2 class="bloc-titre">Comment ceci a été relevé</h2>
      <p>{html.escape(src["methode"])}</p>
      <p class="preuve"><a href="{html.escape(src["url"])}">{html.escape(src["titre"])}</a>,
        consultée le {src["date_consultation"]} ·
        <a href="/data/cas/{r["id"]}/collecte.json">les données brutes archivées</a></p>
      <p class="preuve">{html.escape(r["citation_suggeree"])}</p>
    </section>
''')

    out.append(PIED_DOC.format(editeur=html.escape(DATA["editeur"]),
                              licence=DATA["licence"], ident=r["id"]))
    return "".join(out)


def charger_decorticages():
    if not DECORTICAGES.exists():
        return []
    return [json.loads(f.read_text(encoding="utf-8")) for f in sorted(DECORTICAGES.glob("*.json"))]


if __name__ == "__main__":
    main()
