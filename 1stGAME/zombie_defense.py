"""
=============================================================
  ZOMBIE DEFENSE  —  Pygame Platformer  v2.0
=============================================================
  HOW TO RUN:
    1.  pip install pygame
    2.  Copy this file into your  1st GAME  folder
        (same level as background_3, Soldier_2, Wild Zombie,
         Zombie Man, Zombie Woman folders)
    3.  python zombie_defense.py

  CONTROLS:
    A / D  or  ←/→     — move left / right
    W / SPACE  or  ↑   — jump
    S  or  ↓            — crouch
    LEFT MOUSE          — shoot  (aims at cursor)
    R                   — restart after Game Over / Win
    ESC                 — quit
=============================================================
"""

import pygame, sys, math, random, os
from pathlib import Path

# ─────────────────────────────────────────────────────────
#  PATHS  (game lives inside 1st GAME folder)
# ─────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent

def asset(*parts):
    return str(BASE_DIR / Path(*parts))


# ─────────────────────────────────────────────────────────
#  CONSTANTS
# ─────────────────────────────────────────────────────────
SCREEN_W, SCREEN_H = 1280, 720
FPS       = 60
GRAVITY   = 0.55
GROUND_Y  = SCREEN_H - 110
SOUND_GUN    = "gamesounds/gunsound.mp3"
SOUND_HORDE  = "gamesounds/HordeSound.mp3"
SOUND_WILD_Z = "gamesounds/wildzombiesound.mp3"
SOUND_ZOMBIE = "gamesounds/zombiesound.mp3"
SOUND_MENU   = "gamesounds/menusound.mp3"# feet land here

# UI colours
C_WHITE   = (255, 255, 255)
C_BLACK   = (0,   0,   0)
C_YELLOW  = (255, 220,  50)
C_ORANGE  = (255, 140,  40)
C_RED     = (220,  60,  60)
C_GREEN   = ( 60, 220,  80)
C_BARSBG  = ( 30,  30,  30)


# ─────────────────────────────────────────────────────────
#  SPRITE-SHEET LOADER
# ─────────────────────────────────────────────────────────
def load_sheet(path, frame_w, frame_h, scale=1.0):
    """
    Slice a horizontal sprite sheet into a list of Surfaces.
    Returns [] if the file is missing (game still runs with placeholders).
    scale=1.0 keeps original size; use e.g. 0.75 to shrink.
    """
    try:
        sheet = pygame.image.load(path).convert_alpha()
    except (FileNotFoundError, pygame.error):
        print(f"  [WARN] missing sprite: {path}")
        return []

    cols   = sheet.get_width() // frame_w
    frames = []
    for c in range(cols):
        surf = pygame.Surface((frame_w, frame_h), pygame.SRCALPHA)
        surf.blit(sheet, (0, 0), (c * frame_w, 0, frame_w, frame_h))
        if scale != 1.0:
            new_w = max(1, int(frame_w * scale))
            new_h = max(1, int(frame_h * scale))
            surf = pygame.transform.scale(surf, (new_w, new_h))
        frames.append(surf)
    return frames


def placeholder(w, h, colour, label=""):
    """Coloured rect used when a PNG is missing."""
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.rect(surf, colour, (0, 0, w, h), border_radius=6)
    if label:
        f = pygame.font.SysFont(None, 18)
        t = f.render(label, True, C_WHITE)
        surf.blit(t, (4, 4))
    return surf


# ─────────────────────────────────────────────────────────
#  ASSET REGISTRY
#  All PNG info in one place — tweak scale here.
# ─────────────────────────────────────────────────────────
SOLDIER_SCALE = 0.85          # soldier drawn at 85 % of 128 px = ~109 px tall
ZOMBIE_SCALE  = 0.85          # zombies at 85 % of 96 px  = ~82 px tall
WILD_Z_SCALE  = 0.85

#  Each entry: (relative_path, frame_w, frame_h, scale)
SOLDIER_SHEETS = {
    "idle":     ("Soldier_2/Idle.png",     128, 128, SOLDIER_SCALE),
    "run":      ("Soldier_2/Run.png",      128, 128, SOLDIER_SCALE),
    "walk":     ("Soldier_2/Walk.png",     128, 128, SOLDIER_SCALE),
    "jump":     ("Soldier_2/Idle.png",     128, 128, SOLDIER_SCALE),   # reuse idle if no jump sheet
    "crouch":   ("Soldier_2/Idle.png",     128, 128, SOLDIER_SCALE),
    "attack":   ("Soldier_2/Attack.png",   128, 128, SOLDIER_SCALE),
    "shot1":    ("Soldier_2/Shot_1.png",   128, 128, SOLDIER_SCALE),
    "shot2":    ("Soldier_2/Shot_2.png",   128, 128, SOLDIER_SCALE),
    "hurt":     ("Soldier_2/Hurt.png",     128, 128, SOLDIER_SCALE),
    "dead":     ("Soldier_2/Dead.png",     128, 128, SOLDIER_SCALE),
    "recharge": ("Soldier_2/Recharge.png", 128, 128, SOLDIER_SCALE),
}

WILD_ZOMBIE_SHEETS = {
    "idle":    ("Wild Zombie/Idle.png",     96,  96, WILD_Z_SCALE),
    "walk":    ("Wild Zombie/Walk.png",     96,  96, WILD_Z_SCALE),
    "run":     ("Wild Zombie/Run.png",      96,  96, WILD_Z_SCALE),
    "attack1": ("Wild Zombie/Attack_1.png", 128, 128, WILD_Z_SCALE),
    "attack2": ("Wild Zombie/Attack_2.png", 128, 128, WILD_Z_SCALE),
    "hurt":    ("Wild Zombie/Hurt.png",     96,  96, WILD_Z_SCALE),
    "dead":    ("Wild Zombie/Dead.png",     96,  96, WILD_Z_SCALE),
}

ZOMBIE_MAN_SHEETS = {
    "idle":    ("Zombie Man/Idle.png",     96,  96, ZOMBIE_SCALE),
    "walk":    ("Zombie Man/Walk.png",     96,  96, ZOMBIE_SCALE),
    "run":     ("Zombie Man/Run.png",      96,  96, ZOMBIE_SCALE),
    "attack1": ("Zombie Man/Attack_1.png", 128, 128, ZOMBIE_SCALE),
    "attack2": ("Zombie Man/Attack_2.png", 128, 128, ZOMBIE_SCALE),
    "bite":    ("Zombie Man/Bite.png",     96,  96, ZOMBIE_SCALE),
    "hurt":    ("Zombie Man/Hurt.png",     96,  96, ZOMBIE_SCALE),
    "dead":    ("Zombie Man/Dead.png",     96,  96, ZOMBIE_SCALE),
}

