import pygame
import random

class Particule(pygame.sprite.Sprite):
    def __init__(self, x, y, couleur=(200, 200, 200), duree=20, vitesse_x=0, vitesse_y=-1, rayon=5):
        super().__init__()
        self.x, self.y = x, y
        self.vitesse_x = vitesse_x
        self.vitesse_y = vitesse_y
        self.duree = duree
        self.duree_max = duree
        self.rayon = rayon
        self.couleur = couleur
        self.image = pygame.Surface((rayon*2, rayon*2), pygame.SRCALPHA)
        pygame.draw.circle(self.image, couleur, (rayon, rayon), rayon)
        self.rect = self.image.get_rect(center=(x, y))

    def update(self):
        self.x += self.vitesse_x
        self.y += self.vitesse_y
        self.duree -= 1
        
        if self.duree <= 0:
            self.kill()
        else:
            ratio = self.duree / self.duree_max
            r = max(1, int(self.rayon * ratio))
            self.image = pygame.Surface((self.rayon*2, self.rayon*2), pygame.SRCALPHA)
            pygame.draw.circle(self.image, self.couleur, (self.rayon, self.rayon), r)
            self.rect = self.image.get_rect(center=(int(self.x), int(self.y)))