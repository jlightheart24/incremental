from __future__ import annotations

import os

from enum import Enum, auto
from typing import Callable, Dict, Optional

import pygame


class RenderLayer(Enum):
    """Logical render layers processed in back-to-front order."""

    BACKGROUND = auto()
    ACTORS = auto()
    FX = auto()
    UI = auto()


class RenderSystem:
    """Owns shared render state such as the board and sprite layers."""

    def __init__(self) -> None:
        self._background_color: tuple[int, int, int] = (20, 20, 20)
        self._board_factory: Optional[Callable[[pygame.Rect], object]] = None
        self._screen_size: tuple[int, int] | None = None
        self.board: object | None = None
        self.layers: Dict[RenderLayer, pygame.sprite.LayeredUpdates] = {
            layer: pygame.sprite.LayeredUpdates() for layer in RenderLayer
        }
        self._background_image_path: str | None = None
        self._background_surface: pygame.Surface | None = None
        self._scaled_background: pygame.Surface | None = None
        self._scaled_background_size: tuple[int, int] | None = None

    def set_background_color(self, color: tuple[int, int, int]) -> None:
        self._background_color = tuple(int(c) for c in color)

    def set_board_factory(self, factory: Callable[[pygame.Rect], object]) -> None:
        """Register a callable that builds a board for the current screen."""

        self._board_factory = factory

    def set_background_image(self, path: str | None) -> None:
        """Assign a background image path, reloading on the next draw."""

        self._background_image_path = path
        self._background_surface = None
        self._scaled_background = None
        self._scaled_background_size = None

    def ensure_board(self, screen_rect: pygame.Rect) -> bool:
        """Ensure the board matches the current screen; return True if rebuilt."""

        if self._board_factory is None:
            return False
        size = screen_rect.size
        if self.board is None or self._screen_size != size:
            self.board = self._board_factory(screen_rect)
            self._screen_size = size
            return True
        return False

    def draw(self, surface: pygame.Surface) -> None:
        """Draw background, board, and any registered sprite layers."""

        background = self._background_for_size(surface.get_size())
        if background is not None:
            surface.blit(background, (0, 0))
        else:
            surface.fill(self._background_color)
        if self.board is not None:
            try:
                self.board.draw(surface)
            except AttributeError:
                pass
        for layer in RenderLayer:
            group = self.layers.get(layer)
            if group:
                group.draw(surface)

    # --- internal helpers -------------------------------------------------

    def _background_for_size(self, size: tuple[int, int]) -> pygame.Surface | None:
        image = self._load_background_surface()
        if image is None:
            return None
        if self._scaled_background is not None and self._scaled_background_size == size:
            return self._scaled_background
        self._scaled_background = pygame.transform.smoothscale(image, size)
        self._scaled_background_size = size
        return self._scaled_background

    def _load_background_surface(self) -> pygame.Surface | None:
        if self._background_image_path is None:
            return None
        if self._background_surface is not None:
            return self._background_surface
        if not os.path.exists(self._background_image_path):
            self._background_surface = None
            return None
        try:
            self._background_surface = pygame.image.load(
                self._background_image_path
            ).convert()
        except pygame.error:
            self._background_surface = None
        return self._background_surface
