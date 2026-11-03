from collections import Counter
from pathlib import Path
import json

from antidictionnaire import est_mot_vide


DOSSIER_TOKENISE = Path("corpus/tokenise")
DOSSIER_NGRAMS = Path("corpus/ngrams")

LISTES = {
    "Liste L (candidats)": Path("corpus/liste_L.json"),
    "Liste L filtrée": Path("corpus/liste_L_filtre.json"),
    "Liste LN (personnages)": Path("corpus/liste_LN.json"),
    "Liste LL (lieux)": Path("corpus/liste_LL.json"),
}

SORTIE_JSON = Path("corpus/statistiques.json")
SORTIE_TEXTE = Path("corpus/statistiques.txt")

MARQUEUR_PHRASE = "__FIN_PHRASE__"
TOP = 20


def stats_fichier(tokens):
    mots = [t for t in tokens if t != MARQUEUR_PHRASE]
    compteur = Counter(m.casefold() for m in mots)

    phrases = tokens.count(MARQUEUR_PHRASE) + 1 if mots else 0
    types = len(compteur)

    return compteur, {
        "tokens": len(mots),
        "phrases": phrases,
        "mots_par_phrase": round(len(mots) / phrases, 1) if phrases else 0,
        "vocabulaire": types,
        "hapax": sum(1 for n in compteur.values() if n == 1),
        "richesse_lexicale": round(types / len(mots), 3) if mots else 0,
    }


def stats_ngrams():
    """Nombre de n-grams DISTINCTS (tout le corpus) pour chaque taille."""
    distincts = {}

    for fichier in sorted(DOSSIER_NGRAMS.glob("*.json")):
        donnees = json.loads(fichier.read_text(encoding="utf-8"))

        for taille, ngrams in donnees.items():
            distincts.setdefault(taille, set()).update(ngrams)

    return {f"{t}-grammes": len(s) for t, s in sorted(distincts.items())}


def taille_liste(chemin):
    if not chemin.exists():
        return None

    return len(json.loads(chemin.read_text(encoding="utf-8")))


def main():
    fichiers = sorted(DOSSIER_TOKENISE.glob("*.json"))

    if not fichiers:
        raise SystemExit(f"Aucun fichier JSON dans {DOSSIER_TOKENISE}")

    total = Counter()
    nb_tokens = nb_phrases = 0
    par_livre = {}

    for fichier in fichiers:
        tokens = json.loads(fichier.read_text(encoding="utf-8"))
        compteur, stats = stats_fichier(tokens)

        par_livre[fichier.stem] = stats
        total.update(compteur)
        nb_tokens += stats["tokens"]
        nb_phrases += stats["phrases"]

    global_ = {
        "fichiers": len(fichiers),
        "tokens": nb_tokens,
        "phrases": nb_phrases,
        "mots_par_phrase": round(nb_tokens / nb_phrases, 1) if nb_phrases else 0,
        "vocabulaire": len(total),
        "hapax": sum(1 for n in total.values() if n == 1),
        "richesse_lexicale": round(len(total) / nb_tokens, 3) if nb_tokens else 0,
    }

    resultats = {
        "global": global_,
        "par_livre": par_livre,
        "top_mots": total.most_common(TOP),
        "top_mots_sans_mots_vides": [
            (m, n) for m, n in total.most_common()
            if not est_mot_vide(m) and not m.isdigit()
        ][:TOP],
        "ngrams_distincts": stats_ngrams(),
        "listes": {nom: taille_liste(c) for nom, c in LISTES.items()},
    }

    SORTIE_JSON.write_text(
        json.dumps(resultats, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    lignes = ["STATISTIQUES DU CORPUS", ""]
    lignes += [f"{k} : {v}" for k, v in global_.items()]

    lignes += ["", "PAR LIVRE"]
    for livre, s in par_livre.items():
        lignes.append(
            f"{livre} : {s['tokens']} tokens, {s['phrases']} phrases, "
            f"vocabulaire {s['vocabulaire']}"
        )

    lignes += ["", f"{TOP} MOTS LES PLUS FREQUENTS"]
    lignes += [f"{m}\t{n}" for m, n in resultats["top_mots"]]

    lignes += ["", f"{TOP} MOTS LES PLUS FREQUENTS (sans mots vides)"]
    lignes += [f"{m}\t{n}" for m, n in resultats["top_mots_sans_mots_vides"]]

    lignes += ["", "N-GRAMMES DISTINCTS"]
    lignes += [f"{k} : {v}" for k, v in resultats["ngrams_distincts"].items()]

    lignes += ["", "TAILLE DES LISTES"]
    lignes += [
        f"{nom} : {'absente' if n is None else n}"
        for nom, n in resultats["listes"].items()
    ]

    SORTIE_TEXTE.write_text("\n".join(lignes) + "\n", encoding="utf-8")

    print(f"Statistiques : {SORTIE_TEXTE} et {SORTIE_JSON}")


if __name__ == "__main__":
    main()