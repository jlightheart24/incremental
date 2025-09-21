import pygame

BAR_WIDTH = 260
BUTTON_HEIGHT = 44
PADDING = 12


class ActionBar:
    def __init__(
        self,
        font,
        *,
        on_attack,
        on_spell_assign,
        get_party,
        get_spells,
    ):
        self._font = font
        self._on_attack = on_attack
        self._on_spell_assign = on_spell_assign
        self._get_party = get_party
        self._get_spells = get_spells
        self._mode = "root"
        self._buttons = []
        self._selected_actor = None
        self._bounds = pygame.Rect(0, 0, BAR_WIDTH, 0)
        self._pending_activation = None

    def width(self) -> int:
        return BAR_WIDTH

    def draw(self, surface: pygame.Surface, bar_rect: pygame.Rect) -> None:
        self._bounds = bar_rect
        self._buttons = []

        bg_color = (32, 32, 48)
        border_color = (70, 70, 90)
        text_color = (230, 230, 230)

        surface.fill(bg_color, bar_rect)
        pygame.draw.rect(surface, border_color, bar_rect, width=2)

        title_surf = self._font.render("Action Bar", True, text_color)
        title_rect = title_surf.get_rect()
        title_rect.topleft = (bar_rect.left + PADDING, bar_rect.top + PADDING)
        surface.blit(title_surf, title_rect)

        items = self._items_for_mode()

        y = title_rect.bottom + PADDING
        button_width = bar_rect.width - PADDING * 2
        for label, payload in items:
            btn_rect = pygame.Rect(
                bar_rect.left + PADDING,
                y,
                button_width,
                BUTTON_HEIGHT,
            )
            pygame.draw.rect(surface, (55, 55, 85), btn_rect)
            pygame.draw.rect(surface, border_color, btn_rect, width=2)

            label_surf = self._font.render(label, True, text_color)
            label_rect = label_surf.get_rect(center=btn_rect.center)
            surface.blit(label_surf, label_rect)

            self._buttons.append({"rect": btn_rect, "payload": payload})
            y += BUTTON_HEIGHT + PADDING

    def estimate_height(self, button_count: int) -> int:
        button_count = max(0, int(button_count))
        title_height = self._font.get_height()
        height = PADDING + title_height + PADDING  # top padding + title + gap
        if button_count:
            height += button_count * BUTTON_HEIGHT
            height += (button_count - 1) * PADDING
        height += PADDING  # bottom padding
        return height

    def handle_event(self, event) -> bool:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if not self._bounds.collidepoint(event.pos):
                self._pending_activation = None
                return False
            for button in self._buttons:
                if button["rect"].collidepoint(event.pos):
                    self._pending_activation = button
                    return True
            self._pending_activation = None
            return self._bounds.collidepoint(event.pos)

        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self._pending_activation is None:
                return False
            button = self._pending_activation
            self._pending_activation = None
            if button["rect"].collidepoint(event.pos):
                self._activate(button["payload"])
                return True
        return False

    def _items_for_mode(self):
        if self._mode == "root":
            return self._build_root_buttons()
        if self._mode == "choose_actor":
            return self._build_actor_buttons()
        if self._mode == "choose_spell" and self._selected_actor is not None:
            return self._build_spell_buttons(self._selected_actor)
        return []

    def _build_root_buttons(self):
        return [
            ("Attack", {"action": "attack"}),
            ("Spells", {"action": "choose_actor"}),
        ]

    def _build_actor_buttons(self):
        items = []
        party = self._get_party() or []
        for idx, actor in enumerate(party):
            label = getattr(actor, "name", None) or f"Member {idx + 1}"
            items.append(
                (
                    label,
                    {
                        "action": "actor_selected",
                        "actor_index": idx,
                    },
                )
            )
        return items

    def _build_spell_buttons(self, actor_index):
        items = []
        spells = self._get_spells(actor_index) or []
        for spell_id in spells:
            label = str(spell_id).title()
            items.append(
                (
                    label,
                    {
                        "action": "assign_spell",
                        "actor_index": actor_index,
                        "spell_id": spell_id,
                    },
                )
            )
        return items

    def _activate(self, payload: dict) -> None:
        action = payload.get("action")
        if action == "attack":
            self._on_attack()
            self._mode = "root"
            self._selected_actor = None
        elif action == "choose_actor":
            self._mode = "choose_actor"
            self._selected_actor = None
        elif action == "actor_selected":
            self._selected_actor = payload.get("actor_index")
            self._mode = "choose_spell"
        elif action == "assign_spell":
            actor_index = payload.get("actor_index")
            spell_id = payload.get("spell_id")
            if actor_index is not None and spell_id is not None:
                self._on_spell_assign(actor_index, spell_id)
            self._selected_actor = None
            self._mode = "root"
