#!/usr/bin/env python3
"""Genere le site a partir de public/data/.

Usage : python3 build.py
Aucune dependance. Les JSON sont la source ; ce script ne fabrique jamais une
valeur. Un controle qui echoue arrete tout, et rien n'est ecrit.

Trois pages, un seul chassis :
  /ressources/                  la porte, les neuf chapitres
  /ressources/<n>-<slug>/       un chapitre et ses items
  /ressources/cas/<slug>/       un decorticage complet
"""

import datetime
import html
import json
import pathlib

import controles
import figures

RACINE = pathlib.Path(__file__).parent
PUBLIC = RACINE / "public"
EDITEUR = "Behind The Scale"
LICENCE = "CC BY 4.0"
AUJOURD_HUI = datetime.date(2026, 8, 23)

CHAPITRES = PUBLIC / "data" / "chapitres"
CAS = PUBLIC / "data" / "cas"

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
<body class="doc">

<aside class="side">
  <a class="side-marque" href="/ressources/">Behind The Scale</a>
  <nav class="sommaire">
{sommaire}  </nav>
  <a class="side-cta" href="mailto:alois@behindthescale.io?subject=Behind%20The%20Scale">Travailler avec nous</a>
</aside>

<div class="doc-col">
  <a class="doc-dl" href="{telechargement}">Les données</a>
  <main class="doc-main">
"""

PIED = """
    <footer>
      <p>{editeur} · {licence}</p>
      <p><a href="/ressources/">Tous les chapitres</a> · <a href="{donnees}">les données de cette page</a></p>
    </footer>
  </main>
