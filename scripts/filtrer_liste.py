from pathlib import Path
import json

# Réutilise la logique de antidictionnaire.py : elle gère "l'", "qu'",
# "peut-être", "aujourd'hui"... (le fichier doit être dans le même dossier)
from antidictionnaire import est_mot_vide


SOURCE_LISTE = Path("corpus/liste_L.json")
SORTIE_LISTE = Path("corpus/liste_L_filtre.json")
SORTIE_LISTE_TEXTE = Path("corpus/liste_L_filtre.txt")

# Part minimale des occurrences écrites avec majuscule.
# "Seldon" ~ 1.0 ; "Murmura", "Quelquefois" ~ 0.0 (début de phrase seulement).
# Pour LL (Empire, Galaxie...) on pourra descendre ce seuil.
RATIO_MIN = 0.5

# False : tout mot vide (même au milieu) élimine le candidat.
# True  : on tolère les particules au milieu ("Fondation et Empire").
GARDER_PARTICULES = False
PARTICULES = {"de", "du", "des", "la", "le", "les", "l'", "d'", "et"}


def est_bruit(candidat, informations):
    tokens = candidat.split()

    if not tokens:
        return True

    # Acronymes / mots entièrement en majuscules ("II", "A")
    if candidat.isupper():
        return True

    # Candidats contenant un nombre
    if any(char.isdigit() for char in candidat):
        return True

    # Mot trop souvent en minuscule : majuscule de début de phrase
    if informations.get("ratio_majuscule", 1.0) < RATIO_MIN:
        return True

    # Mots vides (premier, milieu ou dernier mot)
    dernier = len(tokens) - 1

    for position, token in enumerate(tokens):
        if not est_mot_vide(token):
            continue

        if (
            GARDER_PARTICULES
            and 0 < position < dernier
            and token.casefold() in PARTICULES
        ):
            continue

        return True

    return False


def main():
    liste = json.loads(SOURCE_LISTE.read_text(encoding="utf-8"))

    liste_filtree = {
        candidat: informations
        for candidat, informations in liste.items()
        if not est_bruit(candidat, informations)
    }

    SORTIE_LISTE.write_text(
        json.dumps(liste_filtree, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    SORTIE_LISTE_TEXTE.write_text(
        "".join(
            f"{candidat}\t{infos['frequence']}\n"
            for candidat, infos in liste_filtree.items()
        ),
        encoding="utf-8",
    )

    print(
        f"Liste L filtrée : {SORTIE_LISTE} "
        f"({len(liste)} -> {len(liste_filtree)} candidats)"
    )


if __name__ == "__main__":
    main()