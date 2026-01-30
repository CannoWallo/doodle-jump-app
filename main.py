import pygame
import random
import math
import asyncio
import sys

# ================== НАСТРОЙКИ ==================
WIDTH, HEIGHT = 360, 640
FPS = 60

# Цвета
WHITE, YELLOW, RED = (255, 255, 255), (255, 255, 0), (255, 50, 50)
BLACK, DARK_BLUE, GOLD, SKY_BLUE = (0, 0, 0), (0, 0, 139), (255, 215, 0), (210, 230, 250)

# Физика
BASE_GRAVITY = 0.6
BASE_JUMP = -16
SPRING_JUMP = -32
ROCKET_MAX_SPEED = -28 
ROCKET_SLOWDOWN = 45

# ================== КЛАССЫ ==================
class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        # ВНИМАНИЕ: Проверь регистр этих имен на GitHub!
        self.char_paths = ["liza.webp", "nika.webp", "tvorch.webp", "egor.webp"]
        self.char_names = ["LIZA", "NIKA", "TVORCH", "EGOR"]
        
        self.char_game_images = []
        self.char_menu_images = []
        self.current_char_idx = 0
        self.load_sprites()
        self.high_score = 0
        self.reset()

    def load_sprites(self):
        for path in self.char_paths:
            try:
                # В вебе конвертация в .convert_alpha() обязательна после pygame.init()
                original_img = pygame.image.load(path).convert_alpha()
                
                h_game = 80
                w_game = int(h_game * (original_img.get_width() / original_img.get_height()))
                self.char_game_images.append(pygame.transform.smoothscale(original_img, (w_game, h_game)))
                
                h_menu = 280
                w_menu = int(h_menu * (original_img.get_width() / original_img.get_height()))
                self.char_menu_images.append(pygame.transform.smoothscale(original_img, (w_menu, h_menu)))
            except Exception as e:
                print(f"DEBUG: Ошибка загрузки {path}: {e}")
                f = pygame.Surface((60, 80), pygame.SRCALPHA)
                f.fill((200, 100, 200))
                self.char_game_images.append(f)
                self.char_menu_images.append(pygame.transform.scale(f, (180, 240)))
        self.select_char(0)

    def select_char(self, idx):
        self.current_char_idx = idx
        self.original_image = self.char_game_images[idx]
        self.image = self.original_image
        self.rect = self.image.get_rect()

    def get_menu_image(self):
        return self.char_menu_images[self.current_char_idx]
    
    def get_current_name(self):
        return self.char_names[self.current_char_idx]

    def reset(self):
        self.pos = pygame.Vector2(WIDTH // 2, HEIGHT - 100)
        self.vel = pygame.Vector2(0, 0)
        self.accel_x = 0.7 
        self.friction = 0.9 
        self.angle = 0
        self.score = 0
        self.speed_multiplier = 1.0
        self.rocket_timer = 0

    def update(self, target_x, is_pressing):
        if is_pressing:
            dx = target_x - self.pos.x
            if dx > WIDTH / 2: dx -= WIDTH
            elif dx < -WIDTH / 2: dx += WIDTH
            if abs(dx) > 10:
                if dx > 0: self.vel.x += self.accel_x
                else: self.vel.x -= self.accel_x
        
        self.vel.x *= self.friction
        limit = 10 * self.speed_multiplier
        if self.vel.x > limit: self.vel.x = limit
        if self.vel.x < -limit: self.vel.x = -limit

        if self.rocket_timer > ROCKET_SLOWDOWN:
            self.vel.y = ROCKET_MAX_SPEED
            self.rocket_timer -= 1
            self.angle += 15
        elif self.rocket_timer > 0:
            self.vel.y += 0.55 
            self.rocket_timer -= 1
            if self.angle % 360 != 0: self.angle -= 10
        else:
            self.vel.y += BASE_GRAVITY * self.speed_multiplier
            target_angle = -self.vel.x * 3
            self.angle += (target_angle - self.angle) * 0.1

        self.pos += self.vel
        if self.pos.x > WIDTH: self.pos.x -= WIDTH
        elif self.pos.x < 0: self.pos.x += WIDTH
        
        img = self.original_image if self.vel.x >= 0 else pygame.transform.flip(self.original_image, True, False)
        self.image = pygame.transform.rotate(img, self.angle)
        self.rect = self.image.get_rect(center=(int(self.pos.x), int(self.pos.y)))

# Обязательные классы (Booster, Platform, Bullet, Enemy) остаются без изменений
class Booster(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        try:
            img = pygame.image.load("burn.webp").convert_alpha()
            h = 45; w = int(h * (img.get_width() / img.get_height()))
            self.image = pygame.transform.smoothscale(img, (w, h))
        except:
            self.image = pygame.Surface((30, 45)); self.image.fill(GOLD)
        self.rect = self.image.get_rect(center=(x, y))
    def update(self, shift):
        self.rect.y += shift
        if self.rect.top > HEIGHT: self.kill()

class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y, width=75, p_type="normal"):
        super().__init__()
        self.type, self.rect, self.active = p_type, pygame.Rect(x, y, width, 18), True
        self.speed = random.choice([-2, 2]); self.has_spring = False; self.has_booster = False
        if p_type == "normal":
            rnd = random.random()
            if rnd > 0.92: self.has_spring = True
            elif rnd > 0.88: self.has_booster = True
    def update(self, shift, mult):
        self.rect.y += shift
        if self.type == "moving":
            self.rect.x += self.speed * mult
            if self.rect.left <= 0 or self.rect.right >= WIDTH: self.speed *= -1
    def draw(self, screen):
        if not self.active: return
        c = WHITE if self.type == "normal" else YELLOW if self.type == "moving" else RED
        pygame.draw.rect(screen, BLACK, self.rect, border_radius=10)
        pygame.draw.rect(screen, c, self.rect.inflate(-4, -4), border_radius=8)
        if self.has_spring:
            s_r = pygame.Rect(self.rect.centerx-12, self.rect.y-10, 24, 10)
            pygame.draw.rect(screen, BLACK, s_r, border_radius=4)
            pygame.draw.rect(screen, (0, 200, 255), s_r.inflate(-2,-2), border_radius=3)

class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        try:
            img = pygame.image.load("igla.webp").convert_alpha()
            self.image = pygame.transform.smoothscale(img, (int(40 * (img.get_width()/img.get_height())), 40))
        except:
            self.image = pygame.Surface((4, 25)); self.image.fill((100, 100, 100))
        self.rect = self.image.get_rect(center=(x, y))
        self.pos_y = float(y)
    def update(self, shift):
        self.pos_y += -22 + shift
        self.rect.centery = self.pos_y
        if self.rect.bottom < 0: self.kill()

class Enemy(pygame.sprite.Sprite):
    def __init__(self, y):
        super().__init__()
        try:
            img = pygame.image.load("hot.webp").convert_alpha()
            h = 65; w = int(h * (img.get_width()/img.get_height()))
            self.image = pygame.transform.smoothscale(img, (w, h))
        except:
            self.image = pygame.Surface((50, 50)); self.image.fill(RED)
        self.rect = self.image.get_rect(center=(random.randint(50, WIDTH-50), y))
        self.offset = random.uniform(0, 6.28)
    def update(self, shift):
        self.rect.y += shift
        self.rect.x += math.sin(pygame.time.get_ticks() * 0.005 + self.offset) * 3
        if self.rect.top > HEIGHT: self.kill()

# ================== MAIN ==================
async def main():
    pygame.init()
    # Принудительная активация звука для веба
    try: pygame.mixer.init()
    except: pass
    
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()
    
    # Шрифты - используем стандартные системные, так надежнее в вебе
    font_s = pygame.font.SysFont("Arial", 18, bold=True)
    font_b = pygame.font.SysFont("Arial", 36, bold=True)
    font_name = pygame.font.SysFont("Arial", 28, bold=True)

    try:
        bg = pygame.image.load("bg.jpg").convert()
        bg = pygame.transform.smoothscale(bg, (WIDTH, HEIGHT))
    except:
        bg = pygame.Surface((WIDTH, HEIGHT)); bg.fill(SKY_BLUE)

    player = Player()
    platforms = []
    boosters = pygame.sprite.Group(); bullets = pygame.sprite.Group(); enemies = pygame.sprite.Group()
    shoot_btn = pygame.Rect(WIDTH//2 - 35, HEIGHT - 90, 70, 70)

    def reset_game():
        player.reset()
        platforms.clear(); boosters.empty(); bullets.empty(); enemies.empty()
        platforms.append(Platform(WIDTH//2 - 60, HEIGHT - 50, 120, "normal"))
        for i in range(1, 10): 
            p = Platform(random.randint(0, WIDTH-80), HEIGHT - 50 - i*100)
            platforms.append(p)
            if p.has_booster: boosters.add(Booster(p.rect.centerx, p.rect.top-25))

    reset_game()
    state = "MENU"

    while True:
        screen.blit(bg, (0, 0))
        m_pos = pygame.mouse.get_pos()
        m_down = pygame.mouse.get_pressed()[0]
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT: return
            if event.type == pygame.MOUSEBUTTONDOWN and state == "PLAYING":
                if shoot_btn.collidepoint(event.pos):
                    if player.rocket_timer <= 0: bullets.add(Bullet(player.rect.centerx, player.rect.top))
            if event.type == pygame.MOUSEBUTTONUP:
                if state == "MENU" and event.pos[1] > 450:
                    reset_game(); state = "PLAYING"
                elif state == "GAMEOVER":
                    if pygame.Rect(WIDTH//2-85, HEIGHT//2+20, 170, 45).collidepoint(event.pos):
                        reset_game(); state = "PLAYING"
                    elif pygame.Rect(WIDTH//2-85, HEIGHT//2+80, 170, 45).collidepoint(event.pos):
                        state = "MENU"

        if state == "MENU":
            title = font_b.render("Doodle Jump App", True, DARK_BLUE)
            screen.blit(title, (WIDTH//2 - title.get_width()//2, 70))
            screen.blit(player.get_menu_image(), (WIDTH//2 - player.get_menu_image().get_width()//2, 150))
            
            start_area = pygame.Rect(WIDTH//2 - 100, HEIGHT - 100, 200, 55)
            pygame.draw.rect(screen, DARK_BLUE, start_area, border_radius=18)
            st_txt = font_s.render("ИГРАТЬ", True, WHITE)
            screen.blit(st_txt, (start_area.centerx - st_txt.get_width()//2, start_area.centery - st_txt.get_height()//2))

        elif state == "PLAYING":
            player.update(m_pos[0], m_down)
            # Логика платформы и камеры...
            shift = max(0, (HEIGHT//2 - player.pos.y) * 0.15) if player.pos.y < HEIGHT//2 else 0
            player.pos.y += shift
            
            boosters.update(shift); bullets.update(shift); enemies.update(shift)
            for p in platforms[:]:
                p.update(shift, 1.0)
                if p.rect.top > HEIGHT:
                    platforms.remove(p)
                    new_p = Platform(random.randint(0, WIDTH-80), -50)
                    platforms.append(new_p)
                    player.score += 1
            
            if player.vel.y > 0:
                for p in platforms:
                    if p.active and player.rect.colliderect(p.rect) and player.rect.bottom <= p.rect.top + 20:
                        player.vel.y = SPRING_JUMP if p.has_spring else BASE_JUMP
                if pygame.sprite.spritecollideany(player, boosters): player.rocket_timer = 130

            if player.pos.y > HEIGHT: state = "GAMEOVER"

            for p in platforms: p.draw(screen)
            boosters.draw(screen); enemies.draw(screen); bullets.draw(screen)
            screen.blit(player.image, player.rect)
            pygame.draw.circle(screen, GOLD, shoot_btn.center, 35)

        elif state == "GAMEOVER":
            msg = font_b.render("GAME OVER", True, RED)
            screen.blit(msg, (WIDTH//2 - msg.get_width()//2, HEIGHT//2-50))

        pygame.display.flip()
        await asyncio.sleep(0) # Критично для Pygbag!
        clock.tick(FPS)

asyncio.run(main())
