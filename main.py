import pygame
import sys
import os
import random
import math
import json
from parametres import *; sauvegarder_touches 
from entites.joueur import Joueur
from entites.ennemi import Ennemi
from entites.coequipier import Coequipier
from entites.loot import Loot

pygame.init()
pygame.mixer.set_num_channels(16) 
ecran = pygame.display.set_mode((LARGEUR_ECRAN, HAUTEUR_ECRAN), pygame.FULLSCREEN | pygame.SCALED)
surface_principale = pygame.Surface((LARGEUR_ECRAN, HAUTEUR_ECRAN)) 

pygame.mouse.set_visible(False)
pygame.display.set_caption("Action Survival 2D - L'Ombre Solaire")
horloge = pygame.time.Clock()

pygame.font.init()
police_menu = pygame.font.SysFont("Arial", 36)
police_titre = pygame.font.SysFont("Arial", 60, bold=True)
police_bouton = pygame.font.SysFont("Arial", 24, bold=True)
police_desc = pygame.font.SysFont("Arial", 16, bold=True)
police_kills = pygame.font.SysFont("Impact", 45) 
police_carte = pygame.font.SysFont("Arial", 24, bold=True)
police_or = pygame.font.SysFont("Impact", 35)
police_combo = pygame.font.SysFont("Impact", 60, italic=True) 

chemin_bgm = os.path.join("assets", "audio", "background.wav")
def jouer_musique(boss=False):
    try:
        piste = os.path.join("assets", "audio", "boss.wav") if boss and os.path.exists(os.path.join("assets", "audio", "boss.wav")) else chemin_bgm
        if os.path.exists(piste):
            pygame.mixer.music.load(piste)
            pygame.mixer.music.set_volume(0.3)
            pygame.mixer.music.play(-1) 
    except: pass
jouer_musique()

dossier_backgrounds = os.path.join("assets", "images", "backgrounds")
tous_les_decors = [] 
if os.path.exists(dossier_backgrounds):
    for element in os.listdir(dossier_backgrounds):
        chemin_sd = os.path.join(dossier_backgrounds, element)
        if os.path.isdir(chemin_sd):
            calques = [pygame.transform.scale(pygame.image.load(os.path.join(chemin_sd, f)).convert_alpha(), (LARGEUR_ECRAN, HAUTEUR_ECRAN)) for f in sorted(os.listdir(chemin_sd)) if f.endswith((".png", ".jpg", ".jpeg"))]
            if len(calques) > 0: tous_les_decors.append(calques)
index_bg_actuel, camera_x, camera_x_menu = 0, 0, 0 

dossier_heros_base = os.path.join("assets", "images", "heros")
liste_heros = [d for d in os.listdir(dossier_heros_base) if os.path.isdir(os.path.join(dossier_heros_base, d))] if os.path.exists(dossier_heros_base) else ["shinobi"]
index_heros_choisi = 0 

icones_heros = {}
for h in liste_heros:
    try:
        f = pygame.image.load(os.path.join("assets", "images", "heros", h, "Idle.png")).convert_alpha()
        l_f = f.get_width() // max(1, f.get_width() // f.get_height())
        icones_heros[h] = pygame.transform.scale_by(f.subsurface(pygame.Rect(0, 0, l_f, f.get_height())), 2.5)
    except:
        sec = pygame.Surface((50, 70)); sec.fill((0, 255, 100)); icones_heros[h] = sec

dossier_ennemis = os.path.join("assets", "images", "ennemis")
types_ennemis_complets = [d for d in os.listdir(dossier_ennemis) if os.path.isdir(os.path.join(dossier_ennemis, d))] if os.path.exists(dossier_ennemis) else ["orc_berserk"]
noms_bosses = ["gorgon_1", "gorgon_2", "gorgon_3", "kitsune", "yamabushi_tengu", "karasu_tengu"]
bosses_possibles = [d for d in types_ennemis_complets if d.lower() in noms_bosses]
ennemis_normaux = [d for d in types_ennemis_complets if d.lower() not in noms_bosses] or types_ennemis_complets

heros = None 
groupe_sprites, groupe_ennemis, groupe_effets, groupe_coequipiers, groupe_loot, groupe_particules = [pygame.sprite.Group() for _ in range(6)]

