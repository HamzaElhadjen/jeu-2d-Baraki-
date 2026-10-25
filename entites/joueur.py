import pygame
import os
import random
from parametres import *
from entites.effects import TexteDegat, AnimationEffet
from entites.particules import Particule 

class Joueur(pygame.sprite.Sprite):
    def __init__(self, x, y, nom_dossier="shinobi"):
        super().__init__()
        self.nom_dossier = nom_dossier
        chemin_idle = os.path.join("assets", "images", "heros", nom_dossier, "Idle.png")
        chemin_run = os.path.join("assets", "images", "heros", nom_dossier, "Run.png")
        self.frames_idle = self.decouper_spritesheet(chemin_idle)
        self.frames_run = self.decouper_spritesheet(chemin_run) 
        self.est_invincible = False 
        
        if nom_dossier.lower() == "fire_wizard": fichiers_attaques, self.type_attaques = ["Attack_1.png", "Attack_2.png", "Fireball.png"], ["melee", "melee", "distance"]
        elif nom_dossier.lower() == "kitsuni": fichiers_attaques, self.type_attaques = ["Attack_1.png", "Fire_1.png", "Fire_2.png"], ["melee", "distance", "zone"]
        elif nom_dossier.lower() == "shinobi": fichiers_attaques, self.type_attaques = ["Attack_1.png", "Attack_2.png", "Shield.png"], ["melee", "melee", "defense"]
        elif nom_dossier.lower() == "enchantress": fichiers_attaques, self.type_attaques = ["Attack_1.png", "Attack_2.png", "Attack_3.png", "Attack_4.png"], ["melee", "melee", "distance", "ultime"]
        else: fichiers_attaques, self.type_attaques = ["Attack_1.png", "Attack_2.png", "Attack_3.png"], ["melee", "melee", "melee"]

        self.frames_attaques = [self.decouper_spritesheet(os.path.join("assets", "images", "heros", nom_dossier, f)) for f in fichiers_attaques]
        
        self.frames_actuelles, self.index_frame, self.vitesse_animation = self.frames_idle, 0, 0.2
        self.image = self.frames_actuelles[0]
        self.rect, self.hitbox = self.image.get_rect(), pygame.Rect(x, y, 40, 80) 
        
        self.pv_max, self.pv, self.kills, self.jauge_ultime, self.or_accumule = 300, 300, 0, 0, 0 
        
        self.cooldown_atk2, self.cooldown_atk3 = 0, 0
        self.vitesse_x, self.vitesse_y, self.vitesse_deplacement = 0, 0, 6
        self.force_saut, self.gravite, self.sur_le_sol, self.sauts_max, self.sauts_restants, self.touche_saut_relachee = -14, 0.8, False, 2, 2, True
        self.en_dash, self.duree_dash, self.cooldown_dash = False, 0, 0
        self.regarde_a_droite, self.en_attaque = True, False 
        
        self.cd_max_dash = 60 
        self.gain_ultime_kill = 15 
        
        self.invincible_timer = 0
        self.hit_flash_timer = 0
        
        self.combo = 0
        self.combo_timer = 0
        
        self.son_slash = charger_son(os.path.join("assets", "audio", "slash.wav"))
        self.son_hit = charger_son(os.path.join("assets", "audio", "attack.wav"))

    def decouper_spritesheet(self, chemin):
        try: feuille = pygame.image.load(chemin).convert_alpha()
        except FileNotFoundError: return [pygame.Surface((50, 60))]
        l_tot, h_tot = feuille.get_size()
        cols = max(1, l_tot // h_tot)
        l_frame = l_tot // cols
        return [pygame.transform.scale_by(feuille.subsurface(pygame.Rect(i * l_frame, 0, l_frame, h_tot)), 2.5) for i in range(cols)]

    def attaquer(self, index_attaque, groupe_ennemis, groupe_effets, groupe_loot, bonus_degats=0):
        if index_attaque >= len(self.frames_attaques): return False, 0, False 
            
        if not self.en_attaque:
            type_action = self.type_attaques[index_attaque]
            
            force_recul, force_shake = 0, 0
            chemin_effet = ""
            
            # --- NOUVEAU : ATTRIBUTION PRÉCISE DES EFFETS DE SLASH ---
            if index_attaque == 0: 
                portee, degats, force_recul, force_shake = 120, 80, 2, 5 
                chemin_effet = os.path.join("slash", str(random.choice([1, 2, 3, 4])))
            elif index_attaque == 1:
                if self.cooldown_atk2 > 0: return False, 0, False
                self.cooldown_atk2, portee, degats, force_recul, force_shake = 120, 120, 130, 8, 10 
                chemin_effet = os.path.join("slash", str(random.choice([5, 6, 7])))
            elif index_attaque == 2:
                if self.cooldown_atk3 > 0: return False, 0, False
                self.cooldown_atk3, portee, degats, force_recul, force_shake = 300, (400 if type_action == "distance" else 200), 200, 15, 15 
                chemin_effet = os.path.join("slash", str(random.choice([8, 9, 10])))
            elif index_attaque == 3 or type_action == "ultime":
                if self.jauge_ultime < 100: return False, 0, False
                self.jauge_ultime, portee, degats, force_recul, force_shake = 0, 600, 100, 30, 25 
                chemin_effet = "explosion" # Dossier "explosion"
                
            if type_action == "defense":
                self.est_invincible, self.en_attaque, self.index_frame, self.frames_actuelles = True, True, 0, self.frames_attaques[index_attaque]
                return False, 0, False
                
            self.en_attaque, self.index_frame, self.frames_actuelles = True, 0, self.frames_attaques[index_attaque]
            if self.son_slash: self.son_slash.play()
            degats += bonus_degats 
                
            hitbox_coup = pygame.Rect(self.hitbox.centerx - portee, self.hitbox.y, portee * 2, self.hitbox.height) if type_action == "zone" else pygame.Rect(self.hitbox.right if self.regarde_a_droite else self.hitbox.left - portee, self.hitbox.y, portee, self.hitbox.height)
            groupe_effets.add(AnimationEffet(hitbox_coup.centerx, hitbox_coup.centery, chemin_effet, self.regarde_a_droite))
            
            a_fait_mouche, boss_tue, direction_recul = False, False, 1 if self.regarde_a_droite else -1
            
            for ennemi in groupe_ennemis:
                if hitbox_coup.colliderect(ennemi.hitbox):
                    a_fait_mouche = True
                    pv_avant = ennemi.pv
                    
                    est_mort_boss = ennemi.recevoir_degats(degats, self, groupe_loot, force_recul * direction_recul) 
                    if est_mort_boss: boss_tue = True
                    
                    if ennemi.pv <= 0 and pv_avant > 0: self.jauge_ultime = min(100, self.jauge_ultime + self.gain_ultime_kill)
                    
                    self.combo += 1
                    self.combo_timer = 180 
                    
                    if self.son_hit:
                        self.son_hit.set_volume(random.uniform(0.3, 0.6))
                        self.son_hit.play()
                    groupe_effets.add(TexteDegat(ennemi.hitbox.centerx, ennemi.hitbox.top, degats))
                    
            return a_fait_mouche, force_shake, boss_tue 
        return False, 0, False

    def recevoir_degats(self, montant):
        if self.est_invincible or self.en_dash or self.invincible_timer > 0: return 
        self.pv -= montant
        self.invincible_timer = 60 
        self.hit_flash_timer = 4
        if self.pv <= 0: self.pv = 0

    def appliquer_gravite(self, groupe_particules):
        self.vitesse_y += self.gravite
        self.hitbox.y += self.vitesse_y 
        if self.hitbox.bottom >= SOL_Y:
            if not self.sur_le_sol: 
                for _ in range(5): groupe_particules.add(Particule(self.hitbox.centerx, self.hitbox.bottom, vitesse_x=random.uniform(-2, 2)))
            self.hitbox.bottom, self.vitesse_y, self.sur_le_sol, self.sauts_restants = SOL_Y, 0, True, self.sauts_max 
        else: self.sur_le_sol = False

    def deplacer(self, groupe_ennemis, groupe_particules):
        if self.en_attaque: self.vitesse_x = 0; return

        touches = pygame.key.get_pressed()
        self.vitesse_x, en_mouvement = 0, False
        
        if self.combo_timer > 0:
            self.combo_timer -= 1
            if self.combo_timer <= 0: self.combo = 0 
            
        if self.invincible_timer > 0: self.invincible_timer -= 1
        if self.cooldown_dash > 0: self.cooldown_dash -= 1
        if self.cooldown_atk2 > 0: self.cooldown_atk2 -= 1
        if self.cooldown_atk3 > 0: self.cooldown_atk3 -= 1
            
        if touches[TOUCHES["DASH"]] and self.cooldown_dash == 0 and not self.en_dash:
            self.en_dash, self.duree_dash, self.cooldown_dash = True, 12, self.cd_max_dash 
            if self.son_slash: self.son_slash.play() 

        if self.en_dash:
            self.vitesse_x, self.vitesse_y = (18 if self.regarde_a_droite else -18), 0 
            self.duree_dash -= 1
            if self.duree_dash <= 0: self.en_dash = False
            if random.random() < 0.5: groupe_particules.add(Particule(self.hitbox.centerx, self.hitbox.bottom, vitesse_x=random.uniform(-1, 1)))
        else:
            if touches[TOUCHES["GAUCHE"]]: self.vitesse_x, self.regarde_a_droite, en_mouvement = -self.vitesse_deplacement, False, True
            if touches[TOUCHES["DROITE"]]: self.vitesse_x, self.regarde_a_droite, en_mouvement = self.vitesse_deplacement, True, True
            if touches[TOUCHES["SAUT"]]:
                if self.touche_saut_relachee and self.sauts_restants > 0:
                    self.vitesse_y, self.sauts_restants, self.touche_saut_relachee = self.force_saut, self.sauts_restants - 1, False
                    for _ in range(3): groupe_particules.add(Particule(self.hitbox.centerx, self.hitbox.bottom, vitesse_x=random.uniform(-1, 1)))
            else: self.touche_saut_relachee = True
            
        hitbox_future = self.hitbox.copy()
        hitbox_future.x += self.vitesse_x
        for ennemi in groupe_ennemis:
            if hitbox_future.colliderect(ennemi.hitbox):
                if not self.en_dash: self.vitesse_x = 0
                break
                
        self.hitbox.x += self.vitesse_x
        
        if en_mouvement:
            if self.frames_actuelles != self.frames_run: self.frames_actuelles, self.index_frame = self.frames_run, 0
        else:
            if self.frames_actuelles != self.frames_idle: self.frames_actuelles, self.index_frame = self.frames_idle, 0

    def animer(self):
        self.index_frame += self.vitesse_animation
        if self.index_frame >= len(self.frames_actuelles):
            if self.en_attaque: self.en_attaque, self.est_invincible, self.frames_actuelles = False, False, self.frames_idle
            self.index_frame = 0
            
        img = self.frames_actuelles[int(self.index_frame)]
        self.image = img if self.regarde_a_droite else pygame.transform.flip(img, True, False)
        
        if self.invincible_timer > 0:
            if (self.invincible_timer // 4) % 2 == 0: self.image.set_alpha(100)
            else: self.image.set_alpha(255)
        else: self.image.set_alpha(255)
            
        if self.hit_flash_timer > 0:
            self.hit_flash_timer -= 1
            self.image.fill((150, 150, 150), special_flags=pygame.BLEND_RGB_ADD)
            
        self.rect = self.image.get_rect()
        self.rect.midbottom = self.hitbox.midbottom

    def dessiner_interface_dbz(self, surface):
        if self.pv <= 0: return
        couleurs = [(255, 0, 0), (255, 128, 0), (255, 255, 0), (0, 255, 0), (0, 255, 255), (0, 0, 255), (128, 0, 128)]
        nb_c = len(couleurs)
        niv = int((self.pv - 1) // 100) 
        pv_bar = int(self.pv % 100)
        if pv_bar == 0: pv_bar = 100
        x, y, l_max, h = 30, 30, 300, 25

        if niv > 0: pygame.draw.rect(surface, couleurs[(niv - 1) % nb_c], (x, y, l_max, h), border_radius=5)
        else: pygame.draw.rect(surface, (50, 50, 50), (x, y, l_max, h), border_radius=5)

        l_act = int((pv_bar / 100) * l_max)
        if l_act > 0: pygame.draw.rect(surface, couleurs[niv % nb_c], (x, y, l_act, h), border_radius=5)
        pygame.draw.rect(surface, (255, 255, 255), (x, y, l_max, h), 3, border_radius=5)
        surface.blit(pygame.font.SysFont("Arial", 28, bold=True).render(f"x{niv + 1}", True, (255, 255, 255)), (x + l_max + 15, y - 2))

        y_ult = y + h + 5
        pygame.draw.rect(surface, (50, 50, 50), (x, y_ult, l_max, 10), border_radius=3)
        l_ult = int((self.jauge_ultime / 100) * l_max)
        if l_ult > 0: pygame.draw.rect(surface, (180, 50, 255), (x, y_ult, l_ult, 10), border_radius=3)
        pygame.draw.rect(surface, (255, 255, 255), (x, y_ult, l_max, 10), 1, border_radius=3)

    def dessiner_competences(self, surface):
        l_box, h_box, esp = 60, 60, 20
        x_d = (LARGEUR_ECRAN - ((l_box * 5) + (esp * 4))) // 2
        y_d = HAUTEUR_ECRAN - h_box - 20 

        font_t, font_cd = pygame.font.SysFont("Arial", 16, bold=True), pygame.font.SysFont("Impact", 28)
        def fmt_key(c):
            n = pygame.key.name(c).upper()
            return "L-SHIFT" if n == "LEFT SHIFT" else "SPACE" if n == "SPACE" else n

        slots = [
            ("DASH", fmt_key(TOUCHES["DASH"]), self.cooldown_dash, self.cd_max_dash),
            ("ATK 1", fmt_key(TOUCHES["ATTAQUE_1"]), 0, 1),
            ("ATK 2", fmt_key(TOUCHES["ATTAQUE_2"]), self.cooldown_atk2, 120),
            ("ATK 3", fmt_key(TOUCHES["ATTAQUE_3"]), self.cooldown_atk3, 300),
            ("ULTIME", fmt_key(TOUCHES["ATTAQUE_4"]), 100 - self.jauge_ultime, 100) 
        ]

        for i, (nom, t, cd_act, cd_max) in enumerate(slots):
            x = x_d + i * (l_box + esp)
            r_box = pygame.Rect(x, y_d, l_box, h_box)
            pygame.draw.rect(surface, (30, 30, 40), r_box, border_radius=8)
            pygame.draw.rect(surface, (150, 150, 150), r_box, 2, border_radius=8)
            surface.blit(font_t.render(t, True, (200, 200, 200)), (x + 5, y_d + 5))

            if cd_act > 0:
                h_cd = int(h_box * (cd_act / cd_max))
                voile = pygame.Surface((l_box, h_cd), pygame.SRCALPHA)
                voile.fill((0, 0, 0, 180)) 
                surface.blit(voile, (x, y_d + (h_box - h_cd)))
                txt_cd = font_cd.render(f"{int(self.jauge_ultime)}%" if nom == "ULTIME" else str((cd_act // 60) + 1), True, (180, 100, 255) if nom == "ULTIME" else (255, 80, 80))
                surface.blit(txt_cd, (x + l_box//2 - txt_cd.get_width()//2, y_d + h_box//2 - txt_cd.get_height()//2 + 5))
            else:
                pygame.draw.rect(surface, (200, 50, 255) if nom == "ULTIME" else (50, 255, 50), r_box, 3, border_radius=8)
                txt_ok = font_cd.render("MAX" if nom == "ULTIME" else "OK", True, (220, 150, 255) if nom == "ULTIME" else (100, 255, 100))
                surface.blit(txt_ok, (x + l_box//2 - txt_ok.get_width()//2, y_d + h_box//2 - txt_ok.get_height()//2 + 5))

    def update(self, groupe_ennemis, groupe_particules):
        self.deplacer(groupe_ennemis, groupe_particules)
        self.appliquer_gravite(groupe_particules)
        self.animer()