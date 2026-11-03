from collections import Counter, defaultdict
from pathlib import Path
import json

from antidictionnaire import est_mot_vide


DOSSIER_TOKENISE = Path("corpus/tokenise")

SOURCE_LN = Path("corpus/liste_L_filtre.json")   # base des personnages
SOURCE_LL = Path("corpus/liste_L.json")          # base des lieux (non filtrée)

SORTIE_LN = Path("corpus/liste_LN.json")
SORTIE_LN_TEXTE = Path("corpus/liste_LN.txt")
SORTIE_LL = Path("corpus/liste_LL.json")
SORTIE_LL_TEXTE = Path("corpus/liste_LL.txt")

MARQUEUR_PHRASE = "__FIN_PHRASE__"

# --------------------------------------------------
# SEUILS (à ajuster en regardant les résultats)
# --------------------------------------------------

# Part des occurrences d'un candidat où l'on trouve un indice "personne"
# (titre avant, verbe de parole/geste après).
SEUIL_PERSONNE = 0.10

# Part des occurrences précédées d'une préposition de lieu.
SEUIL_LIEU = 0.20

# Pour LL : le mot doit être très majoritairement écrit avec majuscule.
RATIO_MIN_LL = 0.3

# --------------------------------------------------
# INDICES LINGUISTIQUES (ressources, pas des mots du corpus)
# --------------------------------------------------

# "à" est volontairement absent : "à Terminus" (lieu) mais aussi
# "dit à Hardin" (personne).
PREPOSITIONS_LIEU = {
    "sur", "vers", "dans", "depuis", "jusqu'", "près", "hors",
    "autour", "en",
}

TITRES = {
    "m", "mm", "mme", "mlle", "dr", "docteur", "monsieur", "madame",
    "mademoiselle", "maire", "lord", "empereur", "seigneur", "capitaine",
    "commandant", "général", "amiral", "sire", "professeur", "prince",
    "princesse", "roi", "reine", "consul", "ministre", "sergent",
    "colonel", "lieutenant", "maître", "père", "frère", "oncle", "tante",
    "orateur", "commissaire", "marchand", "ambassadeur", "ingénieur",
}

VERBES_PAROLE = {
    "dit", "répondit", "demanda", "murmura", "fit", "ajouta", "déclara",
    "répliqua", "reprit", "lança", "continua", "écria", "annonça",
    "observa", "remarqua", "grommela", "soupira", "sourit", "haussa",
    "hocha", "secoua", "regarda", "pensa", "songea", "répéta", "cria",
    "rit", "acquiesça", "protesta", "intervint", "commença", "voulut",
}


# --------------------------------------------------
# CONTEXTES DANS LE CORPUS
# --------------------------------------------------

def collecter_contextes(candidats):
    """
    Pour chaque candidat : nombre d'occurrences, et combien sont
    précédées d'un titre / d'une préposition de lieu / suivies d'un verbe
    de parole. Parcourt le corpus tokenisé (avec majuscules).
    """
    tailles = sorted({len(c.split()) for c in candidats})
    stats = defaultdict(Counter)

    for fichier in sorted(DOSSIER_TOKENISE.glob("*.json")):
        tokens = json.loads(fichier.read_text(encoding="utf-8"))
        n = len(tokens)

        for i in range(n):
            for taille in tailles:
                fin = i + taille

                if fin > n:
                    break

                morceau = tokens[i:fin]

                if MARQUEUR_PHRASE in morceau:
                    break

                ngram = " ".join(morceau)

                if ngram not in candidats:
                    continue

                gauche = tokens[i - 1].casefold() if i > 0 else ""
                droite = tokens[fin].casefold() if fin < n else ""

                s = stats[ngram]
                s["occ"] += 1

                if gauche in TITRES:
                    s["titre"] += 1
                if gauche in PREPOSITIONS_LIEU:
                    s["lieu"] += 1
                if droite in VERBES_PAROLE:
                    s["parole"] += 1

    return stats


def ratios(s):
    occ = s["occ"] or 1
    return (s["titre"] + s["parole"]) / occ, s["lieu"] / occ