ZOMBIE_WOMAN_SHEETS = {
    "idle":    ("Zombie Woman/Idle.png",     96, 96, ZOMBIE_SCALE),
    "walk":    ("Zombie Woman/Walk.png",     96, 96, ZOMBIE_SCALE),
    "run":     ("Zombie Woman/Run.png",      96, 96, ZOMBIE_SCALE),
    "attack1": ("Zombie Woman/Attack_1.png", 96, 96, ZOMBIE_SCALE),
    "attack2": ("Zombie Woman/Attack_2.png", 96, 96, ZOMBIE_SCALE),
    "hurt":    ("Zombie Woman/Hurt.png",     96, 96, ZOMBIE_SCALE),
    "dead":    ("Zombie Woman/Dead.png",     96, 96, ZOMBIE_SCALE),
    "scream":  ("Zombie Woman/Scream.png",   96, 96, ZOMBIE_SCALE),
}


def load_all_sheets(sheet_dict):
    """Load every sheet in a dict, fall back to placeholder on missing."""
    result = {}
    for key, (rel, fw, fh, sc) in sheet_dict.items():
        frames = load_sheet(asset(rel), fw, fh, scale=sc)
        if not frames:
            # placeholder: single coloured frame
            ph_w = max(1, int(fw * sc))
            ph_h = max(1, int(fh * sc))
            frames = [placeholder(ph_w, ph_h, (100, 200, 100), key)]
        result[key] = frames
    return result


# ─────────────────────────────────────────────────────────
#  ANIMATOR
# ─────────────────────────────────────────────────────────
class Animator:
    def __init__(self, frames_dict, anim_fps=10):
        self.frames   = frames_dict
        self.state    = next(iter(frames_dict))
        self.idx      = 0.0
        self.fps      = anim_fps
        self.done     = False      # True when a one-shot anim finishes

    def play(self, state, force=False):
        if state not in self.frames:
            return
        if state != self.state or force:
            self.state = state
            self.idx   = 0.0
            self.done  = False

    def update(self, dt, loop=True):
        flist = self.frames.get(self.state, [])
        if len(flist) <= 1:
            self.done = True
            return
        self.idx += self.fps * dt
        if self.idx >= len(flist):
            if loop:
                self.idx = self.idx % len(flist)
            else:
                self.idx = len(flist) - 1
                self.done = True

    def image(self, flip_x=False):
        flist = self.frames.get(self.state, [])
        if not flist:
            return pygame.Surface((1, 1), pygame.SRCALPHA)
        img = flist[int(self.idx) % len(flist)]
        return pygame.transform.flip(img, True, False) if flip_x else img

    def frame_index(self):
        return int(self.idx)


# ─────────────────────────────────────────────────────────
#  BULLET
# ─────────────────────────────────────────────────────────
class Bullet(pygame.sprite.Sprite):
    SPEED  = 16
    RADIUS = 5

    def __init__(self, x, y, angle):
        super().__init__()
        self.image = pygame.Surface((self.RADIUS*2, self.RADIUS*2), pygame.SRCALPHA)
        pygame.draw.circle(self.image, C_YELLOW, (self.RADIUS, self.RADIUS), self.RADIUS)
        # glow ring
        pygame.draw.circle(self.image, (255, 200, 80), (self.RADIUS, self.RADIUS), self.RADIUS, 1)
        self.rect = self.image.get_rect(center=(x, y))
        self.vx   = math.cos(angle) * self.SPEED
        self.vy   = math.sin(angle) * self.SPEED
        self.fx   = float(x)
        self.fy   = float(y)

    def update(self):
        self.fx += self.vx
        self.fy += self.vy
        self.rect.center = (int(self.fx), int(self.fy))
        if not (-40 < self.fx < SCREEN_W+40 and -40 < self.fy < SCREEN_H+40):
            self.kill()


# ─────────────────────────────────────────────────────────
#  PARTICLE
# ─────────────────────────────────────────────────────────
class Particle(pygame.sprite.Sprite):
    def __init__(self, x, y, colour, size=4):
        super().__init__()
        self.image = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.rect(self.image, colour, (0, 0, size, size))
        self.rect = self.image.get_rect(center=(x, y))
        self.vx   = random.uniform(-3.5, 3.5)
        self.vy   = random.uniform(-5.5, -0.5)
        self.life = random.randint(18, 38)
        self.maxl = self.life

    def update(self):
        self.vy  += 0.3
        self.rect.x += int(self.vx)
        self.rect.y += int(self.vy)
        self.life -= 1
        if self.life <= 0:
            self.kill()
            return
        self.image.set_alpha(int(255 * self.life / self.maxl))


def burst(group, x, y, colour, n=8, size=4):
    for _ in range(n):
        group.add(Particle(x, y, colour, size))


