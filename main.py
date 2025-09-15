import sys
import os
import pygame
from core.entities import Actor, Enemy
from core.combat import CombatSystem, TickController
from core.encounters import EncounterPool, DEFAULT_ENCOUNTER_POOLS
from core.party import DEFAULT_PARTY_TEMPLATES, build_party
from core.spells import spell_ids

class CombatScene:
    def __init__(self, screen, font):
        self.screen = screen
        self.font = font
        # Party setup lives in core.party; swap templates there or inject your own here.
        self.party_templates = DEFAULT_PARTY_TEMPLATES
        self.actors = build_party(self.party_templates)
        self.available_spells = spell_ids()
        # Encounter selection: swap the default pool or inject a custom EncounterPool.
        self.encounter_pool = EncounterPool(
            DEFAULT_ENCOUNTER_POOLS,
            default_pool="shadowlands",
        )
        self.enemy = self.encounter_pool.next_enemy()
        self.cs = CombatSystem(self.actors, self.enemy)
        self.tc = TickController(0.2)
        self.actor_portraits = [self._load_portrait(actor.portrait_path) for actor in self.actors]
        self.enemy_portrait = self._load_portrait(self.enemy.portrait_path)
        pass

    def _spawn_enemy(self):
        self.enemy = self.encounter_pool.next_enemy()
        self.enemy_portrait = self._load_portrait(self.enemy.portrait_path)
        self.cs.enemy = self.enemy
        pass

    def cycle_actor_spell(self, actor_index: int) -> None:
        if not self.available_spells:
            return
        if not (0 <= actor_index < len(self.actors)):
            return
        actor = self.actors[actor_index]
        current_id = actor.spell_id or self.available_spells[0]
        try:
            current_idx = self.available_spells.index(current_id)
        except ValueError:
            current_idx = -1
        next_id = self.available_spells[(current_idx + 1) % len(self.available_spells)]
        actor.set_spell(next_id)

    def update(self, dt):
        self.tc.update(dt, self.cs.on_tick)
        if self.enemy.health.is_dead():
            reward = getattr(self.enemy, "xp_reward", 0)  # Configure per-enemy in encounter pools.
            for actor in self.actors:
                actor.gain_xp(reward)
            self._spawn_enemy()
        pass

    def draw(self):
        screen_rect = self.screen.get_rect()
        self.screen.fill((20, 20, 20))
        self._draw_enemy_panel(screen_rect=screen_rect)

        portrait_height = self.actor_portraits[0].get_height()
        spacing = 70  # Control vertical spacing between actor cards.
        total_height = len(self.actor_portraits) * portrait_height + (len(self.actor_portraits) - 1) * spacing
        start_y = screen_rect.centery - total_height // 2

        for index, (actor, portrait) in enumerate(zip(self.actors, self.actor_portraits)):
            top = start_y + index * (portrait_height + spacing)
            self._draw_actor_panel(
                actor,
                portrait,
                left=screen_rect.left + 60,  # Horizontal anchor for actor portraits.
                top=top,
            )

        hint = self.font.render(
            "ESC: Quit | 1-3: Cycle Spells",
            True,
            (180, 180, 180),
        )
        hint_rect = hint.get_rect()
        hint_rect.midbottom = (
            screen_rect.centerx,
            screen_rect.bottom - 40,
        )  # Adjust to move the on-screen hint.
        self.screen.blit(hint, hint_rect)
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

    def _draw_enemy_panel(self, screen_rect):
        portrait = self.enemy_portrait
        portrait_rect = portrait.get_rect()
        portrait_rect.center = (
            screen_rect.right - portrait_rect.width // 2 - 60,
            screen_rect.centery,
        )  # Controls the enemy portrait anchor (right/center).
        self.screen.blit(portrait, portrait_rect)
        text_surface = self.font.render(
            f"Enemy HP: {self.enemy.health.current}", True, (255, 255, 255)
        )
        text_rect = text_surface.get_rect()
        text_rect.midright = (
            portrait_rect.left - 30,
            portrait_rect.centery,
        )  # Move this to change where the enemy HP text sits.
        self.screen.blit(text_surface, text_rect)

    def _draw_actor_panel(self, actor, portrait, *, left, top):
        portrait_rect = portrait.get_rect()
        portrait_rect.topleft = (left, top)
        self.screen.blit(portrait, portrait_rect)
        info_x = (
            portrait_rect.right + 28
        )  # Adjust to move the actor stat text relative to the portrait.
        y = portrait_rect.top
        stats = [
            f"{actor.name}",
            f"HP: {actor.health.current}/{actor.health.max}",
            f"MP: {actor.mana.current}/{actor.mana.max}",
            f"Spell: {actor.current_spell.name if actor.current_spell else 'None'}",
            f"Level: {actor.level}",
            f"XP: {actor.xp}/{actor.xp_to_level}",
        ]
        for line in stats:
            surf = self.font.render(line, True, (255, 255, 255))
            self.screen.blit(surf, (info_x, y))
            y += 28
    
def run_combat_ui():
    pygame.init()
    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
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
                elif event.key == pygame.K_1:
                    scene.cycle_actor_spell(0)
                elif event.key == pygame.K_2:
                    scene.cycle_actor_spell(1)
                elif event.key == pygame.K_3:
                    scene.cycle_actor_spell(2)
        scene.update(dt)
        scene.draw()
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
