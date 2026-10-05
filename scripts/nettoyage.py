
from pathlib import Path
import re

# --------------------------------------------------
# DOSSIERS
# --------------------------------------------------

DOSSIER_BRUT = Path("corpus/txt")
DOSSIER_PROPRE = Path("corpus/nettoyage")

FICHIER_ANTIDICTIONNAIRE = Path(
    "ressource/antidictionnaire.txt"
)


# --------------------------------------------------
# CHARGEMENT DE L'ANTIDICTIONNAIRE
# --------------------------------------------------

def charger_antidictionnaire():
    """
    Charge les mots présents dans l'antidictionnaire.
    """

    mots = set()

    for ligne in FICHIER_ANTIDICTIONNAIRE.read_text(
        encoding="utf-8"
    ).splitlines():

        ligne = ligne.strip()

        if not ligne:
            continue

        if ligne.startswith("#"):
            continue

        mots.add(ligne.casefold())

    return mots


MOTS_VIDES = charger_antidictionnaire()


# --------------------------------------------------
# VERIFICATION D'UN MOT FRANCAIS
# --------------------------------------------------

def est_mot_francais(mot):
    """
    Vérifie si un mot est suffisamment fréquent
    en français grâce à wordfreq.

    La fréquence Zipf doit être >= 3.0.
    """

    try:
        from wordfreq import zipf_frequency

    except ImportError as erreur:

        raise SystemExit(
            "La bibliothèque wordfreq n'est pas installée.\n"
            "Installe-la avec : pip install wordfreq"
        ) from erreur

    return (
        zipf_frequency(
            mot.casefold(),
            "fr"
        ) >= 3.0
    )


# --------------------------------------------------
# APOSTROPHES
# --------------------------------------------------

def corriger_apostrophes(texte):
    """
    Corrige les espaces artificiels autour des apostrophes.

    Exemples :

        j ' aimerais -> j'aimerais
        qu ' on      -> qu'on
        d ' un       -> d'un
        c ' est      -> c'est
    """

    motif_mot = re.compile(
        r"[A-Za-zÀ-ÿ]+(?:['’][A-Za-zÀ-ÿ]+)*"
    )
    return re.sub(
        r"([A-Za-zÀ-ÿ]+)\s*['’]\s*([A-Za-zÀ-ÿ]+)",
        r"\1'\2",
        texte
    )


# --------------------------------------------------
# MOTS COUPES PAR UN TIRET
# --------------------------------------------------

def corriger_tirets(texte):
    """
    Corrige les mots coupés par un tiret en fin de ligne.

    Exemple :

        inter-
        galactique

    devient :

        intergalactique
    """

    return re.sub(
        r"(?<=[A-Za-zÀ-ÿ])-\s*\n\s*(?=[A-Za-zÀ-ÿ])",
        "",
        texte
    )


# --------------------------------------------------
# COUPURES DE MOTS
# --------------------------------------------------

def fusion_possible(gauche, droite):
    """
    Détermine si deux fragments séparés par un espace
                # Une forme avec apostrophe (l'ai, qu'on, c'est...) est
                # un bloc : ne pas fusionner sa dernière partie au mot suivant.
                if "'" in mot or "’" in mot:
                    remplacements.append((debut, fin, mot))
                    position += 1
                    continue
    doivent probablement être fusionnés.

    Exemple :

        éga + l
        hom + mes
        marc + hes

    peuvent donner :

        égal
        hommes
        marches
    """

    gauche_min = gauche.casefold()
    droite_min = droite.casefold()

    candidat = gauche + droite
    candidat_min = candidat.casefold()

    # --------------------------------------------------
    # Cas où les deux fragments sont des mots indépendants
    # --------------------------------------------------

    gauche_est_mot = est_mot_francais(gauche)
    droite_est_mot = est_mot_francais(droite)

    candidat_est_mot = est_mot_francais(candidat)

    # Si les deux morceaux sont de vrais mots français
    # et que leur concaténation n'apporte rien,
    # on garde l'espace.
    if gauche_est_mot and droite_est_mot:
        return False

    # --------------------------------------------------
    # Le résultat doit être un mot français
    # --------------------------------------------------

    if not candidat_est_mot:
        return False

    # --------------------------------------------------
    # Antidictionnaire
    #
    # Exemple :
    #
    # "le plus"
    #
    # ne doit pas devenir "leplus".
    # --------------------------------------------------

    if (
        gauche_min in MOTS_VIDES
        and droite_min in MOTS_VIDES
    ):
        return False

    # --------------------------------------------------
    # Fragments d'une seule lettre
    # --------------------------------------------------

    if len(gauche) == 1 or len(droite) == 1:

        # Certains mots d'une lettre doivent rester
        # indépendants.
        mots_courts = {
            "a",
            "à",
            "y",
            "o",
            "e"
        }

        if gauche_min in mots_courts:
            return False

        if droite_min in mots_courts:

            # Exemple :
            #
            # M a -> Ma
            #
            # Une majuscule suivie de "a" peut être
            # une coupure artificielle.
            if (
                len(gauche) == 1
                and gauche.isupper()
            ):
                return True

            return False

        return True

    # --------------------------------------------------
    # Cas général
    # --------------------------------------------------

    return True


