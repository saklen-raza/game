import math
import random
import pygame

# ------------------------------------------------------------
# NEON SPACE SHOOTER
# Controls: Arrow keys / WASD = move, SPACE = shoot, P = pause,
#           ENTER = restart after game over, ESC = quit
# Install first: py -m pip install pygame
# Run: py space_shooter.py
# ------------------------------------------------------------

pygame.init()

WIDTH, HEIGHT = 700, 800
FPS = 60
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Neon Space Shooter")
clock = pygame.time.Clock()

# Colours
BLACK = (4, 3, 15)
WHITE = (245, 240, 255)
PURPLE = (155, 55, 255)
PINK = (255, 45, 115)
CYAN = (100, 220, 255)
DARK_PURPLE = (35, 12, 65)

font = pygame.font.SysFont("consolas", 25, bold=True)
small_font = pygame.font.SysFont("consolas", 17, bold=True)
big_font = pygame.font.SysFont("consolas", 52, bold=True)


def glow_circle(surface, colour, pos, radius, strength=3):
    """Draw a soft neon glow and a bright centre."""
    x, y = int(pos[0]), int(pos[1])
    for i in range(strength, 0, -1):
        r = radius + i * 5
        alpha = max(8, 35 - i * 5)
        layer = pygame.Surface((r * 2 + 4, r * 2 + 4), pygame.SRCALPHA)
        pygame.draw.circle(layer, (*colour, alpha), (r + 2, r + 2), r)
        surface.blit(layer, (x - r - 2, y - r - 2), special_flags=pygame.BLEND_ADD)
    pygame.draw.circle(surface, colour, (x, y), radius)


def neon_line(surface, colour, start, end, width=2):
    pygame.draw.line(surface, colour, start, end, width)
    glow = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    pygame.draw.line(glow, (*colour, 55), start, end, width + 8)
    surface.blit(glow, (0, 0), special_flags=pygame.BLEND_ADD)


def make_stars(count=100):
    return [[random.randrange(WIDTH), random.randrange(HEIGHT),
             random.choice([1, 1, 1, 2]), random.uniform(0.3, 1.5)]
            for _ in range(count)]


def draw_background(surface, stars, tick):
    surface.fill(BLACK)

    # Distant stars
    for star in stars:
        x, y, size, speed = star
        brightness = 130 + int(100 * abs(math.sin(tick * 0.025 + x)))
        pygame.draw.circle(surface, (brightness, brightness, 255), (int(x), int(y)), size)
        star[1] += speed
        if star[1] > HEIGHT:
            star[1] = 0
            star[0] = random.randrange(WIDTH)

    # Large purple planet, partly outside the lower-left corner
    planet_center = (-35, 615)
    for radius, colour in [(180, (27, 8, 55)), (173, (45, 13, 85)),
                           (164, (24, 8, 48))]:
        pygame.draw.circle(surface, colour, planet_center, radius)
    pygame.draw.arc(surface, (120, 45, 210),
                    (-210, 435, 350, 350), 4.55, 6.1, 3)

    # Small distant planet
    pygame.draw.circle(surface, (35, 15, 60), (570, 440), 42)
    pygame.draw.circle(surface, (95, 45, 150), (570, 440), 42, 2)


class Bullet:
    def __init__(self, x, y):
        self.x, self.y = x, y
        self.speed = 11
        self.radius = 4

    def update(self):
        self.y -= self.speed

    def draw(self, surface):
        glow_circle(surface, (190, 130, 255), (self.x, self.y), self.radius, 2)
        pygame.draw.rect(surface, WHITE, (self.x - 2, self.y - 10, 4, 15), border_radius=2)

    def off_screen(self):
        return self.y < -20


