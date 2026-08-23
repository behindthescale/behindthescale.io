#!/usr/bin/env python3
"""Les figures d'un decorticage, en SVG ecrit a la main.

La chronologie n'est pas dessinee : elle est calculee depuis le catalogue
archive. Un point ne peut donc pas apparaitre sans une ligne dans les donnees.
"""

import datetime
import html
import json
import pathlib


def _jour(s):
    return datetime.date.fromisoformat(s)


def figure(svg, legende, aria):
    return (f'<figure class="fig">\n<svg viewBox="{svg["vb"]}" role="img" '
            f'aria-label="{html.escape(aria)}" class="schema">\n{svg["corps"]}\n</svg>\n'
            f'<figcaption>{legende}</figcaption>\n</figure>')


# --- Figure 1 : la carte du systeme ---------------------------------------

def carte_du_systeme():
    etapes = [
        ("Chaîne YouTube", "et les autres réseaux", None),
        ("Calculateurs et PDF", "gratuits, sans achat", "amènent sur le site"),
        ("Liste de diffusion", "adresse collectée", "échange contre l'adresse"),
        ("Questionnaire", "oriente vers un programme", "ou accès direct depuis le site"),
        ("28 produits", "un seul prix : 49,99 $", "recommande"),
        ("3 lots", "arrivés un an après", "une fois les paires connues"),
    ]
    L, H = 300, 54           # boite
    X, PAS = 40, 92          # colonne, pas vertical
    corps = ['<defs><marker id="fl" viewBox="0 0 10 10" refX="9" refY="5" '
             'markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
             '<path d="M0,0 L10,5 L0,10 z" fill="currentColor"/></marker></defs>']
    for i, (titre, sous, arete) in enumerate(etapes):
        y = 20 + i * PAS
        classe = "boite-cle" if i == 4 else "boite"
        corps.append(f'<rect class="{classe}" x="{X}" y="{y}" width="{L}" height="{H}" rx="2"/>')
        corps.append(f'<text class="t-titre" x="{X + 16}" y="{y + 23}">{html.escape(titre)}</text>')
        corps.append(f'<text class="t-sous" x="{X + 16}" y="{y + 41}">{html.escape(sous)}</text>')
        if arete:
            y0 = y - PAS + H
            corps.append(f'<line class="arete" x1="{X + 28}" y1="{y0}" x2="{X + 28}" y2="{y - 4}" '
                         f'marker-end="url(#fl)"/>')
            corps.append(f'<text class="t-arete" x="{X + 44}" y="{y0 + 24}">{html.escape(arete)}</text>')
    return figure({"vb": f"0 0 {X + L + 40} {20 + len(etapes) * PAS - 30}", "corps": "\n".join(corps)},
                  "Le chemin complet, de l'audience gratuite à l'encaissement. "
                  "Chaque étage est observable publiquement ; aucun volume n'est connu.",
                  "Chaîne YouTube vers calculateurs et PDF gratuits, vers liste de diffusion, "
                  "vers questionnaire d'orientation, vers un catalogue de vingt-huit produits "
                  "à prix unique, puis vers trois lots.")


# --- Figure 2 : la chronologie des prix, calculee -------------------------

def chronologie_des_prix(catalogue):
    """Un point par produit. Exclut la carte cadeau, dont le prix est choisi par l'acheteur."""
    pts = [(p["publie"], min(float(v) for v in p["prix"]), p["titre"])
           for p in catalogue if "gift card" not in p["titre"].lower()]
    pts.sort()

    W, H = 700, 330
    GA, GD, GH, GB = 58, 20, 26, 46
    d0, d1 = _jour(pts[0][0]), _jour(pts[-1][0])
    span = (d1 - d0).days or 1
    pmax = 110.0

    def px(d): return GA + (_jour(d) - d0).days / span * (W - GA - GD)
    def py(p): return H - GB - (p / pmax) * (H - GH - GB)

    corps = []
    for prix in (0, 25, 50, 75, 100):
        y = py(prix)
        corps.append(f'<line class="grille" x1="{GA}" y1="{y:.1f}" x2="{W - GD}" y2="{y:.1f}"/>')
        corps.append(f'<text class="t-axe" x="{GA - 10}" y="{y + 4:.1f}" text-anchor="end">{prix} $</text>')

    y49 = py(49.99)
    corps.append(f'<line class="ligne-cle" x1="{GA}" y1="{y49:.1f}" x2="{W - GD}" y2="{y49:.1f}"/>')
    corps.append(f'<text class="t-cle" x="{W - GD}" y="{y49 - 9:.1f}" text-anchor="end">'
                 f'49,99 $ · le prix qui n’a jamais bougé</text>')

    annees = sorted({p[0][:4] for p in pts})
    for a in annees:
        prem = min(p[0] for p in pts if p[0][:4] == a)
        x = px(prem)
        corps.append(f'<line class="grille-v" x1="{x:.1f}" y1="{GH}" x2="{x:.1f}" y2="{H - GB}"/>')
        corps.append(f'<text class="t-axe" x="{x:.1f}" y="{H - GB + 20}" text-anchor="middle">{a}</text>')

    for d, prix, titre in pts:
        cle = abs(prix - 49.99) < 0.01
        corps.append(f'<circle class="{"pt-cle" if cle else "pt"}" cx="{px(d):.1f}" '
                     f'cy="{py(prix):.1f}" r="{5 if cle else 3.8}"><title>'
                     f'{html.escape(titre)} — {prix:.2f} $ — {d}</title></circle>')

    n_bas = sum(1 for _, p, _ in pts if p < 30)

    return figure({"vb": f"0 0 {W} {H}", "corps": "\n".join(corps)},
                  f"Le catalogue entier, un point par produit, à sa date de mise en vente. "
                  f"Les {n_bas} produits sous trente dollars sont tous du même jour de mars 2022, "
                  f"et aucun n’a suivi. Cette figure est calculée depuis le catalogue archivé : "
                  f"elle ne peut pas montrer un produit qui n’existe pas.",
                  "Nuage de points des vingt-sept produits par date de mise en vente et par prix. "
                  "Une ligne horizontale marque quarante-neuf dollars quatre-vingt-dix-neuf, "
                  "sur laquelle se pose la majorité des points, de deux mille vingt-deux à deux mille vingt-six.")


