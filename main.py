import sys
import math
import os
import pygame
from core.entities import Actor, Enemy
from core.combat import CombatSystem, TickController

class CombatScene:
    def __init__(self, screen, font):
        self.screen = screen
        self.font = font
        self.a1 = Actor(
            "Sora",
            cd=0.2,
            atk=5,
            portrait_path=os.path.join("assets", "portraits", "sora.png"),
        )
        self.a2 = Actor(
            "Donald",
            cd=0.3,
            atk=4,
            portrait_path=os.path.join("assets", "portraits", "donald.png"),
        )
        self.a3 = Actor(
            "Goofy",
            cd = 0.4,
            atk = 3,
            portrait_path=os.path.join("assets", "portraits", "goofy.png"),
        )
        self.enemy = Enemy(
            hp=100,
            defense=2,
            portrait_path=os.path.join("assets", "portraits", "shadow.png"),
        )
        self.cs = CombatSystem([self.a1, self.a2], self.enemy)
        self.tc = TickController(0.2)
        self.actor_portraits = [
            self._load_portrait(self.a1.portrait_path),
            self._load_portrait(self.a2.portrait_path),
            self._load_portrait(self.a3.portrait_path)
        ]
        self.enemy_portrait = self._load_portrait(self.enemy.portrait_path)
        self.spawn_enemy(self.enemy)
        pass
    
    def spawn_enemy(self, enemy):
        self.enemy = enemy
        self.enemy_portrait = self._load_portrait(self.enemy.portrait_path)
        self.cs.enemy = enemy
        pass

    def update(self, dt):
        self.tc.update(dt, self.cs.on_tick)
        if self.enemy.health.is_dead():
            self.spawn_enemy(Enemy(hp=100, defense=2, portrait_path=self.enemy.portrait_path))
        pass

    def draw(self):
        self.screen.fill((20,20,20))
        self._draw_enemy_panel()
        self._draw_actor_panel(self.a1, self.actor_portraits[0], top=80)
        self._draw_actor_panel(self.a2, self.actor_portraits[1], top=220)
        self._draw_actor_panel(self.a3, self.actor_portraits[2], top=360)
        hint = self.font.render("Press ESC to quit", True, (180, 180, 180))
        self.screen.blit(hint, (40, 500))
        pass

    def _load_portrait(self, portrait_path, size=(96, 96)):
        surface = pygame.Surface(size)
        surface.fill((60, 60, 60))
        if portrait_path and os.path.exists(portrait_path):
            try:
                image = pygame.image.load(portrait_path)
                surface = pygame.transform.smoothscale(image, size)
            except pygame.error:
                # Keep fallback surface if the image fails to load.
                pass
        pygame.draw.rect(surface, (10, 10, 10), surface.get_rect(), 2)
        return surface.convert_alpha()

    def _draw_enemy_panel(self):
        portrait = self.enemy_portrait
        portrait_rect = portrait.get_rect()
        portrait_rect.topright = (600, 60)
        self.screen.blit(portrait, portrait_rect)
        text_surface = self.font.render(
            f"Enemy HP: {self.enemy.health.current}", True, (255, 255, 255)
        )
        text_rect = text_surface.get_rect()
        text_rect.midtop = (portrait_rect.centerx, portrait_rect.bottom + 12)
        self.screen.blit(text_surface, text_rect)

    def _draw_actor_panel(self, actor, portrait, *, top):
        portrait_rect = portrait.get_rect()
        portrait_rect.topleft = (40, top)
        self.screen.blit(portrait, portrait_rect)
        info_x = portrait_rect.right + 20
        stats = [
            f"{actor.name}",
            f"HP: {actor.health.current}/{actor.health.max}",
            f"MP: {actor.mana.current}/{actor.mana.max}",
        ]
        y = portrait_rect.top
        for line in stats:
            surf = self.font.render(line, True, (255, 255, 255))
            self.screen.blit(surf, (info_x, y))
            y += 32
    
def run_combat_ui():
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    font = pygame.font.Font("assets/Orbitron-VariableFont_wght.ttf", 24)
    scene = CombatScene(screen, font)
    clock = pygame.time.Clock()
    running = True
    while running:
        dt = clock.tick(60) / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
        scene.update(dt)
        scene.draw()
        pygame.display.flip()
    pygame.quit()


# def run_shop_ui():
#     import pygame
#     import item

#     print("Mode: Shop UI | Python:", sys.executable)

#     pygame.init()
#     WIDTH, HEIGHT = 640, 408
#     screen = pygame.display.set_mode((WIDTH, HEIGHT))
#     pygame.display.set_caption("Item Shop")

#     shop = item.Item("Shop", 1, 1)
#     money = 10

#     font_path = "assets/Orbitron-VariableFont_wght.ttf"
#     font_size = 32

#     font = pygame.font.Font(font_path, font_size)

#     button_rect = pygame.Rect(250, 300, 140, 50)

#     running = True
#     while running:
#         for event in pygame.event.get():
#             if event.type == pygame.QUIT:
#                 running = False
#             elif event.type == pygame.MOUSEBUTTONDOWN:
#                 if button_rect.collidepoint(event.pos):
#                     if money >= shop.price:
#                         money -= shop.price
#                         money = math.ceil(money * 100) / 100
#                         shop.purchase()
#                     else:
#                         print("Not Enough Gold!")

#         screen.fill((30, 30, 30))

#         # Draw item info
#         item_text = font.render(
#             f"Item: {shop.name} - Price: {shop.price} - Stat: {shop.stat}",
#             True,
#             (255, 255, 255),
#         )
#         screen.blit(item_text, (50, 50))

#         # Draw player's gold
#         gold_text = font.render(f"Gold: {money}", True, (255, 215, 0))
#         screen.blit(gold_text, (50, 100))

#         # Draw purchase button
#         pygame.draw.rect(screen, (70, 130, 180), button_rect)
#         btn_text = font.render("Purchase", True, (255, 255, 255))
#         screen.blit(btn_text, (button_rect.x + 20, button_rect.y + 10))

#         pygame.display.flip()

#     pygame.quit()


def run_combat_demo():
    """Headless demo: simulate combat ticks and print events."""
    from core.stats import Stats, Health, Mana
    from core.attack import AttackProfile, AttackState
    from core.combat import CombatSystem, TickController

    print("Mode: Combat Demo | Python:", sys.executable)

    class LoggingCombat(CombatSystem):
        def basic_attack(self, attacker, defender) -> int:
            dmg = super().basic_attack(attacker, defender)
            print(f"{attacker.name} hits enemy for {dmg} | Enemy HP: {defender.health.current}")
            return dmg

    # Setup demo combatants
    a1 = Actor("A1", cd=0.2, atk=5)
    a2 = Actor("A2", cd=0.3, atk=4)
    enemy = Enemy(hp=18, defense=2)
    cs = LoggingCombat([a1, a2], enemy)

    tc = TickController(0.2)
    print("Starting combat...")

    # Simulate 30 updates of 0.1s (~3s), stop early if enemy dies
    for i in range(30):
        if enemy.health.is_dead():
            print("Enemy defeated!\n")
            break
        tc.update(0.1, cs.on_tick)

    print("Final state:")
    print(a1)
    print(a2)
    print(enemy)


if __name__ == "__main__":
    args = [a.lower() for a in sys.argv[1:]]
    if "demo" in args:
        run_combat_demo()
    else:
        run_combat_ui()