def corriger_coupures(texte):
    """
    Corrige les mots coupés artificiellement par l'extraction PDF.

    Exemples :

        éga l       -> égal
        hom mes     -> hommes
        marc hes    -> marches
        éner gique  -> énergique
        fa ire      -> faire
        cont inue   -> continue
        Trev ize    -> Trevize
    """

    # Normalisation des espaces
    texte = re.sub(
        r"[ \t]+",
        " ",
        texte
    )

    # --------------------------------------------------
    # Cas particulier :
    #
    # c'es t -> c'est
    #
    # Après la correction des apostrophes,
    # il peut rester une lettre séparée.
    # --------------------------------------------------

    def corriger_apostrophe_coupee(match):

        gauche = match.group(1)
        droite = match.group(2)

        candidat = gauche + droite

        if est_mot_francais(candidat):
            return candidat

        return match.group(0)

    texte = re.sub(
        r"([A-Za-zÀ-ÿ]+['’][A-Za-zÀ-ÿ]+)\s+([tn])\b",
        corriger_apostrophe_coupee,
        texte,
        flags=re.IGNORECASE,
    )

    # --------------------------------------------------
    # Recherche de deux fragments consécutifs
    # --------------------------------------------------

    motif_mot = re.compile(
        r"[A-Za-zÀ-ÿ]+(?:['’][A-Za-zÀ-ÿ]+)*"
    )
    mots = list(motif_mot.finditer(texte))
    remplacements = []
    position = 0

    while position < len(mots):
        debut = mots[position].start()
        fin = mots[position].end()
        mot = mots[position].group()
        suivant = position + 1

        # Une contraction complète ne doit pas absorber le mot suivant.
        if "'" in mot or "’" in mot:
            remplacements.append((debut, fin, mot))
            position += 1
            continue

        while suivant < len(mots):
            separation = texte[fin:mots[suivant].start()]
            prochain_mot = mots[suivant].group()

            if not separation or not separation.isspace():
                break

            if not fusion_possible(mot, prochain_mot):
                break

            mot += prochain_mot
            fin = mots[suivant].end()
            suivant += 1

        remplacements.append((debut, fin, mot))
        position = suivant if suivant > position + 1 else position + 1

    resultat = []
    debut_texte = 0

    for debut, fin, mot in remplacements:
        resultat.append(texte[debut_texte:debut])
        resultat.append(mot)
        debut_texte = fin

    resultat.append(texte[debut_texte:])
    return "".join(resultat)


# --------------------------------------------------
# NETTOYAGE COMPLET
# --------------------------------------------------

def nettoyer_texte(texte):
    """
    Applique toutes les étapes de nettoyage.
    """

    # Normalisation des retours à la ligne
    texte = texte.replace(
        "\r\n",
        "\n"
    )

    texte = texte.replace(
        "\r",
        "\n"
    )

    # 1. Mots coupés par un tiret
    texte = corriger_tirets(
        texte
    )

    # 2. Apostrophes
    texte = corriger_apostrophes(
        texte
    )

    # 3. Mots coupés par l'extraction PDF
    texte = corriger_coupures(
        texte
    )

    # 4. Espaces multiples
    texte = re.sub(
        r"[ \t]+",
        " ",
        texte
    )

    # 5. Trop nombreux retours à la ligne
    texte = re.sub(
        r"\n{3,}",
        "\n\n",
        texte
    )

    return texte.strip() + "\n"


# --------------------------------------------------
# PROGRAMME PRINCIPAL
# --------------------------------------------------

def main():

    # Création du dossier de sortie
    DOSSIER_PROPRE.mkdir(
        parents=True,
        exist_ok=True
    )

    # Recherche des textes bruts
    fichiers = sorted(
        DOSSIER_BRUT.glob("*.txt")
    )

    print(
        f"Fichiers trouves : {len(fichiers)}"
    )

    print(
        f"Mots dans l'antidictionnaire : "
        f"{len(MOTS_VIDES)}"
    )

    # --------------------------------------------------
    # Traitement de chaque livre
    # --------------------------------------------------

    for fichier in fichiers:

        print(
            f"Nettoyage : {fichier.name}"
        )

        texte = fichier.read_text(
            encoding="utf-8"
        )

        texte_nettoye = nettoyer_texte(
            texte
        )

        sortie = (
            DOSSIER_PROPRE
            / fichier.name
        )

        sortie.write_text(
            texte_nettoye,
            encoding="utf-8"
        )

        print(
            f"  -> {sortie}"
        )


if __name__ == "__main__":
    main()
