from __future__ import annotations

from typing import Callable, List

import pygame

from core.locations import LocationDef, iter_locations
from core.scenes.scene import Manager, Scene


class MapScene(Scene):
    """Simple world map list allowing the player to choose a destination."""

    def __init__(
        self,
        font,
        *,
        controller: Manager.Controller,
        current_location_id: str,
        on_select: Callable[[str], None],
    ) -> None:
        self.font = font
        self.controller = controller
        self.current_location_id = current_location_id
        self._on_select = on_select
        self._buttons: List[dict] = []
        self._locations: List[LocationDef] = sorted(
            iter_locations(),
            key=lambda loc: (loc.title, loc.subtitle),
        )

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill((15, 25, 45))
        screen_rect = surface.get_rect()
        self._buttons = []

        header = self.font.render("World Map", True, (245, 245, 255))
        header_rect = header.get_rect()
        header_rect.midtop = (screen_rect.centerx, 40)
        surface.blit(header, header_rect)

        hint = self.font.render("Click a destination", True, (200, 200, 220))
        hint_rect = hint.get_rect()
        hint_rect.midtop = (screen_rect.centerx, header_rect.bottom + 12)
        surface.blit(hint, hint_rect)

        list_top = hint_rect.bottom + 30
        list_left = screen_rect.centerx - 220
        item_width = 440
        item_height = self.font.get_height() + 16
        gap = 12

        for location in self._locations:
            rect = pygame.Rect(list_left, list_top, item_width, item_height)
            is_current = location.location_id == self.current_location_id
            fill = (50, 80, 110) if is_current else (35, 55, 85)
            border = (110, 160, 210) if is_current else (70, 100, 140)
            pygame.draw.rect(surface, fill, rect)
            pygame.draw.rect(surface, border, rect, width=2)

            label = f"{location.title} - {location.subtitle}"
            label_surf = self.font.render(label, True, (240, 240, 250))
            label_rect = label_surf.get_rect(center=rect.center)
            surface.blit(label_surf, label_rect)

            self._buttons.append({
                "rect": rect,
                "location_id": location.location_id,
            })
            list_top += item_height + gap

    def handle_event(self, event) -> bool:
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.controller.pop()
            return True
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for button in self._buttons:
                if button["rect"].collidepoint(event.pos):
                    self._on_select(button["location_id"])
                    return True
        return False

    def update(self, dt):
        return None