# ─────────────────────────────────────────────────────────
#  PLAYER
# ─────────────────────────────────────────────────────────
class Player(pygame.sprite.Sprite):
    SPEED       = 4.5
    JUMP_VEL    = -13.5
    SHOOT_CD    = 0.22          # seconds between shots
    MAX_HP      = 120
    HITBOX_W    = 36            # narrower than sprite for fairness
    HITBOX_H    = 72

    def __init__(self, x, y):
        super().__init__()
        print("Loading Soldier sprites…")
        self.anim   = Animator(load_all_sheets(SOLDIER_SHEETS), anim_fps=12)
        self.image  = self.anim.image()
        # Use a fixed hitbox rect; visual rect updated each frame
        self.rect   = pygame.Rect(0, 0, self.HITBOX_W, self.HITBOX_H)
        self.rect.midbottom = (x, y)

        self.vx          = 0.0
        self.vy          = 0.0
        self.on_ground   = False
        self.crouching   = False
        self.facing_left = False
        self.shooting    = False
        self.hp          = self.MAX_HP
        self.shoot_timer = 0.0
        self.hurt_timer  = 0.0
        self.dead        = False
        self.dead_locked = False

    # ── helper ────────────────────────────────────────────
    @property
    def alive_flag(self):
        return self.hp > 0

    def take_damage(self, dmg):
        if self.hurt_timer > 0 or self.dead:
            return
        self.hp         = max(0, self.hp - dmg)
        self.hurt_timer = 0.7
        if self.hp <= 0:
            self.dead = True
            self.anim.play("dead", force=True)

    # ── update ────────────────────────────────────────────
    def update(self, dt, keys, m_btns, m_pos, bullets, particles):
        if self.dead:
            self.anim.update(dt, loop=False)
            self.image = self.anim.image(self.facing_left)
            return

        self.hurt_timer  = max(0.0, self.hurt_timer  - dt)
        self.shoot_timer = max(0.0, self.shoot_timer - dt)

        # ── input ──
        self.vx        = 0
        self.crouching = False
        self.shooting  = False

        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            self.crouching = True
        else:
            if keys[pygame.K_a] or keys[pygame.K_LEFT]:
                self.vx = -self.SPEED
                self.facing_left = True
            if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
                self.vx =  self.SPEED
                self.facing_left = False
            if (keys[pygame.K_w] or keys[pygame.K_UP] or keys[pygame.K_SPACE]) \
               and self.on_ground:
                self.vy = self.JUMP_VEL
                self.on_ground = False

        if m_btns[0] and self.shoot_timer <= 0:
            self.shooting = True
            self._fire(m_pos, bullets, particles)

        # ── physics ──
        self.vy += GRAVITY
        self.rect.x += int(self.vx)
        self.rect.y += int(self.vy)

        if self.rect.bottom >= GROUND_Y:
            self.rect.bottom = GROUND_Y
            self.vy = 0
            self.on_ground = True
        else:
            self.on_ground = False

        self.rect.left  = max(0,        self.rect.left)
        self.rect.right = min(SCREEN_W, self.rect.right)

        # ── animation state ──
        if self.hurt_timer > 0.4:
            state = "hurt"
        elif self.crouching:
            state = "crouch"
        elif self.shooting:
            state = "shot1"
        elif not self.on_ground:
            state = "jump"
        elif abs(self.vx) > 0.1:
            state = "run"
        else:
            state = "idle"

        self.anim.play(state)
        loop = state not in ("shot1", "shot2", "hurt", "attack", "dead")
        self.anim.update(dt, loop=loop)
        self.image = self.anim.image(self.facing_left)

    def _fire(self, m_pos, bullets, particles):
        self.shoot_timer = self.SHOOT_CD
        cx, cy  = self.rect.centerx, self.rect.centery - 8
        angle   = math.atan2(m_pos[1] - cy, m_pos[0] - cx)
        bullets.add(Bullet(cx + (20 if not self.facing_left else -20), cy, angle))
        burst(particles, cx, cy, C_YELLOW, n=5, size=3)

    # ── draw ──────────────────────────────────────────────
    def draw_hpbar(self, surface):
        bw, bh = 140, 14
        x = 14
        y = SCREEN_H - 50
        font = pygame.font.SysFont(None, 20)
        surface.blit(font.render("Soldier", True, C_WHITE), (x, y - 20))
        pygame.draw.rect(surface, C_BARSBG, (x, y, bw, bh), border_radius=5)
        fill = int(bw * max(0, self.hp) / self.MAX_HP)
        col  = C_GREEN if self.hp > self.MAX_HP * 0.4 else C_RED
        if fill > 0:
            pygame.draw.rect(surface, col, (x, y, fill, bh), border_radius=5)
        surface.blit(font.render(f"{max(0,self.hp)}/{self.MAX_HP}", True, C_WHITE),
                     (x + bw + 6, y))

    def draw_sprite(self, surface):
        # Centre sprite image over hitbox
        img  = self.image
        rect = img.get_rect(midbottom=self.rect.midbottom)
        # Flicker when hurt
        if self.hurt_timer > 0 and int(self.hurt_timer * 12) % 2 == 0:
            return
        surface.blit(img, rect)


# ─────────────────────────────────────────────────────────
#  ZOMBIE BASE CLASS
# ─────────────────────────────────────────────────────────
class Zombie(pygame.sprite.Sprite):
    HITBOX_W    = 30
    HITBOX_H    = 60
    BULLET_DMG  = 15            # damage per bullet hit

    def __init__(self, x, y, hp, speed, contact_dmg, score_val,
                 anim_frames, anim_fps=9):
        super().__init__()
        self.anim        = Animator(anim_frames, anim_fps)
        self.image       = self.anim.image()
        self.rect        = pygame.Rect(0, 0, self.HITBOX_W, self.HITBOX_H)
        self.rect.midbottom = (x, y)

        self.hp          = hp
        self.max_hp      = hp
        self.speed       = speed
        self.contact_dmg = contact_dmg
        self.score_val   = score_val

        self.dying       = False
        self.die_timer   = 0.0
        self.attacking   = False
        self.attack_cd   = 0.0
        self.hurt_timer  = 0.0

    # ── public ────────────────────────────────────────────
    def hit(self, damage, particles):
        if self.dying:
            return
        self.hp -= damage
        burst(particles, self.rect.centerx, self.rect.centery,
              (180, 240, 100), n=7)
        if self.hp <= 0:
            self._begin_die(particles)
        else:
            self.hurt_timer = 0.25
            self.anim.play("hurt", force=True)

    def _begin_die(self, particles):
        if self.dying:
            return
        self.dying = True
        burst(particles, self.rect.centerx, self.rect.centery - 20,
              (220, 60, 60), n=14, size=5)
        self.anim.play("dead", force=True)
        # measure how long the death anim takes
        dead_frames = len(self.anim.frames.get("dead", [1]))
        self.die_timer = dead_frames / self.anim.fps + 0.1

    def update(self, dt, base_rect, player, particles):
        """Returns True if zombie deals damage to the base this frame."""
        self.attack_cd  = max(0.0, self.attack_cd  - dt)
        self.hurt_timer = max(0.0, self.hurt_timer - dt)

        if self.dying:
            self.die_timer -= dt
            self.anim.update(dt, loop=False)
            self.image = self.anim.image(flip_x=True)
            if self.die_timer <= 0:
                self.kill()
            return False

        if self.hurt_timer > 0:
            self.anim.update(dt, loop=False)
            self.image = self.anim.image(flip_x=True)
            return False

        # march left
        self.rect.x -= int(self.speed)

        # attack base
        if self.rect.left <= base_rect.right:
            if self.attack_cd <= 0:
                self.attack_cd = 1.2
                self.anim.play("attack1", force=True)
                return True   # signal: deal damage to base
            self.anim.update(dt, loop=False)
            self.image = self.anim.image(flip_x=True)
            return False

        # attack player on contact
        if self.rect.colliderect(player.rect) and self.attack_cd <= 0:
            player.take_damage(self.contact_dmg)
            self.attack_cd = 1.0
            self.anim.play("attack1", force=True)

        self._choose_walk_anim()
        self.anim.update(dt)
        self.image = self.anim.image(flip_x=True)
        return False

    def _choose_walk_anim(self):
        self.anim.play("walk")   # subclasses may override

    def draw_hpbar(self, surface):
        if self.dying:
            return
        bw, bh = 38, 5
        x = self.rect.centerx - bw // 2
        y = self.rect.top - 8
        pygame.draw.rect(surface, C_BARSBG, (x, y, bw, bh), border_radius=2)
        fill = int(bw * max(0, self.hp) / self.max_hp)
        if fill > 0:
            col = C_GREEN if self.hp > self.max_hp * 0.5 else C_RED
            pygame.draw.rect(surface, col, (x, y, fill, bh), border_radius=2)

    def draw_sprite(self, surface):
        img  = self.image
        rect = img.get_rect(midbottom=self.rect.midbottom)
        surface.blit(img, rect)


