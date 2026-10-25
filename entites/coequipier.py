import pygame
import os
import random
from parametres import *
from entites.effects import TexteDegat, AnimationEffet

class Coequipier(pygame.sprite.Sprite):
    def __init__(self, x, y, nom_dossier, joueur_leader):
        super().__init__()
        self.nom_dossier = nom_dossier
        self.joueur = joueur_leader 

        chemin_idle = os.path.join("assets", "images", "heros", nom_dossier, "Idle.png")
        chemin_run = os.path.join("assets", "images", "heros", nom_dossier, "Run.png")
        
        self.frames_idle = self.decouper_spritesheet(chemin_idle)
        self.frames_run = self.decouper_spritesheet(chemin_run)
        
        chemin_attack = os.path.join("assets", "images", "heros", nom_dossier, "Attack_1.png")
        if not os.path.exists(chemin_attack):
            chemin_attack = os.path.join("assets", "images", "heros", nom_dossier, "Walk.png")
        self.frames_attaque = self.decouper_spritesheet(chemin_attack)

        self.frames_actuelles = self.frames_idle
        self.index_frame = 0
        self.vitesse_animation = 0.2
        self.image = self.frames_actuelles[0]
        self.rect = self.image.get_rect()
        self.hitbox = pygame.Rect(x, y, 40, 80)
        
        self.vitesse_x, self.vitesse_y, self.vitesse_deplacement = 0, 0, 5.5
        self.gravite, self.sur_le_sol, self.regarde_a_droite = 0.8, False, True
        self.en_attaque, self.delai_attaque = False, 0
        self.son_slash = charger_son(os.path.join("assets", "audio", "slash.wav"), 0.3)

    def decouper_spritesheet(self, chemin):
        try: feuille = pygame.image.load(chemin).convert_alpha()
        except FileNotFoundError: return [pygame.Surface((50, 60))]
        l_tot, h_tot = feuille.get_size()
        cols = max(1, l_tot // h_tot)
        l_frame = l_tot // cols
        return [pygame.transform.scale_by(feuille.subsurface(pygame.Rect(i * l_frame, 0, l_frame, h_tot)), 2.5) for i in range(cols)]

    def IA_comportement(self, groupe_ennemis, groupe_effets):
        if self.en_attaque: self.vitesse_x = 0; return
        if self.delai_attaque > 0: self.delai_attaque -= 1

        ennemi_cible = None
        distance_min = 250 
        
        for ennemi in groupe_ennemis:
            if not ennemi.est_mort:
                dist = abs(self.hitbox.centerx - ennemi.hitbox.centerx)
                if dist < distance_min:
                    distance_min = dist
                    ennemi_cible = ennemi

        en_mouvement = False
        
        if ennemi_cible:
            self.regarde_a_droite = False if ennemi_cible.hitbox.centerx < self.hitbox.centerx else True
            if distance_min <= 120 and self.delai_attaque == 0: self.attaquer(ennemi_cible, groupe_effets)
            elif distance_min > 90:
                direction = 1 if self.regarde_a_droite else -1
                self.vitesse_x = self.vitesse_deplacement * direction
                en_mouvement = True
        else:
            distance_joueur = abs(self.hitbox.centerx - self.joueur.hitbox.centerx)
            if distance_joueur > 120:
                if self.joueur.hitbox.centerx < self.hitbox.centerx: self.regarde_a_droite, self.vitesse_x = False, -self.vitesse_deplacement
                else: self.regarde_a_droite, self.vitesse_x = True, self.vitesse_deplacement
                en_mouvement = True
            else: self.vitesse_x, self.regarde_a_droite = 0, self.joueur.regarde_a_droite 

        self.hitbox.x += self.vitesse_x
        if en_mouvement:
            if self.frames_actuelles != self.frames_run: self.frames_actuelles, self.index_frame = self.frames_run, 0
        else:
            if self.frames_actuelles != self.frames_idle: self.frames_actuelles, self.index_frame = self.frames_idle, 0

    def attaquer(self, ennemi_cible, groupe_effets):
        self.en_attaque, self.index_frame, self.frames_actuelles, self.delai_attaque = True, 0, self.frames_attaque, 90 
        if self.son_slash: self.son_slash.play()
        
        portee = 120
        hitbox_coup = pygame.Rect(self.hitbox.right if self.regarde_a_droite else self.hitbox.left - portee, self.hitbox.y, portee, self.hitbox.height)
        groupe_effets.add(AnimationEffet(hitbox_coup.centerx, hitbox_coup.centery, os.path.join("slash", str(random.choice([1, 2, 3]))), self.regarde_a_droite))
        
        if hitbox_coup.colliderect(ennemi_cible.hitbox):
            degats = 25
            # Force de recul à 0
            ennemi_cible.recevoir_degats(degats, self.joueur, None, 0) 
            groupe_effets.add(TexteDegat(ennemi_cible.hitbox.centerx, ennemi_cible.hitbox.top, degats))

    def appliquer_gravite(self):
        self.vitesse_y += self.gravite
        self.hitbox.y += self.vitesse_y 
        if self.hitbox.bottom >= SOL_Y: self.hitbox.bottom, self.vitesse_y, self.sur_le_sol = SOL_Y, 0, True
        else: self.sur_le_sol = False

    def animer(self):
        self.index_frame += self.vitesse_animation
        if self.index_frame >= len(self.frames_actuelles):
            if self.en_attaque: self.en_attaque, self.frames_actuelles = False, self.frames_idle
            self.index_frame = 0
            
        img = self.frames_actuelles[int(self.index_frame)]
        self.image = img if self.regarde_a_droite else pygame.transform.flip(img, True, False)
        self.rect = self.image.get_rect()
        self.rect.midbottom = self.hitbox.midbottom

    def update(self, groupe_ennemis, groupe_effets):
        self.IA_comportement(groupe_ennemis, groupe_effets)
        self.appliquer_gravite()
        self.animer()