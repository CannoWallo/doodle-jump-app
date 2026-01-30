import pygame
import random
import math
import asyncio

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
ROCKET_DURATION, ROCKET_SLOWDOWN = 85, 45

# ================== КЛАССЫ ==================
class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.char_paths = ["liza.webp", "nika.webp", "tvorch.webp", "egor.webp"]
        self.char_images = []
        self.current_char_idx = 0
        self.load_sprites()
        self.reset()
        self.high_score = 0

    def load_sprites(self):
        for path in self.char_paths:
            try:
                img = pygame.image.load(path).convert_alpha()
                h = 80
                w = int(h * (img.get_width() / img.get_height()))
                self.char_images.append(pygame.transform.smoothscale(img, (w, h)))
            except:
                f = pygame.Surface((60, 80)); f.fill((200, 100, 200))
                self.char_images.append(f)
        self.original_image = self.char_images[0]
        self.image = self.original_image
        self.rect = self.image.get_rect()

    def select_char(self, idx):
        if 0 <= idx < len(self.char_images):
            self.current_char_idx = idx
            self.original_image = self.char_images[idx]
            self.image = self.original_image
            self.rect = self.image.get_rect()

    def reset(self):
        self.pos = pygame.Vector2(WIDTH // 2, HEIGHT - 100)
        self.vel = pygame.Vector2(0, 0)
        self.angle = 0
        self.score = 0
        self.speed_multiplier = 1.0
        self.rocket_timer = 0

    def update(self, target_x):
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
            # Плавное следование за пальцем
            dx = target_x - self.pos.x
            self.vel.x = dx * 0.18 # Чуть увеличил отзывчивость
            self.angle = (-self.vel.x * 2.5)

        self.pos += self.vel
        if self.pos.x > WIDTH: self.pos.x = 0
        elif self.pos.x < 0: self.pos.x = WIDTH
        
        self.rect.midtop = self.pos
        img = self.original_image if self.vel.x >= 0 else pygame.transform.flip(self.original_image, True, False)
        self.image = pygame.transform.rotate(img, self.angle)
        self.rect = self.image.get_rect(center=self.rect.center)

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
        self.speed = random.choice([-2, 2])
        self.has_spring = random.random() > 0.88 and p_type == "normal" and width < 100
        self.has_booster = random.random() > 0.94 and p_type == "normal"

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
    # Использование SCALED важно для мобильных версий
    screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.SCALED)
    clock = pygame.time.Clock()
    
    # Безопасная инициализация шрифтов (иногда в WebApp они ломаются)
    try:
        font_s = pygame.font.SysFont("Arial", 18, bold=True)
        font_b = pygame.font.SysFont("Arial", 32, bold=True)
    except:
        font_s = pygame.font.Font(None, 24)
        font_b = pygame.font.Font(None, 40)

    # ЛОАДЕР
    screen.fill(BLACK)
    pygame.display.flip()
    await asyncio.sleep(0.5) 

    try:
        bg = pygame.transform.smoothscale(pygame.image.load("bg.jpg").convert(), (WIDTH, HEIGHT))
    except:
        bg = pygame.Surface((WIDTH, HEIGHT)); bg.fill(SKY_BLUE)

    player = Player()
    platforms, boosters = [], pygame.sprite.Group()
    bullets, enemies = pygame.sprite.Group(), pygame.sprite.Group()
    shoot_btn = pygame.Rect(WIDTH//2 - 35, HEIGHT - 90, 70, 70)

    def reset_game():
        player.reset()
        platforms.clear(); boosters.empty(); bullets.empty(); enemies.empty()
        platforms.append(Platform(0, HEIGHT - 20, WIDTH, "normal"))
        for i in range(10): platforms.append(Platform(random.randint(0, 285), HEIGHT - 110 - i*90))

    reset_game()
    state = "MENU"

    while True:
        screen.blit(bg, (0, 0))
        m_pos, m_down = pygame.mouse.get_pos(), pygame.mouse.get_pressed()[0]
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT: return
            if event.type == pygame.MOUSEBUTTONDOWN:
                if state == "MENU":
                    # КЛИК ПО ПЕРСОНАЖАМ (Увеличенная зона выбора)
                    clicked_char = False
                    for i in range(4):
                        char_zone = pygame.Rect((WIDTH//4)*i, 200, WIDTH//4, 200)
                        if char_zone.collidepoint(m_pos):
                            player.select_char(i)
                            clicked_char = True
                            break
                    if not clicked_char and m_pos[1] > 400: # Клик в нижней части экрана для старта
                        reset_game(); state = "PLAYING"
                
                elif state == "PLAYING":
                    if shoot_btn.collidepoint(m_pos):
                        if player.rocket_timer <= 0: bullets.add(Bullet(player.rect.centerx, player.rect.top))
                
                elif state == "GAMEOVER":
                    if pygame.Rect(WIDTH//2-85, HEIGHT//2+20, 170, 45).collidepoint(m_pos): reset_game(); state = "PLAYING"
                    elif pygame.Rect(WIDTH//2-85, HEIGHT//2+80, 170, 45).collidepoint(m_pos): state = "MENU"

        if state == "MENU":
            txt = font_b.render("ВЫБЕРИ ГЕРОЯ", True, DARK_BLUE)
            screen.blit(txt, (WIDTH//2 - txt.get_width()//2, 80))
            
            for i, img in enumerate(player.char_images):
                center_x = (WIDTH // 4) * i + (WIDTH // 8)
                char_rect = img.get_rect(center=(center_x, 300))
                if i == player.current_char_idx:
                    pygame.draw.rect(screen, YELLOW, char_rect.inflate(20, 20), 4, border_radius=10)
                screen.blit(img, char_rect)
            
            start_txt = font_s.render("НАЖМИ ВНИЗУ ДЛЯ СТАРТА", True, DARK_BLUE)
            screen.blit(start_txt, (WIDTH//2 - start_txt.get_width()//2, 500))

        elif state == "PLAYING":
            # СЛЕДОВАНИЕ ЗА ПАЛЬЦЕМ
            target_x = m_pos[0] if m_down and not shoot_btn.collidepoint(m_pos) else player.pos.x
            player.speed_multiplier = 1.0 + (player.score // 70) * 0.2
            player.update(target_x)

            shift = max(0, (HEIGHT//2 - player.pos.y) * 0.15) if player.pos.y < HEIGHT//2 else 0
            player.pos.y += shift
            
            boosters.update(shift); bullets.update(shift); enemies.update(shift)
            for p in platforms[:]:
                p.update(shift, player.speed_multiplier)
                if p.rect.top > HEIGHT:
                    platforms.remove(p)
                    new_y = min(pl.rect.y for pl in platforms) - 90
                    platforms.append(Platform(random.randint(0, 285), new_y, p_type="breakable" if random.random()>0.9 else "moving" if random.random()>0.8 else "normal"))
                    if platforms[-1].has_booster: boosters.add(Booster(platforms[-1].rect.centerx, platforms[-1].rect.top-25))
                    player.score += 1
                    if random.random() > 0.96: enemies.add(Enemy(-100))

            if player.vel.y > 0:
                for p in platforms:
                    if p.active and player.rect.colliderect(p.rect) and player.rect.bottom <= p.rect.top + 20:
                        player.vel.y = (SPRING_JUMP if p.has_spring else BASE_JUMP) * (player.speed_multiplier**0.3)
                        if p.type == "breakable": p.active = False
                b_hit = pygame.sprite.spritecollideany(player, boosters)
                if b_hit: player.rocket_timer = 130; b_hit.kill()

            if player.rocket_timer <= 0 and pygame.sprite.spritecollide(player, enemies, False): state = "GAMEOVER"
            pygame.sprite.groupcollide(bullets, enemies, True, True)

            for p in platforms: p.draw(screen)
            boosters.draw(screen); enemies.draw(screen); bullets.draw(screen)
            screen.blit(player.image, player.rect)
            
            # UI
            pygame.draw.rect(screen, (0,0,0,100), (0,0,WIDTH,40))
            screen.blit(font_s.render(f"СЧЕТ: {player.score}", True, WHITE), (15, 10))
            pygame.draw.circle(screen, GOLD, shoot_btn.center, 35)
            pygame.draw.circle(screen, BLACK, shoot_btn.center, 35, 3)

            if player.pos.y > HEIGHT: state = "GAMEOVER"

        elif state == "GAMEOVER":
            if player.score > player.high_score: player.high_score = player.score
            screen.blit(font_s.render("КОНЕЦ ИГРЫ", True, RED), (WIDTH//2-60, HEIGHT//2-100))
            pygame.draw.rect(screen, WHITE, (WIDTH//2-85, HEIGHT//2+20, 170, 45), border_radius=10)
            screen.blit(font_s.render("ЕЩЕ РАЗ", True, BLACK), (WIDTH//2-40, HEIGHT//2+30))
            pygame.draw.rect(screen, DARK_BLUE, (WIDTH//2-85, HEIGHT//2+80, 170, 45), border_radius=10)
            screen.blit(font_s.render("В МЕНЮ", True, WHITE), (WIDTH//2-35, HEIGHT//2+90))

        pygame.display.flip()
        await asyncio.sleep(0)
        clock.tick(FPS)

if __name__ == "__main__":
    asyncio.run(main())