# ─────────────────────────────────────────────────────────
#  ZOMBIE TYPES
# ─────────────────────────────────────────────────────────
class WildZombie(Zombie):
    """Fast, low HP — runs at the base."""
    def __init__(self, x, y):
        print("  spawning WildZombie")
        frames = load_all_sheets(WILD_ZOMBIE_SHEETS)
        super().__init__(x, y,
                         hp=35, speed=2.2, contact_dmg=10, score_val=15,
                         anim_frames=frames, anim_fps=10)

    def _choose_walk_anim(self):
        self.anim.play("run")


class ZombieMan(Zombie):
    """Tanky, slow walker — high base damage."""
    def __init__(self, x, y):
        print("  spawning ZombieMan")
        frames = load_all_sheets(ZOMBIE_MAN_SHEETS)
        super().__init__(x, y,
                         hp=65, speed=1.1, contact_dmg=16, score_val=20,
                         anim_frames=frames, anim_fps=8)


class ZombieWoman(Zombie):
    """Medium speed, screams before charging."""
    SCREAM_DIST = 380   # pixels from player to trigger scream

    def __init__(self, x, y):
        print("  spawning ZombieWoman")
        frames = load_all_sheets(ZOMBIE_WOMAN_SHEETS)
        super().__init__(x, y,
                         hp=45, speed=1.6, contact_dmg=12, score_val=18,
                         anim_frames=frames, anim_fps=9)
        self._screamed = False

    def _choose_walk_anim(self):
        # Scream once when close, then charge
        if not self._screamed:
            self.anim.play("scream")
            if self.anim.done:
                self._screamed = True
        else:
            self.anim.play("walk")


# ─────────────────────────────────────────────────────────
#  BASE (structure to defend)
# ─────────────────────────────────────────────────────────
class Base(pygame.sprite.Sprite):
    MAX_HP = 350
    W, H   = 90, 170

    def __init__(self):
        super().__init__()
        self.hp    = self.MAX_HP
        self.image = self._build_image()
        self.rect  = self.image.get_rect(bottomleft=(8, GROUND_Y))

    def _build_image(self):
        surf = pygame.Surface((self.W, self.H), pygame.SRCALPHA)
        # Body
        pygame.draw.rect(surf, (160, 120, 70), (0, 0, self.W, self.H), border_radius=6)
        # Roof
        pygame.draw.polygon(surf, (120, 85, 45),
                            [(0, 0), (self.W, 0), (self.W//2, -24)])
        # Windows
        for wy in range(16, self.H - 60, 44):
            for wx in (12, 54):
                pygame.draw.rect(surf, (200, 230, 255), (wx, wy, 22, 22), border_radius=3)
                pygame.draw.rect(surf, (150, 180, 220), (wx, wy, 22, 22), border_radius=3, width=2)
        # Door
        pygame.draw.rect(surf, (100, 65, 30), (30, self.H - 55, 30, 55), border_radius=4)
        # HP crack overlay — drawn dynamically in draw()
        return surf

    def take_damage(self, amount):
        self.hp = max(0, self.hp - amount)

    def draw(self, surface):
        surface.blit(self.image, self.rect)
        # HP bar above base
        bw, bh = 160, 16
        x, y   = 8, self.rect.top - 30
        font   = pygame.font.SysFont(None, 20)
        surface.blit(font.render("BASE", True, C_WHITE), (x, y - 18))
        pygame.draw.rect(surface, C_BARSBG, (x, y, bw, bh), border_radius=5)
        fill = int(bw * self.hp / self.MAX_HP)
        col  = C_GREEN if self.hp > self.MAX_HP * 0.35 else C_RED
        if fill > 0:
            pygame.draw.rect(surface, col, (x, y, fill, bh), border_radius=5)
        surface.blit(font.render(f"{self.hp}/{self.MAX_HP}", True, C_WHITE),
                     (x + bw + 6, y + 1))
        # Shake when low HP
        if self.hp < self.MAX_HP * 0.3:
            shake = random.randint(-1, 1)
            self.rect.x = 8 + shake


# ─────────────────────────────────────────────────────────
#  HORDE BANNER
# ─────────────────────────────────────────────────────────
class SoundManager:
    def __init__(self):
        pygame.mixer.init()
        self.gun   = self._load(SOUND_GUN,    volume=0.5)
        self.horde = self._load(SOUND_HORDE,  volume=0.8)
        self.wildz = self._load(SOUND_WILD_Z, volume=0.4)
        self.zombie= self._load(SOUND_ZOMBIE, volume=0.4)
        self.menu   = self._load(SOUND_MENU,   volume=0.5)

    @staticmethod
    def _load(path, volume=1.0):
        try:
            s = pygame.mixer.Sound(asset(path))
            s.set_volume(volume)
            return s
        except Exception:
            print(f"  [WARN] missing sound: {path}")
            return None

    def play_gun(self):
        if self.gun:
            self.gun.stop()
            self.gun.play()

    def play_horde(self):
        if self.horde:
            self.horde.stop()
            self.horde.play()
    def play_menu_music(self):
        if self.menu:
          pygame.mixer.Sound.stop(self.menu)
        self.menu.play(-1)   # -1 = loop forever

    def stop_menu_music(self):
         if self.menu:
          self.menu.stop()

    def play_zombie_spawn(self, zombie_type):
        """Play different sound per zombie type."""
        if zombie_type == "wild" and self.wildz:
            self.wildz.stop()
            self.wildz.play()
        elif zombie_type == "normal" and self.zombie:
            self.zombie.stop()
            self.zombie.play()
class MainMenu:
    def __init__(self, screen, bg, sounds):
        self.screen  = screen
        self.bg      = bg
        self.sounds  = sounds
        self.done    = False
        self.choice  = None   # "play" or "quit"

        self.f_title  = pygame.font.SysFont(None, 110)
        self.f_sub    = pygame.font.SysFont(None, 34)
        self.f_btn    = pygame.font.SysFont(None, 54)
        self.f_small  = pygame.font.SysFont(None, 26)

        self.buttons  = [
    {"label": "[ PLAY ]",      "action": "play"},
    {"label": "[ SETTINGS ]",  "action": "settings"},
    {"label": "[ QUIT ]",      "action": "quit"},
]
        self.selected  = 0
        self.btn_rects = []

        self.sounds.play_menu_music()

        # Spooky flicker timer
        self.flicker   = 0.0
        self.alpha_dir = -1

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_UP, pygame.K_w):
                self.selected = (self.selected - 1) % len(self.buttons)
            if event.key in (pygame.K_DOWN, pygame.K_s):
                self.selected = (self.selected + 1) % len(self.buttons)
            if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self._confirm()
        if event.type == pygame.MOUSEMOTION:
            for i, r in enumerate(self.btn_rects):
                if r.collidepoint(event.pos):
                    self.selected = i
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, r in enumerate(self.btn_rects):
                if r.collidepoint(event.pos):
                    self.selected = i
                    self._confirm()

    def _confirm(self):
        self.choice = self.buttons[self.selected]["action"]
        self.done   = True

    def update(self, dt):
        self.flicker += dt * 1.4 * self.alpha_dir
        if self.flicker <= 0.0:
            self.flicker   = 0.0
            self.alpha_dir = 1
        if self.flicker >= 1.0:
            self.flicker   = 1.0
            self.alpha_dir = -1

    def draw(self):
        # Background
        self.bg.draw(self.screen)

        # Dark overlay for readability
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 155))
        self.screen.blit(overlay, (0, 0))

        cx = SCREEN_W // 2

        # Title with spooky flicker
        flicker_alpha = int(180 + 75 * self.flicker)
        title1 = self.f_title.render("ZOMBIE", True, (200, 30, 30))
        title2 = self.f_title.render("DEFENSE", True, (220, 50, 50))
        title1.set_alpha(flicker_alpha)
        title2.set_alpha(flicker_alpha)
        self.screen.blit(title1, title1.get_rect(center=(cx, 140)))
        self.screen.blit(title2, title2.get_rect(center=(cx, 230)))

        # Subtitle
        sub = self.f_sub.render("Defend the base. Kill them all.", True, (180, 140, 140))
        sub.set_alpha(200)
        self.screen.blit(sub, sub.get_rect(center=(cx, 295)))

        # Divider line
        pygame.draw.line(self.screen, (120, 40, 40),
                         (cx - 220, 320), (cx + 220, 320), 2)

        # Buttons
        self.btn_rects = []
        for i, btn in enumerate(self.buttons):
            is_sel = (i == self.selected)
            by     = 370 + i * 80
            colour = (255, 80, 80)   if is_sel else (180, 130, 130)
            size   = self.f_btn

            # Glow box behind selected
            if is_sel:
                box = pygame.Surface((340, 58), pygame.SRCALPHA)
                box.fill((180, 20, 20, 60))
                self.screen.blit(box, box.get_rect(center=(cx, by)))
                pygame.draw.rect(self.screen, (200, 40, 40),
                                 pygame.Rect(cx - 170, by - 29, 340, 58),
                                 width=2, border_radius=8)

            txt  = size.render(btn["label"], True, colour)
            rect = txt.get_rect(center=(cx, by))
            self.screen.blit(txt, rect)
            self.btn_rects.append(pygame.Rect(cx - 170, by - 29, 340, 58))

        # Controls hint
        hint = self.f_small.render("W/S or ↑↓ to navigate   •   ENTER or click to select",
                                   True, (120, 100, 100))
        self.screen.blit(hint, hint.get_rect(center=(cx, SCREEN_H - 30)))

        pygame.display.flip()

