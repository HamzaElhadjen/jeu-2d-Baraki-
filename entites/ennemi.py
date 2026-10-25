import pygame
import os
import random
from parametres import *
from entites.loot import Loot

class Ennemi(pygame.sprite.Sprite):
    font_alerte = None 

    def __init__(self, x, y, nom_dossier, niveau=1):
        super().__init__()
        
        # Initialisation de la police d'alerte (une seule fois pour tous les ennemis)
        if Ennemi.font_alerte is None:
            Ennemi.font_alerte = pygame.font.SysFont("Impact", 50)
            
        self.nom_dossier = nom_dossier
        chemin_anim = os.path.join("assets", "images", "ennemis", nom_dossier, "Attack_1.png")
        if not os.path.exists(chemin_anim): 
            chemin_anim = os.path.join("assets", "images", "ennemis", nom_dossier, "Walk.png")
            
        self.frames_marche = self.decouper_spritesheet(chemin_anim)
        
        chemin_mort = os.path.join("assets", "images", "ennemis", nom_dossier, "Dead.png")
        if not os.path.exists(chemin_mort): 
            chemin_mort = os.path.join("assets", "images", "ennemis", nom_dossier, "Death.png")
            
        if os.path.exists(chemin_mort): 
            self.frames_mort = self.decouper_spritesheet(chemin_mort)
        else: 
            self.frames_mort = [] 
            
        self.frames = self.frames_marche
        self.index_frame, self.vitesse_animation = 0, 0.15
        self.image = self.frames[0]
        self.rect, self.hitbox = self.image.get_rect(), pygame.Rect(x, y, 40, 75)
        self.est_mort = False
        
        # Détection du statut de boss
        noms_bosses = ["gorgon_1", "gorgon_2", "gorgon_3", "kitsune", "yamabushi_tengu", "karasu_tengu"]
        self.est_boss = "boss" in nom_dossier.lower() or nom_dossier.lower() in noms_bosses
        
        self.type_ia = "normal"
        self.phase_2 = False 
        
        # Vitesse Max (pour gérer l'accélération et le lissage)
        self.vitesse_actuelle_x = 0
        
        # Attribution des statistiques et comportements
        if self.est_boss:
            self.type_ia = "boss"
            self.vitesse_max = random.uniform(1.2, 1.5)
            pv_base = random.randint(3000, 4500) 
            self.hitbox = pygame.Rect(x, y, 60, 90) 
            self.degats = 40 + (niveau * 5)
            self.portee_attaque = 110 
        elif "shaman" in nom_dossier.lower() or "mage" in nom_dossier.lower(): 
            self.type_ia = "distance"
            self.vitesse_max, pv_base = random.uniform(1.0, 1.5), random.randint(25, 35)
            self.degats = 10 + (niveau * 2)
            self.portee_attaque = 250 
        elif "warrior" in nom_dossier.lower() or "knight" in nom_dossier.lower(): 
            self.type_ia = "chargeur"
            self.vitesse_max, pv_base = random.uniform(2.5, 3.5), random.randint(40, 50)
            self.degats = 20 + (niveau * 2)
            self.portee_attaque = 80 
        else: 
            self.vitesse_max, pv_base = random.uniform(1.8, 2.3), random.randint(30, 45)
            self.degats = 15 + (niveau * 2)
            self.portee_attaque = 60
            
        self.pv_max = int(pv_base * (1.0 + ((niveau - 1) * 0.25)))
        self.pv = self.pv_max
        self.vitesse_y, self.gravite, self.direction, self.delai_attaque = 0, 0.8, -1, 0 
        
        self.hit_flash_timer = 0
        self.recul_x = 0
        self.en_preparation = False
        self.timer_preparation = 0

    def decouper_spritesheet(self, chemin):
        try: 
            feuille = pygame.image.load(chemin).convert_alpha()
        except FileNotFoundError: 
            return [pygame.Surface((50, 50))]
            
        l_tot, h_tot = feuille.get_size()
        cols = max(1, l_tot // h_tot)
        l_frame = l_tot // cols
        return [pygame.transform.scale_by(feuille.subsurface(pygame.Rect(i * l_frame, 0, l_frame, h_tot)), 2.5) for i in range(cols)]
        
    def recevoir_degats(self, montant, joueur, groupe_loot=None, force_recul=0):
        if self.est_mort: 
            return False
            
        self.pv -= montant
        self.hit_flash_timer = 4 
        # Les boss subissent beaucoup moins de recul
        self.recul_x = force_recul * 0.2 if self.est_boss else force_recul 
        
        if self.pv <= 0:
            self.pv, joueur.kills, self.est_mort = 0, joueur.kills + 1, True
            
            if groupe_loot is not None:
                nb_loot = 5 if self.est_boss else 1
                for _ in range(nb_loot):
                    groupe_loot.add(Loot(self.hitbox.centerx + random.randint(-30, 30), self.hitbox.centery, "vie" if random.random() < 0.2 else "or"))
                    
            if len(self.frames_mort) > 0: 
                self.index_frame, self.frames, self.vitesse_actuelle_x = 0, self.frames_mort, 0 
            else: 
                self.kill() 
                
            return self.est_boss
            
        return False

    def appliquer_physique(self):
        self.vitesse_y += self.gravite
        self.hitbox.y += self.vitesse_y
        
        if self.hitbox.bottom >= SOL_Y: 
            self.hitbox.bottom, self.vitesse_y = SOL_Y, 0
            
        if abs(self.recul_x) > 0.5:
            self.hitbox.x += self.recul_x
            self.recul_x *= 0.8 
        else: 
            self.recul_x = 0

    def IA_comportement(self, joueur):
        if self.est_mort: 
            return 
            
        # Interruption d'attaque si l'ennemi subit un gros recul (sauf boss)
        if abs(self.recul_x) > 2 and not self.est_boss: 
            self.en_preparation = False 
            return 
        
        distance = abs(self.hitbox.centerx - joueur.hitbox.centerx)
        cible_vitesse_x = 0 # Vitesse ciblée pour le lissage
        
        # Passage en Phase 2 pour les boss
        if self.est_boss and self.pv <= self.pv_max / 2 and not self.phase_2:
            self.phase_2 = True
            self.vitesse_max *= 1.4 
            self.degats = int(self.degats * 1.3) 
        
        # Logique d'attaque télégraphiée
        if self.en_preparation:
            self.timer_preparation -= 1
            if self.timer_preparation <= 0:
                self.en_preparation = False
                
                # Exécution de l'attaque selon le type d'IA
                if self.type_ia == "distance":
                    if distance <= self.portee_attaque + 50: 
                        joueur.recevoir_degats(self.degats)
                elif self.type_ia == "chargeur":
                    self.recul_x = 18 * self.direction # Le Dash (utilisation du système physique)
                    if distance <= 120: 
                        joueur.recevoir_degats(self.degats)
                else: 
                    if distance <= self.portee_attaque + 20: 
                        joueur.recevoir_degats(self.degats)
                    
                self.delai_attaque = 40 if self.phase_2 else 60 
        else:
            if self.delai_attaque > 0: 
                self.delai_attaque -= 1
                
            self.direction = -1 if joueur.hitbox.centerx < self.hitbox.centerx else 1
            
            # Logique de déplacement
            if self.type_ia == "distance":
                if distance > self.portee_attaque: 
                    cible_vitesse_x = self.vitesse_max * self.direction
                elif distance < self.portee_attaque - 80: 
                    cible_vitesse_x = -self.vitesse_max * self.direction 
                else:
                    if self.delai_attaque == 0:
                        self.en_preparation, self.timer_preparation = True, 45 
                        
            elif self.type_ia == "chargeur":
                if distance > self.portee_attaque: 
                    cible_vitesse_x = self.vitesse_max * self.direction
                else:
                    if self.delai_attaque == 0:
                        self.en_preparation, self.timer_preparation = True, 20 
                        
            else: 
                if distance > self.portee_attaque: 
                    cible_vitesse_x = self.vitesse_max * self.direction
                else:
                    if self.delai_attaque == 0:
                        self.en_preparation, self.timer_preparation = True, (20 if self.phase_2 else 30)

        # Lissage du mouvement (Inertie)
        self.vitesse_actuelle_x += (cible_vitesse_x - self.vitesse_actuelle_x) * 0.15
        self.hitbox.x += self.vitesse_actuelle_x

    def animer(self):
        self.index_frame += self.vitesse_animation
        if self.index_frame >= len(self.frames):
            if self.est_mort: 
                self.kill()
                return
            else: 
                self.index_frame = 0 
            
        img = self.frames[int(self.index_frame)]
        self.image = pygame.transform.flip(img, True, False) if self.direction == -1 else img.copy()
        
        # Aura rouge pour la Phase 2 du Boss
        if self.phase_2 and not self.est_mort:
            self.image.fill((80, 0, 0), special_flags=pygame.BLEND_RGB_ADD)
            
        # Hit Flash blanc
        if self.hit_flash_timer > 0:
            self.hit_flash_timer -= 1
            self.image.fill((150, 150, 150), special_flags=pygame.BLEND_RGB_ADD)
            
        self.rect = self.image.get_rect()
        self.rect.midbottom = self.hitbox.midbottom

    def dessiner_barre_vie(self, ecran, camera_x):
        if self.est_mort: 
            return 
            
        x_pos, y_pos = self.hitbox.x - camera_x, self.hitbox.y - 15
        
        # On ne dessine pas de barre flottante pour le boss
        if not self.est_boss:
            pygame.draw.rect(ecran, (255, 0, 0), (x_pos, y_pos, self.hitbox.width, 5)) 
            pygame.draw.rect(ecran, (0, 255, 0), (x_pos, y_pos, self.hitbox.width * max(0, self.pv / self.pv_max), 5)) 
        
        # Symbole "!" lors de la préparation d'une attaque
        if self.en_preparation:
            txt = Ennemi.font_alerte.render("!", True, (255, 50, 50))
            shake_x, shake_y = random.randint(-2, 2), random.randint(-2, 2)
            ecran.blit(txt, (x_pos + self.hitbox.width//2 - txt.get_width()//2 + shake_x, y_pos - 45 + shake_y))

    def update(self, joueur=None):
        self.appliquer_physique()
        if joueur: 
            self.IA_comportement(joueur)
        self.animer()