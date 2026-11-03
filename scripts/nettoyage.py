"""
Nettoyage d'un corpus extrait de PDF (mots coupés, mots collés, tirets).

Principe : on ne regarde pas les mots un par un. Pour chaque suite de
fragments séparés par un espace, on cherche la meilleure façon de découper
la chaîne complète en mots (programmation dynamique, façon "word
segmentation"). Le score d'un mot vient de deux sources :
  1. wordfreq (français courant),
  2. un lexique construit automatiquement sur ton corpus (noms propres,
     vocabulaire spécifique comme "psychohistoire").

"""

import math
import re
from collections import Counter
from functools import lru_cache
from pathlib import Path

from wordfreq import zipf_frequency


# --------------------------------------------------
# PARAMETRES
# --------------------------------------------------

DOSSIER_BRUT = Path("corpus/txt")
DOSSIER_PROPRE = Path("corpus/nettoyage")

SEUIL = 3.0            # zipf minimal pour qu'un mot soit "français connu"
MIN_OCC = 2            # occurrences minimales dans le corpus pour le lexique
MAX_MOT = 25           # longueur maximale d'un mot dans la segmentation
MAX_GROUPE = 8         # nombre maximal de fragments traités ensemble
MARGE = 3.0            # gain minimal de score pour modifier un groupe
COUT_INCONNU_BASE = 12.0
COUT_INCONNU_LETTRE = 6.0
UNE_LETTRE = {"a", "à", "y"}   # seuls mots d'une lettre acceptés

LETTRES = "A-Za-zÀ-ÖØ-öø-ÿŒœ"
MOT = re.compile(f"[{LETTRES}]+")
COMPOSE = re.compile(f"[{LETTRES}]+(?:-[{LETTRES}]+)+")
SUITE = re.compile(f"[{LETTRES}]+(?: [{LETTRES}]+)*")

# Rempli par construire_lexique()
LEXIQUE = {}


# --------------------------------------------------
# FREQUENCES
# --------------------------------------------------

@lru_cache(maxsize=None)
def zipf(mot):
    return zipf_frequency(mot, "fr")


def mot_francais(mot):
    """Mot reconnu par wordfreq (minuscules)."""
    if len(mot) == 1:
        return mot in UNE_LETTRE
    return zipf(mot) >= SEUIL


def cout_inconnu(longueur):
    return COUT_INCONNU_BASE + COUT_INCONNU_LETTRE * longueur


def cout_mot(mot):
    """Coût (plus petit = plus plausible) ou None si mot inconnu."""
    couts = []

    if mot_francais(mot):
        couts.append((9.0 - zipf(mot)) * math.log(10))

    if mot in LEXIQUE:
        couts.append(LEXIQUE[mot][1])

    return min(couts) if couts else None


# --------------------------------------------------
# LEXIQUE DU CORPUS
# --------------------------------------------------

def decomposable(mot):
    """
    Vrai si le mot est probablement deux mots collés (ex. "dela"),
    donc à ne PAS ajouter au lexique.
    """
    for i in range(1, len(mot)):
        a, b = mot[:i], mot[i:]

        if len(a) <= 3 and zipf(a) >= 5.0 and mot_francais(b):
            return True
        if len(b) <= 3 and zipf(b) >= 5.0 and mot_francais(a):
            return True

    return False


def construire_lexique():
    compteur = Counter()
    composes = Counter()

    for fichier in DOSSIER_BRUT.glob("*.txt"):
        texte = fichier.read_text(encoding="utf-8")
        compteur.update(m.lower() for m in MOT.findall(texte))
        composes.update(m.lower() for m in COMPOSE.findall(texte))

    total = sum(compteur.values()) or 1
    lexique = {}

    # Mots du corpus inconnus de wordfreq (noms propres, termes rares)
    for mot, n in compteur.items():
        if n < MIN_OCC or len(mot) < 4:
            continue
        if mot_francais(mot) or decomposable(mot):
            continue
        lexique[mot] = (mot, math.log(total / n) + 2.0)

    # Mots composés avec tiret présents dans le corpus :
    # clé sans tiret -> forme avec tiret ("euxmêmes" -> "eux-mêmes")
    for compose, n in composes.items():
        if n < MIN_OCC:
            continue
        cle = compose.replace("-", "")
        lexique[cle] = (compose, math.log(total / n) - 1.0)

    return lexique


# --------------------------------------------------
# SEGMENTATION (programmation dynamique)
# --------------------------------------------------

def segmenter(chaine):
    """Meilleur découpage de `chaine` en mots. Renvoie (coût, spans)."""
    bas = chaine.lower()
    n = len(chaine)

    meilleur = [math.inf] * (n + 1)
    precedent = [0] * (n + 1)
    meilleur[0] = 0.0

    for j in range(1, n + 1):
        for i in range(max(0, j - MAX_MOT), j):
            if meilleur[i] == math.inf:
                continue

            mot = bas[i:j]
            cout = cout_mot(mot)
            if cout is None:
                cout = cout_inconnu(len(mot))

            total = meilleur[i] + cout
            if total < meilleur[j]:
                meilleur[j] = total
                precedent[j] = i

    spans = []
    j = n
    while j > 0:
        i = precedent[j]
        spans.append((i, j))
        j = i
    spans.reverse()

    return meilleur[n], spans