class PauseMenu:
    def __init__(self, screen):
        self.screen   = screen
        self.f_title  = pygame.font.SysFont(None, 80)
        self.f_btn    = pygame.font.SysFont(None, 50)
        self.f_small  = pygame.font.SysFont(None, 26)
        self.selected = 0
        self.done     = False
        self.choice   = None
        self.buttons  = [
            {"label": "[ RESUME ]",      "action": "resume"},
            {"label": "[ MAIN MENU ]",   "action": "menu"},
            {"label": "[ QUIT ]",        "action": "quit"},
        ]
        self.btn_rects = []
        pygame.mouse.set_visible(True)

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.choice = "resume"
                self.done   = True
            if event.key in (pygame.K_UP, pygame.K_w):
                self.selected = (self.selected - 1) % len(self.buttons)
            if event.key in (pygame.K_DOWN, pygame.K_s):
                self.selected = (self.selected + 1) % len(self.buttons)
            if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self._confirm()
        if event.type == pygame.MOUSEMOTION:
            for i, r in enumerate(self.btn_rects):
                if r.collidepoint(event.pos):
                    self.selected = i
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, r in enumerate(self.btn_rects):
                if r.collidepoint(event.pos):
                    self.selected = i
                    self._confirm()

    def _confirm(self):
        self.choice = self.buttons[self.selected]["action"]
        self.done   = True

    def draw(self, surface):
        # Dim the game behind
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 175))
        surface.blit(overlay, (0, 0))

        cx = SCREEN_W // 2

        title = self.f_title.render("PAUSED", True, (220, 180, 80))
        surface.blit(title, title.get_rect(center=(cx, 220)))
        pygame.draw.line(surface, (150, 120, 40),
                         (cx - 180, 270), (cx + 180, 270), 2)

        self.btn_rects = []
        for i, btn in enumerate(self.buttons):
            is_sel = (i == self.selected)
            by     = 330 + i * 80
            colour = (255, 200, 80) if is_sel else (180, 160, 120)

            if is_sel:
                box = pygame.Surface((300, 54), pygame.SRCALPHA)
                box.fill((180, 140, 20, 55))
                surface.blit(box, box.get_rect(center=(cx, by)))
                pygame.draw.rect(surface, (200, 160, 40),
                                 pygame.Rect(cx - 150, by - 27, 300, 54),
                                 width=2, border_radius=8)

            txt  = self.f_btn.render(btn["label"], True, colour)
            rect = txt.get_rect(center=(cx, by))
            surface.blit(txt, rect)
            self.btn_rects.append(pygame.Rect(cx - 150, by - 27, 300, 54))

        hint = self.f_small.render("ESC to resume   •   W/S or mouse to navigate",
                                   True, (120, 100, 80))
        surface.blit(hint, hint.get_rect(center=(cx, SCREEN_H - 30)))
