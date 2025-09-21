import os
import random
from collections import OrderedDict

import pygame

from core.combat import CombatSystem, TickController
from core.encounters import DEFAULT_ENCOUNTER_POOLS, EncounterPool
from core.entities import Actor, Enemy
from core.inventory import Inventory
from core.items import get_item
from core.party import DEFAULT_PARTY_TEMPLATES, build_party
from core.spells import spell_ids
from core.ui.actionbar import ActionBar


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
        self.inventory = Inventory(
            keyblade_slots=3,
            armor_slots=10,
            accessory_slots=10,
        )
        self.actors = build_party(
            DEFAULT_PARTY_TEMPLATES,
            inventory=self.inventory,
        )
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
                # Keep fallback surface if the image fails to load.
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
        info_x = (
            portrait_rect.right + 28
        )  # Adjust to move the actor stat text relative to the portrait.
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
        spacing = 70  # Control vertical spacing between actor cards.
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
        )  # Adjust to move the on-screen hint.
        surface.blit(hint, hint_rect)

    def handle_event(self, event):
        if self.action_bar.handle_event(event):
            return
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
            defeated_enemy = self.enemy
            # Configure per-enemy rewards in encounter pools.
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


class InventoryScene(Scene):
    def __init__(
        self,
        font,
        *,
        change_scene,
        inventory: Inventory,
        actors,
        battle_scene,
    ):
        self.font = font
        self.change_scene = change_scene
        self.inventory = inventory
        self.actors = actors
        self.battle_scene = battle_scene
        self._back_button_rect = pygame.Rect(0, 0, 0, 0)
        self._back_button_label = self.font.render(
            "Back to Battle",
            True,
            (0, 0, 0),
        )
        self._selected_item_id: str | None = None
        self._selected_item_slot: str | None = None
        self._selected_slot: tuple[int, str] | None = None
        self._item_buttons = []
        self._slot_buttons = []

    def _draw_button(
        self,
        surface: pygame.Surface,
        rect: pygame.Rect,
        *,
        label: str,
        fill_color: tuple[int, int, int],
        border_color: tuple[int, int, int],
        text_color: tuple[int, int, int],
        highlight: bool = False,
        highlight_color: tuple[int, int, int] | None = None,
        payload_list: list | None = None,
        payload: dict | None = None,
    ) -> None:
        surface.fill(fill_color, rect)
        pygame.draw.rect(surface, border_color, rect, width=2)
        if highlight:
            pygame.draw.rect(
                surface,
                highlight_color or border_color,
                rect,
                width=3,
            )

        label_surf = self.font.render(label, True, text_color)
        label_rect = label_surf.get_rect()
        label_rect.midleft = (rect.left + 12, rect.centery)
        surface.blit(label_surf, label_rect)

        if payload_list is not None and payload is not None:
            payload_list.append({"rect": rect.copy(), "payload": payload})

    def draw(self, surface):
        surface.fill((15, 15, 30))
        screen_rect = surface.get_rect()
        self._slot_buttons = []
        self._item_buttons = []

        panel_left = 60
        panel_width = 220
        panel_padding = 12
        slot_height = 48
        slot_spacing = 8
        slot_bg = (45, 45, 70)
        slot_border = (90, 90, 140)

        button_padding = 16
        btn_w = self._back_button_label.get_width() + button_padding * 2
        btn_h = self._back_button_label.get_height() + button_padding
        self._back_button_rect = pygame.Rect(40, 40, btn_w, btn_h)
        pygame.draw.rect(surface, (200, 200, 200), self._back_button_rect)
        pygame.draw.rect(surface, (50, 50, 50), self._back_button_rect, 2)
        label_rect = self._back_button_label.get_rect(
            center=self._back_button_rect.center
        )
        surface.blit(self._back_button_label, label_rect)

        panel_top = self._back_button_rect.bottom + 40
        y = panel_top
        for idx, actor in enumerate(self.actors):
            name_surf = self.font.render(actor.name, True, (245, 245, 255))
            surface.blit(name_surf, (panel_left, y))
            y += name_surf.get_height() + panel_padding

            equipment = getattr(actor, "equipment", {})
            for slot in ("keyblade", "armor", "accessory"):
                slot_rect = pygame.Rect(
                    panel_left,
                    y,
                    panel_width,
                    slot_height,
                )
                item_name = "(Empty)"
                if slot in equipment:
                    equipped_id, equipped_item = equipment[slot]
                    item_name = f"{equipped_item.name} ({equipped_id})"
                slot_title = slot.title()
                label = f"{slot_title}: {item_name}"
                is_slot_selected = self._selected_slot == (idx, slot)

                self._draw_button(
                    surface,
                    slot_rect,
                    label=label,
                    fill_color=slot_bg,
                    border_color=slot_border,
                    text_color=(220, 220, 230),
                    highlight=is_slot_selected,
                    highlight_color=(200, 170, 60),
                    payload_list=self._slot_buttons,
                    payload={"actor_index": idx, "slot": slot},
                )

                y += slot_height + slot_spacing

            y += panel_padding * 2

        column_width = 320
        inv_left = screen_rect.right - column_width - 60
        inv_top = self._back_button_rect.bottom + 40

        header = self.font.render("Inventory", True, (235, 235, 235))
        surface.blit(header, (inv_left, inv_top))
        inv_top += header.get_height() + 10

        munny_text = self.font.render(
            f"Munny: {self.inventory.munny}",
            True,
            (230, 230, 230),
        )
        surface.blit(munny_text, (inv_left, inv_top))
        inv_top += munny_text.get_height() + 18

        item_width = column_width
        item_height = 42
        item_gap = 10

        available_items = []
        for slot in ("keyblade", "armor", "accessory"):
            slot_items = list(
                self.inventory.items_by_slot.get(slot, [])
            )
            if slot_items:
                counts: dict[str, int] = OrderedDict()
                for item_id in slot_items:
                    counts[item_id] = counts.get(item_id, 0) + 1
                available_items.append((slot, counts))

        if not available_items:
            empty_text = self.font.render(
                "(No unequipped items)",
                True,
                (200, 200, 200),
            )
            surface.blit(empty_text, (inv_left, inv_top))
            inv_top += empty_text.get_height()
        else:
            for slot, item_counts in available_items:
                slot_header = self.font.render(
                    f"{slot.title()}s",
                    True,
                    (210, 210, 230),
                )
                header_position = (inv_left, inv_top)
                surface.blit(slot_header, header_position)
                inv_top += slot_header.get_height() + 6

                for item_id, count in item_counts.items():
                    item = get_item(item_id)
                    item_rect = pygame.Rect(
                        inv_left,
                        inv_top,
                        item_width,
                        item_height,
                    )
                    label = item.name
                    if count > 1:
                        label = f"{label} x{count}"
                    is_selected = self._selected_item_id == item_id
                    self._draw_button(
                        surface,
                        item_rect,
                        label=label,
                        fill_color=(38, 38, 58),
                        border_color=(80, 80, 120),
                        text_color=(220, 220, 230),
                        highlight=is_selected,
                        highlight_color=(60, 150, 200),
                        payload_list=self._item_buttons,
                        payload={"item_id": item_id, "slot": slot},
                    )

                    inv_top += item_height + item_gap

                inv_top += item_gap

        drop_messages = []
        if (
            self.battle_scene is not None
            and hasattr(self.battle_scene, "get_recent_drop_messages")
        ):
            drop_messages = self.battle_scene.get_recent_drop_messages()
        if drop_messages:
            inv_top += 20
            for message in drop_messages:
                text = self.font.render(message, True, (250, 220, 120))
                surface.blit(text, (inv_left, inv_top))
                inv_top += text.get_height() + 6

    def handle_event(self, event):
        if (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
        ):
            back_clicked = self._back_button_rect.collidepoint(event.pos)
            scene_change_requested = (
                back_clicked and self.battle_scene is not None
            )
            if scene_change_requested:
                self.change_scene(self.battle_scene)
                return

            for button in self._item_buttons:
                if button["rect"].collidepoint(event.pos):
                    payload = button["payload"]
                    item_id = payload["item_id"]
                    slot = payload["slot"]
                    if self._selected_item_id == item_id:
                        self._selected_item_id = None
                        self._selected_item_slot = None
                    else:
                        self._selected_item_id = item_id
                        self._selected_item_slot = slot
                    return

            for button in self._slot_buttons:
                if button["rect"].collidepoint(event.pos):
                    payload = button["payload"]
                    actor_index = payload["actor_index"]
                    slot = payload["slot"]
                    actor = self.actors[actor_index]

                    if self._selected_item_id:
                        selected_item_id = self._selected_item_id
                        if self._selected_item_slot != slot:
                            self._selected_slot = (actor_index, slot)
                            return
                        try:
                            self.inventory.equip_item(actor, selected_item_id)
                        except ValueError:
                            pass
                        else:
                            self._selected_item_id = None
                            self._selected_item_slot = None
                        self._selected_slot = (actor_index, slot)
                        return

                    self._selected_slot = (actor_index, slot)
                    return

    def update(self, dt):
        pass


class MainMenu(Scene):
    def __init__(self, font, *, change_scene):
        self.font = font
        self.change_scene = change_scene

    def draw(self, surface):
        screen_rect = surface.get_rect()
        surface.fill((30, 30, 30))
        title = self.font.render(
            "Main Menu - Press Enter to Start Battle",
            True,
            (255, 255, 255),
        )
        title_rect = title.get_rect(center=screen_rect.center)
        surface.blit(title, title_rect)

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                self.change_scene(
                    BattleScene(self.font, change_scene=self.change_scene)
                )
