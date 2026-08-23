#!/usr/bin/env python3
"""Les figures d'un decorticage.

Regle unique : une figure porte une donnee, ou elle n'existe pas. Un schema en
boites qui redit le texte est une decoration, et il a ete retire pour ca.
Deux formes seulement : la chose observee, capturee telle quelle et annotee ;
et une mesure, calculee depuis les donnees archivees.
"""

import datetime
import html
import json
import pathlib

ACCENT = "#93A9F4"


def _jour(s):
    return datetime.date.fromisoformat(s)


def figure(vb, corps, legende, aria, classe=""):
    return (f'<figure class="fig {classe}">\n'
            f'<svg viewBox="{vb}" role="img" aria-label="{html.escape(aria)}" class="schema">\n'
            f'{corps}\n</svg>\n<figcaption>{legende}</figcaption>\n</figure>')


# --- Figure 1 : la chose observee, capturee et annotee ---------------------

def preuve_des_prix():
    """Trois cartes produit du site, cote a cote. Le prix est le meme sur les trois."""
    W, HI, H = 1070, 250, 322
    xs = [8, 371, 733]          # abscisse des trois prix dans la capture
    ligne = HI + 34

    corps = [f'<image href="cartes.png" x="0" y="0" width="{W}" height="{HI}"/>']
    for x in xs:
        corps.append(f'<rect class="cadre" x="{x - 5}" y="33" width="62" height="24" rx="2"/>')
        corps.append(f'<line class="rappel" x1="{x + 26}" y1="59" x2="{x + 26}" y2="{ligne - 2}"/>')
    corps.append(f'<line class="rappel-h" x1="{xs[0] + 26}" y1="{ligne}" x2="{xs[-1] + 26}" y2="{ligne}"/>')
    corps.append(f'<text class="t-annot" x="{xs[0] + 26}" y="{ligne + 24}">'
                 f'le même prix, sur les trois — et sur la moitié du catalogue</text>')

    return figure(f"0 0 {W} {H}", "\n".join(corps),
                  "Trois programmes voisins sur sa page de catalogue, capturés le 23 août 2026. "
                  "Sous chaque titre : le prix, la note, puis deux barres de position. "
                  "Le prix ne distingue rien, les deux barres font tout le travail. "
                  "<a href=\"https://jeffnippard.com/collections/training-programs\">Voir la page</a>.",
                  "Capture de trois fiches produit affichant le même prix de quarante-neuf dollars "
                  "quatre-vingt-dix-neuf, chacune suivie de deux barres de position, "
                  "l'une pour le niveau, l'autre pour l'objectif.")


# --- Figure 2 : la chronologie des prix, calculee --------------------------

def chronologie_des_prix(catalogue):
    """Un point par produit. Exclut la carte cadeau, dont le montant est choisi par l'acheteur."""
    pts = sorted((p["publie"], min(float(v) for v in p["prix"]), p["titre"])
                 for p in catalogue if "gift card" not in p["titre"].lower())

    W, H = 640, 330
    GA, GD, GH, GB = 48, 118, 26, 44
    d0, d1 = _jour(pts[0][0]), _jour(pts[-1][0])
    span = (d1 - d0).days or 1
    pmax = 110.0

    def px(d): return GA + (_jour(d) - d0).days / span * (W - GA - GD)
    def py(p): return H - GB - (p / pmax) * (H - GH - GB)

    corps = []
    for prix in (0, 25, 50, 75, 100):
        y = py(prix)
        corps.append(f'<line class="grille" x1="{GA}" y1="{y:.1f}" x2="{W - GD}" y2="{y:.1f}"/>')
        corps.append(f'<text class="t-axe" x="{GA - 12}" y="{y + 5:.1f}" text-anchor="end">{prix} $</text>')

    y49 = py(49.99)
    corps.append(f'<line class="ligne-cle" x1="{GA}" y1="{y49:.1f}" x2="{W - GD + 6}" y2="{y49:.1f}"/>')
    corps.append(f'<text class="t-cle" x="{W - GD + 16}" y="{y49 - 6:.1f}">49,99 $</text>')
    corps.append(f'<text class="t-annot-s" x="{W - GD + 16}" y="{y49 + 14:.1f}">jamais augmenté</text>')
    corps.append(f'<text class="t-annot-s" x="{W - GD + 16}" y="{y49 + 30:.1f}">en quatre ans</text>')

    for a in sorted({p[0][:4] for p in pts}):
        x = px(min(p[0] for p in pts if p[0][:4] == a))
        corps.append(f'<line class="grille-v" x1="{x:.1f}" y1="{GH}" x2="{x:.1f}" y2="{H - GB}"/>')
        corps.append(f'<text class="t-axe" x="{x:.1f}" y="{H - GB + 22}" text-anchor="middle">{a}</text>')

    # le bloc de mars 2022 : neuf produits sous trente dollars, jamais reconduits
    bas = [p for p in pts if p[1] < 30]
    if bas:
        x = px(bas[0][0])
        y_haut, y_bas = py(max(p[1] for p in bas)), py(min(p[1] for p in bas))
        corps.append(f'<rect class="zone" x="{x - 16:.1f}" y="{y_haut - 12:.1f}" width="32" '
                     f'height="{y_bas - y_haut + 24:.1f}" rx="3"/>')
        corps.append(f'<line class="rappel" x1="{x + 18:.1f}" y1="{(y_haut + y_bas) / 2:.1f}" '
                     f'x2="{x + 70:.1f}" y2="{(y_haut + y_bas) / 2:.1f}"/>')
        corps.append(f'<text class="t-annot" x="{x + 78:.1f}" y="{(y_haut + y_bas) / 2 - 3:.1f}">'
                     f'{len(bas)} produits sous 30 $,</text>')
        corps.append(f'<text class="t-annot" x="{x + 78:.1f}" y="{(y_haut + y_bas) / 2 + 15:.1f}">'
                     f'tous le même jour, aucun depuis</text>')

    for d, prix, titre in pts:
        cle = abs(prix - 49.99) < 0.01
        corps.append(f'<circle class="{"pt-cle" if cle else "pt"}" cx="{px(d):.1f}" '
                     f'cy="{py(prix):.1f}" r="{5 if cle else 3.6}"><title>'
                     f'{html.escape(titre)} — {prix:.2f} $ — {d}</title></circle>')

    return figure(f"0 0 {W} {H}", "\n".join(corps),
                  "Le catalogue entier, un point par produit, à sa date de mise en vente. "
                  "Cette figure est calculée depuis le catalogue archivé : elle ne peut pas montrer "
                  "un produit qui n’existe pas. Chaque point donne son titre et sa date au survol.",
                  "Nuage de points des produits par date et par prix, de deux mille vingt-deux à "
                  "deux mille vingt-six. La quasi-totalité des points récents se pose sur une ligne "
                  "horizontale à quarante-neuf dollars quatre-vingt-dix-neuf.")