class SettingsMenu:
    def __init__(self, screen, sounds):
        self.screen   = screen
        self.sounds   = sounds
        self.done     = False
        self.f_title  = pygame.font.SysFont(None, 64)
        self.f_item   = pygame.font.SysFont(None, 40)
        self.f_small  = pygame.font.SysFont(None, 26)
        self.selected = 0

        # Settings state
        self.gun_vol    = 5    # 0-10
        self.zombie_vol = 4
        self.music_vol  = 5
        self.items      = ["Gun Volume", "Zombie Volume", "Music Volume", "← Back"]

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_UP, pygame.K_w):
                self.selected = (self.selected - 1) % len(self.items)
            if event.key in (pygame.K_DOWN, pygame.K_s):
                self.selected = (self.selected + 1) % len(self.items)
            if event.key in (pygame.K_LEFT, pygame.K_a):
                self._adjust(-1)
            if event.key in (pygame.K_RIGHT, pygame.K_d):
                self._adjust(1)
            if event.key in (pygame.K_RETURN, pygame.K_ESCAPE):
                if self.selected == len(self.items) - 1 or event.key == pygame.K_ESCAPE:
                    self.done = True
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 4:   # scroll up
                self._adjust(1)
            if event.button == 5:   # scroll down
                self._adjust(-1)

    def _adjust(self, direction):
        if self.selected == 0:
            self.gun_vol    = max(0, min(10, self.gun_vol    + direction))
        elif self.selected == 1:
            self.zombie_vol = max(0, min(10, self.zombie_vol + direction))
        elif self.selected == 2:
            self.music_vol  = max(0, min(10, self.music_vol  + direction))
        self._apply_volumes()

    def _apply_volumes(self):
        if self.sounds.gun:
            self.sounds.gun.set_volume(self.gun_vol / 10)
        if self.sounds.zombie:
            self.sounds.zombie.set_volume(self.zombie_vol / 10)
        if self.sounds.wildz:
            self.sounds.wildz.set_volume(self.zombie_vol / 10)
        if self.sounds.menu:
            self.sounds.menu.set_volume(self.music_vol / 10)
        if self.sounds.horde:
            self.sounds.horde.set_volume(self.music_vol / 10)

    def draw(self, bg):
        bg.draw(self.screen)
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 170))
        self.screen.blit(overlay, (0, 0))

        cx = SCREEN_W // 2
        title = self.f_title.render("[ SETTINGS ]", True, (220, 180, 100))
        self.screen.blit(title, title.get_rect(center=(cx, 100)))
        pygame.draw.line(self.screen, (150, 100, 40),
                         (cx - 200, 140), (cx + 200, 140), 2)

        vols = [self.gun_vol, self.zombie_vol, self.music_vol, None]
        for i, item in enumerate(self.items):
            is_sel = (i == self.selected)
            iy     = 220 + i * 90
            colour = (255, 200, 80) if is_sel else (180, 160, 120)

            label = self.f_item.render(item, True, colour)
            self.screen.blit(label, label.get_rect(center=(cx, iy - 14)))

            if vols[i] is not None:
                # Volume bar
                bx = cx - 150
                pygame.draw.rect(self.screen, (60, 60, 60),
                                 (bx, iy + 10, 300, 14), border_radius=6)
                fill = int(300 * vols[i] / 10)
                if fill > 0:
                    pygame.draw.rect(self.screen, (200, 140, 40),
                                     (bx, iy + 10, fill, 14), border_radius=6)
                pygame.draw.rect(self.screen, (150, 100, 40),
                                 (bx, iy + 10, 300, 14), border_radius=6, width=2)
                vol_txt = self.f_small.render(f"{vols[i]*10}%", True, (200, 180, 140))
                self.screen.blit(vol_txt, (bx + 310, iy + 10))

        hint = self.f_small.render("← → or scroll to adjust   •   ESC or Back to return",
                                   True, (120, 100, 80))
        self.screen.blit(hint, hint.get_rect(center=(cx, SCREEN_H - 30)))
        pygame.display.flip()            
class HordeBanner:
    
    DURATION = 3.0

    def __init__(self):
        self.active  = False
        self.text    = ""
        self.timer   = 0.0
        self.fbig    = pygame.font.SysFont(None, 88)
        self.fsub    = pygame.font.SysFont(None, 38)

    def show(self, n):
        self.active = True
        self.timer  = self.DURATION
        sfx = {1:"1st",2:"2nd",3:"3rd"}.get(n, f"{n}th")
        self.text   = f"HORDE  {sfx.upper()}  COMES!"

    def update(self, dt):
        if self.timer > 0:
            self.timer -= dt
        else:
            self.active = False

    def draw(self, surface):
        if not self.active:
            return
        prog  = self.timer / self.DURATION
        alpha = min(255, int(prog * 510))

        cx, cy = SCREEN_W // 2, SCREEN_H // 3
        shake  = int(math.sin(self.timer * 18) * 4 * prog)

        def blit_alpha(surf, center):
            surf.set_alpha(alpha)
            r = surf.get_rect(center=center)
            surface.blit(surf, r)

        shadow = self.fbig.render(self.text, True, C_BLACK)
        main   = self.fbig.render(self.text, True, C_ORANGE)
        sub    = self.fsub.render("Defend the base — don't let them through!", True, C_YELLOW)

        blit_alpha(shadow, (cx + 3 + shake, cy + 4))
        blit_alpha(main,   (cx     + shake, cy))
        blit_alpha(sub,    (cx, cy + 62))


# ─────────────────────────────────────────────────────────
#  WAVE CONFIGURATION
# ─────────────────────────────────────────────────────────
# Each wave: (total_zombies, {ZombieClass: weight}, spawn_interval_sec)
WAVE_DEFS = [
    (6,  {ZombieMan: 10},                              2.2),
    (10, {ZombieMan: 8,  WildZombie: 3},               1.9),
    (12, {ZombieMan: 6,  WildZombie: 5,  ZombieWoman: 2}, 1.7),
    (15, {ZombieMan: 5,  WildZombie: 7,  ZombieWoman: 4}, 1.5),
    (18, {ZombieMan: 4,  WildZombie: 8,  ZombieWoman: 6}, 1.3),
    (22, {ZombieMan: 3,  WildZombie: 10, ZombieWoman: 8}, 1.1),
    (26, {ZombieMan: 3,  WildZombie: 12, ZombieWoman: 10}, 0.9),
    (32, {ZombieMan: 4,  WildZombie: 15, ZombieWoman: 12}, 0.75),
]


def weighted_choice(weight_dict):
    pool  = []
    for cls, w in weight_dict.items():
        pool.extend([cls] * w)
    return random.choice(pool)


class WaveManager:
    PREP_TIME = 4.5

    def __init__(self, zombies_group, banner):
        self.zombies    = zombies_group
        self.banner     = banner
        self.wave_idx   = 0
        self.spawned    = 0
        self.total      = 0
        self.weights    = {}
        self.spawn_int  = 2.0
        self.spawn_t    = 0.0
        self.prep_t     = 1.2       # short delay before first wave
        self.in_prep    = True
        self.all_done   = False
        self.sounds     = None

    @property
    def wave_num(self):
        return self.wave_idx + 1

    def update(self, dt):
        if self.all_done:
            return

        if self.in_prep:
            self.prep_t -= dt
            if self.prep_t <= 0:
                self.in_prep = False
                self._start()
            return

        if self.spawned < self.total:
            self.spawn_t -= dt
            if self.spawn_t <= 0:
                self._spawn()
                self.spawn_t = self.spawn_int
            return

        # wait for all zombies to be killed
        if len(self.zombies) == 0:
            if self.wave_idx + 1 >= len(WAVE_DEFS):
                self.all_done = True
            else:
                self.wave_idx += 1
                self.in_prep   = True
                self.prep_t    = self.PREP_TIME

    def _start(self):
        cfg            = WAVE_DEFS[self.wave_idx]
        self.total     = cfg[0]
        self.weights   = cfg[1]
        self.spawn_int = cfg[2]
        self.spawned   = 0
        self.spawn_t   = 0.05
        self.banner.show(self.wave_idx + 1)
        if self.sounds:
            self.sounds.play_horde()

    def _spawn(self):
        y   = GROUND_Y
        x   = SCREEN_W + random.randint(30, 150)
        cls = weighted_choice(self.weights)
        self.zombies.add(cls(x, y))
        self.spawned += 1
        if self.sounds:
            ztype = "wild" if cls == WildZombie else "normal"
            self.sounds.play_zombie_spawn(ztype)


