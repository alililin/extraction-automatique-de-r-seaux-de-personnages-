from pathlib import Path
import json

from antidictionnaire import MOTS_VIDES


SOURCE_LISTE = Path(
    "corpus/liste_L_filtre.json"
)

SORTIE_LN = Path(
    "corpus/liste_LN.json"
)

SORTIE_LN_TEXTE = Path(
    "corpus/liste_LN.txt"
)


LIEUX_CONNUS = {
    "Anacréon",
    "Askone",
    "Gaïa",
    "Galaxie",
    "Korell",
    "Synnax",
    "Terminus",
    "Trantor",
    "Siwenna",
    "Smyrno",
    "Terre",
    "Empire Galactique",
}


MOTS_NON_PERSONNAGES = {
    "Fondation",
    "Empire",
    "Galaxie",
    "Encyclopedia Galactica",
    "Espace",
    "Partie",
    "Première Partie",
    "Deuxième Partie",
    "Troisième Partie",
    "Commission",
    "Conseil",
    "Procureur",
    "Plan",
    "Premier",
    "Première",
    "Deuxième",
    "Troisième",
    "Seconde",
    "Orateur",
    "Maire",
    "Maître",
    "Terre",
    "Peut-être",
    "Est-ce",
    "Oh",
    "Ily",
    "Cen'est",
    "Enfait",
    "Biensûr",
    "Etc'est",
    "Parceque",
    "Etes-vous",
    "Avez-vous",
    "Ecoutez",
    "Jen'ai",
    "Jen'en",
    "LeGrand",
}


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


def frequence_mot(mot):
    """
    Retourne la fréquence lexicale Zipf.

    Cette information sert uniquement à éliminer les mots
    français très courants lorsqu'ils apparaissent seuls.
    """

    try:
        from wordfreq import zipf_frequency
    except ImportError:
        return 0.0

    return zipf_frequency(
        mot.casefold(),
        "fr"
    )


def score_candidat(candidat, informations):

    tokens = candidat.split()

    normalise = candidat.casefold()

    exclusions = {
        valeur.casefold()
        for valeur in (
            LIEUX_CONNUS
            | MOTS_NON_PERSONNAGES
        )
    }

    score = 0

    # --------------------------------------------------
    # 1. Structure de nom propre
    # --------------------------------------------------

    if all(
        token[:1].isupper()
        for token in tokens
    ):
        score += 2

    # Nom complet :
    # Golan Trevize
    # Salvor Hardin
    # Janov Pelorat
    if (
        len(tokens) >= 2
        and all(
            token[:1].isupper()
            for token in tokens
        )
    ):
        score += 3

    # --------------------------------------------------
    # 2. Fréquence dans le corpus
    # --------------------------------------------------

    if informations["frequence"] >= 5:
        score += 1

    if informations["frequence"] >= 20:
        score += 1

    # --------------------------------------------------
    # 3. Présence dans plusieurs livres
    # --------------------------------------------------

    if len(informations["livres"]) >= 2:
        score += 1

    # --------------------------------------------------
    # 4. Exclusions
    # --------------------------------------------------

    if normalise in exclusions:
        score -= 8

    # Un titre / terme non-personnage dans un groupe
    if (
        len(tokens) >= 2
        and any(
            token.casefold() in exclusions
            for token in tokens
        )
    ):
        score -= 8

    # Mot fonctionnel
    if normalise in MOTS_VIDES:
        score -= 8

    if any(
        token.casefold() in MOTS_VIDES
        for token in tokens
    ):
        score -= 8

    # Contractions
    if normalise.startswith(
        PREFIXES_CONTRACTION
    ):
        score -= 8

    # Tout en majuscules
    if candidat.isupper():
        score -= 5

    # --------------------------------------------------
    # 5. Mots français très fréquents
    # --------------------------------------------------

    if (
        len(tokens) == 1
        and frequence_mot(candidat) >= 4.5
    ):
        score -= 4

    # Quelques artefacts / mots communs
    if (
        len(tokens) == 1
        and normalise in {
            "joie",
            "allons",
            "galactique",
            "marchand",
            "marchands",
            "table",
            "spatiaux",
            "commodore",
            "écoutez",
            "avez-vous",
            "êtes-vous",
            "parceque",
            "biensûr",
            "enfait",
            "etc'est",
            "premier",
            "première",
            "seconde",
            "orateur",
            "maire",
            "maître",
            "plan",
            "terre",
            "oh",
        }
    ):
        score -= 8

    # --------------------------------------------------
    # 6. Groupe qui ressemble à un morceau de phrase
    # --------------------------------------------------

    if (
        len(tokens) >= 2
        and not all(
            token[:1].isupper()
            for token in tokens
        )
    ):
        score -= 4

    return score


def est_personnage(candidat, informations):

    tokens = candidat.split()

    score = score_candidat(
        candidat,
        informations
    )

    # Pour un groupe de plusieurs mots,
    # tous les tokens doivent commencer par une majuscule.
    if (
        len(tokens) >= 2
        and not all(
            token[:1].isupper()
            for token in tokens
        )
    ):
        return False

    return score >= 3


def main():

    liste = json.loads(
        SOURCE_LISTE.read_text(
            encoding="utf-8"
        )
    )

    personnages = {}

    for candidat, informations in liste.items():

        if est_personnage(
            candidat,
            informations
        ):

            personnages[candidat] = {
                **informations,
                "score": score_candidat(
                    candidat,
                    informations
                )
            }

    SORTIE_LN.write_text(
        json.dumps(
            personnages,
            ensure_ascii=False,
            indent=2
        ),
        encoding="utf-8"
    )

    SORTIE_LN_TEXTE.write_text(
        "\n".join(personnages) + "\n",
        encoding="utf-8"
    )

    print(
        f"Liste LN creee : "
        f"{SORTIE_LN} "
        f"({len(personnages)} personnages)"
    )


if __name__ == "__main__":
    main()