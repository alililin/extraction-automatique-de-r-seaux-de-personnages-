from pathlib import Path
import json

# on supprime les mots vides qui servent a rien pour l'analyse de texte
DOSSIER_TOKENISE = Path("corpus/tokenise")
DOSSIER_FILTRAGE = Path("corpus/sans_mots_vides")
FICHIER_ANTIDICTIONNAIRE = Path("ressource/antidictionnaire.txt")


def charger_antidictionnaire():
    """Charge un mot interdit par ligne depuis la ressource du projet."""
    return {
        ligne.strip().casefold()
        for ligne in FICHIER_ANTIDICTIONNAIRE.read_text(encoding="utf-8").splitlines()
        if ligne.strip() and not ligne.lstrip().startswith("#")
    }


MOTS_VIDES = charger_antidictionnaire()


def filtrer_tokens(tokens):
    """Supprime les mots vides en conservant les autres tokens."""
    return [token for token in tokens if token.casefold() not in MOTS_VIDES]


def main():
    DOSSIER_FILTRAGE.mkdir(parents=True, exist_ok=True)

    fichiers = sorted(DOSSIER_TOKENISE.glob("*.json"))
    print(f"Fichiers trouves : {len(fichiers)}")

    for fichier in fichiers:
        tokens = json.loads(fichier.read_text(encoding="utf-8"))
        tokens_filtres = filtrer_tokens(tokens)
        sortie = DOSSIER_FILTRAGE / fichier.name
        sortie.write_text(
            json.dumps(tokens_filtres, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(
            f"{fichier.name} -> {sortie} "
            f"({len(tokens)} -> {len(tokens_filtres)} tokens)"
        )


if __name__ == "__main__":
    main()