# ─────────────────────────────────────────────────────────
#  BACKGROUND  (parallax-ready)
# ─────────────────────────────────────────────────────────
class Background:
    BG_FILE = "background 3/orig_big.png"
    SOUND_GUN        = "gamesounds/gunsound.mp3"
    SOUND_HORDE      = "gamesounds/HordeSound.mp3"
    SOUND_WILD_Z     = "gamesounds/wildzombiesound.mp3"
    SOUND_ZOMBIE     = "gamesounds/zombiesound.mp3"

    def __init__(self):
        self.scroll_x = 0.0
        self._load()

    def _load(self):
        try:
            raw = pygame.image.load(asset(self.BG_FILE)).convert()
            # Scale to screen height, keep aspect
            scale  = SCREEN_H / raw.get_height()
            new_w  = int(raw.get_width() * scale)
            self.bg = pygame.transform.scale(raw, (new_w, SCREEN_H))
            self.bg_w = new_w
            self.has_bg = True
            print(f"Background loaded: {new_w}×{SCREEN_H}")
        except (FileNotFoundError, pygame.error):
            print("[WARN] background not found — using gradient")
            self.has_bg = False
            self._build_gradient()

    def _build_gradient(self):
        self.grad = pygame.Surface((SCREEN_W, SCREEN_H))
        for y in range(SCREEN_H):
            t   = y / SCREEN_H
            col = (int(18+55*t), int(18+35*t), int(40+20*t))
            pygame.draw.line(self.grad, col, (0, y), (SCREEN_W, y))
        # ground
        pygame.draw.rect(self.grad, (55, 44, 33),
                         (0, GROUND_Y, SCREEN_W, SCREEN_H - GROUND_Y))
        pygame.draw.line(self.grad, (80, 65, 48),
                         (0, GROUND_Y), (SCREEN_W, GROUND_Y), 3)
        # distant ruins silhouette
        rng = random.Random(42)
        for bx in range(0, SCREEN_W, 55):
            bh = rng.randint(30, 110)
            pygame.draw.rect(self.grad, (28, 28, 48),
                             (bx + 4, GROUND_Y - bh, 44, bh))

    def scroll(self, dx):
        """Call with player vx for subtle parallax."""
        self.scroll_x = (self.scroll_x + dx * 0.2) % SCREEN_W

    def draw(self, surface):
        if self.has_bg:
            # Tile the wide background for endless scroll
            offset = int(self.scroll_x) % self.bg_w
            surface.blit(self.bg, (-offset, 0))
            if -offset + self.bg_w < SCREEN_W:
                surface.blit(self.bg, (-offset + self.bg_w, 0))
        else:
            surface.blit(self.grad, (0, 0))


