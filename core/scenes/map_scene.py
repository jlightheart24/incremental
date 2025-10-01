from __future__ import annotations

from typing import Callable, Dict, List, Optional

import pygame

from core.data.locations import get_location, iter_locations
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
        self._world_buttons: List[dict] = []
        self._location_buttons: List[dict] = []

        self._worlds: Dict[str, dict] = {}
        for location in iter_locations():
            world = self._worlds.setdefault(
                location.world_id,
                {
                    "name": location.title,
                    "locations": [],
                },
            )
            world["locations"].append(location)
        for world in self._worlds.values():
            world["locations"].sort(key=lambda loc: loc.subtitle)

        self._world_order: List[str] = sorted(
            self._worlds.keys(),
            key=lambda wid: (self._worlds[wid]["name"].lower(), wid),
        )

        self._current_world_id = self._resolve_initial_world(current_location_id)

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill((15, 25, 45))
        screen_rect = surface.get_rect()
        self._world_buttons = []
        self._location_buttons = []

        header = self.font.render("World Map", True, (245, 245, 255))
        header_rect = header.get_rect()
        header_rect.midtop = (screen_rect.centerx, 40)
        surface.blit(header, header_rect)

        hint = self.font.render("Click a destination", True, (200, 200, 220))
        hint_rect = hint.get_rect()
        hint_rect.midtop = (screen_rect.centerx, header_rect.bottom + 12)
        surface.blit(hint, hint_rect)

        worlds_top = hint_rect.bottom + 30
        worlds_height = self.font.get_height() + 16
        world_gap = 16
        world_button_width = 220
        total_world_width = (
            len(self._world_order) * (world_button_width + world_gap) - world_gap
            if self._world_order
            else 0
        )
        worlds_left = screen_rect.centerx - total_world_width // 2

        for index, world_id in enumerate(self._world_order):
            info = self._worlds[world_id]
            rect = pygame.Rect(
                worlds_left + index * (world_button_width + world_gap),
                worlds_top,
                world_button_width,
                worlds_height,
            )
            is_current_world = world_id == self._current_world_id
            fill = (70, 100, 140) if is_current_world else (40, 60, 90)
            border = (140, 190, 240) if is_current_world else (80, 110, 150)
            pygame.draw.rect(surface, fill, rect)
            pygame.draw.rect(surface, border, rect, width=2)

            label_surf = self.font.render(info["name"], True, (240, 240, 250))
            label_rect = label_surf.get_rect(center=rect.center)
            surface.blit(label_surf, label_rect)

            self._world_buttons.append({
                "rect": rect,
                "world_id": world_id,
            })

        list_top = worlds_top + worlds_height + 36
        list_left = screen_rect.centerx - 220
        item_width = 440
        item_height = self.font.get_height() + 16
        gap = 12

        locations = self._worlds.get(self._current_world_id, {}).get("locations", [])
        for location in locations:
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

            self._location_buttons.append({
                "rect": rect,
                "location_id": location.location_id,
            })
            list_top += item_height + gap

    def handle_event(self, event) -> bool:
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.controller.pop()
            return True
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for button in self._world_buttons:
                if button["rect"].collidepoint(event.pos):
                    self._set_world(button["world_id"])
                    return True
            for button in self._location_buttons:
                if button["rect"].collidepoint(event.pos):
                    location_id = button["location_id"]
                    self.current_location_id = location_id
                    self._on_select(location_id)
                    return True
        return False

    def update(self, dt):
        return None

    def _set_world(self, world_id: str) -> None:
        if world_id not in self._worlds or world_id == self._current_world_id:
            return
        self._current_world_id = world_id
        locations = self._worlds[world_id].get("locations", [])
        if not any(loc.location_id == self.current_location_id for loc in locations):
            if locations:
                self.current_location_id = locations[0].location_id

    def _resolve_initial_world(self, location_id: str) -> Optional[str]:
        try:
            location = get_location(location_id)
        except KeyError:
            location = None
        if location is not None:
            return location.world_id
        if self._world_order:
            first_world = self._world_order[0]
            locations = self._worlds[first_world].get("locations", [])
            if locations:
                self.current_location_id = locations[0].location_id
            return first_world
        return None
