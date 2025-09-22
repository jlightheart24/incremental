import math
from typing import Any

import pygame

class HexBoard:
    DIRECTIONS = [(1, 0), (1, -1), (0, -1), (-1, 0), (-1, 1), (0, 1)]
    SQRT3 = math.sqrt(3)

    def __init__(self, screen_rect, cols=6, rows=6, *, size=48, margin=40):
        self.cols = cols
        self.rows = rows
        self.size = size
        self.margin = margin
        self.screen_rect = screen_rect
        self._bounds = self._calculate_bounds()
        self.origin = self._compute_origin()
        self._occupants: dict[tuple[int, int], object | None] = {
            (q, r): None for q in range(cols) for r in range(rows)
        }
        self._sprite_cache: dict[Any, pygame.Surface] = {}

    def _calculate_bounds(self) -> tuple[float, float, float, float]:
        min_x = float("inf")
        max_x = float("-inf")
        min_y = float("inf")
        max_y = float("-inf")
        for q, r in self.tiles():
            cx, cy = self._axial_to_pixel_local(q, r)
            for corner in self._hex_corners_local(cx, cy):
                x, y = corner
                min_x = min(min_x, x)
                max_x = max(max_x, x)
                min_y = min(min_y, y)
                max_y = max(max_y, y)
        width = max_x - min_x
        height = max_y - min_y
        return min_x, min_y, width, height

    def _compute_origin(self):
        min_x, min_y, board_w, board_h = self._bounds
        origin_x = self.screen_rect.right - board_w - self.margin - min_x
        origin_y = self.screen_rect.centery - board_h / 2 - min_y
        return origin_x, origin_y

    def _axial_to_pixel_local(self, q, r):
        x = self.size * self.SQRT3 * (q + r / 2)
        y = self.size * 1.5 * r
        return x, y

    def axial_to_pixel(self, q, r):
        origin_x, origin_y = self.origin
        x, y = self._axial_to_pixel_local(q, r)
        return origin_x + x, origin_y + y

    def in_bounds(self, q: int, r: int) -> bool:
        return 0 <= q < self.cols and 0 <= r < self.rows
    
    def neighbors(self, q, r):
        for dq, dr in self.DIRECTIONS:
            nq, nr = q + dq, r + dr
            if self.in_bounds(nq, nr):
                yield nq, nr

    def tiles(self):
        for q in range(self.cols):
            for r in range(self.rows):
                yield (q, r)

    def occupant_at(self, q, r):
        return self._occupants.get((q, r))

    def place(self, token, q, r):
        if not self.in_bounds(q, r):
            raise ValueError("out of bounds")
        if self._occupants[(q, r)] is not None:
            raise ValueError("tile already occupied")
        self._occupants[(q, r)] = token

    def remove(self, q, r):
        if not self.in_bounds(q, r):
            raise ValueError("out of bounds")
        token = self._occupants[(q, r)]
        self._occupants[(q, r)] = None
        return token

    def move(self, src, dest):
        src_q, src_r = src
        dest_q, dest_r = dest
        if not self.in_bounds(src_q, src_r):
            raise ValueError("src out of bounds")
        if not self.in_bounds(dest_q, dest_r):
            raise ValueError("dest out of bounds")
        token = self.occupant_at(src_q, src_r)
        if token is None:
            raise ValueError("no occupant at src")
        if self._occupants.get((dest_q, dest_r)) is not None:
            raise ValueError("destination occupied")
        self.remove(src_q, src_r)
        self.place(token, dest_q, dest_r)
        return token

    def _hex_corners_local(self, cx: float, cy: float) -> list[tuple[float, float]]:
        corners: list[tuple[float, float]] = []
        for i in range(6):
            angle_deg = 60 * i - 30
            angle_rad = math.radians(angle_deg)
            x = cx + self.size * math.cos(angle_rad)
            y = cy + self.size * math.sin(angle_rad)
            corners.append((x, y))
        return corners

    def _hex_corners(self, cx: float, cy: float) -> list[tuple[int, int]]:
        return [(int(x), int(y)) for x, y in self._hex_corners_local(cx, cy)]

    def _sprite_for_token(self, token) -> pygame.Surface | None:
        sprite = getattr(token, "board_sprite", None)
        if sprite is not None:
            return sprite

        cache_key = getattr(token, "portrait_path", None)
        if not cache_key:
            return None
        cached = self._sprite_cache.get(cache_key)
        if cached is not None:
            return cached
        try:
            image = pygame.image.load(cache_key)
        except pygame.error:
            return None
        size = int(self.size * 1.6)
        sprite = pygame.transform.smoothscale(image, (size, size))
        sprite = sprite.convert_alpha()
        self._sprite_cache[cache_key] = sprite
        return sprite

    def draw(self, surface):
        fill_color = (45, 45, 70)
        border_color = (90, 90, 140)
        for q, r in self.tiles():
            cx, cy = self.axial_to_pixel(q, r)
            corners = self._hex_corners(cx, cy)
            pygame.draw.polygon(surface, fill_color, corners)
            pygame.draw.polygon(surface, border_color, corners, width=2)

            token = self.occupant_at(q, r)
            if token is None:
                continue

            sprite = self._sprite_for_token(token)
            if sprite is None:
                radius = int(self.size * 0.35)
                pygame.draw.circle(
                    surface,
                    (200, 80, 80),
                    (int(cx), int(cy)),
                    radius,
                )
                continue

            sprite_rect = sprite.get_rect(center=(int(cx), int(cy)))
            surface.blit(sprite, sprite_rect)
