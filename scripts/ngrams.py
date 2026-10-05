from collections import Counter
from pathlib import Path
import json

DOSSIER_TOKENISE = Path("corpus/tokenise")
DOSSIER_NGRAMS = Path("corpus/ngrams")

TAILLES_NGRAMS = (1, 2, 3)

MARQUEUR_PHRASE = "__FIN_PHRASE__"


def creer_ngrams(tokens, taille):
    """
    Construit les n-grams sans traverser une fin de phrase.
    """

    compte = Counter()

    phrase = []

    for token in tokens:

        if token == MARQUEUR_PHRASE:

            if phrase:

                for position in range(
                    len(phrase) - taille + 1
                ):

                    groupe = " ".join(
                        phrase[
                            position:
                            position + taille
                        ]
                    )

                    compte[groupe] += 1

            phrase = []

        else:
            phrase.append(token)

    # Dernière phrase du fichier
    if phrase:

        for position in range(
            len(phrase) - taille + 1
        ):

            groupe = " ".join(
                phrase[
                    position:
                    position + taille
                ]
            )

            compte[groupe] += 1

    return compte


def main():

    DOSSIER_NGRAMS.mkdir(
        parents=True,
        exist_ok=True
    )

    fichiers = sorted(
        DOSSIER_TOKENISE.glob("*.json")
    )

    print(
        f"Fichiers trouves : {len(fichiers)}"
    )

    for fichier in fichiers:

        tokens = json.loads(
            fichier.read_text(
                encoding="utf-8"
            )
        )

        resultats = {}

        for taille in TAILLES_NGRAMS:

            compte = creer_ngrams(
                tokens,
                taille
            )

            resultats[str(taille)] = dict(
                compte
            )

        sortie = (
            DOSSIER_NGRAMS
            / fichier.name
        )

        sortie.write_text(
            json.dumps(
                resultats,
                ensure_ascii=False,
                indent=2
            ),
            encoding="utf-8"
        )

        print(
            f"{fichier.name} -> {sortie}"
        )


if __name__ == "__main__":
    main()