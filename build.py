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
DATA = json.loads((PUBLIC / "data" / "perimetre.json").read_text(encoding="utf-8"))
CHAPITRES = PUBLIC / "data" / "chapitres"
CAS = PUBLIC / "data" / "cas"

AUJOURD_HUI = datetime.date.fromisoformat(DATA["date"])

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

    publies = sum(len(publiables(ch)) for ch in chapitres)

    out = [TETE.format(
        titre="Le manuel",
        desc=html.escape("Le manuel de la monétisation d’audience pour un créateur francophone. "
                         "Chaque affirmation dit d’où elle vient et quand elle a été vérifiée."),
        sommaire="".join(som),
        telechargement="/data/perimetre.json",
    )]

    out.append(f'''    <p class="doc-eyebrow">Behind The Scale</p>
    <h1>Le manuel</h1>
    <p class="doc-lede">Ce qu’il faut savoir entre une audience et une première vente encaissée,
      en neuf chapitres. Chaque affirmation dit d’où elle vient et quand elle a été vérifiée
      pour la dernière fois.</p>
    <p class="doc-resume">Le périmètre est fermé à {DATA["total"]} questions : une question qui
      n’entre pas dans ces neuf chapitres ne sera pas traitée. <strong>{publies} sont publiées</strong>
      à ce jour. Les autres sont listées à leur place, sans réponse, parce qu’annoncer un manuel
      complet qui ne l’est pas serait la première chose à ne pas croire ici.</p>
''')

    for ch in chapitres:
        n_pub, n_tot = len(publiables(ch)), len(ch.get("items", []))
        n_out = len(ch.get("outils", []))
        etat = {"complet": "complet", "en_cours": "en cours", "annonce": "annoncé"}[ch["etat"]]
        out.append(f'''
    <a class="carte" href="/ressources/{ch["n"]}-{ch["slug"]}/">
      <span class="carte-eyebrow">Chapitre {ch["n"]} · {etat}</span>
      <span class="carte-titre">{html.escape(ch["titre"])}</span>
      <span class="carte-sous">{html.escape(ch["annonce"])}</span>
      <span class="carte-pied">{n_pub} publié{"s" if n_pub > 1 else ""} sur {n_tot}{f" · {n_out} outils" if n_out else ""}</span>
    </a>''')

    if cas:
        out.append('''
    <section class="bloc">
      <p class="bloc-n">À part</p>
      <h2 class="bloc-titre">Les cas</h2>
      <p class="bloc-pourquoi">Un chapitre dit ce qu’on sait. Un cas montre un système entier qui
        tourne, décision par décision, avec le verdict de ce qui se copie et de ce qui ne se copie
        pas. Les chapitres y renvoient.</p>
    </section>''')
        for c in cas:
            n_cop = sum(1 for x in c["decisions"] if x["verdict"] == "copiable")
            out.append(f'''
    <a class="carte" href="/ressources/cas/{c["id"]}/">
      <span class="carte-eyebrow">Cas · {html.escape(c["cout_de_lecture"])}</span>
      <span class="carte-titre">{html.escape(c["titre"])}</span>
      <span class="carte-sous">{html.escape(c["sujet"])}</span>
      <span class="carte-pied">{len(c["decisions"])} décisions · {n_cop} copiables telles quelles ·
        observé le {c["date_observation"]}</span>
    </a>''')

    out.append(PIED.format(editeur=html.escape(DATA["editeur"]), licence=DATA["licence"],
                           donnees="/data/perimetre.json"))
    return "".join(out)


def rendu_item(it):
    chiffres = {c["id"]: c for c in it.get("chiffres", [])}
    t = it["type"]
    out = [f'''
    <section class="bloc" id="{it["id"].lower()}">
      <p class="bloc-n"><span class="etiq etiq-{t}">{LIBELLE_TYPE[t]}</span>{it["id"]}</p>
      <h2 class="bloc-titre">{html.escape(it["titre"])}</h2>''']

    if t == "a_rediger":
        out.append('''
      <p class="bloc-attente">Pas encore publié. Le recensement signale qu’une source pourrait
        exister ; tant qu’elle n’est pas lue et datée, rien n’est affirmé ici.</p>''')

    elif t == "zone_blanche":
        out.append(f'''
      <p class="bloc-fait">{FORMULE_ZONE_BLANCHE}</p>
      <p class="bloc-pourquoi"><strong>Ce qu’il faudrait pour la combler.</strong>
        {ancrer(it["ce_qu_il_faudrait"], chiffres)}</p>
      <p class="bloc-pourquoi"><strong>Qui pourrait le mesurer.</strong>
        {ancrer(it["qui_pourrait_le_mesurer"], chiffres)}</p>''')

    elif t == "cas":
        out.append(f'''
      <p class="bloc-fait">{ancrer(it["texte"], chiffres)}</p>
      <p class="preuve"><a href="/ressources/cas/{it["cas_slug"]}/">Lire le cas entier</a></p>''')

    else:
        out.append(f'''
      <p class="bloc-fait">{ancrer(it["texte"], chiffres)}</p>''')
        if it.get("limites"):
            out.append(f'''
      <p class="bloc-pourquoi">{ancrer(it["limites"], chiffres)}</p>''')
        if t == "principe":
            out.append(f'''
      <p class="bloc-pourquoi"><strong>D’où vient ce raisonnement.</strong>
        {ancrer(it["fondement"], chiffres)}</p>''')

    srcs = it.get("sources", [])
    if len(srcs) == 1:
        s = srcs[0]
        i = s.get("interet")
        mention = ("éditeur sans intérêt dans le champ" if i == 0
                   else f"intérêt de l’éditeur : niveau {i}" if i is not None else "")
        out.append(f'''
      <p class="preuve">{html.escape(s["titre"])} ·
        <a href="{html.escape(s["url"])}">source</a>{" · " + mention if mention else ""}</p>''')
    elif srcs:
        # plusieurs sources : une seule ligne, sinon la trace pese plus que le texte
        liens = " · ".join(f'<a href="{html.escape(s["url"])}" title="{html.escape(s["titre"])}">'
                           f'{html.escape(s.get("court") or s["titre"].split()[-1])}</a>'
                           for s in srcs)
        niveaux = {s.get("interet") for s in srcs}
        n = (f"tous de niveau {niveaux.pop()}" if len(niveaux) == 1
             else "niveaux d’intérêt mêlés")
        out.append(f'''
      <p class="preuve">Sources : {liens} · intérêt de l’éditeur : {n}</p>''')

    if it.get("verifie_le"):
        out.append(f'''
      <p class="preuve">Vérifié le {it["verifie_le"]}</p>{bandeau_fraicheur(it["verifie_le"])}''')

    out.append('''
    </section>''')
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


