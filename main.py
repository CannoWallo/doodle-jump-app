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
ROCKET_SLOWDOWN = 45

# ================== КЛАССЫ ==================
class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        # Список файлов (проверь регистр на GitHub!)
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
                img = pygame.image.load(path).convert_alpha()
                # Игровая версия
                h_g = 80
                w_g = int(h_g * (img.get_width() / img.get_height()))
                self.char_game_images.append(pygame.transform.smoothscale(img, (w_g, h_g)))
                # Меню версия
                h_m = 280
                w_m = int(h_m * (img.get_width() / img.get_height()))
                self.char_menu_images.append(pygame.transform.smoothscale(img, (w_m, h_m)))
            except:
                print(f"Ошибка: {path} не найден")
                surf = pygame.Surface((60, 80), pygame.SRCALPHA)
                surf.fill((200, 100, 200))
                self.char_game_images.append(surf)
                self.char_menu_images.append(pygame.transform.scale(surf, (180, 240)))
        self.select_char(0)

    def select_char(self, idx):
        self.current_char_idx = idx % len(self.char_paths)
        self.original_image = self.char_game_images[self.current_char_idx]
        self.image = self.original_image
        self.rect = self.image.get_rect()

    def reset(self):
        self.pos = pygame.Vector2(WIDTH // 2, HEIGHT - 100)
        self.vel = pygame.Vector2(0, 0)
        self.accel_x = 0.75 
        self.friction = 0.88
        self.angle = 0
        self.score = 0
        self.rocket_timer = 0
        self.speed_multiplier = 1.0

    def update(self, target_x, is_pressing):
        # Горизонтальная физика (Doodle Jump Style)
        if is_pressing:
            dx = target_x - self.pos.x
            if dx > WIDTH / 2: dx -= WIDTH
            elif dx < -WIDTH / 2: dx += WIDTH
            if abs(dx) > 10:
                self.vel.x += self.accel_x if dx > 0 else -self.accel_x
        
        self.vel.x *= self.friction
        limit = 11 * self.speed_multiplier
        if self.vel.x > limit: self.vel.x = limit
        if self.vel.x < -limit: self.vel.x = -limit

        # Полет на ракете или обычная гравитация
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
        # Бесконечный экран
        if self.pos.x > WIDTH: self.pos.x -= WIDTH
        elif self.pos.x < 0: self.pos.x += WIDTH
        
        # Поворот и отражение спрайта
        img = self.original_image if self.vel.x >= 0 else pygame.transform.flip(self.original_image, True, False)
        self.image = pygame.transform.rotate(img, self.angle)
        self.rect = self.image.get_rect(center=(int(self.pos.x), int(self.pos.y)))

class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y, p_type="normal"):
        super().__init__()
        self.type = p_type
        self.rect = pygame.Rect(x, y, 70, 16)
        self.active = True
        self.speed = random.choice([-2, 2])
        self.has_spring = (random.random() > 0.92 and p_type == "normal")
        self.has_booster = (random.random() > 0.95 and p_type == "normal" and not self.has_spring)

    def update(self, shift, mult):
        self.rect.y += shift
        if self.type == "moving":
            self.rect.x += self.speed * mult
            if self.rect.left <= 0 or self.rect.right >= WIDTH: self.speed *= -1

    def draw(self, screen):
        if not self.active: return
        color = WHITE if self.type == "normal" else YELLOW if self.type == "moving" else RED
        pygame.draw.rect(screen, BLACK, self.rect, border_radius=8)
        pygame.draw.rect(screen, color, self.rect.inflate(-4, -4), border_radius=6)
        if self.has_spring:
            pygame.draw.rect(screen, (0, 200, 255), (self.rect.centerx-10, self.rect.y-8, 20, 8), border_radius=3)

