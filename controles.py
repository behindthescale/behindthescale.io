#!/usr/bin/env python3
"""Les controles au build (Standards/ressources-publiques/protocole-tracabilite.md).

Un seul qui echoue et rien ne part. Ce fichier ne rend jamais un verdict nuance :
il leve EchecControle, ou il se tait.
"""

import re

# Champs obligatoires sur tout repere, quel que soit son etat (C1, C14).
CHAMPS_REQUIS = [
    "id", "question", "etape", "etat", "cout_de_lecture",
    "notre_interet", "citation_suggeree", "date_consultation",
    "version", "liens_sortants",
]

# Attributs obligatoires de tout objet chiffre (C2).
ATTRS_CHIFFRE = ["id", "valeur", "unite", "libelle", "source"]

# Attributs obligatoires de toute source de famille « mesure » (P1).
ATTRS_MESURE = [
    "titre", "auteurs", "reference", "url", "n", "terrain",
    "methode_consultable", "acces_ouvert", "interet", "beneficiaire",
]

# Champs rediges soumis a l'interdiction de nombre libre (C3).
CHAMPS_REDIGES = [
    "reponse", "limites", "lecture_inversion", "limite_inversion", "notre_interet",
]

ANCRE = re.compile(r"\{\{c:([a-z0-9_]+)\}\}")


class EchecControle(Exception):
    """Un controle a echoue. La construction s'arrete, rien n'est publie."""


def _echec(repere_id, controle, message):
    raise EchecControle(f"[{repere_id}] {controle} : {message}")


def c1_champs_requis(r):
    for champ in CHAMPS_REQUIS:
        if not r.get(champ):
            _echec(r.get("id", "?"), "C1", f"champ obligatoire absent ou vide : {champ}")
    if r["etat"] not in ("mesure", "norme", "zone_blanche"):
        _echec(r["id"], "C1", f"etat inconnu : {r['etat']}")


def c2_attributs_chiffres(r):
    """Tout chiffre porte ses attributs, et sa source existe et est complete."""
    sources = {s["id"]: s for s in r.get("sources", [])}
    for c in r.get("chiffres", []):
        for attr in ATTRS_CHIFFRE:
            if c.get(attr) in (None, ""):
                _echec(r["id"], "C2", f"chiffre '{c.get('id', '?')}' sans attribut {attr}")
        if c["source"] not in sources:
            _echec(r["id"], "C2", f"chiffre '{c['id']}' renvoie a une source inconnue : {c['source']}")
    for s in sources.values():
        if s.get("famille") != "mesure":
            continue
        for attr in ATTRS_MESURE:
            if s.get(attr) in (None, ""):
                _echec(r["id"], "C2", f"source '{s['id']}' sans attribut {attr}")


def c3_aucun_nombre_libre(r):
    """Le seul garde-fou mecanique contre l'interdit permanent 4.

    Tout nombre d'un champ redige doit venir d'une ancre {{c:id}} vers un chiffre
    declare. Une exception se declare explicitement dans `nombres_hors_mesure`,
    avec son motif : elle se lit, elle ne se subit pas.
    """
    declares = {c["id"] for c in r.get("chiffres", [])}
    tolere = {str(n["ecrit"]) for n in r.get("nombres_hors_mesure", [])}

    for champ in CHAMPS_REDIGES:
        texte = r.get(champ) or ""
        if isinstance(texte, list):
            texte = " ".join(texte)

        for ref in ANCRE.findall(texte):
            if ref not in declares:
                _echec(r["id"], "C3", f"{champ} ancre un chiffre non declare : {ref}")

        nu = ANCRE.sub(" ", texte)
        for brut in re.findall(r"\d+(?:[\s.,  ]\d+)*", nu):
            nombre = re.sub(r"[\s  ]+", " ", brut).strip()
            if nombre not in tolere:
                _echec(r["id"], "C3",
                       f"nombre libre dans {champ} : « {nombre} ». "
                       f"L'ancrer a un chiffre declare, ou le declarer dans nombres_hors_mesure.")


def c4_niveau_d_interet(r):
    """Un chiffre de niveau 3 ne porte jamais la reponse ; un niveau 2 seul non plus (P4)."""
    if r["etat"] != "mesure":
        return
    sources = {s["id"]: s for s in r.get("sources", [])}
    portants = {c["source"] for c in r.get("chiffres", []) if c.get("porte_la_reponse")}
    if not portants:
        _echec(r["id"], "C4", "etat 'mesure' mais aucun chiffre ne porte la reponse")
    for sid in portants:
        niveau = sources[sid]["interet"]
        if niveau >= 3:
            _echec(r["id"], "C4", f"source '{sid}' de niveau {niveau} en position de reponse")
        if niveau == 2 and len(portants) == 1:
            _echec(r["id"], "C4",
                   f"source '{sid}' de niveau 2 seule en reponse : l'etat doit etre zone_blanche")


def c6_zone_blanche(r):
    """Une zone blanche se publie, mais elle doit dire ce qu'il faudrait pour la combler."""
    if r["etat"] != "zone_blanche":
        if not r.get("chiffres"):
            _echec(r["id"], "C6", "aucun chiffre mais l'etat n'est pas zone_blanche")
        return
    if r.get("chiffres"):
        _echec(r["id"], "C6", "etat zone_blanche mais des chiffres sont declares")
    for champ in ("ce_qu_il_faudrait", "qui_pourrait_le_mesurer"):
        if not r.get(champ):
            _echec(r["id"], "C6", f"zone blanche sans {champ}")


def c11_liens(r):
    if not r.get("liens_sortants"):
        _echec(r["id"], "C11", "aucun lien sortant vers un autre repere")


def c13_inversion(r, deja_vues):
    """La lecture qui manque au champ, et sa limite, sont propres a ce repere.

    Semi-mecanique (protocole, note sur C5/C12/C13) : le script detecte une limite
    recopiee mot pour mot, pas une limite reformulee. Il signale, il ne bloque pas.
    """
    alertes = []
    for champ in ("lecture_inversion", "limite_inversion"):
        texte = (r.get(champ) or "").strip()
        if not texte:
            alertes.append(f"[{r['id']}] C13 : {champ} vide")
            continue
        if texte in deja_vues:
            alertes.append(f"[{r['id']}] C13 : {champ} identique a un autre repere")
        deja_vues.add(texte)
    return alertes


def controler(r, deja_vues=None):
    """Passe tous les controles bloquants. Rend la liste des alertes non bloquantes."""
    deja_vues = deja_vues if deja_vues is not None else set()
    c1_champs_requis(r)
    c2_attributs_chiffres(r)
    c3_aucun_nombre_libre(r)
    c4_niveau_d_interet(r)
    c6_zone_blanche(r)
    c11_liens(r)
    return c13_inversion(r, deja_vues)
