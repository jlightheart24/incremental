from collections import OrderedDict

import pygame

from core.inventory import Inventory
from core.items import get_item
from core.scenes.scene import Scene


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
                surface.blit(slot_header, (inv_left, inv_top))
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
