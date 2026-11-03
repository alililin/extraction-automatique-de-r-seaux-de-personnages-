from pathlib import Path
import json
import re

# On supprime les mots vides qui ne servent à rien pour l'analyse de texte.
DOSSIER_TOKENISE = Path("corpus/tokenise")
DOSSIER_FILTRAGE = Path("corpus/sans_mots_vides")
FICHIER_ANTIDICTIONNAIRE = Path("ressource/antidictionnaire.txt")

MARQUEUR_PHRASE = "__FIN_PHRASE__"

# Sépare un token sur les apostrophes et les tirets :
# "peut-être" -> peut, être ; "aujourd'hui" -> aujourd, hui
DECOUPE = re.compile(r"['’\-]")


def charger_antidictionnaire():
    """Charge un mot vide par ligne (les lignes # sont des commentaires)."""
    if not FICHIER_ANTIDICTIONNAIRE.exists():
        raise SystemExit(
            f"Antidictionnaire introuvable : {FICHIER_ANTIDICTIONNAIRE}"
        )

    return {
        ligne.strip().casefold()
        for ligne in FICHIER_ANTIDICTIONNAIRE.read_text(
            encoding="utf-8"
        ).splitlines()
        if ligne.strip() and not ligne.lstrip().startswith("#")
    }


MOTS_VIDES = charger_antidictionnaire()


def est_mot_vide(token):
    """
    Vrai si le token est un mot vide.

    - "l'", "qu'", "d'" : l'apostrophe finale est ignorée, car la liste
      contient "l", "qu", "d".
    - "peut-être", "dit-il", "aujourd'hui" : supprimés si TOUTES leurs
      parties sont des mots vides.
    """
    mot = token.casefold()

    if mot in MOTS_VIDES:
        return True

    parties = [p for p in DECOUPE.split(mot) if p]

    return bool(parties) and all(p in MOTS_VIDES for p in parties)


def filtrer_tokens(tokens):
    """
    Supprime les mots vides en conservant les autres tokens et les
    frontières de phrase (sans doublons, ni au début, ni à la fin).
    """
    resultat = []

    for token in tokens:
        if token == MARQUEUR_PHRASE:
            if resultat and resultat[-1] != MARQUEUR_PHRASE:
                resultat.append(token)
        elif not est_mot_vide(token):
            resultat.append(token)

    if resultat and resultat[-1] == MARQUEUR_PHRASE:
        resultat.pop()

    return resultat


def main():
    DOSSIER_FILTRAGE.mkdir(parents=True, exist_ok=True)

    fichiers = sorted(DOSSIER_TOKENISE.glob("*.json"))
    print(f"Fichiers trouvés : {len(fichiers)}")
    print(f"Mots vides chargés : {len(MOTS_VIDES)}")

    for fichier in fichiers:
        tokens = json.loads(fichier.read_text(encoding="utf-8"))
        tokens_filtres = filtrer_tokens(tokens)

        sortie = DOSSIER_FILTRAGE / fichier.name
        sortie.write_text(
            json.dumps(tokens_filtres, ensure_ascii=False),
            encoding="utf-8",
        )

        print(
            f"{fichier.name} -> {sortie} "
            f"({len(tokens)} -> {len(tokens_filtres)} tokens)"
        )


if __name__ == "__main__":
    main()