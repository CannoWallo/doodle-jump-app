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
        self.char_paths = ["liza.webp", "nika.webp", "tvorch.webp", "egor.webp"]
        self.char_names = [p.split('.')[0].upper() for p in self.char_paths]
        
        self.char_game_images = []
        self.char_menu_images = []
        self.current_char_idx = 0
        self.load_sprites()
        self.high_score = 0
        self.reset()

    def load_sprites(self):
        for path in self.char_paths:
            try:
                original_img = pygame.image.load(path).convert_alpha()
                h_game = 80
                w_game = int(h_game * (original_img.get_width() / original_img.get_height()))
                self.char_game_images.append(pygame.transform.smoothscale(original_img, (w_game, h_game)))
                
                h_menu = 280
                w_menu = int(h_menu * (original_img.get_width() / original_img.get_height()))
                self.char_menu_images.append(pygame.transform.smoothscale(original_img, (w_menu, h_menu)))
            except:
                f = pygame.Surface((60, 80), pygame.SRCALPHA); f.fill((200, 100, 200))
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
        # Исправленное горизонтальное управление
        if is_pressing:
            dx = target_x - self.pos.x
            
            # Учет перелета через край экрана для расчета кратчайшего пути
            if dx > WIDTH / 2: dx -= WIDTH
            elif dx < -WIDTH / 2: dx += WIDTH
            
            # "Мертвая зона" — если мышь в пределах 10 пикселей, не ускоряемся (убирает дрожание)
            if abs(dx) > 10:
                if dx > 0: self.vel.x += self.accel_x
                else: self.vel.x -= self.accel_x
        
        # Плавное торможение
        self.vel.x *= self.friction
        
        # Ограничение скорости
        limit = 10 * self.speed_multiplier
        if self.vel.x > limit: self.vel.x = limit
        if self.vel.x < -limit: self.vel.x = -limit

        # Вертикальное движение
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
            # Наклон зависит от скорости, но плавно
            target_angle = -self.vel.x * 3
            self.angle += (target_angle - self.angle) * 0.1

        # Применяем физику
        self.pos += self.vel

        # Бесконечный экран
        if self.pos.x > WIDTH: self.pos.x -= WIDTH
        elif self.pos.x < 0: self.pos.x += WIDTH
        
        # Отрисовка
        img = self.original_image if self.vel.x >= 0 else pygame.transform.flip(self.original_image, True, False)
        self.image = pygame.transform.rotate(img, self.angle)
        self.rect = self.image.get_rect(center=(int(self.pos.x), int(self.pos.y)))

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
        self.has_spring = False
        self.has_booster = False
        
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
    screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.SCALED)
    clock = pygame.time.Clock()
    
    try:
        font_s = pygame.font.SysFont("Arial", 18, bold=True)
        font_b = pygame.font.SysFont("Arial", 36, bold=True)
        font_name = pygame.font.SysFont("Arial", 28, bold=True)
    except:
        font_s = pygame.font.Font(None, 24); font_b = pygame.font.Font(None, 40); font_name = pygame.font.Font(None, 34)

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

    swipe_start_x = 0
    is_swiping = False

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
            if event.type == pygame.MOUSEBUTTONDOWN:
                swipe_start_x = event.pos[0]
                is_swiping = True
            if event.type == pygame.MOUSEBUTTONUP:
                if is_swiping and state == "MENU":
                    swipe_dist = event.pos[0] - swipe_start_x
                    if abs(swipe_dist) > 40:
                        idx = (player.current_char_idx + (1 if swipe_dist < 0 else -1)) % len(player.char_paths)
                        player.select_char(idx)
                    elif event.pos[1] > 450:
                        reset_game(); state = "PLAYING"
                elif state == "GAMEOVER":
                    if pygame.Rect(WIDTH//2-85, HEIGHT//2+20, 170, 45).collidepoint(event.pos): 
                        reset_game(); state = "PLAYING"
                    elif pygame.Rect(WIDTH//2-85, HEIGHT//2+80, 170, 45).collidepoint(event.pos): 
                        state = "MENU"
                is_swiping = False
            if event.type == pygame.MOUSEBUTTONDOWN and state == "PLAYING":
                if shoot_btn.collidepoint(event.pos):
                    if player.rocket_timer <= 0: bullets.add(Bullet(player.rect.centerx, player.rect.top))

        if state == "MENU":
            title = font_b.render("ВЫБЕРИ ГЕРОЯ", True, DARK_BLUE)
            screen.blit(title, (WIDTH//2 - title.get_width()//2, 70))
            t = pygame.time.get_ticks() * 0.004
            pulse = 1.0 + math.sin(t) * 0.03
            bobbing = math.sin(t * 0.8) * 10
            char_img = player.get_menu_image()
            w, h = char_img.get_size()
            scaled_char = pygame.transform.smoothscale(char_img, (int(w * pulse), int(h * pulse)))
            char_rect = scaled_char.get_rect(center=(WIDTH//2, HEIGHT//2 - 10 + bobbing))
            screen.blit(scaled_char, char_rect)
            name_text = font_name.render(player.get_current_name(), True, DARK_BLUE)
            name_bg = pygame.Rect(0, 0, name_text.get_width() + 30, 44)
            name_bg.center = (WIDTH//2, char_rect.bottom + 40 - bobbing)
            pygame.draw.rect(screen, WHITE, name_bg, border_radius=12)
            screen.blit(name_text, (name_bg.centerx - name_text.get_width()//2, name_bg.centery - name_text.get_height()//2))
            start_area = pygame.Rect(WIDTH//2 - 100, HEIGHT - 100, 200, 55)
            pygame.draw.rect(screen, DARK_BLUE, start_area, border_radius=18)
            screen.blit(font_s.render("ИГРАТЬ", True, WHITE), (start_area.centerx - 30, start_area.centery - 10))

        elif state == "PLAYING":
            player.speed_multiplier = 1.0 + (player.score // 70) * 0.2
            player.update(m_pos[0], m_down)
            
            shift = max(0, (HEIGHT//2 - player.pos.y) * 0.15) if player.pos.y < HEIGHT//2 else 0
            player.pos.y += shift
            
            boosters.update(shift); bullets.update(shift); enemies.update(shift)
            for p in platforms[:]:
                p.update(shift, player.speed_multiplier)
                if p.rect.top > HEIGHT:
                    platforms.remove(p)
                    new_y = min([pl.rect.y for pl in platforms]) - 100
                    new_p = Platform(random.randint(0, WIDTH-80), new_y, p_type="breakable" if random.random()>0.9 else "moving" if random.random()>0.8 else "normal")
                    platforms.append(new_p)
                    if new_p.has_booster: boosters.add(Booster(new_p.rect.centerx, new_p.rect.top-25))
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
            
            pygame.draw.rect(screen, (0,0,0,100), (0,0,WIDTH,40))
            screen.blit(font_s.render(f"СЧЕТ: {player.score}", True, WHITE), (15, 10))
            pygame.draw.circle(screen, GOLD, shoot_btn.center, 35)
            pygame.draw.circle(screen, BLACK, shoot_btn.center, 35, 3)

            if player.pos.y > HEIGHT: state = "GAMEOVER"

        elif state == "GAMEOVER":
            if player.score > player.high_score: player.high_score = player.score
            msg = font_b.render("КОНЕЦ ИГРЫ", True, RED)
            screen.blit(msg, (WIDTH//2 - msg.get_width()//2, HEIGHT//2-100))
            btn_restart = pygame.Rect(WIDTH//2-85, HEIGHT//2+20, 170, 45)
            pygame.draw.rect(screen, WHITE, btn_restart, border_radius=10)
            screen.blit(font_s.render("ЕЩЕ РАЗ", True, BLACK), (btn_restart.centerx-35, btn_restart.centery-10))
            btn_menu = pygame.Rect(WIDTH//2-85, HEIGHT//2+80, 170, 45)
            pygame.draw.rect(screen, DARK_BLUE, btn_menu, border_radius=10)
            screen.blit(font_s.render("В МЕНЮ", True, WHITE), (btn_menu.centerx-30, btn_menu.centery-10))

        pygame.display.flip()
        await asyncio.sleep(0)
        clock.tick(FPS)

if __name__ == "__main__":
    asyncio.run(main())
