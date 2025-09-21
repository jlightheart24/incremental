import os
import random

import pygame

from core.combat import CombatSystem, TickController
from core.encounters import DEFAULT_ENCOUNTER_POOLS, EncounterPool
from core.entities import Actor
from core.inventory import Inventory
from core.items import get_item
from core.scenes.scene import Scene
from core.spells import spell_ids
from core.ui.actionbar import ActionBar
from core.scenes.inventory_scene import InventoryScene


class BattleScene(Scene):
    def __init__(self, font, *, change_scene):
        self.font = font
        self.change_scene = change_scene
        self.encounter_pool = EncounterPool(
            DEFAULT_ENCOUNTER_POOLS,
            default_pool="shadowlands",
        )
        self.enemy = self.encounter_pool.next_enemy()
        self.inventory = Inventory(
            keyblade_slots=3,
            armor_slots=10,
            accessory_slots=10,
        )
        self.actors = self._build_party()
        self.enemy_portrait = self._load_portrait(self.enemy.portrait_path)
        self.actor_portraits = [
            self._load_portrait(actor.portrait_path)
            for actor in self.actors
        ]
        self.cs = CombatSystem(self.actors, self.enemy)
        self.tc = TickController(0.2)
        self.available_spells = spell_ids()
        self._rng = random.Random()
        self._recent_drop_messages = []
        self._inventory_button_rect = pygame.Rect(0, 0, 0, 0)
        self._inventory_button_label = self.font.render(
            "Inventory",
            True,
            (0, 0, 0),
        )
        self.action_bar = ActionBar(
            font=self.font,
            on_attack=self._handle_action_attack,
            on_spell_assign=self._assign_spell_to_actor,
            get_party=lambda: self.actors,
            get_spells=self._spells_for_actor,
        )

    def _build_party(self):
        from core.party import DEFAULT_PARTY_TEMPLATES, build_party

        return build_party(
            DEFAULT_PARTY_TEMPLATES,
            inventory=self.inventory,
        )

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
        next_id = self.available_spells[
            (current_idx + 1) % len(self.available_spells)
        ]
        actor.set_spell(next_id)

    def _handle_action_attack(self) -> None:
        if self.enemy.health.is_dead():
            return
        for actor in self.actors:
            if actor.health.is_dead():
                continue
            self.cs.basic_attack(actor, self.enemy)
            break

    def _assign_spell_to_actor(self, actor_index: int, spell_id: str) -> None:
        if not (0 <= actor_index < len(self.actors)):
            return
        actor = self.actors[actor_index]
        actor.set_spell(spell_id)

    def _spells_for_actor(self, actor_index: int | None):
        return list(self.available_spells)

    def _spawn_enemy(self):
        self.enemy = self.encounter_pool.next_enemy()
        self.cs.enemy = self.enemy
        self.enemy_portrait = self._load_portrait(self.enemy.portrait_path)

    def _grant_enemy_drops(self, enemy) -> list:
        messages = []
        for drop in getattr(enemy, "drops", []):
            item_id = drop.get("item_id")
            if not item_id:
                continue
            chance = float(drop.get("chance", 1.0))
            if self._rng.random() > chance:
                continue
            item = get_item(item_id)
            try:
                self.inventory.add_item(item_id)
            except ValueError:
                messages.append(f"Inventory full: {item.name}")
                continue
            messages.append(f"Obtained {item.name}!")
        return messages

    def get_recent_drop_messages(self) -> list:
        return list(self._recent_drop_messages)

    def _load_portrait(self, portrait_path, size=(96, 96)):
        surface = pygame.Surface(size)
        surface.fill((60, 60, 60))
        if portrait_path and os.path.exists(portrait_path):
            try:
                image = pygame.image.load(portrait_path)
                surface = pygame.transform.smoothscale(image, size)
            except pygame.error:
                pass
        pygame.draw.rect(surface, (10, 10, 10), surface.get_rect(), 2)
        return surface.convert_alpha()

    def _draw_actor_panel(
        self,
        surface,
        actor: Actor,
        portrait: pygame.Surface,
        left: int,
        top: int,
    ) -> None:
        portrait_rect = portrait.get_rect()
        portrait_rect.topleft = (left, top)
        surface.blit(portrait, portrait_rect)
        info_x = portrait_rect.right + 28
        y = portrait_rect.top
        spell = actor.current_spell
        spell_name = spell.name if spell else "None"
        stats = [
            f"{actor.name}",
            f"HP: {actor.health.current}/{actor.health.max}",
            f"MP: {actor.mana.current}/{actor.mana.max}",
            f"Spell: {spell_name}",
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
        )
        surface.blit(portrait, portrait_rect)
        text_surface = self.font.render(
            f"Enemy HP: {self.enemy.health.current}", True, (255, 255, 255)
        )
        text_rect = text_surface.get_rect()
        text_rect.midright = (
            portrait_rect.left - 30,
            portrait_rect.centery,
        )
        surface.blit(text_surface, text_rect)

    def draw(self, surface):
        screen_rect = surface.get_rect()
        surface.fill((20, 20, 20))
        munny_text = self.font.render(
            f"Munny: {self.inventory.munny}",
            True,
            (250, 220, 120),
        )
        surface.blit(munny_text, (40, 40))
        self._draw_enemy_panel(surface, screen_rect)

        button_padding = 16
        btn_w = self._inventory_button_label.get_width() + button_padding * 2
        btn_h = self._inventory_button_label.get_height() + button_padding
        self._inventory_button_rect = pygame.Rect(0, 0, btn_w, btn_h)
        self._inventory_button_rect.topright = (screen_rect.right - 40, 40)
        pygame.draw.rect(surface, (200, 200, 200), self._inventory_button_rect)
        pygame.draw.rect(surface, (50, 50, 50), self._inventory_button_rect, 2)
        label_rect = self._inventory_button_label.get_rect(
            center=self._inventory_button_rect.center
        )
        surface.blit(self._inventory_button_label, label_rect)

        portrait_height = self.actor_portraits[0].get_height()
        spacing = 70
        total_height = (
            len(self.actor_portraits) * portrait_height
            + (len(self.actor_portraits) - 1) * spacing
        )
        start_y = screen_rect.centery - total_height // 2

        for index, (actor, portrait) in enumerate(
            zip(self.actors, self.actor_portraits)
        ):
            top = start_y + index * (portrait_height + spacing)
            self._draw_actor_panel(
                surface,
                actor,
                portrait,
                left=screen_rect.left + 60,
                top=top,
            )

        max_button_count = max(
            2,
            len(self.actors),
            len(self.available_spells) if self.available_spells else 0,
        )
        bar_height = self.action_bar.estimate_height(max_button_count)
        bar_margin = 40
        bar_rect = pygame.Rect(
            screen_rect.left + bar_margin,
            screen_rect.bottom - bar_height - bar_margin,
            self.action_bar.width(),
            bar_height,
        )
        self.action_bar.draw(surface, bar_rect)

        hint = self.font.render(
            "ESC: Quit | 1-3: Cycle Spells",
            True,
            (180, 180, 180),
        )
        hint_rect = hint.get_rect()
        hint_rect.midbottom = (
            screen_rect.centerx,
            screen_rect.bottom - 40,
        )
        surface.blit(hint, hint_rect)

    def handle_event(self, event):
        if self.action_bar.handle_event(event):
            return
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
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
            defeated_enemy = self.enemy
            reward = getattr(defeated_enemy, "xp_reward", 0)
            for actor in self.actors:
                actor.gain_xp(reward)
            messages = self._grant_enemy_drops(defeated_enemy)
            munny_reward = getattr(defeated_enemy, "munny_reward", 0)
            munny_reward = max(0, int(munny_reward or 0))
            if munny_reward:
                self.inventory.add_munny(munny_reward)
                messages.append(f"Collected {munny_reward} munny.")
            self._recent_drop_messages = messages
            self._spawn_enemy()
