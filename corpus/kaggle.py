"""
Détection d'entités nommées avec un modèle spaCy pré-entraîné (PER, LOC, ORG).
Utilisable sur Kaggle (notebook) ou en local.

Sur Kaggle :
  1. Active Internet dans les paramètres du notebook.
  2. Dans une cellule :  !python -m spacy download fr_core_news_md
  3. Ajoute le dossier corpus/nettoyage comme dataset PRIVÉ nommé
     "corpus-nettoyage" (ou change DOSSIER_TEXTES ci-dessous).
  4. Récupère /kaggle/working/ner_spacy.json à la fin.

En local :  pip install spacy  puis  python -m spacy download fr_core_news_md
"""

from collections import Counter
from pathlib import Path
import json

import spacy


KAGGLE = Path("/kaggle/input").exists()

DOSSIER_TEXTES = (
    Path("/kaggle/input/corpus-nettoyage")
    if KAGGLE
    else Path("corpus/nettoyage")
)

SORTIE = (
    Path("/kaggle/working/ner_spacy.json")
    if KAGGLE
    else Path("corpus/ner_spacy.json")
)

MODELE = "fr_core_news_md"
TAILLE_BLOC = 50_000

ETIQUETTES = {"PER": "personnes", "LOC": "lieux", "ORG": "organisations"}


def blocs(texte, taille):
    """Découpe aux fins de paragraphe pour ne pas couper une phrase."""
    bloc = []
    longueur = 0

    for paragraphe in texte.split("\n\n"):
        if bloc and longueur + len(paragraphe) > taille:
            yield "\n\n".join(bloc)
            bloc = []
            longueur = 0

        bloc.append(paragraphe)
        longueur += len(paragraphe) + 2

    if bloc:
        yield "\n\n".join(bloc)


def main():
    fichiers = sorted(DOSSIER_TEXTES.glob("*.txt"))

    if not fichiers:
        raise SystemExit(f"Aucun fichier .txt dans {DOSSIER_TEXTES}")

    nlp = spacy.load(MODELE, disable=["lemmatizer"])

    resultats = {nom: Counter() for nom in ETIQUETTES.values()}

    for fichier in fichiers:
        print(f"Analyse : {fichier.name}")
        texte = fichier.read_text(encoding="utf-8")

        for doc in nlp.pipe(blocs(texte, TAILLE_BLOC), batch_size=4):
            for entite in doc.ents:
                if entite.label_ in ETIQUETTES:
                    nom = " ".join(entite.text.split())
                    resultats[ETIQUETTES[entite.label_]][nom] += 1

    SORTIE.write_text(
        json.dumps(
            {k: dict(c.most_common()) for k, c in resultats.items()},
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print(f"Résultats : {SORTIE}")
    for nom, compteur in resultats.items():
        print(f"  {nom} : {len(compteur)} entités distinctes")


if __name__ == "__main__":
    main()