def page_chapitre(ch, chapitres):
    som = ['    <p class="som-titre">Les chapitres</p>\n']
    for c in chapitres:
        actif = ' class="actif"' if c["n"] == ch["n"] else ""
        som.append(f'    <a href="/ressources/{c["n"]}-{c["slug"]}/"{actif}>'
                   f'<span class="som-n">{c["n"]}</span>{html.escape(c["titre"])}</a>\n')
    pub = publiables(ch)
    if pub:
        som.append('    <p class="som-titre">Dans ce chapitre</p>\n')
        for it in pub:
            som.append(f'    <a href="#{it["id"].lower()}"><span class="som-n">·</span>'
                       f'{html.escape(it["titre"][:58])}</a>\n')
    if ch.get("outils"):
        som.append('    <p class="som-titre">Les outils</p>\n')
        som.append('    <a href="#outils"><span class="som-n">·</span>Ce avec quoi on le fait</a>\n')

    out = [TETE.format(
        titre=html.escape(ch["titre"]),
        desc=html.escape(ch["annonce"]),
        sommaire="".join(som),
        telechargement=f'/data/chapitres/{ch["n"]}-{ch["slug"]}.json',
    )]

    n_pub, n_tot = len(pub), len(ch.get("items", []))
    out.append(f'''    <p class="doc-eyebrow">Chapitre {ch["n"]}</p>
    <h1>{html.escape(ch["titre"])}</h1>
    <p class="doc-lede">{html.escape(ch["annonce"])}</p>''')
    if ch.get("intro"):
        out.append(f'''
    <p class="doc-resume">{html.escape(ch["intro"])}</p>''')
    out.append(f'''
    <p class="preuve">{n_pub} publié{"s" if n_pub > 1 else ""} sur {n_tot} · chapitre {ch["etat"].replace("_", " ")}</p>
''')

    for it in ch.get("items", []):
        out.append(rendu_item(it))

    if ch.get("outils"):
        out.append('''
    <section class="bloc" id="outils">
      <p class="bloc-n">Les outils</p>
      <h2 class="bloc-titre">Ce avec quoi on le fait</h2>
      <p class="bloc-pourquoi">Un outil se juge dans le problème qu’il règle, jamais dans une liste
        à part. Chacun porte ce qu’il ne fait pas, sinon c’est une recommandation déguisée.</p>''')
        for o in ch["outils"]:
            out.append(rendu_outil(o))
        out.append('''
    </section>''')

    out.append(PIED.format(editeur=html.escape(DATA["editeur"]), licence=DATA["licence"],
                           donnees=f'/data/chapitres/{ch["n"]}-{ch["slug"]}.json'))
    return "".join(out)


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

    out.append(PIED.format(editeur=html.escape(DATA["editeur"]), licence=DATA["licence"],
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
    slugs_cas = {c["id"] for c in cas}

    for ch in chapitres:
        controles.controler_chapitre(ch, slugs_cas)
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
        n_out = len(ch.get("outils", []))
        print(f"écrit : /ressources/{ch['n']}-{ch['slug']}/ "
              f"({len(publiables(ch))}/{len(ch.get('items', []))} publiés"
              f"{f', {n_out} outils' if n_out else ''})")

    for c in cas:
        d = base / "cas" / c["id"]
        d.mkdir(parents=True, exist_ok=True)
        (d / "index.html").write_text(page_cas(c), encoding="utf-8")
        (d / "chronologie-des-prix.svg").write_text(
            figures.svg_autonome(figures.chronologie_des_prix(figures.charger_catalogue(RACINE))),
            encoding="utf-8")
        print(f"écrit : /ressources/cas/{c['id']}/ ({len(c['decisions'])} décisions)")

    for ancienne, vers, motif in [
        ("r-004", "/ressources/0-le-seuil/#r-004",
         "Les repères sont devenus les items des chapitres. Celui-ci vit désormais dans le "
         "chapitre 0, à la même place dans le parcours."),
        ("jeff-nippard", "/ressources/cas/jeff-nippard/",
         "Les cas ont désormais leur propre dossier."),
    ]:
        d = base / ancienne
        d.mkdir(exist_ok=True)
        (d / "index.html").write_text(page_redirection(vers, motif), encoding="utf-8")
        print(f"redirigé : /ressources/{ancienne}/ → {vers}")


if __name__ == "__main__":
    main()