def afficher(chaine, i, j):
    """Texte final d'un morceau (recrée le tiret des composés connus)."""
    morceau = chaine[i:j]
    cle = morceau.lower()

    if cle in LEXIQUE and "-" in LEXIQUE[cle][0]:
        forme = LEXIQUE[cle][0]
        if morceau[0].isupper():
            forme = forme[0].upper() + forme[1:]
        return forme

    return morceau


def traiter_groupe(fragments):
    chaine = "".join(fragments)

    cout_original = 0.0
    for fragment in fragments:
        cout = cout_mot(fragment.lower())
        cout_original += (
            cout if cout is not None else cout_inconnu(len(fragment))
        )

    cout_nouveau, spans = segmenter(chaine)

    # On ne modifie que si le gain est net.
    if cout_nouveau + MARGE < cout_original:
        return " ".join(afficher(chaine, i, j) for i, j in spans)

    return " ".join(fragments)


def traiter_suite(match):
    """
    Une "suite" = fragments séparés par un seul espace, sans ponctuation.
    On regroupe les fragments voisins dont au moins un est inconnu :
    deux mots français valides côte à côte ne sont jamais fusionnés.
    """
    fragments = match.group().split(" ")
    resultat = []
    i = 0

    while i < len(fragments):
        groupe = [fragments[i]]

        while (
            len(groupe) < MAX_GROUPE
            and i + len(groupe) < len(fragments)
            and not (
                mot_francais(groupe[-1].lower())
                and mot_francais(fragments[i + len(groupe)].lower())
            )
        ):
            groupe.append(fragments[i + len(groupe)])

        if len(groupe) == 1 and mot_francais(groupe[0].lower()):
            resultat.append(groupe[0])
        else:
            resultat.append(traiter_groupe(groupe))

        i += len(groupe)

    return " ".join(resultat)


# --------------------------------------------------
# AUTRES CORRECTIONS
# --------------------------------------------------

def supprimer_numeros_page(texte):
    """Supprime les lignes du type '– 17 –' ou '17'."""
    return re.sub(
        r"(?m)^[ \t]*[–—-]?[ \t]*\d{1,4}[ \t]*[–—-]?[ \t]*$\n?",
        "",
        texte,
    )


def corriger_tirets(texte):
    """Recolle les mots coupés par un tiret en fin de ligne.
    Le tiret des composés est rétabli ensuite par la segmentation."""
    return re.sub(
        rf"(?<=[{LETTRES}])-[ \t]*\n[ \t]*(?=[{LETTRES}])",
        "",
        texte,
    )


def corriger_apostrophes(texte):
    """Supprime les espaces artificiels autour des apostrophes."""
    return re.sub(
        rf"([{LETTRES}]+)\s+(['’])\s*([{LETTRES}]+)",
        r"\1\2\3",
        texte,
    )


# --------------------------------------------------
# NETTOYAGE COMPLET
# --------------------------------------------------

def nettoyer_texte(texte):
    texte = texte.replace("\r\n", "\n").replace("\r", "\n")

    texte = supprimer_numeros_page(texte)
    texte = corriger_tirets(texte)
    texte = corriger_apostrophes(texte)

    texte = re.sub(r"[ \t]+", " ", texte)
    texte = SUITE.sub(traiter_suite, texte)

    texte = re.sub(r"[ \t]+\n", "\n", texte)
    texte = re.sub(r"\n{3,}", "\n\n", texte)

    return texte.strip() + "\n"


# --------------------------------------------------
# PROGRAMME PRINCIPAL
# --------------------------------------------------

def main():
    global LEXIQUE

    if not DOSSIER_BRUT.exists():
        raise SystemExit(f"Dossier source introuvable : {DOSSIER_BRUT}")

    fichiers = sorted(DOSSIER_BRUT.glob("*.txt"))
    if not fichiers:
        raise SystemExit(f"Aucun fichier .txt trouvé dans {DOSSIER_BRUT}")

    DOSSIER_PROPRE.mkdir(parents=True, exist_ok=True)

    print(f"Fichiers trouvés : {len(fichiers)}")
    print("Construction du lexique du corpus...")
    LEXIQUE = construire_lexique()
    print(f"Entrées dans le lexique : {len(LEXIQUE)}")

    for fichier in fichiers:
        print(f"Nettoyage : {fichier.name}")

        texte = fichier.read_text(encoding="utf-8")
        propre = nettoyer_texte(texte)

        sortie = DOSSIER_PROPRE / fichier.name
        sortie.write_text(propre, encoding="utf-8")
        print(f"  -> {sortie}")

    print("Nettoyage terminé.")


if __name__ == "__main__":
    main()