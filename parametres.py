import pygame
import json
import os

try:
    pygame.mixer.init()
except Exception as e:
    print(f"Erreur d'initialisation audio : {e}")

LARGEUR_ECRAN = 1280
HAUTEUR_ECRAN = 720
FPS = 60
SOL_Y = 600

FICHIER_CONFIG = "config.json"

TOUCHES = {
    "GAUCHE": pygame.K_q,
    "DROITE": pygame.K_d,
    "SAUT": pygame.K_SPACE,
    "DASH": pygame.K_LSHIFT,
    "ATTAQUE_1": pygame.K_f, 
    "ATTAQUE_2": pygame.K_g, 
    "ATTAQUE_3": pygame.K_h,  
    "ATTAQUE_4": pygame.K_j,
    "APPEL_COEQ": pygame.K_c  # --- NOUVELLE TOUCHE : Appel d'escouade ---
}

if os.path.exists(FICHIER_CONFIG):
    with open(FICHIER_CONFIG, "r") as fichier:
        try:
            touches_sauvees = json.load(fichier)
            for action, touche in touches_sauvees.items():
                if action in TOUCHES: TOUCHES[action] = touche
        except: pass

def sauvegarder_touches():
    with open(FICHIER_CONFIG, "w") as fichier:
        json.dump(TOUCHES, fichier)

SPAWN_ENNEMI = pygame.USEREVENT + 1

def charger_son(chemin, volume=0.5):
    try:
        son = pygame.mixer.Sound(chemin)
        son.set_volume(volume)
        return son
    except Exception: return None