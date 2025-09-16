import pygame
import os
from core.combat import CombatSystem, TickController
from core.entities import Actor, Enemy
from core.encounters import EncounterPool, DEFAULT_ENCOUNTER_POOLS
from core.party import DEFAULT_PARTY_TEMPLATES, build_party
from core.spells import spell_ids
from core.inventory import Inventory

class Scene:
    def update(self, dt):
        pass

    def handle_event(self, event):
        pass

    def draw(self, surface):
        pass
    
class Manager:
    def __init__(self, initial_scene: Scene):
        self.current_scene = initial_scene

    def set_scene(self, scene: Scene):
        self.current_scene = scene

    def update(self, dt):
        self.current_scene.update(dt)

    def handle_event(self, event):
        self.current_scene.handle_event(event)

    def draw(self, surface):
        self.current_scene.draw(surface)

class BattleScene(Scene):
    def __init__(self, font, *, change_scene):
        self.font = font
        self.change_scene = change_scene
        self.encounter_pool = EncounterPool(
            DEFAULT_ENCOUNTER_POOLS,
            default_pool="shadowlands",
        )
        self.enemy = self.encounter_pool.next_enemy()
        self.inventory = Inventory()
        self.actors = build_party(DEFAULT_PARTY_TEMPLATES, inventory=self.inventory)
        self.enemy_portrait = self._load_portrait(self.enemy.portrait_path)
        self.actor_portraits = [self._load_portrait(actor.portrait_path) for actor in self.actors]
        self.cs = CombatSystem(self.actors, self.enemy)
        self.tc = TickController(0.2)
        self.available_spells = spell_ids()
        self._inventory_button_rect = pygame.Rect(0, 0, 0, 0)
        self._inventory_button_label = self.font.render("Inventory", True, (0, 0, 0))
        

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
    
    def _spawn_enemy(self):
        self.enemy = self.encounter_pool.next_enemy()
        self.cs.enemy = self.enemy
        self.enemy_portrait = self._load_portrait(self.enemy.portrait_path)
        

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

    def _draw_actor_panel(self, surface, actor: Actor, portrait: pygame.Surface, left: int, top: int) -> None:
        portrait_rect = portrait.get_rect()
        portrait_rect.topleft = (left, top)
        surface.blit(portrait, portrait_rect)
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
            surface.blit(surf, (info_x, y))
            y += 28

    def _draw_enemy_panel(self, surface, screen_rect: pygame.Rect) -> None:
        portrait = self.enemy_portrait
        portrait_rect = portrait.get_rect()
        portrait_rect.center = (
            screen_rect.right - portrait_rect.width // 2 - 60,
            screen_rect.centery,
        )  # Controls the enemy portrait anchor (right/center).
        surface.blit(portrait, portrait_rect)
        text_surface = self.font.render(
            f"Enemy HP: {self.enemy.health.current}", True, (255, 255, 255)
        )
        text_rect = text_surface.get_rect()
        text_rect.midright = (
            portrait_rect.left - 30,
            portrait_rect.centery,
        )  # Move this to change where the enemy HP text sits.
        surface.blit(text_surface, text_rect)

    def draw(self, surface):
        screen_rect = surface.get_rect()
        surface.fill((20, 20, 20))
        self._draw_enemy_panel(surface, screen_rect)

        button_padding = 16
        btn_w = self._inventory_button_label.get_width() + button_padding * 2
        btn_h = self._inventory_button_label.get_height() + button_padding
        self._inventory_button_rect = pygame.Rect(0, 0, btn_w, btn_h)
        self._inventory_button_rect.topright = (screen_rect.right - 40, 40)
        pygame.draw.rect(surface, (200, 200, 200), self._inventory_button_rect)
        pygame.draw.rect(surface, (50, 50, 50), self._inventory_button_rect, 2)
        label_rect = self._inventory_button_label.get_rect(center=self._inventory_button_rect.center)
        surface.blit(self._inventory_button_label, label_rect)

        portrait_height = self.actor_portraits[0].get_height()
        spacing = 70  # Control vertical spacing between actor cards.
        total_height = len(self.actor_portraits) * portrait_height + (len(self.actor_portraits) - 1) * spacing
        start_y = screen_rect.centery - total_height // 2

        for index, (actor, portrait) in enumerate(zip(self.actors, self.actor_portraits)):
            top = start_y + index * (portrait_height + spacing)
            self._draw_actor_panel(
                surface,
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
        surface.blit(hint, hint_rect)

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                # You might want to signal scene change or quit here
                pass
            elif event.key in (pygame.K_1, pygame.K_2, pygame.K_3):
                idx = event.key - pygame.K_1
                self.cycle_actor_spell(idx)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self._inventory_button_rect.collidepoint(event.pos):
                inventory_scene = InventoryScene(
                    self.font,
                    change_scene=self.change_scene,
                    inventory=self.inventory,
                    actors=self.actors,
                    battle_scene=self,
                )
                self.change_scene(inventory_scene)


    def update(self, dt):
        self.tc.update(dt, self.cs.on_tick)
        if self.enemy.health.is_dead():
            reward = getattr(self.enemy, "xp_reward", 0)  # Configure per-enemy in encounter pools.
            for actor in self.actors:
                actor.gain_xp(reward)
            self._spawn_enemy()


class InventoryScene(Scene):
    def __init__(self, font, *, change_scene, inventory: Inventory, actors, battle_scene):
        self.font = font
        self.change_scene = change_scene
        self.inventory = inventory
        self.actors = actors
        self.battle_scene = battle_scene
        self._back_button_rect = pygame.Rect(0, 0, 0, 0)
        self._back_button_label = self.font.render("Back to Battle", True, (0, 0, 0))

    def draw(self, surface):
        surface.fill((15, 15, 30))
        screen_rect = surface.get_rect()

        button_padding = 16
        btn_w = self._back_button_label.get_width() + button_padding * 2
        btn_h = self._back_button_label.get_height() + button_padding
        self._back_button_rect = pygame.Rect(40, 40, btn_w, btn_h)
        pygame.draw.rect(surface, (200, 200, 200), self._back_button_rect)
        pygame.draw.rect(surface, (50, 50, 50), self._back_button_rect, 2)
        label_rect = self._back_button_label.get_rect(center=self._back_button_rect.center)
        surface.blit(self._back_button_label, label_rect)

        top = self._back_button_rect.bottom + 40
        for actor in self.actors:
            lines = [f"{actor.name} Equipment:"]
            equipment = getattr(actor, "equipment", {})
            if not equipment:
                lines.append("  (None equipped)")
            else:
                for slot, (item_id, item) in equipment.items():
                    lines.append(f"  {slot.title()}: {item.name} ({item_id})")
            for line in lines:
                text = self.font.render(line, True, (230, 230, 230))
                surface.blit(text, (60, top))
                top += text.get_height() + 6
            top += 20

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self._back_button_rect.collidepoint(event.pos) and self.battle_scene is not None:
                self.change_scene(self.battle_scene)

    def update(self, dt):
        pass
            
class MainMenu(Scene):
    def __init__(self, font, *, change_scene):
        self.font = font
        self.change_scene = change_scene
        
    def draw(self, surface):
        screen_rect = surface.get_rect()
        surface.fill((30, 30, 30))
        title = self.font.render("Main Menu - Press Enter to Start Battle", True, (255, 255, 255))
        title_rect = title.get_rect(center = screen_rect.center)
        surface.blit(title, title_rect)
        
    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                self.change_scene(BattleScene(self.font, change_scene=self.change_scene))
