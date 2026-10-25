import os
from PIL import Image

# Pointe vers votre dossier contenant toutes les images
dossier_cible = "assets" 

print("Nettoyage des PNG en cours...")
compteur = 0

for dossier_racine, sous_dossiers, fichiers in os.walk(dossier_cible):
    for fichier in fichiers:
        if fichier.lower().endswith(".png"):
            chemin_complet = os.path.join(dossier_racine, fichier)
            try:
                
                # Ouvre et réenregistre l'image pour purger l'iCCP
                with Image.open(chemin_complet) as img:
                    donnees = list(img.getdata())
                    img_propre = Image.new(img.mode, img.size)
                    img_propre.putdata(donnees)
                    img_propre.save(chemin_complet, "PNG")
                compteur += 1
            except Exception as e:
                print(f"Erreur avec {fichier} : {e}")

print(f"Terminé ! {compteur} images nettoyées. Vous pouvez relancer main.py.")