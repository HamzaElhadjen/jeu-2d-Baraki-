import pygame
import random
from parametres import SOL_Y

class Loot(pygame.sprite.Sprite):
    def __init__(self, x, y, type_loot):
        super().__init__()
        self.type_loot = type_loot # "or" ou "vie"
        
        # Dessin procédural de l'objet (Cercles brillants)
        self.image = pygame.Surface((24, 24), pygame.SRCALPHA)
        if type_loot == "or":
            pygame.draw.circle(self.image, (255, 200, 0), (12, 12), 8) # Pièce d'or
            pygame.draw.circle(self.image, (255, 255, 150), (12, 12), 4) # Brillance
        else:
            pygame.draw.circle(self.image, (220, 30, 30), (12, 12), 10) # Orbe de vie
            pygame.draw.circle(self.image, (255, 100, 100), (12, 12), 5) # Brillance
            
        self.rect = self.image.get_rect(center=(x, y))
        self.hitbox = pygame.Rect(x, y, 20, 20)
        
        # Physique (le butin "saute" légèrement hors du corps de l'ennemi)
        self.vitesse_y = random.uniform(-6, -3)
        self.vitesse_x = random.uniform(-2, 2)
        self.gravite = 0.5

    def update(self):
        self.vitesse_y += self.gravite
        self.hitbox.y += self.vitesse_y
        self.hitbox.x += self.vitesse_x
        
        if self.hitbox.bottom >= SOL_Y + 10:
            self.hitbox.bottom = SOL_Y + 10
            self.vitesse_y = 0
            self.vitesse_x = 0 # S'arrête de glisser
            
        self.rect.center = self.hitbox.center