# --- Figure 3 : ce que le prix ne dit pas, et que les filtres disent -------

def distribution_du_catalogue(groupes):
    """Barres horizontales, valeurs relevees telles qu'affichees par les filtres du site."""
    W = 1000
    LIG, TITRE, MARGE = 42, 40, 26
    GA, GD = 210, 170
    H = MARGE * 2 + sum(TITRE + LIG * len(v) for v in groupes.values())
    vmax = max(v for g in groupes.values() for _, v in g)

    corps, y = [], MARGE
    for titre, lignes in groupes.items():
        corps.append(f'<text class="t-groupe" x="0" y="{y + 14}">{html.escape(titre)}</text>')
        y += TITRE
        for nom, val in lignes:
            L = (W - GA - GD) * val / vmax
            corps.append(f'<text class="t-axe" x="{GA - 16}" y="{y + 20}" text-anchor="end">'
                         f'{html.escape(nom)}</text>')
            corps.append(f'<rect class="barre-fond" x="{GA}" y="{y + 7}" '
                         f'width="{W - GA - GD}" height="17" rx="1"/>')
            corps.append(f'<rect class="barre" x="{GA}" y="{y + 7}" width="{L:.1f}" height="17" rx="1"/>')
            corps.append(f'<text class="t-val" x="{GA + L + 12:.1f}" y="{y + 20}">{val}</text>')
            y += LIG
    return figure(f"0 0 {W} {H}", "\n".join(corps),
                  "Ce que les filtres du site comptent, relevé tel qu’affiché. La somme dépasse le "
                  "nombre de programmes de la collection : un même programme est compté sur "
                  "plusieurs niveaux. Nous n’expliquons pas cet écart, nous le signalons. "
                  "<a href=\"https://jeffnippard.com/collections/training-programs\">Voir les filtres</a>.",
                  "Barres horizontales du nombre de programmes par niveau couvert et par objectif, "
                  "telles que les filtres du site les comptent.")


def charger_catalogue(racine):
    f = pathlib.Path(racine) / "public" / "data" / "collectes" / "jeff-nippard" / "collecte.json"
    return json.loads(f.read_text(encoding="utf-8"))["catalogue"]


# --- Le SVG telechargeable -------------------------------------------------

STYLE_AUTONOME = """
  <style>
    text { font-family: Archivo, Helvetica, Arial, sans-serif; }
    .grille { stroke: #22262D; } .grille-v { stroke: #22262D; stroke-dasharray: 2 4; }
    .ligne-cle { stroke: #93A9F4; stroke-width: 1.4; stroke-dasharray: 5 4; }
    .zone { fill: none; stroke: #93A9F4; stroke-width: 1; stroke-dasharray: 3 3; }
    .rappel { stroke: #93A9F4; stroke-width: 1; }
    .pt { fill: #545B69; } .pt-cle { fill: #93A9F4; }
    .t-axe { fill: #7C8493; font-size: 13px; font-family: monospace; }
    .t-cle { fill: #93A9F4; font-size: 15px; font-weight: 600; }
    .t-annot { fill: #B9BFCA; font-size: 13px; }
    .t-annot-s { fill: #7C8493; font-size: 12px; }
  </style>
"""


def svg_autonome(fig_html):
    svg = fig_html[fig_html.index("<svg"):fig_html.index("</svg>") + 6]
    svg = svg.replace("<svg ", '<svg xmlns="http://www.w3.org/2000/svg" '
                      'style="background:#0A0B0D" ', 1)
    i = svg.index(">") + 1
    return '<?xml version="1.0" encoding="UTF-8"?>\n' + svg[:i] + STYLE_AUTONOME + svg[i:] + "\n"