class Enemy:
    def __init__(self):
        self.x = random.randint(45, WIDTH - 45)
        self.y = random.randint(-180, -45)
        self.speed = random.uniform(2.0, 3.7)
        self.size = random.randint(18, 25)
        self.phase = random.random() * math.tau

    def update(self):
        self.y += self.speed
        self.x += math.sin(self.y * 0.025 + self.phase) * 0.8

    def points(self):
        s = self.size
        return [(self.x, self.y + s),
                (self.x - s, self.y - s * 0.65),
                (self.x + s, self.y - s * 0.65)]

    def draw(self, surface):
        pts = self.points()
        glow = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        pygame.draw.polygon(glow, (*PINK, 45), pts, 9)
        surface.blit(glow, (0, 0), special_flags=pygame.BLEND_ADD)
        pygame.draw.polygon(surface, PINK, pts, 4)
        pygame.draw.line(surface, (255, 110, 150),
                         (self.x, self.y + self.size + 5),
                         (self.x, self.y + self.size + 18), 3)

    def off_screen(self):
        return self.y > HEIGHT + 30


class Asteroid:
    def __init__(self):
        self.x = random.randint(25, WIDTH - 25)
        self.y = random.randint(-HEIGHT, -30)
        self.speed = random.uniform(1.0, 2.2)
        self.radius = random.randint(11, 20)
        self.angle = random.random() * 6.28

    def update(self):
        self.y += self.speed
        self.angle += 0.01

    def draw(self, surface):
        points = []
        for i in range(8):
            a = self.angle + i * math.tau / 8
            r = self.radius * (0.8 if i % 2 else 1.15)
            points.append((self.x + math.cos(a) * r,
                           self.y + math.sin(a) * r))
        pygame.draw.polygon(surface, (20, 12, 45), points)
        pygame.draw.polygon(surface, (115, 75, 180), points, 2)

    def off_screen(self):
        return self.y > HEIGHT + 30


