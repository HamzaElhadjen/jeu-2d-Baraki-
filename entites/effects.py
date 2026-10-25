import pygame
import os

class TexteDegat(pygame.sprite.Sprite):
    def __init__(self, x, y, degats):
        super().__init__()
        font = pygame.font.SysFont("Impact", 35)
        self.image = font.render(str(degats), True, (255, 220, 0))
        self.rect = self.image.get_rect(center=(x, y))
        self.vitesse_y = -3
        self.duree_vie = 30 

    def update(self):
        self.rect.y += self.vitesse_y
        self.duree_vie -= 1
        if self.duree_vie <= 0:
            self.kill() 

class AnimationEffet(pygame.sprite.Sprite):
    def __init__(self, x, y, nom_dossier, regarde_a_droite):
        super().__init__()
        # On pointe vers ton dossier 'effects' en anglais
        chemin = os.path.join("assets", "images", "effects", nom_dossier)
        
        # On charge toutes les images contenues dans le dossier (ex: slash)
        self.frames = self.charger_dossier(chemin)
        
        if not regarde_a_droite:
            self.frames = [pygame.transform.flip(f, True, False) for f in self.frames]
            
        self.index_frame = 0
        self.image = self.frames[0]
        self.rect = self.image.get_rect(center=(x, y))

    def charger_dossier(self, chemin):
        frames = []
        try:
            # On trie les fichiers pour que l'animation se lise dans l'ordre (1.png, 2.png...)
            fichiers = sorted(os.listdir(chemin))
            for fichier in fichiers:
                if fichier.endswith((".png", ".jpg")):
                    img = pygame.image.load(os.path.join(chemin, fichier)).convert_alpha()
                    img = pygame.transform.scale_by(img, 1.5)
                    frames.append(img)
        except FileNotFoundError:
            pass
            
        # Si le dossier est vide ou introuvable, on met un cercle blanc de secours
        if not frames:
            secours = pygame.Surface((50, 50), pygame.SRCALPHA)
            pygame.draw.circle(secours, (255, 255, 255, 150), (25, 25), 25)
            return [secours]
            
        return frames

    def update(self):
        self.index_frame += 0.4
        if self.index_frame >= len(self.frames):
            self.kill() 
        else:
            self.image = self.frames[int(self.index_frame)]