import os
import random
from typing import Iterable

import pygame

from core.combat import CombatSystem, TickController
from core.encounters import DEFAULT_ENCOUNTER_POOLS, EncounterPool
from core.entities import Actor, Enemy
from core.inventory import Inventory
from core.items import get_item
from core.locations import DEFAULT_LOCATION_ID, get_location
from core.scenes.scene import Manager, Scene
from core.spells import spell_ids
from core.render import RenderSystem
from core.ui.actionbar import ActionBar
from core.ui.battle_hud import BattleHUD
from core.materials import material_name
from core.scenes.inventory_scene import InventoryScene
from core.scenes.board import HexBoard
from core.scenes.synthesis_scene import SynthesisScene


class BattleScene(Scene):
    def __init__(
        self,
        font,
        *,
        controller: Manager.Controller,
        location_id: str | None = None,
        inventory: Inventory | None = None,
        actors: Iterable[Actor] | None = None,
    ):
        self.font = font
        self.controller = controller
        selected_location_id = location_id or DEFAULT_LOCATION_ID
        try:
            location = get_location(selected_location_id)
        except KeyError:
            location = get_location(DEFAULT_LOCATION_ID)
            selected_location_id = DEFAULT_LOCATION_ID
        self.location_id = selected_location_id
        self.location_name = location.title
        self.location_subtitle = location.subtitle
        self.render_system = RenderSystem()
        self.render_system.set_background_color((20, 20, 20))
        self.render_system.set_board_factory(HexBoard)
        self.render_system.set_background_image(location.background_image)
        self.encounter_pool = EncounterPool(
            DEFAULT_ENCOUNTER_POOLS,
            default_pool=location.encounter_pool,
        )
        if inventory is not None:
            self.inventory = inventory
        else:
            self.inventory = Inventory(
                keyblade_slots=3,
                armor_slots=10,
                accessory_slots=10,
            )
        if actors is not None:
            self.actors = list(actors)
        else:
            self.actors = self._build_party()
        for actor in self.actors:
            actor.attack_state.reset()
            actor.health.clamp()
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
        self.action_bar = ActionBar(
            font=self.font,
            on_attack=self._handle_action_attack,
            on_spell_assign=self._assign_spell_to_actor,
            get_party=lambda: self.actors,
            get_spells=self._spells_for_actor,
        )
        self.hud = BattleHUD(self.font, action_bar=self.action_bar)


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

    def _build_party(self):
        from core.party import DEFAULT_PARTY_TEMPLATES, build_party

        return build_party(
            DEFAULT_PARTY_TEMPLATES,
            inventory=self.inventory,
        )

    def _open_map_scene(self) -> None:
        from core.scenes.map_scene import MapScene

        map_scene = MapScene(
            self.font,
            controller=self.controller,
            current_location_id=self.location_id,
            on_select=self._handle_location_selected,
        )
        self.controller.push(map_scene)

    def _handle_location_selected(self, location_id: str) -> None:
        if location_id == self.location_id:
            self.controller.pop()
            return
        new_scene = BattleScene(
            self.font,
            controller=self.controller,
            location_id=location_id,
            inventory=self.inventory,
            actors=self.actors,
        )
        self.controller.replace(new_scene)

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
            chance = float(drop.get("chance", 1.0))
            if self._rng.random() > chance:
                continue
            item_id = drop.get("item_id")
            material_id = drop.get("material_id")
            amount = int(drop.get("amount", 1) or 1)
            if item_id:
                item = get_item(item_id)
                try:
                    self.inventory.add_item(item_id)
                except ValueError:
                    messages.append(f"Inventory full: {item.name}")
                    continue
                messages.append(f"Obtained {item.name}!")
            elif material_id:
                try:
                    self.inventory.add_material(material_id, amount)
                except ValueError:
                    continue
                name = material_name(material_id)
                suffix = f" x{amount}" if amount > 1 else ""
                messages.append(f"Obtained {name}{suffix}!")
        return messages

    def get_recent_drop_messages(self) -> list:
        return list(self._recent_drop_messages)

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

    def draw(self, surface):
        screen_rect = surface.get_rect()
        board_rebuilt = self.render_system.ensure_board(screen_rect)
        board_obj = self.render_system.board
        self.board = board_obj if isinstance(board_obj, HexBoard) else None
        if board_rebuilt and self.board is not None:
            for enemy in self.enemies:
                self.enemy_positions[enemy] = None
        if self.board is not None:
            self._place_enemies_on_board()
        self.render_system.draw(surface)
        self.hud.draw(
            surface,
            munny=self.inventory.munny,
            actors=self.actors,
            portraits=self.actor_portraits,
            ko_timers=self._ko_timers,
            available_spells=len(self.available_spells),
            location_name=self.location_name,
            location_subtitle=self.location_subtitle,
        )

    def handle_event(self, event) -> bool:
        if self.action_bar.handle_event(event):
            return True
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return False
            elif event.key in (pygame.K_1, pygame.K_2, pygame.K_3):
                idx = event.key - pygame.K_1
                self.cycle_actor_spell(idx)
                return True
            elif event.key == pygame.K_m:
                self._open_map_scene()
                return True
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.hud.inventory_button_rect.collidepoint(event.pos):
                inventory_scene = InventoryScene(
                    self.font,
                    controller=self.controller,
                    inventory=self.inventory,
                    actors=self.actors,
                    battle_scene=self,
                )
                self.controller.push(inventory_scene)
                return True
            if self.hud.synthesis_button_rect.collidepoint(event.pos):
                synthesis_scene = SynthesisScene(
                    self.font,
                    controller=self.controller,
                    inventory=self.inventory,
                )
                self.controller.push(synthesis_scene)
                return True
            if self.hud.map_button_rect.collidepoint(event.pos):
                self._open_map_scene()
                return True
        return False

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
