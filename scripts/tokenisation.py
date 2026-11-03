from pathlib import Path
import json
import re

DOSSIER_NETTOYE = Path("corpus/nettoyage")
DOSSIER_TOKENISE = Path("corpus/tokenise")

MARQUEUR_PHRASE = "__FIN_PHRASE__"

# Séparer les élisions : l'homme -> l' + homme ; qu'il -> qu' + il
SEPARER_ELISIONS = True

# Abréviations après lesquelles un point ne termine pas la phrase.
ABREVIATIONS = {
    "m", "mm", "mme", "mmes", "mlle", "mlles", "dr", "pr", "me",
    "st", "ste", "etc", "cf", "vol", "chap", "fig", "env", "av",
    "apr", "notamment", "ex", "p", "pp", "no", "n",
}

# --------------------------------------------------
# MOTIFS
# --------------------------------------------------

# Toute lettre Unicode (inclut œ, Œ, ç, é, ...) sans chiffre ni "_".
L = r"[^\W\d_]"

ELISION = (
    r"(?i:(?:[cdjlmnst]|qu|jusqu|lorsqu|puisqu|quoiqu|presqu|quelqu)')"
    rf"(?={L})"
)

if SEPARER_ELISIONS:
    MOTIF_TOKEN = re.compile(
        rf"(?i:aujourd'hui)"
        rf"|{ELISION}"
        rf"|{L}+(?:-{L}+)*"
        rf"|\d+(?:[.,]\d+)?"
    )
else:
    MOTIF_TOKEN = re.compile(
        rf"{L}+(?:['\-]{L}+)*|\d+(?:[.,]\d+)?"
    )

# Fin de phrase : . ! ? … + guillemets fermants éventuels + espace,
# SEULEMENT si la suite commence par une majuscule, un guillemet
# ouvrant ou un tiret de dialogue.
MOTIF_PHRASE = re.compile(
    r"(?<=[.!?…])"
    r"(?:\s*[»”\"')\]]+)?"
    r"\s+"
    r"(?=[«“\"'(\[–—-]*\s*[A-ZÀ-ÖØ-ÞŒ0-9])"
)

DERNIER_MOT = re.compile(rf"({L}+)\.$")


# --------------------------------------------------
# DECOUPAGE EN PHRASES
# --------------------------------------------------

def decouper_phrases(texte):
    phrases = []
    debut = 0

    for m in MOTIF_PHRASE.finditer(texte):
        avant = texte[debut:m.start()]

        # Point d'abréviation ou d'initiale : ce n'est pas une fin de phrase.
        trouve = DERNIER_MOT.search(avant)
        if trouve:
            mot = trouve.group(1)
            if len(mot) == 1 or mot.lower() in ABREVIATIONS:
                continue

        phrases.append(avant)
        debut = m.end()

    phrases.append(texte[debut:])
    return phrases


# --------------------------------------------------
# TOKENISATION
# --------------------------------------------------

def tokeniser(texte):
    """
    Transforme le texte en tokens.
    Le marqueur __FIN_PHRASE__ sépare deux phrases (jamais en double).
    """
    texte = texte.replace("’", "'")

    tokens = []

    for phrase in decouper_phrases(texte):
        tokens_phrase = MOTIF_TOKEN.findall(phrase)

        if not tokens_phrase:
            continue

        if tokens:
            tokens.append(MARQUEUR_PHRASE)

        tokens.extend(tokens_phrase)

    return tokens


def main():
    DOSSIER_TOKENISE.mkdir(parents=True, exist_ok=True)

    fichiers = sorted(DOSSIER_NETTOYE.glob("*.txt"))
    print(f"Fichiers trouvés : {len(fichiers)}")

    for fichier in fichiers:
        texte = fichier.read_text(encoding="utf-8")
        tokens = tokeniser(texte)

        sortie = DOSSIER_TOKENISE / f"{fichier.stem}.json"
        sortie.write_text(
            json.dumps(tokens, ensure_ascii=False),
            encoding="utf-8",
        )

        print(f"{fichier.name} -> {sortie} ({len(tokens)} tokens)")


if __name__ == "__main__":
    main()