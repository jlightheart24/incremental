from __future__ import annotations

from typing import Sequence

import pygame

from core.entities import Actor
from core.ui.actionbar import ActionBar


class BattleHUD:
    """Responsible for rendering the battle UI overlays."""

    def __init__(self, font, *, action_bar: ActionBar) -> None:
        self.font = font
        self.action_bar = action_bar
        self.inventory_button_rect = pygame.Rect(0, 0, 0, 0)
        self.synthesis_button_rect = pygame.Rect(0, 0, 0, 0)
        self.map_button_rect = pygame.Rect(0, 0, 0, 0)
        self._inventory_button_label = self.font.render("Inventory", True, (0, 0, 0))
        self._synthesis_button_label = self.font.render("Synthesis", True, (0, 0, 0))
        self._map_button_label = self.font.render("Map", True, (0, 0, 0))
        self._dead_portraits: dict[Actor, pygame.Surface] = {}
        self._hint_text = "ESC: Quit | 1-3: Cycle Spells"
        subtitle_size = max(12, self.font.get_height() - 6)
        try:
            family = self.font.get_name()
            if isinstance(family, (list, tuple)) and family:
                family = family[0]
            self._subtitle_font = pygame.font.SysFont(family, subtitle_size)
        except Exception:
            self._subtitle_font = pygame.font.Font(None, subtitle_size)

    def draw(
        self,
        surface: pygame.Surface,
        *,
        munny: int,
        actors: Sequence[Actor],
        portraits: Sequence[pygame.Surface],
        ko_timers: dict[Actor, float],
        available_spells: int,
        location_name: str | None = None,
        location_subtitle: str | None = None,
    ) -> None:
        screen_rect = surface.get_rect()
        title_baseline = 20
        if location_name:
            title_surf = self.font.render(location_name, True, (245, 245, 255))
            title_rect = title_surf.get_rect()
            title_rect.midtop = (screen_rect.centerx, title_baseline)
            surface.blit(title_surf, title_rect)
            title_baseline = title_rect.bottom + 4
        if location_subtitle:
            subtitle_font = self._subtitle_font or self.font
            subtitle_surf = subtitle_font.render(
                location_subtitle,
                True,
                (210, 210, 230),
            )
            subtitle_rect = subtitle_surf.get_rect()
            subtitle_rect.midtop = (screen_rect.centerx, title_baseline)
            surface.blit(subtitle_surf, subtitle_rect)

        munny_text = self.font.render(
            f"Munny: {munny}",
            True,
            (250, 220, 120),
        )
        surface.blit(munny_text, (40, 40))

        button_padding = 16
        label_width = max(
            self._inventory_button_label.get_width(),
            self._synthesis_button_label.get_width(),
            self._map_button_label.get_width(),
        )
        btn_w = label_width + button_padding * 2
        btn_h = self._inventory_button_label.get_height() + button_padding
        top_right = (screen_rect.right - 40, 40)

        self.inventory_button_rect = pygame.Rect(0, 0, btn_w, btn_h)
        self.inventory_button_rect.topright = top_right
        pygame.draw.rect(surface, (200, 200, 200), self.inventory_button_rect)
        pygame.draw.rect(surface, (50, 50, 50), self.inventory_button_rect, 2)
        inv_label_rect = self._inventory_button_label.get_rect(
            center=self.inventory_button_rect.center
        )
        surface.blit(self._inventory_button_label, inv_label_rect)

        self.synthesis_button_rect = pygame.Rect(0, 0, btn_w, btn_h)
        self.synthesis_button_rect.topright = (
            top_right[0],
            self.inventory_button_rect.bottom + 20,
        )
        pygame.draw.rect(surface, (200, 200, 200), self.synthesis_button_rect)
        pygame.draw.rect(surface, (50, 50, 50), self.synthesis_button_rect, 2)
        synth_label_rect = self._synthesis_button_label.get_rect(
            center=self.synthesis_button_rect.center
        )
        surface.blit(self._synthesis_button_label, synth_label_rect)

        self.map_button_rect = pygame.Rect(0, 0, btn_w, btn_h)
        self.map_button_rect.topright = (
            top_right[0],
            self.synthesis_button_rect.bottom + 20,
        )
        pygame.draw.rect(surface, (200, 200, 200), self.map_button_rect)
        pygame.draw.rect(surface, (50, 50, 50), self.map_button_rect, 2)
        map_label_rect = self._map_button_label.get_rect(
            center=self.map_button_rect.center
        )
        surface.blit(self._map_button_label, map_label_rect)

        if portraits:
            portrait_height = portraits[0].get_height()
            spacing = 70
            total_height = (
                len(portraits) * portrait_height
                + (len(portraits) - 1) * spacing
            )
            start_y = screen_rect.centery - total_height // 2

            for index, (actor, portrait) in enumerate(zip(actors, portraits)):
                top = start_y + index * (portrait_height + spacing)
                self._draw_actor_panel(
                    surface,
                    actor,
                    portrait,
                    left=screen_rect.left + 60,
                    top=top,
                    ko_remaining=ko_timers.get(actor),
                )

        max_button_count = max(2, len(actors), max(0, available_spells))
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
            self._hint_text,
            True,
            (180, 180, 180),
        )
        hint_rect = hint.get_rect()
        hint_rect.midbottom = (
            screen_rect.centerx,
            screen_rect.bottom - 40,
        )
        surface.blit(hint, hint_rect)

    def _draw_actor_panel(
        self,
        surface: pygame.Surface,
        actor: Actor,
        portrait: pygame.Surface,
        *,
        left: int,
        top: int,
        ko_remaining: float | None,
    ) -> None:
        portrait_rect = portrait.get_rect()
        portrait_rect.topleft = (left, top)
        portrait_surface = portrait
        if actor.health.is_dead() or ko_remaining is not None:
            portrait_surface = self._dead_portrait_for(actor, portrait)
        surface.blit(portrait_surface, portrait_rect)
        if ko_remaining is not None:
            countdown = max(0.0, ko_remaining)
            timer_label = self.font.render(
                f"{countdown:.1f}s",
                True,
                (255, 255, 255),
            )
            timer_rect = timer_label.get_rect(center=portrait_rect.center)
            surface.blit(timer_label, timer_rect)
        info_x = portrait_rect.right + 28
        y = portrait_rect.top
        spell = getattr(actor, "current_spell", None)
        spell_name = getattr(spell, "name", "None")
        mana = getattr(actor, "mana", None)
        mp_current = mana.current if mana is not None else 0
        mp_max = mana.max if mana is not None else 0
        xp_to_level = getattr(actor, "xp_to_level", 0)
        stats = [
            f"{actor.name}",
            f"HP: {actor.health.current}/{actor.health.max}",
            f"MP: {mp_current}/{mp_max}",
            f"Spell: {spell_name}",
            f"Level: {getattr(actor, 'level', 1)}",
            f"XP: {getattr(actor, 'xp', 0)}/{xp_to_level}",
        ]
        for line in stats:
            surf = self.font.render(line, True, (255, 255, 255))
            surface.blit(surf, (info_x, y))
            y += 28

    def _dead_portrait_for(
        self,
        actor: Actor,
        base_surface: pygame.Surface,
    ) -> pygame.Surface:
        dead_surface = self._dead_portraits.get(actor)
        if dead_surface is None:
            dead_surface = pygame.Surface(base_surface.get_size(), pygame.SRCALPHA)
            dead_surface.fill((100, 100, 100))
            pygame.draw.rect(dead_surface, (40, 40, 40), dead_surface.get_rect(), 2)
            self._dead_portraits[actor] = dead_surface
        return dead_surface