</div>
</body>
</html>
"""

LIBELLE_VERDICT = {
    "copiable": "Copiable tel quel",
    "conditionnel": "Copiable sous condition",
    "non_copiable": "À ne pas reproduire",
}

LIBELLE_TYPE = {
    "mesure": "Mesure",
    "zone_blanche": "Zone blanche",
    "principe": "Raisonnement",
    "cas": "Cas",
    "a_rediger": "À vérifier",
}

FORMULE_ZONE_BLANCHE = ("Aucune source publiée ne répond à cette question. Ce n’est pas un manque "
                        "de ce manuel, c’est un résultat sur l’état du domaine.")


def ancrer(texte, chiffres):
    """Remplace les ancres {{c:id}} par la valeur declaree.

    Aucune valeur ne s'ecrit a la main dans un texte : c'est ce que verifie C3,
    et c'est ce qui autorise la couleur. Un mot colore porte une source.
    """
    def remplacer(m):
        c = chiffres[m.group(1)]
        titre = html.escape(f'{c["libelle"]} · {c["unite"]}')
        return f'<span class="v" title="{titre}">{html.escape(str(c["valeur"]))}</span>'
    return controles.ANCRE.sub(remplacer, html.escape(texte))


def age_en_mois(d):
    if not d:
        return None
    j = datetime.date.fromisoformat(d)
    return (AUJOURD_HUI.year - j.year) * 12 + AUJOURD_HUI.month - j.month


def bandeau_fraicheur(d):
    """P10 rendu visible : le seul point ou nous depassons la reference."""
    m = age_en_mois(d)
    if m is None or m < 12:
        return ""
    if m < 24:
        return (f'<p class="perime">Vérifié il y a {m} mois. Au-delà d’un an, ce que dit cet item '
                f'peut avoir changé sans que nous l’ayons constaté.</p>')
    return (f'<p class="perime perime-fort">Vérifié il y a {m} mois. Cet item est sorti de l’index '
            f'et n’est plus affirmé, mais son adresse est conservée pour que les citations tiennent.</p>')


def charger(dossier):
    if not dossier.exists():
        return []
    return [json.loads(f.read_text(encoding="utf-8")) for f in sorted(dossier.glob("*.json"))]


def publiables(ch):
    return [i for i in ch.get("items", []) if i["type"] != "a_rediger"]


def page_porte(chapitres, cas):
    som = ['    <p class="som-titre">Les chapitres</p>\n']
    for ch in chapitres:
        som.append(f'    <a href="/ressources/{ch["n"]}-{ch["slug"]}/">'
                   f'<span class="som-n">{ch["n"]}</span>{html.escape(ch["titre"])}</a>\n')
    if cas:
        som.append('    <p class="som-titre">Les cas</p>\n')
        for c in cas:
            som.append(f'    <a href="/ressources/cas/{c["id"]}/"><span class="som-n">→</span>'
                       f'{html.escape(c["titre"])}</a>\n')

    total = sum(n_lecons(ch) for ch in chapitres)
    out = [TETE.format(
        titre="Le manuel",
        desc=html.escape("Ce que je découvre en montant un système d’opérateur, chapitre par "
                         "chapitre. Chaque leçon dit d’où elle vient et quand je l’ai vérifiée."),
        sommaire="".join(som),
        telechargement="/data/chapitres/1-ce-que-gagne-un-createur.json",
    )]

    out.append(f'''    <p class="doc-eyebrow">Behind The Scale · Aloïs Fouquet</p>
    <h1>Le manuel</h1>
    <p class="doc-lede">Je monte un système pour accompagner des créateurs dans leur monétisation.
      Je n’ai encore signé personne. En attendant, je remonte chaque chiffre à sa source, j’éprouve
      les outils, et j’écris ici ce que je trouve.</p>
    <p class="doc-resume">{total} leçons publiées à ce jour. Chacune porte sa date, et dit si elle
      vient d’une source que tu peux vérifier ou d’une chose que j’ai constatée moi-même. Les deux
      ne se valent pas, alors je les distingue.</p>
''')

    for ch in chapitres:
        n = n_lecons(ch)
        etat = f"{n} leçons" if n else "en préparation"
        out.append(f'''
    <a class="carte" href="/ressources/{ch["n"]}-{ch["slug"]}/">
      <span class="carte-eyebrow">Chapitre {ch["n"]} · {etat}</span>
      <span class="carte-titre">{html.escape(ch["titre"])}</span>
      <span class="carte-sous">{html.escape(ch["annonce"])}</span>
    </a>''')

    for c in cas:
        n_cop = sum(1 for x in c["decisions"] if x["verdict"] == "copiable")
        out.append(f'''
    <a class="carte" href="/ressources/cas/{c["id"]}/">
      <span class="carte-eyebrow">Cas · {html.escape(c["cout_de_lecture"])}</span>
      <span class="carte-titre">{html.escape(c["titre"])}</span>
      <span class="carte-sous">{html.escape(c["sujet"])}</span>
      <span class="carte-pied">{len(c["decisions"])} décisions · {n_cop} copiables telles quelles</span>
    </a>''')

    out.append(PIED.format(editeur=html.escape(EDITEUR), licence=LICENCE,
                           donnees="/data/chapitres/1-ce-que-gagne-un-createur.json"))
    return "".join(out)


def n_lecons(ch):
    return sum(len(sp["lecons"]) for sp in ch.get("sous_parties", []))


def rendu_lecon(lec):
    chiffres = {c["id"]: c for c in lec.get("chiffres", [])}
    out = [f'''
      <div class="lecon">
        <p class="lecon-lead">{ancrer(lec["lead"], chiffres)}</p>
        <p class="lecon-texte">{ancrer(lec["texte"], chiffres)}</p>''']

    srcs = lec.get("sources", [])
    if lec["nature"] == "constatee":
        out.append(f'''
        <p class="lecon-trace"><span class="chip chip-constate">constaté</span>{lec["verifie_le"]}</p>''')
    else:
        liens = " · ".join(f'<a href="{html.escape(s["url"])}" title="{html.escape(s["titre"])}">'
                           f'{html.escape(s.get("court") or "source")}</a>' for s in srcs)
        out.append(f'''
        <p class="lecon-trace"><span class="chip">sourcé</span>{liens} · {lec["verifie_le"]}</p>''')
    out.append(bandeau_fraicheur(lec["verifie_le"]))
    out.append('''
      </div>''')
    return "".join(out)


def page_chapitre(ch, chapitres):
    som = ['    <p class="som-titre">Les chapitres</p>\n']
    for c in chapitres:
        actif = ' class="actif"' if c["n"] == ch["n"] else ""
        som.append(f'    <a href="/ressources/{c["n"]}-{c["slug"]}/"{actif}>'
                   f'<span class="som-n">{c["n"]}</span>{html.escape(c["titre"])}</a>\n')
    if ch.get("sous_parties"):
        som.append('    <p class="som-titre">Dans ce chapitre</p>\n')
        for i, sp in enumerate(ch["sous_parties"], 1):
            som.append(f'    <a href="#s{i}"><span class="som-n">·</span>'
                       f'{html.escape(sp["titre"])}</a>\n')
    if ch.get("outils") or ch.get("livrables"):
        som.append('    <a href="#outils"><span class="som-n">·</span>À emporter</a>\n')

    out = [TETE.format(
        titre=html.escape(ch["titre"]),
        desc=html.escape(ch["annonce"]),
        sommaire="".join(som),
        telechargement=f'/data/chapitres/{ch["n"]}-{ch["slug"]}.json',
    )]

    out.append(f'''    <p class="doc-eyebrow">Chapitre {ch["n"]}</p>
    <h1>{html.escape(ch["titre"])}</h1>
    <p class="doc-lede">{html.escape(ch["annonce"])}</p>
''')
    if ch.get("collecte"):
        c = ch["collecte"]
        out.append(f'''    <p class="preuve">{html.escape(c["titre"])} ·
      <a href="{html.escape(c["url"])}">les vérifier</a></p>
''')

    if not ch.get("sous_parties"):
        out.append('''
    <p class="doc-resume">Ce chapitre n’est pas encore écrit. Il le sera quand j’aurai de quoi le
      remplir sans inventer, et il portera alors la date de ce que j’aurai vérifié.</p>''')

    for i, sp in enumerate(ch.get("sous_parties", []), 1):
        out.append(f'''
    <section class="sp" id="s{i}">
      <h2 class="sp-titre">{html.escape(sp["titre"])}</h2>''')
        for lec in sp["lecons"]:
            out.append(rendu_lecon(lec))
        out.append('''
    </section>''')

    if ch.get("outils") or ch.get("livrables"):
        out.append('''
    <section class="sp" id="outils">
      <h2 class="sp-titre">À emporter</h2>''')
        for l in ch.get("livrables", []):
            corps = (f'<pre class="livrable-contenu">{html.escape(l["contenu"])}</pre>'
                     if l.get("contenu") else
                     f'<p class="preuve"><a href="/ressources/outils/{l["page"]}/">Ouvrir</a></p>')
            out.append(f'''
      <div class="livrable">
        <p class="livrable-titre">{html.escape(l["titre"])}</p>
        <p class="livrable-sert">{html.escape(l["a_quoi_ca_sert"])}</p>
        {corps}
      </div>''')
        for o in ch.get("outils", []):
            out.append(rendu_outil(o))
        out.append('''
    </section>''')

    out.append(PIED.format(editeur=html.escape(EDITEUR), licence=LICENCE,
                           donnees=f'/data/chapitres/{ch["n"]}-{ch["slug"]}.json'))
    return "".join(out)


def rendu_outil(o):
    prix = (f'<span class="outil-prix">{html.escape(o["prix"])}</span>'
            f'<span class="outil-prix-date">relevé le {o["prix_verifie_le"]}</span>'
            if o.get("prix") else '')
    return f'''
      <div class="outil">
        <p class="outil-nom"><a href="{html.escape(o["url"])}">{html.escape(o["nom"])}</a>{prix}</p>
        <p class="outil-fait">{html.escape(o["fait"])}</p>
        <p class="outil-pourquoi"><strong>Pourquoi celui-là.</strong> {html.escape(o["pourquoi"])}</p>
        <p class="outil-limite"><strong>Ce qu’il ne fait pas.</strong> {html.escape(o["ne_fait_pas"])}</p>
      </div>'''


def page_cas(r):
    chiffres = {c["id"]: c for c in r.get("chiffres", [])}
    src = r["sources"][0]

    som = ['    <p class="som-titre">Les décisions</p>\n']
    for i, dec in enumerate(r["decisions"], 1):
        som.append(f'    <a href="#d{i}"><span class="som-n">{i:02d}</span>'
                   f'{html.escape(dec["titre"])}</a>\n')
    som.append('    <p class="som-titre">Et ensuite</p>\n')
    for ancre, txt in (("invisible", "Ce qui n’est pas visible"),
                       ("actions", "Ce que tu fais cette semaine"),
                       ("methode", "Comment ceci a été relevé")):
        som.append(f'    <a href="#{ancre}"><span class="som-n">·</span>{txt}</a>\n')

    out = [TETE.format(
        titre=html.escape(r["titre"]),
        desc=html.escape(r["sujet"]),
        sommaire="".join(som),
        telechargement=f'/data/cas/{r["id"]}.json',
    )]

    out.append(f'''    <p class="doc-eyebrow">Cas · observé le {r["date_observation"]}</p>
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
      <p class="bloc-fait">{ancrer(r["invisible"], chiffres)}</p>
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
      <p class="bloc-fait">{html.escape(src["methode"])}</p>
      <p class="preuve"><a href="{html.escape(src["url"])}">{html.escape(src["titre"])}</a>,
        consultée le {src["date_consultation"]} ·
        <a href="/data/collectes/{r["id"]}/collecte.json">les données brutes archivées</a></p>
      <p class="preuve">{html.escape(r["citation_suggeree"])}</p>
    </section>
''')

    out.append(PIED.format(editeur=html.escape(EDITEUR), licence=LICENCE,
                           donnees=f'/data/cas/{r["id"]}.json'))
    return "".join(out)


def page_redirection(vers, motif):
    """Une adresse publiee ne rend jamais une erreur (P10)."""
    return f'''<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta http-equiv="refresh" content="0; url={vers}">
<link rel="canonical" href="{vers}">
<title>Déplacé</title>
<link rel="stylesheet" href="/style.css">
</head>
<body class="doc">
<div class="doc-col"><main class="doc-main">
  <p class="doc-eyebrow">Déplacé</p>
  <h1>Cette page a changé d’adresse</h1>
  <p class="doc-lede">{html.escape(motif)}</p>
  <p><a href="{vers}">Continuer</a></p>
</main></div>
</body>
</html>
'''


def main():
    chapitres = sorted(charger(CHAPITRES), key=lambda c: c["n"])
    cas = charger(CAS)

    for ch in chapitres:
        controles.controler_chapitre(ch)
    for c in cas:
        controles.controler_decorticage(c)

    base = PUBLIC / "ressources"
    base.mkdir(parents=True, exist_ok=True)
    (base / "index.html").write_text(page_porte(chapitres, cas), encoding="utf-8")
    print(f"écrit : /ressources/ ({len(chapitres)} chapitres, {len(cas)} cas)")

    for ch in chapitres:
        d = base / f'{ch["n"]}-{ch["slug"]}'
        d.mkdir(exist_ok=True)
        (d / "index.html").write_text(page_chapitre(ch, chapitres), encoding="utf-8")
        n, sp = n_lecons(ch), len(ch.get("sous_parties", []))
        extra = []
        if ch.get("outils"):    extra.append(f"{len(ch['outils'])} outils")
        if ch.get("livrables"): extra.append(f"{len(ch['livrables'])} livrable")
        print(f"écrit : /ressources/{ch['n']}-{ch['slug']}/ "
              f"({n} leçons en {sp} sous-parties{', ' + ', '.join(extra) if extra else ''})")

    for c in cas:
        d = base / "cas" / c["id"]
        d.mkdir(parents=True, exist_ok=True)
        (d / "index.html").write_text(page_cas(c), encoding="utf-8")
        (d / "chronologie-des-prix.svg").write_text(
            figures.svg_autonome(figures.chronologie_des_prix(figures.charger_catalogue(RACINE))),
            encoding="utf-8")
        print(f"écrit : /ressources/cas/{c['id']}/ ({len(c['decisions'])} décisions)")

    for ancienne, vers, motif in [
        ("r-004", "/ressources/1-ce-que-gagne-un-createur/",
         "Les repères sont devenus des leçons. Celle-ci ouvre le premier chapitre."),
        ("jeff-nippard", "/ressources/cas/jeff-nippard/",
         "Les cas ont désormais leur propre dossier."),
        ("0-le-seuil", "/ressources/1-ce-que-gagne-un-createur/",
         "Les chapitres ont été redécoupés autour de ce que je découvre en construisant."),
        ("6-encaisser", "/ressources/5-encaisser-et-garder/",
         "Ce chapitre a changé de numéro dans le nouveau découpage."),
        ("3-le-prix", "/ressources/cas/jeff-nippard/",
         "Le chapitre sur le prix a été absorbé ; ce qu’il portait vit dans le cas Jeff Nippard."),
    ]:
        d = base / ancienne
        d.mkdir(exist_ok=True)
        (d / "index.html").write_text(page_redirection(vers, motif), encoding="utf-8")
        print(f"redirigé : /ressources/{ancienne}/ → {vers}")


if __name__ == "__main__":
    main()