# ─────────────────────────────────────────────────────────
#  HUD
# ─────────────────────────────────────────────────────────
class HUD:
    def __init__(self):
        self.f_lg  = pygame.font.SysFont(None, 60)
        self.f_md  = pygame.font.SysFont(None, 34)
        self.f_sm  = pygame.font.SysFont(None, 22)

    def draw(self, surface, score, wave_mgr, player):
        # Score — top right
        self._blit(surface, self.f_md, f"Score: {score}",
                   C_WHITE, (SCREEN_W - 14, 14), anchor="topright")

        # Wave — top centre
        if not wave_mgr.all_done:
            self._blit(surface, self.f_md,
                       f"Wave  {wave_mgr.wave_num} / {len(WAVE_DEFS)}",
                       C_YELLOW, (SCREEN_W//2, 14), anchor="topcenter")

        # Prep countdown — screen centre
        if wave_mgr.in_prep and not wave_mgr.all_done:
            secs = max(0, int(math.ceil(wave_mgr.prep_t)))
            msg  = ("Get ready!" if wave_mgr.wave_idx == 0
                    else f"Next horde in  {secs}s…")
            self._blit(surface, self.f_md, msg,
                       (160, 255, 160), (SCREEN_W//2, SCREEN_H//2),
                       anchor="center")

        # Zombie count remaining
        if not wave_mgr.all_done:
            pass  # shown via wave banner

        # Player HP
        player.draw_hpbar(surface)

    def draw_gameover(self, surface, score, highscore):
        self._overlay(surface)
        self._blit(surface, self.f_lg, "-- BASE  DESTROYED --",
                   C_RED, (SCREEN_W//2, SCREEN_H//2 - 100), anchor="center")
        self._blit(surface, self.f_md, f"Score: {score}",
                   C_WHITE, (SCREEN_W//2, SCREEN_H//20), anchor="center")
        self._blit(surface, self.f_md, f"Best Score: {highscore}",
                    C_YELLOW, (SCREEN_W//2, SCREEN_H//2 + 30), anchor="center")
        pygame.draw.line(surface, (150, 40, 40),
                         (SCREEN_W//2 - 220, SCREEN_H//2 + 75),
                         (SCREEN_W//2 + 220, SCREEN_H//2 + 75), 2)
        self._blit(surface, self.f_sm, "R — Play Again     M — Main Menu",
                   (180,180,180), (SCREEN_W//2, SCREEN_H//2 + 100), anchor="center")

    def draw_win(self, surface, score, highscore):
        self._overlay(surface)
        self._blit(surface, self.f_lg, "**  YOU SURVIVED!  **",
                   C_YELLOW, (SCREEN_W//2, SCREEN_H//2 - 100), anchor="center")
        self._blit(surface, self.f_md, f"Score:      {score}",
                    C_WHITE, (SCREEN_W//2, SCREEN_H//2 - 20), anchor="center")
        self._blit(surface, self.f_md, f"Best Score: {highscore}",
                   C_YELLOW, (SCREEN_W//2, SCREEN_H//2 + 30), anchor="center")
        pygame.draw.line(surface, (150, 130, 20),
                        (SCREEN_W//2 - 220, SCREEN_H//2 + 75),
                        (SCREEN_W//2 + 220, SCREEN_H//2 + 75), 2)
        self._blit(surface, self.f_sm, "R — Play Again     M — Main Menu",
                   (180, 180, 180), (SCREEN_W//2, SCREEN_H//2 + 100), anchor="center")

    # ── helpers ───────────────────────────────────────────
    @staticmethod
    def _overlay(surface):
        ov = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 165))
        surface.blit(ov, (0, 0))

    @staticmethod
    def _blit(surface, font, text, colour, pos, anchor="topleft"):
        surf = font.render(text, True, colour)
        r    = surf.get_rect()
        if   anchor == "topright":   r.topright   = pos
        elif anchor == "topcenter":  r.midtop     = pos
        elif anchor == "center":     r.center     = pos
        else:                        r.topleft    = pos
        surface.blit(surf, r)


# ─────────────────────────────────────────────────────────
#  CROSSHAIR
# ─────────────────────────────────────────────────────────
def draw_crosshair(surface, pos):
    x, y = pos
    col  = C_YELLOW
    pygame.draw.circle(surface, col, (x, y), 10, 2)
    pygame.draw.line(surface, col, (x-16, y), (x-11, y), 2)
    pygame.draw.line(surface, col, (x+11, y), (x+16, y), 2)
    pygame.draw.line(surface, col, (x, y-16), (x, y-11), 2)
    pygame.draw.line(surface, col, (x, y+11), (x, y+16), 2)


# ─────────────────────────────────────────────────────────
#  MAIN GAME
# ─────────────────────────────────────────────────────────
class Game:
    SAVE_FILE = "highscore.txt"

    def __init__(self):
        pygame.init()
        pygame.mouse.set_visible(True)
        self.screen    = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        pygame.display.set_caption("Zombie Defense")
        self.clock     = pygame.time.Clock()
        self.highscore = self._load_highscore()
        self._reset()
        self._main_menu()

    def _load_highscore(self):
        try:
            with open(self.SAVE_FILE, "r") as f:
                return int(f.read().strip())
        except Exception:
            return 0

    def _save_highscore(self):
        try:
            with open(self.SAVE_FILE, "w") as f:
                f.write(str(self.highscore))
        except Exception:
            pass

    def _main_menu(self):
        menu = MainMenu(self.screen, self.bg, self.sounds)
        while not menu.done:
            dt = self.clock.tick(FPS) / 1000.0
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                    pygame.quit(); sys.exit()
                menu.handle_event(ev)
            menu.update(dt)
            menu.draw()
        if menu.choice == "quit":
            pygame.quit(); sys.exit()
        if menu.choice == "settings":
            self._settings_menu()
            self._main_menu()   # return to menu after settings
        self.sounds.stop_menu_music()

    def _reset(self):
        self.zombies   = pygame.sprite.Group()
        self.bullets   = pygame.sprite.Group()
        self.particles = pygame.sprite.Group()

        self.player    = Player(280, GROUND_Y)
        self.base      = Base()
        self.bg        = Background()
        self.banner    = HordeBanner()
        self.wave_mgr  = WaveManager(self.zombies, self.banner)
        self.sounds    = SoundManager()
        self.wave_mgr.sounds = self.sounds
        self.hud       = HUD()
        self.score     = 0
        self.game_over = False
        self.won       = False

    # ── main loop ─────────────────────────────────────────
    def _pause(self):
        pause = PauseMenu(self.screen)
        while not pause.done:
            self.clock.tick(FPS)
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    self._save_highscore()
                    pygame.quit(); sys.exit()
                pause.handle_event(ev)
            
            pause.draw(self.screen)
            pygame.display.flip()
        pygame.mouse.set_visible(False)
        if pause.choice == "menu":
            self._reset()
            self._main_menu()
        elif pause.choice == "quit":
            self._save_highscore()
            pygame.quit(); sys.exit()

    def run(self):
        while True:
            dt = self.clock.tick(FPS) / 1000.0
            dt = min(dt, 0.05)   # clamp for lag spikes

            self._events()
            if not self.game_over and not self.won:
                self._update(dt)
            self._draw()
    def run(self):
        while True:
            dt = self.clock.tick(FPS) / 1000.0
            dt = min(dt, 0.05)   # clamp for lag spikes

            self._events()
            if not self.game_over and not self.won:
                self._update(dt)
            self._draw()

    def _events(self):
     for ev in pygame.event.get():
        if ev.type == pygame.QUIT:
            self._save_highscore()
            pygame.quit(); sys.exit()
        if ev.type == pygame.KEYDOWN:
            if ev.key == pygame.K_ESCAPE:
                if not self.game_over and not self.won:
                    self._pause()
                else:
                    self._save_highscore()
                    pygame.quit(); sys.exit()
            if ev.key == pygame.K_r and (self.game_over or self.won):
                self._reset()
            if ev.key == pygame.K_m and (self.game_over or self.won):
                self._reset()
                self._main_menu()

    def _update(self, dt):
        keys    = pygame.key.get_pressed()
        mbtns   = pygame.mouse.get_pressed()
        mpos    = pygame.mouse.get_pos()

        # Player
        fired_before = self.player.shoot_timer
        self.player.update(dt, keys, mbtns, mpos, self.bullets, self.particles)
        if self.player.shoot_timer > fired_before:
            self.sounds.play_gun()
        if self.player.dead:
            self.game_over = True

        # Parallax scroll
        self.bg.scroll(self.player.vx)

        # Bullets
        self.bullets.update()

        # Zombies
        for z in list(self.zombies):
            base_hit = z.update(dt, self.base.rect, self.player, self.particles)
            if base_hit:
                self.base.take_damage(z.contact_dmg)

        # Bullet ↔ Zombie
        hits = pygame.sprite.groupcollide(
            self.bullets, self.zombies, True, False,
            pygame.sprite.collide_rect
        )
        for _b, zlist in hits.items():
            for z in zlist:
                was_alive = not z.dying
                z.hit(Zombie.BULLET_DMG, self.particles)
                if was_alive and z.dying:
                    self.score += z.score_val

        # Particles
        self.particles.update()

        # Waves
        self.wave_mgr.update(dt)
        if self.wave_mgr.all_done and len(self.zombies) == 0:
            self.won = True
            if self.score > self.highscore:
                 self.highscore = self.score
                 self._save_highscore()

        if self.base.hp <= 0:
            self.game_over = True
            if self.score > self.highscore:
                self.highscore = self.score
                self._save_highscore()

        self.banner.update(dt)

    def _draw(self):
        # Background
        self.bg.draw(self.screen)

        # Particles (behind everything)
        self.particles.draw(self.screen)

        # Base
        self.base.draw(self.screen)

        # Zombies (sprite + hp bar)
        for z in self.zombies:
            z.draw_sprite(self.screen)
            z.draw_hpbar(self.screen)

        # Player
        self.player.draw_sprite(self.screen)

        # Bullets
        self.bullets.draw(self.screen)

        # Horde banner
        self.banner.draw(self.screen)

        # HUD
        self.hud.draw(self.screen, self.score, self.wave_mgr, self.player)

        # Game-over / win overlays
        if self.game_over:
            self.hud.draw_gameover(self.screen, self.score, self.highscore)
        elif self.won:
            self.hud.draw_win(self.screen, self.score, self.highscore)

        # Crosshair (always on top)
        draw_crosshair(self.screen, pygame.mouse.get_pos())

        pygame.display.flip()


# ─────────────────────────────────────────────────────────
def _pause(self):
        pause = PauseMenu(self.screen)
        while not pause.done:
            self.clock.tick(FPS)
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    self._save_highscore()
                    pygame.quit(); sys.exit()
                pause.handle_event(ev)
            self._draw()
            pause.draw(self.screen)
            pygame.display.flip()
        pygame.mouse.set_visible(False)
        if pause.choice == "menu":
            self._reset()
            self._main_menu()
        elif pause.choice == "quit":
            self._save_highscore()
            pygame.quit(); sys.exit()
if __name__ == "__main__":
    Game().run()