# --- Figure 3 : les deux axes de positionnement ---------------------------

def grille_des_axes():
    W, H = 620, 330
    GA, GB, GH, GD = 132, 62, 34, 30
    niveaux = ["Débutant", "Intermédiaire", "Avancé"]
    objectifs = ["Muscle", "Les deux", "Force"]
    lc = (W - GA - GD) / len(objectifs)
    lg = (H - GH - GB) / len(niveaux)

    corps = []
    for i in range(len(niveaux) + 1):
        y = GH + i * lg
        corps.append(f'<line class="grille" x1="{GA}" y1="{y:.1f}" x2="{W - GD}" y2="{y:.1f}"/>')
    for j in range(len(objectifs) + 1):
        x = GA + j * lc
        corps.append(f'<line class="grille" x1="{x:.1f}" y1="{GH}" x2="{x:.1f}" y2="{H - GB}"/>')
    for i, n in enumerate(niveaux):
        corps.append(f'<text class="t-axe" x="{GA - 12}" y="{GH + i * lg + lg / 2 + 4:.1f}" '
                     f'text-anchor="end">{n}</text>')
    for j, o in enumerate(objectifs):
        corps.append(f'<text class="t-axe" x="{GA + j * lc + lc / 2:.1f}" y="{H - GB + 20}" '
                     f'text-anchor="middle">{o}</text>')

    corps.append(f'<text class="t-titre" x="{GA}" y="{GH - 12}">Objectif</text>')
    corps.append(f'<text class="t-titre" x="14" y="{GH + 14}">Niveau</text>')
    corps.append(f'<rect class="case-plage" x="{GA + lc + 3:.1f}" y="{GH + lg + 3:.1f}" '
                 f'width="{lc * 2 - 6:.1f}" height="{lg * 2 - 6:.1f}" rx="2"/>')
    corps.append(f'<text class="t-cle" x="{GA + lc + 10:.1f}" y="{GH + lg - 9:.1f}">'
                 f'exemple de plage occupée</text>')

    return figure({"vb": f"0 0 {W} {H}", "corps": "\n".join(corps)},
                  "Les deux seules questions qui séparent les offres, et c’est ce qui rend le prix "
                  "unique tenable : si la différence n’est pas dans le prix, elle doit s’afficher "
                  "ailleurs. Un programme occupe une case ou une plage, comme celle tracée en "
                  "pointillés. La position réelle de chacun des programmes n’a pas été relevée et "
                  "n’est donc pas figurée ici.",
                  "Grille à deux axes : le niveau de débutant à avancé en ordonnée, "
                  "l’objectif du muscle à la force en abscisse. Un programme occupe une case ou une plage.")


def charger_catalogue(racine):
    f = pathlib.Path(racine) / "public" / "data" / "cas" / "jeff-nippard" / "collecte.json"
    return json.loads(f.read_text(encoding="utf-8"))["catalogue"]


# --- Le SVG telechargeable -------------------------------------------------
# Hors de la page, aucune feuille de style externe ne s'applique : le fichier
# doit porter ses couleurs, sinon il s'ouvre vide chez celui qui le telecharge.

STYLE_AUTONOME = """
  <style>
    text { font-family: Archivo, Helvetica, Arial, sans-serif; }
    .boite      { fill: #101216; stroke: #343A45; stroke-width: 1; }
    .boite-cle  { fill: #14182a; stroke: #93A9F4; stroke-width: 1; }
    .arete      { stroke: #343A45; stroke-width: 1.2; fill: none; }
    .t-titre    { fill: #ECEEF2; font-size: 13px; font-weight: 600; }
    .t-sous     { fill: #7C8493; font-size: 11.5px; }
    .t-arete    { fill: #545B69; font-size: 11px; font-family: monospace; }
    .t-note     { fill: #545B69; font-size: 11px; }
  </style>
"""


def svg_autonome(fig_html):
    """Extrait le <svg> d'une figure et le rend lisible hors du site."""
    svg = fig_html[fig_html.index("<svg"):fig_html.index("</svg>") + 6]
    svg = svg.replace(
        "<svg ",
        '<svg xmlns="http://www.w3.org/2000/svg" style="background:#0A0B0D" ', 1)
    i = svg.index(">") + 1
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            + svg[:i] + STYLE_AUTONOME + svg[i:] + "\n")