def est_personne(s):
    ratio_personne, ratio_lieu = ratios(s)
    return ratio_personne >= SEUIL_PERSONNE and ratio_lieu < SEUIL_LIEU


def est_lieu(s):
    ratio_personne, ratio_lieu = ratios(s)
    return ratio_lieu >= SEUIL_LIEU and ratio_lieu > ratio_personne


def forme_lieu_valide(candidat, informations):
    """Écarte le bruit évident avant de classer un lieu."""
    tokens = candidat.split()

    if candidat.isupper() or any(c.isdigit() for c in candidat):
        return False

    if informations.get("ratio_majuscule", 1.0) < RATIO_MIN_LL:
        return False

    return not (est_mot_vide(tokens[0]) or est_mot_vide(tokens[-1]))


# --------------------------------------------------
# REGROUPEMENT DES VARIANTES (Hari / Seldon / Hari Seldon)
# --------------------------------------------------

def contient(long_, court):
    n = len(court)
    return any(
        long_[i:i + n] == court
        for i in range(len(long_) - n + 1)
    )


def regrouper(selection, stats):
    """
    Rattache chaque forme courte à la forme longue qui la contient.
    Le nombre de mentions = plus grande fréquence des formes du groupe
    (une forme courte inclut déjà les occurrences de la forme longue).
    """
    formes = sorted(
        selection,
        key=lambda c: (
            -len(c.split()),
            -selection[c]["frequence"],
            c,
        ),
    )

    entites = []

    for forme in formes:
        tokens = tuple(forme.split())
        frequence = selection[forme]["frequence"]
        parent = None

        for entite in entites:
            if (
                len(tokens) < len(entite["tokens"])
                and contient(entite["tokens"], tokens)
                and (parent is None or entite["mentions"] > parent["mentions"])
            ):
                parent = entite

        if parent is not None:
            parent["variantes"].append(forme)
            parent["mentions"] = max(parent["mentions"], frequence)
        else:
            entites.append(
                {
                    "nom": forme,
                    "tokens": tokens,
                    "mentions": frequence,
                    "variantes": [],
                }
            )

    entites.sort(key=lambda e: (-e["mentions"], e["nom"].casefold()))

    for entite in entites:
        entite.pop("tokens")
        entite["contexte"] = dict(stats[entite["nom"]])

    return entites


# --------------------------------------------------
# SORTIES
# --------------------------------------------------

def ecrire(entites, sortie_json, sortie_texte):
    sortie_json.write_text(
        json.dumps(entites, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    sortie_texte.write_text(
        "".join(
            f"{e['nom']}\t{e['mentions']}\t{';'.join(e['variantes'])}\n"
            for e in entites
        ),
        encoding="utf-8",
    )


def main():
    for source in (SOURCE_LN, SOURCE_LL):
        if not source.exists():
            raise SystemExit(f"Fichier introuvable : {source}")

    liste_ln = json.loads(SOURCE_LN.read_text(encoding="utf-8"))
    liste_ll = json.loads(SOURCE_LL.read_text(encoding="utf-8"))

    candidats = set(liste_ln) | set(liste_ll)
    print(f"Candidats analysés : {len(candidats)}")

    stats = collecter_contextes(candidats)

    personnages = {
        c: infos
        for c, infos in liste_ln.items()
        if est_personne(stats[c])
    }

    lieux = {
        c: infos
        for c, infos in liste_ll.items()
        if c not in personnages
        and forme_lieu_valide(c, infos)
        and est_lieu(stats[c])
    }

    entites_ln = regrouper(personnages, stats)
    entites_ll = regrouper(lieux, stats)

    ecrire(entites_ln, SORTIE_LN, SORTIE_LN_TEXTE)
    ecrire(entites_ll, SORTIE_LL, SORTIE_LL_TEXTE)

    print(f"LN : {SORTIE_LN} ({len(entites_ln)} personnages)")
    print(f"LL : {SORTIE_LL} ({len(entites_ll)} lieux)")


if __name__ == "__main__":
    main()