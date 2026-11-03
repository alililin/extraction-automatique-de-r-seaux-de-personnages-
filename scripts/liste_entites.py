from collections import Counter, defaultdict
from pathlib import Path
import json

DOSSIER_NGRAMS = Path("corpus/ngrams")

SORTIE_LISTE = Path("corpus/liste_L.json")
SORTIE_LISTE_TEXTE = Path("corpus/liste_L.txt")

SEUIL_FREQUENCE = 2

# Mots minuscules autorisés AU MILIEU d'un candidat :
# "Fondation et Empire", "Cité de l' Étoile"...
PARTICULES = {"de", "du", "des", "la", "le", "les", "l'", "d'", "et"}


def commence_par_majuscule(token):
    return token[:1].isalpha() and token[0].isupper()


def est_candidat(ngram):
    """
    Un candidat commence ET finit par un mot à majuscule ;
    les mots du milieu doivent avoir une majuscule ou être une particule.
    L reste volontairement bruitée : aucun filtrage par mot vide ici.
    """
    tokens = ngram.split()

    if not tokens:
        return False

    if not commence_par_majuscule(tokens[0]):
        return False

    if not commence_par_majuscule(tokens[-1]):
        return False

    return all(
        commence_par_majuscule(t) or t.casefold() in PARTICULES
        for t in tokens[1:-1]
    )


def calculer_stats_majuscule(donnees_par_livre):
    """
    Pour chaque mot : part de ses occurrences écrites avec majuscule.
    "Seldon" -> ~1.0 ; "Il", "Mais" -> faible (début de phrase seulement).
    Calculé sur les unigrammes de tout le corpus.
    """
    avec_majuscule = Counter()
    total = Counter()

    for _, donnees in donnees_par_livre:
        for mot, frequence in donnees.get("1", {}).items():
            cle = mot.casefold()
            total[cle] += frequence
            if commence_par_majuscule(mot):
                avec_majuscule[cle] += frequence

    return avec_majuscule, total


def ratio_majuscule(ngram, avec_majuscule, total):
    """Ratio du mot à majuscule le moins "propre" du candidat."""
    ratios = []

    for token in ngram.split():
        if commence_par_majuscule(token):
            cle = token.casefold()
            if total[cle]:
                ratios.append(avec_majuscule[cle] / total[cle])

    return round(min(ratios), 3) if ratios else 0.0


def construire_liste(donnees_par_livre):
    avec_majuscule, total = calculer_stats_majuscule(donnees_par_livre)

    candidats = defaultdict(lambda: {"frequence": 0, "livres": []})

    for livre, donnees in donnees_par_livre:
        for ngrams in donnees.values():
            for ngram, frequence in ngrams.items():
                if not est_candidat(ngram):
                    continue

                candidats[ngram]["frequence"] += frequence
                candidats[ngram]["livres"].append(
                    {"livre": livre, "frequence": frequence}
                )

    resultat = {}

    for ngram, infos in candidats.items():
        if infos["frequence"] < SEUIL_FREQUENCE:
            continue

        resultat[ngram] = {
            "frequence": infos["frequence"],
            "taille": len(ngram.split()),
            "ratio_majuscule": ratio_majuscule(
                ngram, avec_majuscule, total
            ),
            "livres": infos["livres"],
        }

    return resultat


def main():
    fichiers = sorted(DOSSIER_NGRAMS.glob("*.json"))

    if not fichiers:
        raise SystemExit(f"Aucun fichier JSON dans {DOSSIER_NGRAMS}")

    donnees_par_livre = [
        (f.stem, json.loads(f.read_text(encoding="utf-8")))
        for f in fichiers
    ]

    liste = construire_liste(donnees_par_livre)

    liste = dict(
        sorted(
            liste.items(),
            key=lambda e: (-e[1]["frequence"], e[0].casefold()),
        )
    )

    SORTIE_LISTE.write_text(
        json.dumps(liste, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    SORTIE_LISTE_TEXTE.write_text(
        "".join(
            f"{ngram}\t{infos['frequence']}\n"
            for ngram, infos in liste.items()
        ),
        encoding="utf-8",
    )

    print(
        f"Liste L créée : {SORTIE_LISTE} ({len(liste)} candidats)"
    )


if __name__ == "__main__":
    main()