class Enemy(pygame.sprite.Sprite):
    def __init__(self, y):
        super().__init__()
        try:
            img = pygame.image.load("hot.webp").convert_alpha()
            self.image = pygame.transform.smoothscale(img, (60, 60))
        except:
            self.image = pygame.Surface((50, 50)); self.image.fill(RED)
        self.rect = self.image.get_rect(center=(random.randint(50, WIDTH-50), y))
        self.start_x = self.rect.x

    def update(self, shift):
        self.rect.y += shift
        self.rect.x = self.start_x + math.sin(pygame.time.get_ticks() * 0.005) * 50
        if self.rect.top > HEIGHT: self.kill()

class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        try:
            img = pygame.image.load("igla.webp").convert_alpha()
            self.image = pygame.transform.smoothscale(img, (15, 35))
        except:
            self.image = pygame.Surface((5, 20)); self.image.fill(WHITE)
        self.rect = self.image.get_rect(center=(x, y))

    def update(self, shift):
        self.rect.y -= 20 - shift
        if self.rect.bottom < 0: self.kill()

class Booster(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        try:
            img = pygame.image.load("burn.webp").convert_alpha()
            self.image = pygame.transform.smoothscale(img, (30, 45))
        except:
            self.image = pygame.Surface((20, 30)); self.image.fill(GOLD)
        self.rect = self.image.get_rect(center=(x, y))

    def update(self, shift):
        self.rect.y += shift
        if self.rect.top > HEIGHT: self.kill()

# ================== MAIN GAME LOOP ==================
async def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()
    
    # Шрифты
    try:
        font_main = pygame.font.SysFont("Arial", 24, bold=True)
        font_big = pygame.font.SysFont("Arial", 42, bold=True)
    except:
        font_main = pygame.font.Font(None, 30)
        font_big = pygame.font.Font(None, 50)

    # Фон
    try:
        bg = pygame.transform.smoothscale(pygame.image.load("bg.jpg").convert(), (WIDTH, HEIGHT))
    except:
        bg = pygame.Surface((WIDTH, HEIGHT)); bg.fill(SKY_BLUE)

    player = Player()
    platforms = []
    boosters = pygame.sprite.Group()
    bullets = pygame.sprite.Group()
    enemies = pygame.sprite.Group()
    shoot_btn = pygame.Rect(WIDTH//2 - 35, HEIGHT - 90, 70, 70)

    def reset_game():
        player.reset()
        platforms.clear(); boosters.empty(); bullets.empty(); enemies.empty()
        platforms.append(Platform(WIDTH//2 - 35, HEIGHT - 50, "normal"))
        for i in range(1, 12):
            platforms.append(Platform(random.randint(0, WIDTH-70), HEIGHT - i*70))

    reset_game()
    state = "MENU"
    swipe_start_x = 0

    while True:
        screen.blit(bg, (0, 0))
        m_pos = pygame.mouse.get_pos()
        m_down = pygame.mouse.get_pressed()[0]

        for event in pygame.event.get():
            if event.type == pygame.QUIT: return
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                swipe_start_x = event.pos[0]
                if state == "PLAYING" and shoot_btn.collidepoint(event.pos):
                    if player.rocket_timer <= 0:
                        bullets.add(Bullet(player.rect.centerx, player.rect.top))

            if event.type == pygame.MOUSEBUTTONUP:
                if state == "MENU":
                    dist = event.pos[0] - swipe_start_x
                    if abs(dist) > 50: # Свайп для выбора
                        player.select_char(player.current_char_idx + (1 if dist < 0 else -1))
                    elif event.pos[1] > 450: # Кнопка играть
                        reset_game(); state = "PLAYING"
                elif state == "GAMEOVER":
                    if HEIGHT//2 < event.pos[1] < HEIGHT//2 + 100:
                        reset_game(); state = "PLAYING"
                    else: state = "MENU"

        if state == "MENU":
            # Заголовок и выбор
            txt = font_big.render("ВЫБЕРИ ГЕРОЯ", True, DARK_BLUE)
            screen.blit(txt, (WIDTH//2 - txt.get_width()//2, 50))
            
            char_img = player.get_menu_image()
            screen.blit(char_img, (WIDTH//2 - char_img.get_width()//2, 160))
            
            name = font_main.render(player.get_current_name(), True, BLACK)
            screen.blit(name, (WIDTH//2 - name.get_width()//2, 450))
            
            pygame.draw.rect(screen, DARK_BLUE, (WIDTH//2-80, HEIGHT-100, 160, 50), border_radius=15)
            play_txt = font_main.render("ИГРАТЬ", True, WHITE)
            screen.blit(play_txt, (WIDTH//2 - play_txt.get_width()//2, HEIGHT-85))

        elif state == "PLAYING":
            player.speed_multiplier = 1.0 + (player.score // 50) * 0.1
            player.update(m_pos[0], m_down)

            # Движение камеры
            shift = 0
            if player.pos.y < HEIGHT // 2:
                shift = (HEIGHT // 2 - player.pos.y) * 0.1
                player.pos.y += shift
                player.score += 1

            # Обновление объектов
            boosters.update(shift)
            bullets.update(shift)
            enemies.update(shift)
            
            for p in platforms[:]:
                p.update(shift, player.speed_multiplier)
                if p.rect.top > HEIGHT:
                    platforms.remove(p)
                    new_type = "normal"
                    if random.random() > 0.8: new_type = "moving"
                    elif random.random() > 0.95: new_type = "breakable"
                    new_p = Platform(random.randint(0, WIDTH-70), -20, new_type)
                    platforms.append(new_p)
                    if new_p.has_booster: boosters.add(Booster(new_p.rect.centerx, new_p.rect.top-25))
                    if random.random() > 0.97: enemies.add(Enemy(-50))

            # Коллизии
            if player.vel.y > 0:
                for p in platforms:
                    if p.active and player.rect.colliderect(p.rect) and player.rect.bottom <= p.rect.top + 20:
                        player.vel.y = SPRING_JUMP if p.has_spring else BASE_JUMP
                        if p.type == "breakable": p.active = False
                
                b_hit = pygame.sprite.spritecollideany(player, boosters)
                if b_hit:
                    player.rocket_timer = 150
                    b_hit.kill()

            if player.rocket_timer <= 0:
                if pygame.sprite.spritecollideany(player, enemies): state = "GAMEOVER"
            
            pygame.sprite.groupcollide(bullets, enemies, True, True)

            # Отрисовка
            for p in platforms: p.draw(screen)
            boosters.draw(screen)
            bullets.draw(screen)
            enemies.draw(screen)
            screen.blit(player.image, player.rect)
            
            # Интерфейс
            score_txt = font_main.render(f"SCORE: {player.score}", True, BLACK)
            screen.blit(score_txt, (20, 20))
            pygame.draw.circle(screen, GOLD, shoot_btn.center, 35)
            pygame.draw.circle(screen, BLACK, shoot_btn.center, 35, 3)

            if player.pos.y > HEIGHT: state = "GAMEOVER"

        elif state == "GAMEOVER":
            over_txt = font_big.render("GAME OVER", True, RED)
            screen.blit(over_txt, (WIDTH//2 - over_txt.get_width()//2, HEIGHT//2 - 100))
            res_txt = font_main.render(f"FINAL SCORE: {player.score}", True, BLACK)
            screen.blit(res_txt, (WIDTH//2 - res_txt.get_width()//2, HEIGHT//2))
            retry_txt = font_main.render("CLICK TO RESTART", True, DARK_BLUE)
            screen.blit(retry_txt, (WIDTH//2 - retry_txt.get_width()//2, HEIGHT//2 + 60))

        pygame.display.flip()
        await asyncio.sleep(0)
        clock.tick(FPS)

if __name__ == "__main__":
    asyncio.run(main())
