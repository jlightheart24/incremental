from __future__ import annotations

from typing import Iterable, List

import pygame

from core.data.items import get_item
from core.data.materials import material_name
from core.gameplay.inventory import Inventory
from core.scenes.scene import Manager, Scene


class ItemLevelScene(Scene):
    def __init__(
        self,
        font,
        *,
        controller: Manager.Controller,
        inventory: Inventory,
        actors: Iterable,
    ) -> None:
        self.font = font
        self.controller = controller
        self.inventory = inventory
        self.actors = list(actors)
        self._back_button_rect = pygame.Rect(0, 0, 0, 0)
        self._level_button_rect = pygame.Rect(0, 0, 0, 0)
        self._item_buttons: List[dict] = []
        self._message: str | None = None
        self._ordered_items: List[str] = []
        self._selected_item_id: str | None = None
        self._rebuild_item_order()

    def blocks_update(self) -> bool:
        return False

    def blocks_draw(self) -> bool:
        return False

    def _collect_owned_items(self) -> Sequence[str]:
        owned = set(self.inventory.item_list)
        owned.update(self.inventory.item_levels.keys())
        for slot_items in self.inventory.items_by_slot.values():
            owned.update(slot_items)
        for actor in self.actors:
            equipment = getattr(actor, "equipment", {}) or {}
            for entry in equipment.values():
                if not entry:
                    continue
                item_id = entry[0]
                owned.add(item_id)
        return tuple(owned)

    def _rebuild_item_order(self) -> None:
        owned = self._collect_owned_items()
        resolved: List[tuple[str, str]] = []
        for item_id in owned:
            try:
                name = get_item(item_id).name
            except KeyError:
                continue
            resolved.append((name.lower(), item_id))
        resolved.sort(key=lambda entry: entry[0])
        self._ordered_items = [item_id for _, item_id in resolved]
        if self._ordered_items:
            if self._selected_item_id not in self._ordered_items:
                self._selected_item_id = self._ordered_items[0]
        else:
            self._selected_item_id = None

    def _draw_panel_background(self, surface: pygame.Surface, rect: pygame.Rect) -> None:
        surface.fill((35, 35, 60), rect)
        pygame.draw.rect(surface, (90, 90, 140), rect, width=2)

    def _render_materials_panel(self, surface: pygame.Surface, rect: pygame.Rect) -> None:
        self._draw_panel_background(surface, rect)
        title = self.font.render("Materials", True, (230, 230, 240))
        surface.blit(title, (rect.left + 16, rect.top + 16))

        y = rect.top + 16 + title.get_height() + 12
        materials = sorted(
            self.inventory.iter_materials(),
            key=lambda item: material_name(item[0]),
        )
        if not materials:
            empty = self.font.render("(None)", True, (200, 200, 210))
            surface.blit(empty, (rect.left + 16, y))
            return
        for material_id, qty in materials:
            label = f"{material_name(material_id)} x{qty}"
            label_surf = self.font.render(label, True, (220, 220, 230))
            surface.blit(label_surf, (rect.left + 16, y))
            y += label_surf.get_height() + 8

    def _render_items_panel(self, surface: pygame.Surface, rect: pygame.Rect) -> None:
        self._draw_panel_background(surface, rect)
        title = self.font.render("Items", True, (230, 230, 240))
        surface.blit(title, (rect.left + 16, rect.top + 16))

        y = rect.top + 16 + title.get_height() + 12
        button_height = self.font.get_height() + 12
        self._item_buttons = []
        if not self._ordered_items:
            empty = self.font.render("(No items)", True, (200, 200, 210))
            surface.blit(empty, (rect.left + 16, y))
            return
        for item_id in self._ordered_items:
            try:
                item = get_item(item_id)
            except KeyError:
                continue
            level = self.inventory.item_level(item_id)
            duplicates = self.inventory.item_count(item_id)
            label = f"{item.name} Lv.{level}"
            if duplicates > 0:
                label += f" ({duplicates} spare)"
            rect_button = pygame.Rect(
                rect.left + 16,
                y,
                rect.width - 32,
                button_height,
            )
            is_selected = item_id == self._selected_item_id
            fill = (70, 100, 140) if is_selected else (50, 65, 95)
            surface.fill(fill, rect_button)
            pygame.draw.rect(surface, (20, 20, 30), rect_button, width=2)
            label_surf = self.font.render(label, True, (245, 245, 245))
            surface.blit(label_surf, (rect_button.left + 12, rect_button.top + 6))
            self._item_buttons.append({
                "rect": rect_button,
                "item_id": item_id,
            })
            y += button_height + 8

    def _render_details(
        self,
        surface: pygame.Surface,
        rect: pygame.Rect,
        item_id: str,
    ) -> None:
        self._draw_panel_background(surface, rect)
        try:
            base_item = get_item(item_id)
        except KeyError:
            return
        current_level = self.inventory.item_level(item_id)
        current_item = self.inventory.leveled_item(item_id)
        next_level = current_level + 1
        requirement = self.inventory.next_level_requirement(item_id)
        current_title = self.font.render(
            f"{base_item.name} Lv.{current_level}",
            True,
            (235, 235, 245),
        )
        surface.blit(current_title, (rect.left + 16, rect.top + 16))

        stats_y = rect.top + 16 + current_title.get_height() + 12
        stat_lines = [
            f"ATK: {current_item.atk}",
            f"DEF: {current_item.defense}",
            f"MP: {current_item.mp}",
        ]
        for line in stat_lines:
            surf = self.font.render(line, True, (230, 230, 240))
            surface.blit(surf, (rect.left + 16, stats_y))
            stats_y += surf.get_height() + 6

        stats_y += 10
        if requirement is None:
            max_text = self.font.render("Max level reached", True, (220, 200, 200))
            surface.blit(max_text, (rect.left + 16, stats_y))
            self._level_button_rect = pygame.Rect(0, 0, 0, 0)
            return

        next_item = self.inventory.leveled_item_at_level(item_id, next_level)
        preview_lines = [
            f"Next ATK: {next_item.atk}",
            f"Next DEF: {next_item.defense}",
            f"Next MP: {next_item.mp}",
        ]
        for line in preview_lines:
            surf = self.font.render(line, True, (220, 220, 240))
            surface.blit(surf, (rect.left + 16, stats_y))
            stats_y += surf.get_height() + 6

        stats_y += 10
        cost_label = self.font.render("Cost:", True, (235, 235, 245))
        surface.blit(cost_label, (rect.left + 16, stats_y))
        stats_y += cost_label.get_height() + 6

        duplicates = self.inventory.item_count(item_id)
        dup_text = self.font.render(
            f"Copies needed: {requirement.item_cost} (Have {duplicates})",
            True,
            (220, 220, 230),
        )
        surface.blit(dup_text, (rect.left + 32, stats_y))
        stats_y += dup_text.get_height() + 6

        for material_id, qty in requirement.materials.items():
            have = self.inventory.material_count(material_id)
            label = f"{material_name(material_id)} x{qty} (Have {have})"
            color = (220, 220, 230)
            if have < qty:
                color = (220, 170, 170)
            surf = self.font.render(label, True, color)
            surface.blit(surf, (rect.left + 32, stats_y))
            stats_y += surf.get_height() + 4

        button_padding = 16
        button_label = self.font.render("Level Up", True, (0, 0, 0))
        btn_w = button_label.get_width() + button_padding * 2
        btn_h = button_label.get_height() + button_padding
        self._level_button_rect = pygame.Rect(
            rect.left + 16,
            stats_y + 20,
            btn_w,
            btn_h,
        )
        affordable = self.inventory.can_level_item(item_id)
        fill_color = (200, 200, 200) if affordable else (90, 90, 90)
        surface.fill(fill_color, self._level_button_rect)
        pygame.draw.rect(surface, (50, 50, 50), self._level_button_rect, 2)
        surface.blit(
            button_label,
            button_label.get_rect(center=self._level_button_rect.center),
        )

    def draw(self, surface: pygame.Surface) -> None:
        screen_rect = surface.get_rect()
        overlay = pygame.Surface(screen_rect.size, pygame.SRCALPHA)
        overlay.fill((15, 15, 35, 235))
        surface.blit(overlay, (0, 0))

        button_padding = 16
        back_label = self.font.render("Back", True, (0, 0, 0))
        btn_w = back_label.get_width() + button_padding * 2
        btn_h = back_label.get_height() + button_padding
        self._back_button_rect = pygame.Rect(60, 40, btn_w, btn_h)
        pygame.draw.rect(surface, (200, 200, 200), self._back_button_rect)
        pygame.draw.rect(surface, (50, 50, 50), self._back_button_rect, 2)
        back_label_rect = back_label.get_rect(center=self._back_button_rect.center)
        surface.blit(back_label, back_label_rect)

        header = self.font.render("Item Leveling", True, (235, 235, 245))
        surface.blit(header, (screen_rect.centerx - header.get_width() // 2, 50))

        panel_top = self._back_button_rect.bottom + 30
        material_panel_width = 280
        material_panel_rect = pygame.Rect(60, panel_top, material_panel_width, 420)
        self._render_materials_panel(surface, material_panel_rect)

        item_panel_left = material_panel_rect.right + 40
        item_panel_width = screen_rect.right - item_panel_left - 60
        item_panel_rect = pygame.Rect(
            item_panel_left,
            panel_top,
            item_panel_width,
            240,
        )
        self._render_items_panel(surface, item_panel_rect)

        detail_rect = pygame.Rect(
            item_panel_left,
            item_panel_rect.bottom + 20,
            item_panel_width,
            160,
        )
        self._level_button_rect = pygame.Rect(0, 0, 0, 0)
        if self._selected_item_id is not None:
            self._render_details(surface, detail_rect, self._selected_item_id)
        else:
            self._draw_panel_background(surface, detail_rect)
            empty = self.font.render(
                "Select an item to see details",
                True,
                (200, 200, 210),
            )
            surface.blit(empty, (detail_rect.left + 16, detail_rect.top + 16))

        if self._message:
            msg_label = self.font.render(self._message, True, (250, 220, 120))
            msg_rect = msg_label.get_rect()
            msg_rect.midbottom = (
                screen_rect.centerx,
                screen_rect.bottom - 40,
            )
            surface.blit(msg_label, msg_rect)

    def _attempt_level_up(self, item_id: str) -> None:
        try:
            self.inventory.level_up_item(item_id)
        except ValueError as exc:
            self._message = str(exc)
            return
        level = self.inventory.item_level(item_id)
        try:
            name = get_item(item_id).name
        except KeyError:
            name = item_id
        self._message = f"{name} reached Lv.{level}!"
        self._rebuild_item_order()

    def handle_event(self, event) -> bool:
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.controller.pop()
            return True
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self._back_button_rect.collidepoint(event.pos):
                self.controller.pop()
                return True
            for button in self._item_buttons:
                if button["rect"].collidepoint(event.pos):
                    item_id = button["item_id"]
                    if item_id != self._selected_item_id:
                        self._selected_item_id = item_id
                        self._message = None
                    return True
            if self._level_button_rect and self._level_button_rect.collidepoint(event.pos):
                if self._selected_item_id is None:
                    return True
                self._attempt_level_up(self._selected_item_id)
                return True
        return False

    def update(self, dt):
        return None
