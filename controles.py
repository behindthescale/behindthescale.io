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


# --- Controles propres au decorticage -------------------------------------
# Un decorticage decrit un systeme reel. Ses tentations sont differentes de
# celles d'un repere : combler un trou par une estimation, et decrire un succes
# sans jamais dire quoi en faire.

VERDICTS = {"copiable", "conditionnel", "non_copiable"}

CHAMPS_REQUIS_DECORTICAGE = [
    "id", "titre", "sujet", "cout_de_lecture", "date_observation",
    "version", "resume", "invisible", "citation_suggeree",
]

CHAMPS_REDIGES_DECORTICAGE = [
    "resume", "invisible", "fait", "pourquoi", "verdict_texte", "actions",
]


def d1_champs(r):
    for champ in CHAMPS_REQUIS_DECORTICAGE:
        if not r.get(champ):
            _echec(r.get("id", "?"), "D1", f"champ obligatoire absent ou vide : {champ}")


def d2_verdicts(r):
    """Chaque decision porte un verdict, et il rend la page actionnable.

    Sans verdict, on decrit un succes : c'est ce que fait deja tout le champ.
    """
    decisions = r.get("decisions", [])
    if not 3 <= len(decisions) <= 9:
        _echec(r["id"], "D2", f"{len(decisions)} decisions ; il en faut entre 3 et 9")
    for d in decisions:
        for champ in ("titre", "fait", "pourquoi", "verdict", "verdict_texte", "preuve"):
            if not d.get(champ):
                _echec(r["id"], "D2", f"decision '{d.get('id', '?')}' sans {champ}")
        if d["verdict"] not in VERDICTS:
            _echec(r["id"], "D2",
                   f"decision '{d['id']}' : verdict '{d['verdict']}' hors des trois valeurs admises")


def d3_preuves(r):
    """Toute affirmation sur le systeme observe renvoie a une preuve datee."""
    for d in r.get("decisions", []):
        p = d["preuve"]
        for champ in ("quoi", "url", "date"):
            if not p.get(champ):
                _echec(r["id"], "D3", f"decision '{d['id']}' : preuve sans {champ}")


def d4_actions(r):
    """Trois actions, pas dix. Une liste longue ne se fait pas."""
    a = r.get("actions", [])
    if len(a) != 3:
        _echec(r["id"], "D4", f"{len(a)} actions ; il en faut exactement trois")


def d5_nombres_libres(r):
    """C3 applique aux champs rediges du decorticage, decisions comprises."""
    declares = {c["id"] for c in r.get("chiffres", [])}
    tolere = {str(n["ecrit"]) for n in r.get("nombres_hors_mesure", [])}

    textes = [(champ, r.get(champ)) for champ in ("resume", "invisible")]
    textes += [("actions", " ".join(r.get("actions", [])))]
    for d in r.get("decisions", []):
        for champ in ("titre", "fait", "pourquoi", "verdict_texte"):
            textes.append((f'{d["id"]}.{champ}', d.get(champ)))

    for champ, texte in textes:
        texte = texte or ""
        for ref in ANCRE.findall(texte):
            if ref not in declares:
                _echec(r["id"], "D5", f"{champ} ancre un chiffre non declare : {ref}")
        nu = ANCRE.sub(" ", texte)
        for brut in re.findall(r"\d+(?:[\s.,  ]\d+)*", nu):
            nombre = re.sub(r"[\s  ]+", " ", brut).strip()
            if nombre not in tolere:
                _echec(r["id"], "D5",
                       f"nombre libre dans {champ} : « {nombre} ». "
                       f"L'ancrer a un chiffre declare, ou le declarer dans nombres_hors_mesure.")


def controler_decorticage(r):
    d1_champs(r)
    d2_verdicts(r)
    d3_preuves(r)
    d4_actions(r)
    d5_nombres_libres(r)
    c2_attributs_chiffres(r)


# --- Controles d'un chapitre et de ses items -------------------------------
# Un chapitre accueille cinq types d'item. Le contrat par type est ce qui
# permet d'ajouter un sujet nouveau sans casser le gabarit.

TYPES_ITEM = {"mesure", "zone_blanche", "principe", "cas", "a_rediger"}

CHAMPS_PAR_TYPE = {
    "mesure":       ["texte", "verifie_le"],
    "zone_blanche": ["ce_qu_il_faudrait", "qui_pourrait_le_mesurer", "verifie_le"],
    "principe":     ["texte", "fondement", "verifie_le"],
    "cas":          ["texte", "cas_slug", "verifie_le"],
    "a_rediger":    ["etat_estime"],
}

CHAMPS_OUTIL = ["nom", "fait", "pourquoi", "url", "verifie_le"]

