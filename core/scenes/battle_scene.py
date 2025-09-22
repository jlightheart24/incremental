import os
import random

import pygame

from core.combat import CombatSystem, TickController
from core.encounters import DEFAULT_ENCOUNTER_POOLS, EncounterPool
from core.entities import Actor, Enemy
from core.inventory import Inventory
from core.items import get_item
from core.scenes.scene import Scene
from core.spells import spell_ids
from core.ui.actionbar import ActionBar
from core.scenes.inventory_scene import InventoryScene
from core.scenes.board import HexBoard


class BattleScene(Scene):
    def __init__(self, font, *, change_scene):
        self.font = font
        self.change_scene = change_scene
        self.encounter_pool = EncounterPool(
            DEFAULT_ENCOUNTER_POOLS,
            default_pool="shadowlands",
        )
        self.inventory = Inventory(
            keyblade_slots=3,
            armor_slots=10,
            accessory_slots=10,
        )
        self.actors = self._build_party()
        self.actor_positions: dict[Actor, tuple[int, int]] = {}
        self._assign_actor_slots()
        self.actor_portraits = [
            self._load_portrait(actor.portrait_path)
            for actor in self.actors
        ]
        self.enemies: list[Enemy] = []
        self.enemy_positions: dict[Enemy, tuple[int, int] | None] = {}
        self.board: HexBoard | None = None
        self._recent_drop_messages: list[str] = []
        self._rng = random.Random()
        self.available_spells = spell_ids()
        self._ko_timers: dict[Actor, float] = {}
        self._ko_mana: dict[Actor, int] = {}
        self._dead_portraits: dict[Actor, pygame.Surface] = {}
        self._spawn_wave()
        current_enemy = self._current_enemy()
        if current_enemy is None:
            raise RuntimeError("Encounter pool did not provide any enemies")
        self.cs = CombatSystem(
            self.actors,
            current_enemy,
            select_actor_target=self._closest_enemy_for,
            select_enemy_target=self._closest_actor_for,
        )
        original_basic_attack = self.cs.basic_attack

        def wrapped_basic_attack(attacker, defender):
            damage = original_basic_attack(attacker, defender)
            self._handle_post_attack(attacker, defender)
            return damage

        self.cs.basic_attack = wrapped_basic_attack
        self.tc = TickController(0.2)
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


    @staticmethod
    def _hex_distance(a: tuple[int, int], b: tuple[int, int]) -> int:
        aq, ar = a
        bq, br = b
        dq = bq - aq
        dr = br - ar
        return (abs(dq) + abs(dq + dr) + abs(dr)) // 2

    def _assign_actor_slots(self) -> None:
        slot_spacing = 2
        start_r = 1
        for offset, actor in enumerate(self.actors):
            slot_r = start_r + offset * slot_spacing
            self.actor_positions[actor] = (-1, slot_r)

    def _closest_enemy_for(self, actor: Actor) -> Enemy | None:
        actor_coord = self.actor_positions.get(actor)
        if not actor_coord:
            return None

        closest_enemy: Enemy | None = None
        closest_dist: int | None = None

        for enemy in self.enemies:
            if enemy.health.is_dead():
                continue
            enemy_coord = self.enemy_positions.get(enemy)
            if not enemy_coord:
                continue
            distance = self._hex_distance(actor_coord, enemy_coord)
            if closest_dist is None or distance < closest_dist:
                closest_dist = distance
                closest_enemy = enemy

        return closest_enemy

    def _closest_actor_for(self, enemy: Enemy) -> Actor | None:
        enemy_coord = self.enemy_positions.get(enemy)
        if not enemy_coord:
            return None

        closest_actor: Actor | None = None
        closest_dist: int | None = None

        for actor, coord in self.actor_positions.items():
            if actor.health.is_dead():
                continue
            distance = self._hex_distance(coord, enemy_coord)
            if closest_dist is None or distance < closest_dist:
                closest_dist = distance
                closest_actor = actor

        return closest_actor

    def _handle_post_attack(self, attacker, defender) -> None:
        if isinstance(defender, Actor) and defender.health.is_dead():
            if defender not in self._ko_timers:
                self._ko_timers[defender] = 5.0
                if hasattr(defender, "mana"):
                    self._ko_mana[defender] = defender.mana.current
                defender.attack_state.reset()

    def _update_ko_timers(self, dt: float) -> None:
        if not self._ko_timers:
            return
        finished: list[Actor] = []
        for actor, remaining in list(self._ko_timers.items()):
            remaining -= dt
            if remaining <= 0:
                finished.append(actor)
            else:
                self._ko_timers[actor] = remaining
        for actor in finished:
            self._revive_actor(actor)
            self._ko_timers.pop(actor, None)

    def _revive_actor(self, actor: Actor) -> None:
        actor.health.current = actor.health.max
        actor.health.clamp()
        if hasattr(actor, "mana"):
            stored_mana = self._ko_mana.pop(actor, None)
            if stored_mana is not None:
                actor.mana.current = stored_mana
            actor.mana.clamp()
        actor.attack_state.reset()

    def _dead_portrait_for(self, actor: Actor, base_surface: pygame.Surface) -> pygame.Surface:
        dead_surface = self._dead_portraits.get(actor)
        if dead_surface is None:
            dead_surface = pygame.Surface(base_surface.get_size(), pygame.SRCALPHA)
            dead_surface.fill((100, 100, 100))
            pygame.draw.rect(dead_surface, (40, 40, 40), dead_surface.get_rect(), 2)
            self._dead_portraits[actor] = dead_surface
        return dead_surface
    
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
        for actor in self.actors:
            if actor.health.is_dead():
                continue
            enemy = self._closest_enemy_for(actor)
            if enemy is None:
                continue
            self.cs.basic_attack(actor, enemy)
            break

    def _assign_spell_to_actor(self, actor_index: int, spell_id: str) -> None:
        if not (0 <= actor_index < len(self.actors)):
            return
        actor = self.actors[actor_index]
        actor.set_spell(spell_id)

    def _spells_for_actor(self, actor_index: int | None):
        return list(self.available_spells)

    def _spawn_wave(self, *, count: int | None = None) -> None:
        self._clear_board_enemies()
        self.enemies.clear()
        self.enemy_positions.clear()
        wave_size = count if count is not None else self._rng.randint(2, 4)
        wave_size = max(1, min(wave_size, self.board.cols * self.board.rows if self.board else wave_size))
        for _ in range(wave_size):
            enemy = self.encounter_pool.next_enemy()
            self.enemies.append(enemy)
            self.enemy_positions[enemy] = None
        self._recent_drop_messages = []
        self._sync_combat_target()
        if self.board:
            self._place_enemies_on_board()

    def _current_enemy(self) -> Enemy | None:
        for enemy in self.enemies:
            if not enemy.health.is_dead():
                return enemy
        return None

    def _sync_combat_target(self) -> None:
        current = self._current_enemy()
        if current is None:
            return
        if hasattr(self, "cs"):
            self.cs.enemy = current

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

    def _ensure_board(self, screen_rect: pygame.Rect) -> None:
        if self.board is None or self.board.screen_rect.size != screen_rect.size:
            self.board = HexBoard(screen_rect)
            for enemy in self.enemies:
                self.enemy_positions[enemy] = None
        self._place_enemies_on_board()

    def _clear_board_enemies(self) -> None:
        if not self.board:
            return
        for q, r in self.board.tiles():
            if self.board.occupant_at(q, r) is not None:
                try:
                    self.board.remove(q, r)
                except ValueError:
                    pass

    def _place_enemies_on_board(self) -> None:
        if not self.board:
            return
        # Remove any stale occupants from previous waves.
        for q, r in self.board.tiles():
            occupant = self.board.occupant_at(q, r)
            if occupant is None:
                continue
            if occupant not in self.enemies:
                try:
                    self.board.remove(q, r)
                except ValueError:
                    pass
        available = [
            (q, r)
            for q, r in self.board.tiles()
            if self.board.occupant_at(q, r) is None
        ]
        self._rng.shuffle(available)
        for enemy in self.enemies:
            coord = self.enemy_positions.get(enemy)
            if coord and self.board.occupant_at(*coord) is enemy:
                continue
            if not available:
                self.enemy_positions[enemy] = None
                continue
            coord = available.pop()
            try:
                self.board.place(enemy, *coord)
            except ValueError:
                self.enemy_positions[enemy] = None
                continue
            self.enemy_positions[enemy] = coord

    def _handle_enemy_defeated(self, defeated_enemy: Enemy) -> None:
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

        coord = self.enemy_positions.pop(defeated_enemy, None)
        if self.board and coord:
            try:
                self.board.remove(*coord)
            except ValueError:
                pass
        try:
            self.enemies.remove(defeated_enemy)
        except ValueError:
            pass

        next_enemy = self._current_enemy()
        if next_enemy is None:
            self._spawn_wave()
            next_enemy = self._current_enemy()
        if next_enemy is not None:
            self.cs.enemy = next_enemy
            if self.board:
                self._place_enemies_on_board()

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
        ko_remaining = self._ko_timers.get(actor)
        portrait_surface = portrait
        if actor.health.is_dead() or ko_remaining is not None:
            portrait_surface = self._dead_portrait_for(actor, portrait)
        surface.blit(portrait_surface, portrait_rect)
        if ko_remaining is not None:
            countdown = max(0.0, ko_remaining)
            timer_label = self.font.render(f"{countdown:.1f}s", True, (255, 255, 255))
            timer_rect = timer_label.get_rect(center=portrait_rect.center)
            surface.blit(timer_label, timer_rect)
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

    def draw(self, surface):
        screen_rect = surface.get_rect()
        self._ensure_board(screen_rect)
        surface.fill((20, 20, 20))
        munny_text = self.font.render(
            f"Munny: {self.inventory.munny}",
            True,
            (250, 220, 120),
        )
        surface.blit(munny_text, (40, 40))
        if self.board:
            self.board.draw(surface)

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
        self._update_ko_timers(dt)
        current_enemy = self._current_enemy()
        if current_enemy is None:
            self._spawn_wave()
            current_enemy = self._current_enemy()
            if current_enemy is None:
                return
        self.cs.enemy = current_enemy
        self.tc.update(dt, self.cs.on_tick)
        if current_enemy.health.is_dead():
            self._handle_enemy_defeated(current_enemy)