def charger_progression():
    if os.path.exists("progression.json"):
        try:
            with open("progression.json", "r") as f: d = json.load(f)
            upgrades = d.get("upgrades")
            if not upgrades: upgrades = {"pv": d.get("bonus_pv", 0) // 100, "degats": d.get("bonus_degats", 0) // 10, "vitesse": 0, "dash_cd": 0, "ultime": 0, "sauts": 0}
            return (d.get("niveau_max", 1), d.get("or_total", 0), upgrades)
        except: pass
    return 1, 0, {"pv": 0, "degats": 0, "vitesse": 0, "dash_cd": 0, "ultime": 0, "sauts": 0}

def sauvegarder_progression(nv, or_t, ups):
    with open("progression.json", "w") as f: json.dump({"niveau_max": nv, "or_total": or_t, "upgrades": ups}, f)

niveau_max_debloque, or_total_joueur, upgrades_joueur = charger_progression()
bonus_degats_joueur = upgrades_joueur["degats"] * 10

biome_affiche, niveau_actuel, prochain_palier, delai_spawn_actuel = 1, 1, 5, 3000
niveau_en_attente = 1 
est_niveau_boss = False 
pygame.time.set_timer(SPAWN_ENNEMI, delai_spawn_actuel)

hit_stop_frames, screen_shake_frames, timer_victoire, timer_defaite, cooldown_appel_coequipiers, slow_mo_frames = 0, 0, 0, 0, 0, 0 
notifications_boutique = [] 

etat_jeu, etat_precedent, action_a_redefinir = "ACCUEIL", "ACCUEIL", None 

x_btn = LARGEUR_ECRAN // 2 - 200
bouton_start, bouton_parametres, bouton_quitter = pygame.Rect(x_btn, 300, 400, 60), pygame.Rect(x_btn, 400, 400, 60), pygame.Rect(x_btn, 500, 400, 60)

btn_biome_prec, btn_biome_suiv = pygame.Rect(50, HAUTEUR_ECRAN//2 - 30, 60, 60), pygame.Rect(LARGEUR_ECRAN - 110, HAUTEUR_ECRAN//2 - 30, 60, 60)
btn_retour_carte, btn_boutique_carte = pygame.Rect(20, 20, 150, 40), pygame.Rect(LARGEUR_ECRAN - 170, 90, 150, 40) 
btn_pause_reprendre = pygame.Rect(LARGEUR_ECRAN//2 - 200, 250, 400, 60)
btn_pause_params = pygame.Rect(LARGEUR_ECRAN//2 - 200, 350, 400, 60)
btn_pause_quitter = pygame.Rect(LARGEUR_ECRAN//2 - 200, 450, 400, 60)

# --- NOUVEAU : FORMULE DE PRIX LINÉAIRE (Incrément au lieu de Multiplicateur) ---
# Format : (id, Titre, Desc, Prix_Base, Increment_par_Niveau, Lvl_Req, Couleur)
BOUTIQUE_ITEMS = [
    ("pv", "SANTÉ MAX", "Augmente la vie maximum (+100)", 100, 50, 1, (200, 50, 50)),
    ("degats", "FORCE", "Dégâts des attaques augmentés (+10)", 150, 75, 1, (50, 150, 255)),
    ("vitesse", "AGILITÉ", "Vitesse de déplacement accrue (+1)", 300, 150, 10, (50, 255, 150)),
    ("dash_cd", "RÉFLEXES", "Rechargement du Dash réduit (-10%)", 400, 200, 20, (255, 200, 50)),
    ("ultime", "ÉVEIL", "Gain de la Jauge Ultime par kill (+5%)", 600, 300, 30, (180, 50, 255)),
    ("sauts", "PLUMES", "Autorise un saut consécutif (+1)", 1500, 500, 40, (200, 200, 200))
]
MAX_LEVELS = {"pv": 99, "degats": 99, "vitesse": 4, "dash_cd": 4, "ultime": 5, "sauts": 1}

panneau_w, panneau_h = 800, 550
panneau_x, panneau_y = LARGEUR_ECRAN//2 - panneau_w//2, HAUTEUR_ECRAN//2 - panneau_h//2
btn_retour_boutique = pygame.Rect(LARGEUR_ECRAN//2 - 150, panneau_y + 480, 300, 45)

en_cours = True

while en_cours:
    pos_souris = pygame.mouse.get_pos() 
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT: 
            sauvegarder_progression(niveau_max_debloque, or_total_joueur, upgrades_joueur)
            en_cours = False
            
        if event.type == SPAWN_ENNEMI and etat_jeu == "JEU":
            if not est_niveau_boss:
                type_choisi = random.choice(ennemis_normaux)
                nouvel_ennemi = Ennemi(camera_x + LARGEUR_ECRAN + random.randint(50, 500), 400, nom_dossier=type_choisi, niveau=niveau_actuel)
                groupe_ennemis.add(nouvel_ennemi); groupe_sprites.add(nouvel_ennemi)
            
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1: 
            if etat_jeu == "ACCUEIL":
                if bouton_start.collidepoint(pos_souris): etat_jeu, biome_affiche = "CARTE", ((niveau_max_debloque - 1) // 10) + 1
                elif bouton_parametres.collidepoint(pos_souris): etat_precedent, etat_jeu = "ACCUEIL", "MENU" 
                elif bouton_quitter.collidepoint(pos_souris): 
                    sauvegarder_progression(niveau_max_debloque, or_total_joueur, upgrades_joueur)
                    en_cours = False 

            elif etat_jeu == "CARTE":
                if btn_retour_carte.collidepoint(pos_souris): etat_jeu = "ACCUEIL"
                elif btn_boutique_carte.collidepoint(pos_souris): etat_jeu = "BOUTIQUE" 
                elif btn_biome_prec.collidepoint(pos_souris) and biome_affiche > 1: biome_affiche -= 1
                elif btn_biome_suiv.collidepoint(pos_souris) and biome_affiche < 10: biome_affiche += 1
                else:
                    for i in range(10):
                        nv = ((biome_affiche - 1) * 10 + 1) + i
                        if pygame.Rect(250 + (i * 85) - 30, 400 - (abs(i - 4.5) * 40) - 30, 60, 60).collidepoint(pos_souris) and nv <= niveau_max_debloque:
                            niveau_en_attente = nv
                            etat_jeu = "SELECTION_HEROS"

            elif etat_jeu == "SELECTION_HEROS":
                if btn_retour_carte.collidepoint(pos_souris): etat_jeu = "CARTE"
                else:
                    cols, esp_x, esp_y = 4, 160, 180
                    start_x, start_y = panneau_x + 110, panneau_y + 110
                    
                    for i, h_nom in enumerate(liste_heros):
                        btn = pygame.Rect(start_x + (i % cols)*esp_x, start_y + (i // cols)*esp_y, 110, 140)
                        if btn.collidepoint(pos_souris):
                            index_heros_choisi = i
                            niveau_actuel = niveau_en_attente
                            prochain_palier = 10 + (niveau_actuel * 5) 
                            delai_spawn_actuel = max(600, 3000 - (niveau_actuel * 100))
                            cooldown_appel_coequipiers = 0 
                            
                            est_niveau_boss = (niveau_actuel % 5 == 0) and len(bosses_possibles) > 0
                            
                            heros = Joueur(100, 400, nom_dossier=liste_heros[index_heros_choisi])
                            heros.or_accumule = or_total_joueur 
                            heros.pv_max += upgrades_joueur["pv"] * 100
                            heros.pv = heros.pv_max 
                            heros.vitesse_deplacement += upgrades_joueur["vitesse"]
                            heros.cd_max_dash = max(20, 60 - (upgrades_joueur["dash_cd"] * 10))
                            heros.gain_ultime_kill = 15 + (upgrades_joueur["ultime"] * 5)
                            heros.sauts_max = 2 + upgrades_joueur["sauts"]
                            heros.sauts_restants = heros.sauts_max
                            bonus_degats_joueur = upgrades_joueur["degats"] * 10
                            
                            for grp in [groupe_sprites, groupe_ennemis, groupe_effets, groupe_coequipiers, groupe_loot, groupe_particules]: grp.empty()
                            groupe_sprites.add(heros)
                            camera_x = 0
                            
                            if est_niveau_boss:
                                boss = Ennemi(camera_x + LARGEUR_ECRAN + 300, 400, random.choice(bosses_possibles), niveau_actuel)
                                groupe_ennemis.add(boss); groupe_sprites.add(boss)
                                jouer_musique(boss=True)
                                pygame.time.set_timer(SPAWN_ENNEMI, 0) 
                            else: 
                                jouer_musique(boss=False)
                                pygame.time.set_timer(SPAWN_ENNEMI, delai_spawn_actuel)
                                
                            if len(tous_les_decors) > 0: index_bg_actuel = min((niveau_actuel - 1) // 10, len(tous_les_decors) - 1)
                            etat_jeu = "JEU"

            elif etat_jeu == "BOUTIQUE":
                if btn_retour_boutique.collidepoint(pos_souris):
                    sauvegarder_progression(niveau_max_debloque, or_total_joueur, upgrades_joueur)
                    etat_jeu = "CARTE"
                
                for i, item in enumerate(BOUTIQUE_ITEMS):
                    col, row = i % 2, i // 2
                    btn = pygame.Rect(panneau_x + 35 + col*370, panneau_y + 120 + row*115, 350, 105)
                    is_unlocked = niveau_max_debloque >= item[5]
                    current_lvl = upgrades_joueur[item[0]]
                    
                    # --- NOUVEAU : CALCUL DU PRIX LINÉAIRE ---
                    cout = item[3] + (item[4] * current_lvl)
                    
                    if btn.collidepoint(pos_souris) and is_unlocked and or_total_joueur >= cout and current_lvl < MAX_LEVELS[item[0]]:
                        or_total_joueur -= cout
                        upgrades_joueur[item[0]] += 1
                        notifications_boutique.append([btn.centerx, btn.y - 10, "AMÉLIORÉ !", 60])
            
            elif etat_jeu == "PAUSE":
                if btn_pause_reprendre.collidepoint(pos_souris): etat_jeu = "JEU"
                elif btn_pause_params.collidepoint(pos_souris): etat_precedent, etat_jeu = "PAUSE", "MENU"
                elif btn_pause_quitter.collidepoint(pos_souris): 
                    etat_jeu = "CARTE"
                    jouer_musique(boss=False)

        if event.type == pygame.KEYDOWN:
            if etat_jeu == "MENU":
                if action_a_redefinir:
                    TOUCHES[action_a_redefinir], action_a_redefinir = event.key, None
                    sauvegarder_touches() 
                else:
                    if event.key == pygame.K_ESCAPE: etat_jeu = etat_precedent 
                    for i, (act, t) in enumerate(TOUCHES.items()):
                        if event.key == getattr(pygame, f'K_{i+1}', -1): action_a_redefinir = act
            
            elif etat_jeu == "JEU":
                touche, shake, boss_tue = False, 0, False
                if event.key == TOUCHES["ATTAQUE_1"]: touche, shake, boss_tue = heros.attaquer(0, groupe_ennemis, groupe_effets, groupe_loot, bonus_degats_joueur)
                if event.key == TOUCHES["ATTAQUE_2"]: touche, shake, boss_tue = heros.attaquer(1, groupe_ennemis, groupe_effets, groupe_loot, bonus_degats_joueur)
                if event.key == TOUCHES["ATTAQUE_3"]: touche, shake, boss_tue = heros.attaquer(2, groupe_ennemis, groupe_effets, groupe_loot, bonus_degats_joueur)
                if event.key == TOUCHES["ATTAQUE_4"]: touche, shake, boss_tue = heros.attaquer(3, groupe_ennemis, groupe_effets, groupe_loot, bonus_degats_joueur)
                
                if boss_tue:
                    slow_mo_frames = 120 
                    screen_shake_frames = 40
                
                if event.key == TOUCHES.get("APPEL_COEQ", pygame.K_c) and cooldown_appel_coequipiers == 0 and niveau_max_debloque >= 10 and not est_niveau_boss:
                    cooldown_appel_coequipiers = 720 
                    for c in groupe_coequipiers: c.kill()
                    groupe_coequipiers.empty()
                    heros_disps = [h for h in liste_heros if h != liste_heros[index_heros_choisi]]
                    if len(heros_disps) > 0:
                        coeq1 = Coequipier(heros.hitbox.x - 80, 400, heros_disps[0], heros)
                        groupe_coequipiers.add(coeq1); groupe_sprites.add(coeq1)
                    if niveau_max_debloque >= 30 and len(heros_disps) > 1:
                        coeq2 = Coequipier(heros.hitbox.x - 160, 400, heros_disps[1], heros)
                        groupe_coequipiers.add(coeq2); groupe_sprites.add(coeq2)

                if touche: hit_stop_frames = 4 
                if shake > 0: screen_shake_frames = max(screen_shake_frames, shake) 
                if event.key == pygame.K_b and len(tous_les_decors) > 0: index_bg_actuel = (index_bg_actuel + 1) % len(tous_les_decors)
                    
                if event.key == pygame.K_ESCAPE: etat_jeu = "PAUSE"

            elif etat_jeu == "PAUSE":
                if event.key == pygame.K_ESCAPE: etat_jeu = "JEU"

            elif etat_jeu in ["BOUTIQUE", "SELECTION_HEROS"]:
                if event.key == pygame.K_ESCAPE:
                    sauvegarder_progression(niveau_max_debloque, or_total_joueur, upgrades_joueur)
                    etat_jeu = "CARTE"

    ecran.fill((0, 0, 0))
    
    if etat_jeu == "ACCUEIL":
        camera_x_menu += 0.5 
        if len(tous_les_decors) > 0:
            for i, calque in enumerate(tous_les_decors[0]):
                decal = (camera_x_menu * (0.1 + (i * 0.2))) % LARGEUR_ECRAN
                ecran.blit(calque, (-decal, 0)); ecran.blit(calque, (-decal + LARGEUR_ECRAN, 0))
                
        ecran.blit(police_titre.render("ACTION SURVIVAL 2D", True, (0, 0, 0)), (LARGEUR_ECRAN//2 - police_titre.render("ACTION SURVIVAL 2D", True, (0, 0, 0)).get_width()//2 + 3, 103))
        ecran.blit(police_titre.render("ACTION SURVIVAL 2D", True, (255, 255, 255)), (LARGEUR_ECRAN//2 - police_titre.render("ACTION SURVIVAL 2D", True, (255, 255, 255)).get_width()//2, 100))
        
        for btn, texte, col_base in [(bouton_start, "AVENTURE (CARTE)", (70, 180, 70)), (bouton_parametres, "PARAMÈTRES", (100, 100, 150)), (bouton_quitter, "QUITTER", (180, 70, 70))]:
            c_act = (min(col_base[0]+40, 255), min(col_base[1]+40, 255), min(col_base[2]+40, 255)) if btn.collidepoint(pos_souris) else col_base
            pygame.draw.rect(ecran, c_act, btn, border_radius=10) 
            pygame.draw.rect(ecran, (255, 255, 255), btn, 3, border_radius=10) 
            ecran.blit(police_bouton.render(texte, True, (255, 255, 255)), (btn.x + btn.width//2 - police_bouton.render(texte, True, (255, 255, 255)).get_width()//2, btn.y + btn.height//2 - police_bouton.render(texte, True, (255, 255, 255)).get_height()//2))

    elif etat_jeu == "CARTE":
        if len(tous_les_decors) > 0:
            for calque in tous_les_decors[min(biome_affiche - 1, len(tous_les_decors) - 1)]: ecran.blit(calque, (0, 0))
        voile = pygame.Surface((LARGEUR_ECRAN, HAUTEUR_ECRAN), pygame.SRCALPHA); voile.fill((0, 0, 0, 170)); ecran.blit(voile, (0, 0))
        
        t_carte = police_titre.render(f"RÉGION {biome_affiche}", True, (255, 200, 0))
        ecran.blit(t_carte, (LARGEUR_ECRAN//2 - t_carte.get_width()//2, 50))
        t_or = police_or.render(f"OR : {or_total_joueur}", True, (255, 215, 0))
        ecran.blit(t_or, (LARGEUR_ECRAN - t_or.get_width() - 40, 40))
        
        pygame.draw.rect(ecran, (50, 150, 50), btn_boutique_carte, border_radius=5)
        ecran.blit(police_carte.render("Boutique", True, (255, 255, 255)), (btn_boutique_carte.x + 30, btn_boutique_carte.y + 5))
        pygame.draw.rect(ecran, (150, 50, 50), btn_retour_carte, border_radius=5)
        ecran.blit(police_carte.render("Retour", True, (255, 255, 255)), (btn_retour_carte.x + 40, btn_retour_carte.y + 5))
        
        if biome_affiche > 1: pygame.draw.rect(ecran, (100, 100, 150), btn_biome_prec, border_radius=30); ecran.blit(police_titre.render("<", True, (255, 255, 255)), (btn_biome_prec.x + 10, btn_biome_prec.y - 5))
        if biome_affiche < 10: pygame.draw.rect(ecran, (100, 100, 150), btn_biome_suiv, border_radius=30); ecran.blit(police_titre.render(">", True, (255, 255, 255)), (btn_biome_suiv.x + 15, btn_biome_suiv.y - 5))

        noeuds = [(250 + (i * 85), 400 - (abs(i - 4.5) * 40)) for i in range(10)]
        if len(noeuds) > 1:
            pygame.draw.lines(ecran, (20, 20, 20), False, noeuds, 8)
            pygame.draw.lines(ecran, (200, 200, 220), False, noeuds, 3)

        for i, pos in enumerate(noeuds):
            nv, est_deb = ((biome_affiche - 1) * 10 + 1) + i, (((biome_affiche - 1) * 10 + 1) + i) <= niveau_max_debloque
            c_noeud, rayon = (80, 80, 80), 20
            if est_deb:
                c_noeud, rayon = ((200, 0, 50), 35) if nv % 10 == 0 else ((255, 150, 0), 28) if nv % 5 == 0 else ((50, 200, 50), 20)
                if pygame.Rect(pos[0]-rayon, pos[1]-rayon, rayon*2, rayon*2).collidepoint(pos_souris):
                    rayon += 5; pygame.draw.circle(ecran, (255, 255, 255), pos, rayon + 4)
            pygame.draw.circle(ecran, c_noeud, pos, rayon); pygame.draw.circle(ecran, (255, 255, 255), pos, rayon, 3)
            txt = police_carte.render(str(nv), True, (255, 255, 255))
            ecran.blit(txt, (pos[0] - txt.get_width()//2, pos[1] - txt.get_height()//2))

    elif etat_jeu == "SELECTION_HEROS":
        if len(tous_les_decors) > 0:
            for calque in tous_les_decors[min(biome_affiche - 1, len(tous_les_decors) - 1)]: ecran.blit(calque, (0, 0))
        v = pygame.Surface((LARGEUR_ECRAN, HAUTEUR_ECRAN), pygame.SRCALPHA); v.fill((10, 10, 15, 240)); ecran.blit(v, (0, 0))
        
        pygame.draw.rect(ecran, (20, 20, 25), (panneau_x, panneau_y, panneau_w, panneau_h)) 
        pygame.draw.rect(ecran, (35, 35, 40), (panneau_x + 4, panneau_y + 4, panneau_w - 8, panneau_h - 8)) 
        pygame.draw.rect(ecran, (150, 100, 255), (panneau_x + 4, panneau_y + 4, panneau_w - 8, panneau_h - 8), 2) 
        
        t_b = police_titre.render(f"NIVEAU {niveau_en_attente} : CHOISISSEZ VOTRE HÉROS", True, (200, 150, 255))
        ecran.blit(t_b, (LARGEUR_ECRAN//2 - t_b.get_width()//2, panneau_y + 20))
        
        cols, esp_x, esp_y = 4, 160, 180
        start_x, start_y = panneau_x + 110, panneau_y + 110
        
        for i, h_nom in enumerate(liste_heros):
            btn = pygame.Rect(start_x + (i % cols)*esp_x, start_y + (i // cols)*esp_y, 110, 140)
            hover = btn.collidepoint(pos_souris)
            
            pygame.draw.rect(ecran, (70, 75, 80) if hover else (50, 55, 60), btn, border_radius=10)
            pygame.draw.rect(ecran, (255, 255, 255) if hover else (100, 100, 100), btn, 2, border_radius=10)
            
            icone = icones_heros.get(h_nom)
            if icone: ecran.blit(icone, (btn.centerx - icone.get_width()//2, btn.centery - icone.get_height()//2 - 10))
            
            t_nom = police_desc.render(h_nom.upper(), True, (255, 255, 255) if hover else (200, 200, 200))
            ecran.blit(t_nom, (btn.centerx - t_nom.get_width()//2, btn.bottom - 25))

        pygame.draw.rect(ecran, (150, 50, 50), btn_retour_carte, border_radius=5)
        ecran.blit(police_carte.render("Retour", True, (255, 255, 255)), (btn_retour_carte.x + 40, btn_retour_carte.y + 5))

    elif etat_jeu == "BOUTIQUE":
        if len(tous_les_decors) > 0: ecran.blit(tous_les_decors[0][0], (0, 0))
        v = pygame.Surface((LARGEUR_ECRAN, HAUTEUR_ECRAN), pygame.SRCALPHA); v.fill((10, 10, 15, 230)); ecran.blit(v, (0, 0))
        
        pygame.draw.rect(ecran, (20, 20, 25), (panneau_x, panneau_y, panneau_w, panneau_h)) 
        pygame.draw.rect(ecran, (35, 35, 40), (panneau_x + 4, panneau_y + 4, panneau_w - 8, panneau_h - 8)) 
        pygame.draw.rect(ecran, (200, 160, 50), (panneau_x + 4, panneau_y + 4, panneau_w - 8, panneau_h - 8), 2) 
        
        t_b = police_titre.render("MARCHAND CLANDESTIN", True, (255, 215, 0))
        ecran.blit(t_b, (LARGEUR_ECRAN//2 - t_b.get_width()//2, panneau_y + 15))
        t_o = police_or.render(f"OR DISPONIBLE : {or_total_joueur}", True, (255, 230, 100))
        ecran.blit(t_o, (LARGEUR_ECRAN//2 - t_o.get_width()//2, panneau_y + 65))
        
        for i, item in enumerate(BOUTIQUE_ITEMS):
            col, row = i % 2, i // 2
            btn = pygame.Rect(panneau_x + 35 + col*370, panneau_y + 120 + row*115, 350, 105)
            
            is_unlocked = niveau_max_debloque >= item[5]
            current_lvl = upgrades_joueur[item[0]]
            
            # --- CALCUL DU PRIX CORRIGÉ ---
            cout = item[3] + (item[4] * current_lvl) 
            is_maxed = current_lvl >= MAX_LEVELS[item[0]]
            hover = btn.collidepoint(pos_souris)
            
            pygame.draw.rect(ecran, (15, 15, 15), btn) 
            inner = (50, 55, 60) if is_unlocked else (25, 25, 30)
            if hover and is_unlocked and or_total_joueur >= cout and not is_maxed: inner = (70, 75, 80)
            pygame.draw.rect(ecran, inner, btn.inflate(-4, -4))
            
            b_col = item[6] if is_unlocked else (80, 80, 80)
            pygame.draw.rect(ecran, b_col, btn.inflate(-4, -4), 2)
            pygame.draw.rect(ecran, (min(255, b_col[0]+40), min(255, b_col[1]+40), min(255, b_col[2]+40)), btn.inflate(-8, -8), 1)
            
            if is_unlocked:
                titre = police_bouton.render(item[1], True, b_col)
                ecran.blit(titre, (btn.x + 15, btn.y + 10))
                txt_lvl = police_desc.render(f"Niv.{current_lvl}", True, (255, 255, 255))
                ecran.blit(txt_lvl, (btn.right - txt_lvl.get_width() - 15, btn.y + 15))
                txt_desc = police_desc.render(item[2], True, (200, 200, 200))
                ecran.blit(txt_desc, (btn.x + 15, btn.y + 45))
                txt_cout = police_carte.render("MAX" if is_maxed else f"Prix : {cout} Or", True, (100, 255, 100) if is_maxed else (255, 215, 0) if or_total_joueur >= cout else (200, 100, 100))
                ecran.blit(txt_cout, (btn.x + 15, btn.y + 70))
            else:
                lock = police_bouton.render(f"VERROUILLÉ", True, (150, 150, 150))
                ecran.blit(lock, (btn.x + btn.width//2 - lock.get_width()//2, btn.y + 25))
                req = police_desc.render(f"Atteignez le Niveau {item[5]} pour débloquer", True, (200, 100, 100))
                ecran.blit(req, (btn.x + btn.width//2 - req.get_width()//2, btn.y + 65))
                
        hover_ret = btn_retour_boutique.collidepoint(pos_souris)
        pygame.draw.rect(ecran, (15, 15, 15), btn_retour_boutique)
        pygame.draw.rect(ecran, (150, 50, 50) if hover_ret else (120, 40, 40), btn_retour_boutique.inflate(-4, -4))
        txt_ret = police_bouton.render("QUITTER LA BOUTIQUE", True, (255, 255, 255))
        ecran.blit(txt_ret, (btn_retour_boutique.x + btn_retour_boutique.width//2 - txt_ret.get_width()//2, btn_retour_boutique.y + 8))

        for notif in notifications_boutique[:]:
            txt = police_carte.render(notif[2], True, (255, 255, 100))
            txt.set_alpha(int((notif[3] / 60) * 255))
            ecran.blit(txt, (notif[0] - txt.get_width()//2, notif[1]))
            notif[1] -= 1; notif[3] -= 1 
            if notif[3] <= 0: notifications_boutique.remove(notif)

    elif etat_jeu in ["JEU", "VICTOIRE", "DEFAITE", "PAUSE"]:
        if etat_jeu == "JEU":
            if heros.pv <= 0: etat_jeu, timer_defaite = "DEFAITE", 150
            elif hit_stop_frames > 0: hit_stop_frames -= 1
            else:
                skip_update = False
                if slow_mo_frames > 0:
                    slow_mo_frames -= 1
                    if slow_mo_frames % 3 != 0: skip_update = True 
                
                if not skip_update:
                    if cooldown_appel_coequipiers > 0: cooldown_appel_coequipiers -= 1
                    groupe_ennemis.update(joueur=heros) 
                    heros.update(groupe_ennemis, groupe_particules)
                    groupe_coequipiers.update(groupe_ennemis, groupe_effets)
                    groupe_effets.update() 
                    groupe_loot.update()
                    groupe_particules.update() 
                    
                    for butin in groupe_loot:
                        if heros.hitbox.colliderect(butin.hitbox):
                            if butin.type_loot == "or": heros.or_accumule += random.randint(15, 25)
                            elif butin.type_loot == "vie": heros.pv = min(heros.pv_max, heros.pv + 40)
                            butin.kill()
            
            victoire_atteinte = False
            if est_niveau_boss:
                if heros.kills >= 1 and len(groupe_ennemis) == 0: victoire_atteinte = True
            else:
                if heros.kills >= prochain_palier: victoire_atteinte = True
                
            if victoire_atteinte and etat_jeu == "JEU":
                if niveau_actuel == niveau_max_debloque: niveau_max_debloque += 1
                or_total_joueur = heros.or_accumule 
                sauvegarder_progression(niveau_max_debloque, or_total_joueur, upgrades_joueur)
                etat_jeu, timer_victoire = "VICTOIRE", 150 
        
        if heros.rect.right - camera_x > LARGEUR_ECRAN // 2: camera_x = heros.rect.right - (LARGEUR_ECRAN // 2)
        if heros.rect.left - camera_x < LARGEUR_ECRAN // 4: camera_x = heros.rect.left - (LARGEUR_ECRAN // 4)
        
        surface_principale.fill((0, 0, 0))
        if len(tous_les_decors) > 0:
            for i, calque in enumerate(tous_les_decors[index_bg_actuel]):
                decalage = (camera_x * (0.1 + (i * 0.2))) % LARGEUR_ECRAN
                surface_principale.blit(calque, (-decalage, 0)); surface_principale.blit(calque, (-decalage + LARGEUR_ECRAN, 0))
                
        for sprite in groupe_sprites:
            ombre = pygame.Surface((sprite.hitbox.width, 14), pygame.SRCALPHA)
            pygame.draw.ellipse(ombre, (0, 0, 0, 120), (0, 0, sprite.hitbox.width, 14))
            surface_principale.blit(ombre, (sprite.hitbox.x - camera_x, sprite.hitbox.bottom - 7))
        for loot in groupe_loot:
            ombre = pygame.Surface((loot.hitbox.width, 8), pygame.SRCALPHA)
            pygame.draw.ellipse(ombre, (0, 0, 0, 100), (0, 0, loot.hitbox.width, 8))
            surface_principale.blit(ombre, (loot.hitbox.x - camera_x, loot.hitbox.bottom - 4))
                
        for sprite in groupe_loot: surface_principale.blit(sprite.image, (sprite.rect.x - camera_x, sprite.rect.y))
        for p in groupe_particules: surface_principale.blit(p.image, (p.rect.x - camera_x, p.rect.y))
        for sprite in groupe_sprites:
            surface_principale.blit(sprite.image, (sprite.rect.x - camera_x, sprite.rect.y))
            if hasattr(sprite, 'dessiner_barre_vie'): sprite.dessiner_barre_vie(surface_principale, camera_x)
        for effet in groupe_effets: surface_principale.blit(effet.image, (effet.rect.x - camera_x, effet.rect.y))
        
        if heros.pv > 0 and heros.pv <= (heros.pv_max * 0.25):
            pulse = int(50 + math.sin(pygame.time.get_ticks() * 0.008) * 40)
            vignette = pygame.Surface((LARGEUR_ECRAN, HAUTEUR_ECRAN), pygame.SRCALPHA)
            pygame.draw.rect(vignette, (200, 0, 0, pulse), (0, 0, LARGEUR_ECRAN, HAUTEUR_ECRAN), 20) 
            vignette.fill((150, 0, 0, int(pulse/2))) 
            surface_principale.blit(vignette, (0, 0))
            
        heros.dessiner_interface_dbz(surface_principale)
        heros.dessiner_competences(surface_principale)
        
        if heros.combo > 1:
            ratio_tps = heros.combo_timer / 180
            taille_dynamique = 40 + int(math.sin(pygame.time.get_ticks() * 0.02) * 5) + min(heros.combo, 20)
            police_dyn = pygame.font.SysFont("Impact", taille_dynamique, italic=True)
            col = (255, 200, 0) if heros.combo < 10 else (255, 100, 0) if heros.combo < 20 else (255, 50, 255)
            txt_c = police_dyn.render(f"{heros.combo} HITS !", True, col)
            txt_c.set_alpha(int(ratio_tps * 255))
            surface_principale.blit(txt_c, (LARGEUR_ECRAN - txt_c.get_width() - 50, 250))
        
        if est_niveau_boss:
            boss_actuel = next((e for e in groupe_ennemis if e.est_boss), None)
            if boss_actuel:
                bx, by, bl, bh = LARGEUR_ECRAN//2 - 300, 40, 600, 25
                pygame.draw.rect(surface_principale, (50, 50, 50), (bx, by, bl, bh), border_radius=5)
                r_boss = max(0, boss_actuel.pv / boss_actuel.pv_max)
                if r_boss > 0: pygame.draw.rect(surface_principale, (200, 0, 0), (bx, by, int(bl * r_boss), bh), border_radius=5)
                pygame.draw.rect(surface_principale, (255, 215, 0), (bx, by, bl, bh), 3, border_radius=5)
                t_n_b = police_titre.render(boss_actuel.nom_dossier.replace("_", " ").upper(), True, (255, 50, 50))
                surface_principale.blit(t_n_b, (LARGEUR_ECRAN//2 - t_n_b.get_width()//2, by - 55))
                
            if niveau_max_debloque >= 10:
                texte_appel = police_bouton.render("APPEL (C) : DÉSACTIVÉ (DUEL)", True, (255, 100, 100))
                surface_principale.blit(texte_appel, (30, 90))
        else:
            t_n = police_kills.render(f"NIVEAU : {niveau_actuel}", True, (255, 200, 0))
            t_k = police_kills.render(f"KILLS : {heros.kills} / {prochain_palier}", True, (255, 50, 50))
            l_max = max(t_n.get_width(), t_k.get_width())
            surface_principale.blit(t_n, (LARGEUR_ECRAN - l_max - 30, 20))
            surface_principale.blit(t_k, (LARGEUR_ECRAN - l_max - 30, 70))
            
            if niveau_max_debloque >= 10:
                if cooldown_appel_coequipiers > 0: texte_appel = police_bouton.render(f"APPEL (C) : {cooldown_appel_coequipiers//60}s", True, (150, 150, 150))
                else: texte_appel = police_bouton.render("APPEL (C) : PRÊT !", True, (50, 255, 50))
                surface_principale.blit(texte_appel, (30, 90))
                
        t_o = police_or.render(f"OR : {heros.or_accumule}", True, (255, 215, 0))
        surface_principale.blit(t_o, (LARGEUR_ECRAN - t_o.get_width() - 30, 125))

        if etat_jeu == "VICTOIRE":
            v = pygame.Surface((LARGEUR_ECRAN, HAUTEUR_ECRAN), pygame.SRCALPHA); v.fill((0, 0, 0, min(180, (150 - timer_victoire) * 2))); surface_principale.blit(v, (0, 0))
            t_v = police_titre.render("NIVEAU TERMINÉ !" if not est_niveau_boss else "BOSS VAINCU !", True, (255, 215, 0)); t_v.set_alpha(min(255, (150 - timer_victoire) * 3))
            surface_principale.blit(t_v, t_v.get_rect(center=(LARGEUR_ECRAN//2, HAUTEUR_ECRAN//2 - 50)))
            timer_victoire -= 1
            if timer_victoire <= 0: etat_jeu = "CARTE"; jouer_musique(boss=False)
            
        elif etat_jeu == "DEFAITE":
            v = pygame.Surface((LARGEUR_ECRAN, HAUTEUR_ECRAN), pygame.SRCALPHA); v.fill((100, 0, 0, min(180, (150 - timer_defaite) * 2))); surface_principale.blit(v, (0, 0))
            t_d = police_titre.render("VOUS ÊTES MORT", True, (255, 50, 50)); t_d.set_alpha(min(255, (150 - timer_defaite) * 3))
            surface_principale.blit(t_d, t_d.get_rect(center=(LARGEUR_ECRAN//2, HAUTEUR_ECRAN//2 - 50)))
            timer_defaite -= 1
            if timer_defaite <= 0: etat_jeu = "CARTE"; jouer_musique(boss=False)
            
        elif etat_jeu == "PAUSE":
            v = pygame.Surface((LARGEUR_ECRAN, HAUTEUR_ECRAN), pygame.SRCALPHA); v.fill((0, 0, 0, 180)); surface_principale.blit(v, (0, 0))
            t_p = police_titre.render("JEU EN PAUSE", True, (255, 255, 255))
            surface_principale.blit(t_p, (LARGEUR_ECRAN//2 - t_p.get_width()//2, 100))
            
            for btn, txt in [(btn_pause_reprendre, "Reprendre"), (btn_pause_params, "Paramètres"), (btn_pause_quitter, "Abandonner le niveau")]:
                c = (150, 150, 150) if btn.collidepoint(pos_souris) else (100, 100, 100)
                pygame.draw.rect(surface_principale, c, btn, border_radius=10); pygame.draw.rect(surface_principale, (255, 255, 255), btn, 3, border_radius=10)
                surface_principale.blit(police_bouton.render(txt, True, (255, 255, 255)), (btn.x + btn.width//2 - police_bouton.render(txt, True, (255, 255, 255)).get_width()//2, btn.y + btn.height//2 - police_bouton.render(txt, True, (255, 255, 255)).get_height()//2))

        if slow_mo_frames > 0:
            v_noir = pygame.Surface((LARGEUR_ECRAN, HAUTEUR_ECRAN), pygame.SRCALPHA)
            v_noir.fill((0, 0, 0, 100))
            surface_principale.blit(v_noir, (0, 0))

        if screen_shake_frames > 0:
            amp = min(screen_shake_frames, 12) 
            shake_x, shake_y = random.randint(-amp, amp), random.randint(-amp, amp)
            screen_shake_frames -= 1
        else: shake_x, shake_y = 0, 0
            
        ecran.blit(surface_principale, (shake_x, shake_y))

    elif etat_jeu == "MENU":
        ecran.blit(police_titre.render("PARAMÈTRES", True, (255, 200, 0)), (LARGEUR_ECRAN//2 - police_titre.render("PARAMÈTRES", True, (255, 200, 0)).get_width()//2, 80))
        y_pos, index_r = 180, 1
        for act, touche in TOUCHES.items():
            t = police_menu.render(f"{act} : [ APPUYEZ SUR UNE TOUCHE ]", True, (0, 255, 0)) if action_a_redefinir == act else police_menu.render(f"[{index_r}] Modifier {act} : {pygame.key.name(touche).upper()}", True, (255, 255, 255))
            ecran.blit(t, (LARGEUR_ECRAN//2 - 250, y_pos)); y_pos += 50; index_r += 1
        ecran.blit(police_menu.render("Appuyez sur ÉCHAP pour faire retour", True, (150, 150, 150)), (LARGEUR_ECRAN//2 - police_menu.render("Appuyez sur ÉCHAP pour faire retour", True, (150, 150, 150)).get_width()//2, y_pos + 40))
    
    cx, cy = pos_souris
    pygame.draw.circle(ecran, (255, 255, 255), (cx, cy), 8, 2)
    pygame.draw.circle(ecran, (200, 0, 0), (cx, cy), 3)
    
    pygame.display.flip()
    horloge.tick(FPS)

pygame.quit()
sys.exit()