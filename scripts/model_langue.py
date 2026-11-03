
from collections import Counter, defaultdict
from pathlib import Path
import csv
import json
import re


# --------------------------------------------------
# CHEMINS
# --------------------------------------------------

DOSSIER_TOKENISE = Path("corpus/tokenise")
DOSSIER_SORTIE = Path("corpus/modele_langue")

TAILLES_NGRAMMES = (1, 2, 3)


# --------------------------------------------------
# LECTURE DES TOKENS
# --------------------------------------------------

def charger_tokens(fichier):
    """Charge la liste de tokens produite par la tokenisation."""

    donnees = json.loads(
        fichier.read_text(encoding="utf-8")
    )

    if not isinstance(donnees, list):
        raise ValueError(
            f"Format inattendu dans {fichier}: "
            "une liste de tokens était attendue."
        )

    return [str(token) for token in donnees]


def decouper_sequences(tokens):
    """
    Sépare les tokens aux frontières de phrases lorsque la
    ponctuation est présente dans les données.

    Si la tokenisation a supprimé toute ponctuation, les
    frontières de phrases ne peuvent pas être retrouvées ici.
    """

    sequences = []
    sequence = []

    for token in tokens:
        token = token.strip()

        if not token:
            continue

        # Reconnaît les signes de fin de phrase, y compris
        # lorsqu'ils sont attachés au dernier mot.
        fin_phrase = bool(
            re.search(r"[.!?…][\"'»)\]]*$", token)
        )

        # Ignore les tokens qui ne contiennent que de la ponctuation.
        mot = re.sub(r"^[^\wÀ-ÿ]+|[^\wÀ-ÿ]+$", "", token)

        if mot:
            sequence.append(mot)

        if fin_phrase:
            if sequence:
                sequences.append(sequence)
                sequence = []

    if sequence:
        sequences.append(sequence)

    return sequences


# --------------------------------------------------
# CALCUL DES N-GRAMMES
# --------------------------------------------------

def compter_ngrams(sequences, taille):
    compte = Counter()

    for tokens in sequences:
        for position in range(len(tokens) - taille + 1):
            fragment = " ".join(
                tokens[position:position + taille]
            )
            compte[fragment] += 1

    return compte


# --------------------------------------------------
# EXPORT DES TABLES
# --------------------------------------------------

def ecrire_csv(fichier, compte):
    with fichier.open(
        "w",
        encoding="utf-8-sig",
        newline="",
    ) as sortie:
        writer = csv.writer(sortie, delimiter=";")
        writer.writerow(["ngramme", "frequence"])

        for ngramme, frequence in compte.most_common():
            writer.writerow([ngramme, frequence])


# --------------------------------------------------
# PROGRAMME PRINCIPAL
# --------------------------------------------------

def main():
    DOSSIER_SORTIE.mkdir(
        parents=True,
        exist_ok=True,
    )

    fichiers = sorted(DOSSIER_TOKENISE.glob("*.json"))

    if not fichiers:
        raise SystemExit(
            f"Aucun fichier JSON trouvé dans {DOSSIER_TOKENISE}"
        )

    # Fréquences globales et par livre.
    globales = {
        taille: Counter()
        for taille in TAILLES_NGRAMMES
    }

    par_livre = {}
    statistiques = []

    total_tokens = 0
    total_sequences = 0

    for fichier in fichiers:
        tokens_bruts = charger_tokens(fichier)
        sequences = decouper_sequences(tokens_bruts)

        nb_tokens = sum(len(seq) for seq in sequences)
        total_tokens += nb_tokens
        total_sequences += len(sequences)

        resultats_livre = {
            "fichier": fichier.stem,
            "nombre_tokens": nb_tokens,
            "nombre_sequences": len(sequences),
            "vocabulaire": len({
                token.casefold()
                for seq in sequences
                for token in seq
            }),
            "ngrams": {},
        }

        for taille in TAILLES_NGRAMMES:
            compte = compter_ngrams(sequences, taille)

            globales[taille].update(compte)

            resultats_livre["ngrams"][str(taille)] = dict(
                compte.most_common()
            )

        par_livre[fichier.stem] = resultats_livre

        statistiques.append({
            "fichier": fichier.stem,
            "nombre_tokens": nb_tokens,
            "nombre_sequences": len(sequences),
            "vocabulaire": resultats_livre["vocabulaire"],
        })

        print(
            f"{fichier.name} : "
            f"{nb_tokens} tokens, "
            f"{len(sequences)} séquences"
        )

    # Tables globales du modèle de langue.
    modele = {
        "description": (
            "Modèle de langue par fréquences de n-grammes"
        ),
        "tailles_ngrams": list(TAILLES_NGRAMMES),
        "nombre_fichiers": len(fichiers),
        "nombre_tokens": total_tokens,
        "nombre_sequences": total_sequences,
        "ngrams": {},
    }

    for taille, compte in globales.items():
        modele["ngrams"][str(taille)] = dict(
            compte.most_common()
        )

        ecrire_csv(
            DOSSIER_SORTIE / f"ngr ammes_{taille}.csv"
            if False
            else DOSSIER_SORTIE / f"ngr ammes_{taille}.csv",
            compte,
        )

    (DOSSIER_SORTIE / "modele_langue.json").write_text(
        json.dumps(
            modele,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    (DOSSIER_SORTIE / "ngr ammes_par_livre.json").write_text(
        json.dumps(
            par_livre,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    with (
        DOSSIER_SORTIE / "statistiques_corpus.csv"
    ).open(
        "w",
        encoding="utf-8-sig",
        newline="",
    ) as sortie:
        writer = csv.DictWriter(
            sortie,
            fieldnames=[
                "fichier",
                "nombre_tokens",
                "nombre_sequences",
                "vocabulaire",
            ],
            delimiter=";",
        )
        writer.writeheader()
        writer.writerows(statistiques)

    print("\nModèle de langue créé.")
    print(f"Fichiers traités : {len(fichiers)}")
    print(f"Nombre total de tokens : {total_tokens}")
    print(f"Nombre de séquences : {total_sequences}")
    print(f"Résultats : {DOSSIER_SORTIE}")


if __name__ == "__main__":
    main()
