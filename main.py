import sys
import math
import pygame
from core.entities import Actor, Enemy
from core.combat import CombatSystem, TickController

class CombatScene:
    def __init__(self, screen, font):
        self.screen = screen
        self.font = font
        self.a1 = Actor("A1", cd=0.2, atk=5)
        self.a2 = Actor("A2", cd=0.3, atk=4)
        self.enemy = Enemy(hp=18, defense=2)
        self.cs = CombatSystem([self.a1, self.a2], self.enemy)
        self.tc = TickController(0.2)
        pass
    
    def update(self, dt):
        if not self.enemy.health.is_dead():
            self.tc.update(dt, self.cs.on_tick)
        pass
    
    def draw(self):
        self.screen.fill((20,20,20))
        lines = [
            f"Enemy HP: {self.enemy.health.current}",
            f"{self.a1.name} HP: {self.a1.health.current} MP: {self.a1.mana.current}",
            f"{self.a2.name} HP: {self.a2.health.current} MP: {self.a2.mana.current}",
            "Press ESC to quit",
        ]
        y = 60
        for line in lines:
            surf = self.font.render(line, True, (255,255,255))
            self.screen.blit(surf, (40, y))
            y+=40
        pass
    
def run_combat_ui():
    pygame.init()
    screen = pygame.display.set_mode((640, 480))
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
