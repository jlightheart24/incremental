import sys
import pygame
from core.entities import Actor, Enemy
from core.scene import BattleScene
    
def run_combat_ui():
    pygame.init()
    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    font = pygame.font.Font("assets/Orbitron-VariableFont_wght.ttf", 24)
    scene = BattleScene(font)
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
                elif event.key == pygame.K_1:
                    scene.cycle_actor_spell(0)
                elif event.key == pygame.K_2:
                    scene.cycle_actor_spell(1)
                elif event.key == pygame.K_3:
                    scene.cycle_actor_spell(2)
        scene.update(dt)
        scene.draw(screen)
        pygame.display.flip()
    pygame.quit()

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
