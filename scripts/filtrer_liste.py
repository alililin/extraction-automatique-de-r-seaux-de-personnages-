from pathlib import Path
import json

from antidictionnaire import MOTS_VIDES


SOURCE_LISTE = Path(
    "corpus/liste_L.json"
)

SORTIE_LISTE = Path(
    "corpus/liste_L_filtre.json"
)

SORTIE_LISTE_TEXTE = Path(
    "corpus/liste_L_filtre.txt"
)


PREFIXES_CONTRACTION = (
    "c'",
    "d'",
    "j'",
    "l'",
    "m'",
    "n'",
    "qu'",
    "s'",
    "t'",
    "ce n'",
    "cen'",
    "je ",
    "il ",
    "elle ",
    "on ",
    "nous ",
    "vous ",
)


def est_bruit(candidat):

    tokens = candidat.split()

    if not tokens:
        return True

    candidat_normalise = candidat.casefold()

    premier_token = tokens[0].casefold()

    # Candidat entièrement présent dans l'antidictionnaire
    if candidat_normalise in MOTS_VIDES:
        return True

    # Premier mot fonctionnel
    if premier_token in MOTS_VIDES:
        return True

    # Un mot fonctionnel dans le reste du candidat
    if any(
        token.casefold() in MOTS_VIDES
        for token in tokens[1:]
    ):
        return True

    # Contractions / débuts de phrases
    if candidat_normalise.startswith(
        PREFIXES_CONTRACTION
    ):
        return True

    # Acronymes / mots entièrement en majuscules
    if candidat.isupper():
        return True

    # Candidats contenant un nombre
    if any(
        char.isdigit()
        for char in candidat
    ):
        return True

    return False


def main():

    liste = json.loads(
        SOURCE_LISTE.read_text(
            encoding="utf-8"
        )
    )

    liste_filtree = {
        candidat: informations
        for candidat, informations
        in liste.items()
        if not est_bruit(candidat)
    }

    SORTIE_LISTE.write_text(
        json.dumps(
            liste_filtree,
            ensure_ascii=False,
            indent=2
        ),
        encoding="utf-8"
    )

    SORTIE_LISTE_TEXTE.write_text(
        "\n".join(liste_filtree) + "\n",
        encoding="utf-8"
    )

    print(
        f"Liste L filtree : "
        f"{SORTIE_LISTE} "
        f"({len(liste_filtree)} candidats)"
    )


if __name__ == "__main__":
    main()