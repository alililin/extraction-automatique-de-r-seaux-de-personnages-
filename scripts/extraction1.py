from pathlib import Path # permet de manipuler les chemins fichiers 
from pypdf import PdfReader


# Dossiers
DOSSIER_PDF = Path("corpus/pdf") #les pdf a traiter se situe dans corpus/txt 
DOSSIER_TXT = Path("corpus/txt") 

DOSSIER_TXT.mkdir(parents=True, exist_ok=True)


def extraire_pdf(chemin_pdf): # fonction qui lit un pdf
    """Extrait le texte d'un fichier PDF."""
    
    reader = PdfReader(chemin_pdf)

    texte = []

    for page in reader.pages: # on accede aux pages
        contenu = page.extract_text() # Extrais le texte de cette page.
 
        if contenu:
            texte.append(contenu)

    return "\n".join(texte) # À la fin, on transforme notre liste en un seul gros texte.


def main():

    fichiers_pdf = list(DOSSIER_PDF.glob("*.pdf"))

    print(f"Nombre de PDF trouvés : {len(fichiers_pdf)}")

    for fichier_pdf in fichiers_pdf:

        print(f"Traitement : {fichier_pdf.name}")

        texte = extraire_pdf(fichier_pdf)

        # Nom du fichier TXT
        nom_txt = fichier_pdf.stem.replace("_impaires", "") + ".txt"

        chemin_txt = DOSSIER_TXT / nom_txt

        # Écriture UTF-8
        chemin_txt.write_text(
            texte,
            encoding="utf-8"
        )

        print(
            f"  -> {chemin_txt} "
            f"({len(texte)} caractères)"
        )


if __name__ == "__main__":
    main()