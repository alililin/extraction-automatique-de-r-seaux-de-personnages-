from collections import defaultdict
from pathlib import Path
import json

DOSSIER_NGRAMS = Path("corpus/ngrams")

SORTIE_LISTE = Path(
    "corpus/liste_L.json"
)

SORTIE_LISTE_TEXTE = Path(
    "corpus/liste_L.txt"
)

SEUIL_FREQUENCE = 2


def est_candidat(ngram):
    """
    Construit la liste L des candidats.

    L doit rester volontairement bruitée.
    On retient les n-grams dont le premier token
    commence par une majuscule.
    """

    tokens = ngram.split()

    if not tokens:
        return False

    premier_token = tokens[0]

    if premier_token.startswith("__"):
        return False

    if not premier_token[0].isalpha():
        return False

    return premier_token[0].isupper()


def construire_liste(fichiers):

    candidats = defaultdict(
        lambda: {
            "frequence": 0,
            "livres": []
        }
    )

    for fichier in fichiers:

        donnees = json.loads(
            fichier.read_text(
                encoding="utf-8"
            )
        )

        for taille, ngrams in donnees.items():

            for ngram, frequence in ngrams.items():

                if not est_candidat(ngram):
                    continue

                candidats[ngram][
                    "frequence"
                ] += frequence

                candidats[ngram][
                    "livres"
                ].append(
                    {
                        "livre": fichier.stem,
                        "frequence": frequence,
                        "taille": int(taille),
                    }
                )

    return {
        candidat: informations
        for candidat, informations
        in candidats.items()
        if informations["frequence"]
        >= SEUIL_FREQUENCE
    }


def main():

    fichiers = sorted(
        DOSSIER_NGRAMS.glob("*.json")
    )

    liste = construire_liste(
        fichiers
    )

    liste = dict(
        sorted(
            liste.items(),
            key=lambda element: (
                -element[1]["frequence"],
                element[0].casefold()
            )
        )
    )

    SORTIE_LISTE.write_text(
        json.dumps(
            liste,
            ensure_ascii=False,
            indent=2
        ),
        encoding="utf-8"
    )

    SORTIE_LISTE_TEXTE.write_text(
        "\n".join(liste) + "\n",
        encoding="utf-8"
    )

    print(
        f"Liste L creee : "
        f"{SORTIE_LISTE} "
        f"({len(liste)} candidats)"
    )


if __name__ == "__main__":
    main()