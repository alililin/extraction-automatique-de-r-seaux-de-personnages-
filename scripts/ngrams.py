from collections import Counter
from pathlib import Path
import json

# Pour ignorer les mots vides, remplace par Path("corpus/sans_mots_vides")
DOSSIER_TOKENISE = Path("corpus/tokenise")
DOSSIER_NGRAMS = Path("corpus/ngrams")

TAILLES_NGRAMS = (1, 2, 3)

MARQUEUR_PHRASE = "__FIN_PHRASE__"

# False = on garde les majuscules (indispensable pour repérer les noms propres).
# True  = tout en minuscules (utile seulement pour des statistiques de langue).
NORMALISER_CASSE = False


def decouper_en_phrases(tokens):
    """Produit une liste de tokens par phrase."""
    phrase = []

    for token in tokens:
        if token == MARQUEUR_PHRASE:
            if phrase:
                yield phrase
            phrase = []
        else:
            phrase.append(token.casefold() if NORMALISER_CASSE else token)

    # Dernière phrase du fichier
    if phrase:
        yield phrase


def creer_ngrams(tokens, taille):
    """Construit les n-grams sans traverser une fin de phrase."""
    compte = Counter()

    for phrase in decouper_en_phrases(tokens):
        for position in range(len(phrase) - taille + 1):
            groupe = " ".join(phrase[position:position + taille])
            compte[groupe] += 1

    return compte


def main():
    DOSSIER_NGRAMS.mkdir(parents=True, exist_ok=True)

    fichiers = sorted(DOSSIER_TOKENISE.glob("*.json"))
    print(f"Fichiers trouvés : {len(fichiers)}")

    for fichier in fichiers:
        tokens = json.loads(fichier.read_text(encoding="utf-8"))

        resultats = {}

        for taille in TAILLES_NGRAMS:
            compte = creer_ngrams(tokens, taille)

            # Trié du plus fréquent au moins fréquent
            resultats[str(taille)] = dict(compte.most_common())

        sortie = DOSSIER_NGRAMS / fichier.name
        sortie.write_text(
            json.dumps(resultats, ensure_ascii=False),
            encoding="utf-8",
        )

        print(f"{fichier.name} -> {sortie}")


if __name__ == "__main__":
    main()