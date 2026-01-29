import pygame
import random
import math
import asyncio

# ================== НАСТРОЙКИ ==================
WIDTH, HEIGHT = 360, 640
FPS = 60

# Цвета
WHITE = (255, 255, 255)
YELLOW = (255, 255, 0)
RED = (255, 50, 50)
BLACK = (0, 0, 0)
DARK_BLUE = (0, 0, 139)
SKY_BLUE = (210, 230, 250)
GOLD = (255, 215, 0)

# Физика
BASE_GRAVITY = 0.6
BASE_JUMP = -16
SPRING_JUMP = -32
ROCKET_MAX_SPEED = -28 
ROCKET_DURATION = 85  
ROCKET_SLOWDOWN = 45  
FRICTION = -0.12
ACCELERATION = 0.9

# ================== ИГРОК ==================
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
                aspect = img.get_width() / img.get_height()
                h = 80 
                w = int(h * aspect)
                self.char_images.append(pygame.transform.smoothscale(img, (w, h)))
            except:
                fallback = pygame.Surface((50, 80)); fallback.fill((200, 100, 200))
                self.char_images.append(fallback)
        self.original_image = self.char_images[self.current_char_idx]
        self.image = self.original_image
        self.rect = self.image.get_rect()

    def select_char(self, idx):
        self.current_char_idx = idx
        self.original_image = self.char_images[idx]
        self.image = self.original_image
        self.rect = self.image.get_rect()

    def reset(self):
        self.pos = pygame.Vector2(WIDTH // 2, HEIGHT - 100)
        self.vel = pygame.Vector2(0, 0)
        self.acc = pygame.Vector2(0, 0)
        self.rect.midbottom = self.pos
        self.angle = 0
        self.score = 0
        self.speed_multiplier = 1.0
        self.rocket_timer = 0

    def update(self, move_dir):
        if self.rocket_timer > ROCKET_SLOWDOWN:
            self.vel.y = ROCKET_MAX_SPEED
            self.rocket_timer -= 1
            self.angle += 15
        elif self.rocket_timer > 0:
            self.vel.y += 0.55 
            self.rocket_timer -= 1
            self.angle %= 360
            if self.angle > 0: self.angle = max(0, self.angle - 10)
        else:
            self.acc = pygame.Vector2(0, BASE_GRAVITY * self.speed_multiplier)
            if move_dir != 0:
                self.acc.x = move_dir * ACCELERATION * self.speed_multiplier
            self.acc.x += self.vel.x * FRICTION
            self.vel += self.acc
            target_angle = -self.vel.x * 3
            self.angle += (target_angle - self.angle) * 0.1

        self.pos += self.vel + 0.5 * self.acc
        if self.pos.x > WIDTH: self.pos.x = 0
        if self.pos.x < 0: self.pos.x = WIDTH
        self.rect.midtop = self.pos
        
        flipped_img = self.original_image
        if self.vel.x < -0.1:
            flipped_img = pygame.transform.flip(self.original_image, True, False)
        
        self.image = pygame.transform.rotate(flipped_img, self.angle)
        self.rect = self.image.get_rect(center=self.rect.center)

# ================== ОБЪЕКТЫ ==================
class Booster(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        try:
            img = pygame.image.load("burn.webp").convert_alpha()
            aspect = img.get_width() / img.get_height()
            h = 45
            w = int(h * aspect)
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
        self.type = p_type
        self.rect = pygame.Rect(x, y, width, 18)
        self.speed = random.choice([-2, 2])
        self.has_spring = random.random() > 0.88 and p_type == "normal" and width < 100
        self.has_booster = random.random() > 0.94 and p_type == "normal"
        self.active = True

    def update(self, shift, mult):
        self.rect.y += shift
        if self.type == "moving":
            self.rect.x += self.speed * mult
            if self.rect.left <= 0 or self.rect.right >= WIDTH: self.speed *= -1

    def draw(self, screen):
        if not self.active: return
        color = WHITE if self.type == "normal" else YELLOW if self.type == "moving" else RED
        pygame.draw.rect(screen, BLACK, self.rect, border_radius=10)
        inner_rect = self.rect.inflate(-4, -4)
        pygame.draw.rect(screen, color, inner_rect, border_radius=8)
        
        if self.has_spring:
            spring_rect = pygame.Rect(self.rect.centerx-12, self.rect.y-10, 24, 10)
            pygame.draw.rect(screen, BLACK, spring_rect, border_radius=4)
            pygame.draw.rect(screen, (0, 200, 255), spring_rect.inflate(-2,-2), border_radius=3)

class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        try:
            img = pygame.image.load("igla.webp").convert_alpha()
            aspect = img.get_width() / img.get_height()
            self.image = pygame.transform.smoothscale(img, (int(40 * aspect), 40))
        except:
            self.image = pygame.Surface((4, 25)); self.image.fill((100, 100, 100))
        self.rect = self.image.get_rect(center=(x, y))
        self.pos = pygame.Vector2(x, y)
        self.vel = -22

    def update(self, shift):
        self.pos.y += self.vel + shift
        self.rect.center = self.pos
        if self.rect.bottom < 0: self.kill()

class Enemy(pygame.sprite.Sprite):
    def __init__(self, y):
        super().__init__()
        try:
            img = pygame.image.load("hot.webp").convert_alpha()
            h = 65; w = int(h * (img.get_width() / img.get_height()))
            self.image = pygame.transform.smoothscale(img, (w, h))
        except:
            self.image = pygame.Surface((50, 50)); self.image.fill(RED)
        self.rect = self.image.get_rect()
        self.pos = pygame.Vector2(random.randint(50, WIDTH-50), y)
        self.offset = random.uniform(0, math.pi * 2)

    def update(self, shift):
        self.pos.y += shift
        self.pos.x += math.sin(pygame.time.get_ticks() * 0.005 + self.offset) * 3
        self.rect.center = self.pos
        if self.rect.top > HEIGHT: self.kill()

# ================== MAIN ==================
async def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Doodle Jump: Fix Menu")
    clock = pygame.time.Clock()
    
    try:
        bg_img = pygame.image.load("фон швейка тест.jpg").convert()
        bg_img = pygame.transform.smoothscale(bg_img, (WIDTH, HEIGHT))
    except:
        bg_img = pygame.Surface((WIDTH, HEIGHT)); bg_img.fill(SKY_BLUE)

    font_xs = pygame.font.SysFont("Verdana", 14, bold=True)
    font_s = pygame.font.SysFont("Verdana", 18, bold=True)
    font_b = pygame.font.SysFont("Verdana", 32, bold=True)

    player = Player()
    platforms = []; boosters = pygame.sprite.Group()
    bullets = pygame.sprite.Group(); enemies = pygame.sprite.Group()
    shoot_btn_rect = pygame.Rect(WIDTH//2 - 35, HEIGHT - 90, 70, 70)

    def spawn_platform(y, width=75):
        r = random.random()
        t = "breakable" if r > 0.90 else "moving" if r > 0.75 else "normal"
        p = Platform(random.randint(0, WIDTH-width), y, width, t)
        if p.has_booster:
            boosters.add(Booster(p.rect.centerx, p.rect.top - 25))
        return p

    def reset_game():
        if player.score > player.high_score: player.high_score = player.score
        player.reset()
        platforms.clear(); boosters.empty(); bullets.empty(); enemies.empty()
        # Начальная большая платформа
        platforms.append(Platform(0, HEIGHT - 20, WIDTH, "normal"))
        y = HEIGHT - 110
        for _ in range(10):
            platforms.append(spawn_platform(y)); y -= 90

    reset_game()
    game_state = "MENU"

    while True:
        screen.blit(bg_img, (0, 0))
        m_pos = pygame.mouse.get_pos(); m_pressed = pygame.mouse.get_pressed()[0]
        move_dir = 0

        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); return
            if event.type == pygame.MOUSEBUTTONDOWN:
                if game_state == "MENU":
                    for i in range(4):
                        x_area = (WIDTH // 4) * i + (WIDTH // 8)
                        char_rect = pygame.Rect(0, 0, 70, 90); char_rect.center = (x_area, 300)
                        if char_rect.collidepoint(m_pos): player.select_char(i); break
                    else: reset_game(); game_state = "PLAYING"
                elif game_state == "PLAYING" and shoot_btn_rect.collidepoint(m_pos):
                    if player.rocket_timer <= 0:
                        bullets.add(Bullet(player.rect.centerx, player.rect.top))
                elif game_state == "GAMEOVER":
                    # Проверка кликов по кнопкам проигрыша
                    retry_rect = pygame.Rect(WIDTH//2 - 85, HEIGHT//2 + 20, 170, 45)
                    menu_rect = pygame.Rect(WIDTH//2 - 85, HEIGHT//2 + 80, 170, 45)
                    if retry_rect.collidepoint(m_pos): 
                        reset_game(); game_state = "PLAYING"
                    elif menu_rect.collidepoint(m_pos): 
                        game_state = "MENU"

        if game_state == "MENU":
            title = font_b.render("ВЫБЕРИ ГЕРОЯ", True, DARK_BLUE)
            screen.blit(title, (WIDTH//2 - title.get_width()//2, 100))
            for i, img in enumerate(player.char_images):
                x_pos = (WIDTH // 4) * i + (WIDTH // 8)
                char_rect = img.get_rect(center=(x_pos, 300))
                if i == player.current_char_idx:
                    pygame.draw.rect(screen, YELLOW, char_rect.inflate(15, 15), 3, border_radius=8)
                screen.blit(img, char_rect)
            screen.blit(font_s.render("НАЖМИ ДЛЯ СТАРТА", True, DARK_BLUE), (WIDTH//2-100, 480))

        elif game_state == "PLAYING":
            if m_pressed and not shoot_btn_rect.collidepoint(m_pos):
                move_dir = -1 if m_pos[0] < WIDTH // 2 else 1
            
            player.speed_multiplier = 1.0 + max(0, (player.score - 50) // 70) * 0.25
            player.update(move_dir)

            shift = 0
            if player.pos.y < HEIGHT // 2:
                shift = (HEIGHT // 2 - player.pos.y) * 0.15
                player.pos.y += shift

            boosters.update(shift); bullets.update(shift); enemies.update(shift)
            for p in platforms[:]:
                p.update(shift, player.speed_multiplier)
                if p.rect.top > HEIGHT:
                    platforms.remove(p)
                    platforms.append(spawn_platform(min(pl.rect.y for pl in platforms) - 90))
                    player.score += 1
                    if random.random() > 0.95: enemies.add(Enemy(-100))

            if player.vel.y > 0:
                for p in platforms:
                    if p.active and player.rect.colliderect(p.rect):
                        if player.rect.bottom <= p.rect.top + 20:
                            player.vel.y = (SPRING_JUMP if p.has_spring else BASE_JUMP) * (player.speed_multiplier ** 0.3)
                            if p.type == "breakable": p.active = False
                
                hit_booster = pygame.sprite.spritecollideany(player, boosters)
                if hit_booster:
                    player.rocket_timer = ROCKET_DURATION + ROCKET_SLOWDOWN
                    hit_booster.kill()

            if player.rocket_timer <= 0:
                if pygame.sprite.spritecollide(player, enemies, False): game_state = "GAMEOVER"
            
            pygame.sprite.groupcollide(bullets, enemies, True, True)

            for p in platforms: p.draw(screen)
            boosters.draw(screen); enemies.draw(screen); bullets.draw(screen)
            screen.blit(player.image, player.rect)
            
            # UI
            ui_panel = pygame.Surface((WIDTH, 50), pygame.SRCALPHA); pygame.draw.rect(ui_panel, (0,0,0,120), (0,0,WIDTH,50))
            screen.blit(ui_panel, (0, 0))
            screen.blit(font_s.render(f"СЧЕТ: {player.score}", True, WHITE), (15, 12))
            screen.blit(font_xs.render(f"РЕКОРД: {max(player.high_score, player.score)}", True, GOLD), (WIDTH-120, 15))
            
            # Кнопка выстрела
            pygame.draw.circle(screen, BLACK, shoot_btn_rect.center, 37)
            pygame.draw.circle(screen, GOLD, shoot_btn_rect.center, 35)
            pygame.draw.line(screen, BLACK, (shoot_btn_rect.centerx, shoot_btn_rect.centery-15), (shoot_btn_rect.centerx, shoot_btn_rect.centery+15), 4)

            if player.pos.y > HEIGHT: game_state = "GAMEOVER"

        elif game_state == "GAMEOVER":
            if player.score > player.high_score: player.high_score = player.score
            screen.blit(font_b.render("КОНЕЦ ИГРЫ", True, RED), (WIDTH//2-110, HEIGHT//2-60))
            
            # Кнопка ЕЩЕ РАЗ
            btn_retry = pygame.Rect(WIDTH//2 - 85, HEIGHT//2 + 20, 170, 45)
            pygame.draw.rect(screen, BLACK, btn_retry, border_radius=10)
            pygame.draw.rect(screen, WHITE, btn_retry.inflate(-4,-4), border_radius=8)
            screen.blit(font_s.render("ЕЩЕ РАЗ", True, BLACK), (btn_retry.centerx - 40, btn_retry.centery - 12))
            
            # Кнопка В МЕНЮ (была потеряна)
            btn_menu = pygame.Rect(WIDTH//2 - 85, HEIGHT//2 + 80, 170, 45)
            pygame.draw.rect(screen, BLACK, btn_menu, border_radius=10)
            pygame.draw.rect(screen, DARK_BLUE, btn_menu.inflate(-4,-4), border_radius=8)
            screen.blit(font_s.render("В МЕНЮ", True, WHITE), (btn_menu.centerx - 35, btn_menu.centery - 12))

        pygame.display.flip()
        await asyncio.sleep(0)
        clock.tick(FPS)

if __name__ == "__main__":
    asyncio.run(main())