# Champs rediges d'un item, soumis a l'interdiction de nombre libre.
REDIGES_ITEM = ["texte", "fondement", "ce_qu_il_faudrait", "qui_pourrait_le_mesurer"]

DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def ch1_structure(ch):
    """Le chapitre porte son numero, son nom, son etat et ses items."""
    for champ in ("n", "slug", "titre", "etat", "items"):
        if ch.get(champ) in (None, "", []):
            if champ == "items" and ch.get("etat") == "annonce":
                continue
            _echec(ch.get("slug", "?"), "CH1", f"chapitre sans {champ}")
    if ch["etat"] not in ("complet", "en_cours", "annonce"):
        _echec(ch["slug"], "CH1", f"etat de chapitre inconnu : {ch['etat']}")


def ch2_types(ch):
    """Chaque item declare un type admis et porte les champs de ce type."""
    for it in ch.get("items", []):
        t = it.get("type")
        if t not in TYPES_ITEM:
            _echec(ch["slug"], "CH2", f"item '{it.get('id', '?')}' de type inconnu : {t}")
        if not it.get("titre"):
            _echec(ch["slug"], "CH2", f"item '{it.get('id', '?')}' sans titre")
        for champ in CHAMPS_PAR_TYPE[t]:
            if it.get(champ) in (None, "", []):
                _echec(ch["slug"], "CH2",
                       f"item '{it['id']}' de type {t} sans {champ}")


def ch3_fraicheur(ch):
    """Une date de verification lisible, ou rien ne se publie (P10).

    Un item 'a_rediger' n'affirme rien : il est dispense, et c'est pour ca
    qu'il ne peut porter aucun texte.
    """
    for it in ch.get("items", []):
        if it["type"] == "a_rediger":
            if it.get("texte"):
                _echec(ch["slug"], "CH3",
                       f"item '{it['id']}' est a rediger mais porte deja un texte : "
                       f"le publier suppose de le sourcer d'abord")
            continue
        d = it.get("verifie_le") or ""
        if not DATE.match(d):
            _echec(ch["slug"], "CH3", f"item '{it['id']}' : verifie_le illisible ({d!r})")


def ch4_outils(ch):
    """Un outil dit ce qu'il fait, pourquoi lui, et ce qu'il ne fait pas.

    Un prix sans date de relevé est un chiffre orphelin (P7) : il est refuse.
    """
    for o in ch.get("outils", []):
        for champ in CHAMPS_OUTIL:
            if o.get(champ) in (None, "", []):
                _echec(ch["slug"], "CH4", f"outil '{o.get('nom', '?')}' sans {champ}")
        if o.get("prix") and not DATE.match(o.get("prix_verifie_le") or ""):
            _echec(ch["slug"], "CH4",
                   f"outil '{o['nom']}' affiche un prix sans date de releve lisible")
        if not o.get("ne_fait_pas"):
            _echec(ch["slug"], "CH4",
                   f"outil '{o['nom']}' sans 'ne_fait_pas' : un outil qu'on ne borne pas "
                   f"est une recommandation deguisee")


def ch5_nombres_libres(ch):
    """C3 etendu aux champs rediges des items et des outils."""
    for it in ch.get("items", []):
        declares = {c["id"] for c in it.get("chiffres", [])}
        tolere = {str(n["ecrit"]) for n in it.get("nombres_hors_mesure", [])}
        for champ in REDIGES_ITEM:
            texte = it.get(champ) or ""
            for ref in ANCRE.findall(texte):
                if ref not in declares:
                    _echec(ch["slug"], "CH5",
                           f"item '{it['id']}' {champ} ancre un chiffre non declare : {ref}")
            nu = ANCRE.sub(" ", texte)
            for brut in re.findall(r"\d+(?:[\s.,  ]\d+)*", nu):
                nombre = re.sub(r"[\s  ]+", " ", brut).strip()
                if nombre not in tolere:
                    _echec(ch["slug"], "CH5",
                           f"nombre libre dans l'item '{it['id']}' ({champ}) : « {nombre} »")


def ch6_cas_existants(ch, cas_connus):
    for it in ch.get("items", []):
        if it["type"] == "cas" and it["cas_slug"] not in cas_connus:
            _echec(ch["slug"], "CH6", f"item '{it['id']}' renvoie a un cas absent : {it['cas_slug']}")


def controler_chapitre(ch, cas_connus=()):
    ch1_structure(ch)
    ch2_types(ch)
    ch3_fraicheur(ch)
    ch4_outils(ch)
    ch5_nombres_libres(ch)
    ch6_cas_existants(ch, set(cas_connus))