class Player:
    def __init__(self):
        self.x = WIDTH // 2
        self.y = HEIGHT - 75
        self.speed = 6
        self.radius = 20
        self.cooldown = 0
        self.invulnerable = 0

    def update(self, keys):
        dx = (keys[pygame.K_RIGHT] or keys[pygame.K_d]) - (keys[pygame.K_LEFT] or keys[pygame.K_a])
        dy = (keys[pygame.K_DOWN] or keys[pygame.K_s]) - (keys[pygame.K_UP] or keys[pygame.K_w])
        self.x += dx * self.speed
        self.y += dy * self.speed
        self.x = max(28, min(WIDTH - 28, self.x))
        self.y = max(45, min(HEIGHT - 35, self.y))
        if self.cooldown > 0:
            self.cooldown -= 1
        if self.invulnerable > 0:
            self.invulnerable -= 1

    def shoot(self):
        if self.cooldown == 0:
            self.cooldown = 13
            return [Bullet(self.x - 9, self.y - 22),
                    Bullet(self.x + 9, self.y - 22)]
        return []

    def draw(self, surface):
        if self.invulnerable and (self.invulnerable // 5) % 2 == 0:
            return
        x, y = self.x, self.y
        points = [(x, y - 31), (x - 28, y + 22), (x - 9, y + 16),
                  (x, y + 25), (x + 9, y + 16), (x + 28, y + 22)]
        glow = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        pygame.draw.polygon(glow, (*PURPLE, 65), points, 10)
        surface.blit(glow, (0, 0), special_flags=pygame.BLEND_ADD)
        pygame.draw.polygon(surface, WHITE, points, 3)
        pygame.draw.polygon(surface, (80, 30, 150),
                            [(x, y - 20), (x - 7, y + 14), (x + 7, y + 14)])
        pygame.draw.line(surface, CYAN, (x, y - 16), (x, y + 13), 2)
        pygame.draw.polygon(surface, PURPLE,
                            [(x - 19, y + 19), (x - 30, y + 27), (x - 13, y + 24)])
        pygame.draw.polygon(surface, PURPLE,
                            [(x + 19, y + 19), (x + 30, y + 27), (x + 13, y + 24)])
        glow_circle(surface, CYAN, (x, y + 27), 3, 1)


def draw_hud(surface, score, lives):
    score_text = font.render(f"SCORE: {score}", True, WHITE)
    surface.blit(score_text, (24, 18))
    label = font.render("LIVES:", True, WHITE)
    surface.blit(label, (WIDTH - 190, 18))
    for i in range(3):
        colour = (230, 35, 190) if i < lives else (65, 25, 70)
        pygame.draw.polygon(surface, colour,
                            [(WIDTH - 85 + i * 27, 30),
                             (WIDTH - 94 + i * 27, 21),
                             (WIDTH - 103 + i * 27, 30),
                             (WIDTH - 94 + i * 27, 42)])


def new_game():
    return Player(), [], [], [], 0, 3, 0, 0


def main():
    stars = make_stars()
    player, bullets, enemies, asteroids, score, lives, spawn_timer, asteroid_timer = new_game()
    tick = 0
    paused = False
    game_over = False
    running = True

    while running:
        clock.tick(FPS)
        tick += 1

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_p and not game_over:
                    paused = not paused
                elif event.key == pygame.K_RETURN and game_over:
                    player, bullets, enemies, asteroids, score, lives, spawn_timer, asteroid_timer = new_game()
                    game_over = False
                    paused = False

        keys = pygame.key.get_pressed()
        draw_background(screen, stars, tick)

        if not paused and not game_over:
            player.update(keys)
            if keys[pygame.K_SPACE]:
                bullets.extend(player.shoot())

            spawn_timer += 1
            asteroid_timer += 1
            # Difficulty gradually increases with score
            enemy_interval = max(22, 55 - score // 50)
            if spawn_timer >= enemy_interval:
                enemies.append(Enemy())
                spawn_timer = 0
            if asteroid_timer >= 105:
                asteroids.append(Asteroid())
                asteroid_timer = 0

            for bullet in bullets:
                bullet.update()
            bullets = [b for b in bullets if not b.off_screen()]

            for enemy in enemies:
                enemy.update()
            for asteroid in asteroids:
                asteroid.update()
            enemies = [e for e in enemies if not e.off_screen()]
            asteroids = [a for a in asteroids if not a.off_screen()]

            # Bullet-enemy collisions
            for enemy in enemies[:]:
                hit = next((b for b in bullets
                            if math.hypot(b.x - enemy.x, b.y - enemy.y) < enemy.size + 8), None)
                if hit:
                    bullets.remove(hit)
                    enemies.remove(enemy)
                    score += 10

            # Player-enemy and asteroid collisions
            if player.invulnerable == 0:
                for enemy in enemies[:]:
                    if math.hypot(player.x - enemy.x, player.y - enemy.y) < enemy.size + 20:
                        enemies.remove(enemy)
                        lives -= 1
                        player.invulnerable = 90
                        break
                for asteroid in asteroids:
                    if math.hypot(player.x - asteroid.x, player.y - asteroid.y) < asteroid.radius + 18:
                        lives -= 1
                        player.invulnerable = 90
                        asteroid.y = HEIGHT + 100
                        break

            if lives <= 0:
                game_over = True

        # Draw objects
        for asteroid in asteroids:
            asteroid.draw(screen)
        for enemy in enemies:
            enemy.draw(screen)
        for bullet in bullets:
            bullet.draw(screen)
        player.draw(screen)
        draw_hud(screen, score, lives)

        # Bottom control hint
        hint = small_font.render("MOVE: WASD / ARROWS     SHOOT: SPACE     PAUSE: P", True, (150, 125, 185))
        screen.blit(hint, hint.get_rect(center=(WIDTH // 2, HEIGHT - 17)))

        if paused:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 150))
            screen.blit(overlay, (0, 0))
            text = big_font.render("PAUSED", True, WHITE)
            screen.blit(text, text.get_rect(center=(WIDTH // 2, HEIGHT // 2)))
            sub = font.render("Press P to continue", True, PURPLE)
            screen.blit(sub, sub.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 55)))

        if game_over:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 175))
            screen.blit(overlay, (0, 0))
            title = big_font.render("GAME OVER", True, PINK)
            screen.blit(title, title.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 55)))
            final_score = font.render(f"FINAL SCORE: {score}", True, WHITE)
            screen.blit(final_score, final_score.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 5)))
            restart = small_font.render("Press ENTER to play again  |  ESC to quit", True, PURPLE)
            screen.blit(restart, restart.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 55)))

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
