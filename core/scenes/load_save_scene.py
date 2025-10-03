from __future__ import annotations

from typing import List

import pygame

from core.data.savegame import (
    SaveSlotInfo,
    create_default_state,
    list_slots,
    load_state,
    save_state,
)
from core.scenes.scene import Manager, Scene


class LoadSaveScene(Scene):
    """Menu scene that lets the player choose or create a save slot."""

    def __init__(self, font, *, controller: Manager.Controller) -> None:
        self.font = font
        self.controller = controller
        self._slots: List[SaveSlotInfo] = list_slots()
        self._slot_buttons: list[tuple[pygame.Rect, SaveSlotInfo]] = []

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill((18, 24, 40))
        screen_rect = surface.get_rect()

        header = self.font.render("Select Save Slot", True, (240, 240, 255))
        header_rect = header.get_rect(center=(screen_rect.centerx, 80))
        surface.blit(header, header_rect)

        hint = self.font.render("ESC to return to Main Menu", True, (190, 190, 210))
        hint_rect = hint.get_rect(center=(screen_rect.centerx, header_rect.bottom + 24))
        surface.blit(hint, hint_rect)

        slot_width = min(560, screen_rect.width - 120)
        slot_height = 110
        gap = 20
        top = hint_rect.bottom + 36
        left = screen_rect.centerx - slot_width // 2

        self._slot_buttons = []
        for index, info in enumerate(self._slots):
            rect = pygame.Rect(left, top + index * (slot_height + gap), slot_width, slot_height)
            self._draw_slot(surface, rect, info)
            self._slot_buttons.append((rect, info))

        footer = self.font.render("Enter number keys (1-3) or click to confirm", True, (180, 180, 200))
        footer_rect = footer.get_rect(center=(screen_rect.centerx, screen_rect.height - 60))
        surface.blit(footer, footer_rect)

    def _draw_slot(self, surface: pygame.Surface, rect: pygame.Rect, info: SaveSlotInfo) -> None:
        is_existing = info.exists
        fill = (55, 85, 130) if is_existing else (35, 55, 85)
        border = (130, 185, 240) if is_existing else (80, 110, 150)
        pygame.draw.rect(surface, fill, rect, border_radius=12)
        pygame.draw.rect(surface, border, rect, width=3, border_radius=12)

        title_text = f"{info.title} - {'Continue' if is_existing else 'New Game'}"
        title = self.font.render(title_text, True, (245, 245, 255))
        title_rect = title.get_rect()
        title_rect.midtop = (rect.centerx, rect.top + 16)
        surface.blit(title, title_rect)

        body_lines: list[str] = []
        location_name = info.location_display()
        body_lines.append(f"Location: {location_name}")
        if is_existing and info.party:
            body_lines.append(f"Party: {', '.join(info.party)}")
        if is_existing:
            timestamp = info.updated_at.strftime("%Y-%m-%d %H:%M") if info.updated_at else "Unknown"
            body_lines.append(f"Last Played: {timestamp}")
            body_lines.append(f"Munny: {info.munny}")
        else:
            body_lines.append("Start a new adventure from the beginning.")

        for offset, line in enumerate(body_lines):
            text = self.font.render(line, True, (220, 220, 235))
            text_rect = text.get_rect()
            text_rect.midtop = (rect.centerx, title_rect.bottom + 12 + offset * (self.font.get_height() + 4))
            surface.blit(text, text_rect)

    def handle_event(self, event) -> bool:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.controller.pop()
                return True
            if pygame.K_1 <= event.key <= pygame.K_3:
                index = event.key - pygame.K_1
                if 0 <= index < len(self._slots):
                    self._start_slot(self._slots[index])
                    return True
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for rect, info in self._slot_buttons:
                if rect.collidepoint(event.pos):
                    self._start_slot(info)
                    return True
        return False

    def _start_slot(self, info: SaveSlotInfo) -> None:
        if info.exists:
            state = load_state(info.slot_id)
            if state is None:
                # Fallback: treat as new game if load failed.
                state = create_default_state(info.slot_id)
                save_state(state)
        else:
            state = create_default_state(info.slot_id)
            save_state(state)
        from core.scenes.battle_scene import BattleScene

        battle_scene = BattleScene(
            self.font,
            controller=self.controller,
            location_id=state.location_id,
            inventory=state.inventory,
            actors=state.actors,
            save_slot=state.slot_id,
            save_created_at=state.created_at,
            save_updated_at=state.updated_at,
        )
        self.controller.replace(battle_scene)

    def blocks_draw(self) -> bool:
        return True

    def blocks_input(self) -> bool:
        return True

    def blocks_update(self) -> bool:
        return True
