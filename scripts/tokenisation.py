from pathlib import Path
import json
import re

DOSSIER_NETTOYE = Path("corpus/nettoyage")
DOSSIER_TOKENISE = Path("corpus/tokenise")

MARQUEUR_PHRASE = "__FIN_PHRASE__"

MOTIF_TOKEN = re.compile(
    r"[A-Za-zÀ-ÿ]+(?:['’-][A-Za-zÀ-ÿ]+)*|\d+(?:[.,]\d+)?"
)

MOTIF_PHRASE = re.compile(
    r"(?<=[.!?…])(?:[\"»”')\]]+)?\s+"
)


def tokeniser(texte):
    """
    Transforme le texte en tokens.

    Le marqueur __FIN_PHRASE__ permet de conserver
    l'information de frontière entre deux phrases.
    """

    tokens = []

    phrases = MOTIF_PHRASE.split(texte)

    for index, phrase in enumerate(phrases):

        tokens.extend(
            MOTIF_TOKEN.findall(phrase)
        )

        if index < len(phrases) - 1:
            tokens.append(MARQUEUR_PHRASE)

    return tokens


def main():

    DOSSIER_TOKENISE.mkdir(
        parents=True,
        exist_ok=True
    )

    fichiers = sorted(
        DOSSIER_NETTOYE.glob("*.txt")
    )

    print(
        f"Fichiers trouves : {len(fichiers)}"
    )

    for fichier in fichiers:

        texte = fichier.read_text(
            encoding="utf-8"
        )

        tokens = tokeniser(texte)

        sortie = (
            DOSSIER_TOKENISE
            / f"{fichier.stem}.json"
        )

        sortie.write_text(
            json.dumps(
                tokens,
                ensure_ascii=False,
                indent=2
            ),
            encoding="utf-8"
        )

        print(
            f"{fichier.name} -> "
            f"{sortie} "
            f"({len(tokens)} tokens)"
        )


if __name__ == "__main__":
    main()