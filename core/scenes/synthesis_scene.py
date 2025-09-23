import pygame

from core.inventory import Inventory
from core.items import get_item
from core.materials import material_name
from core.scenes.scene import Manager, Scene
from core.synthesis import SynthesisRecipe, iter_recipes


class SynthesisScene(Scene):
    def __init__(
        self,
        font,
        *,
        controller: Manager.Controller,
        inventory: Inventory,
    ) -> None:
        self.font = font
        self.controller = controller
        self.inventory = inventory
        self._recipes: dict[str, SynthesisRecipe] = {
            recipe.recipe_id: recipe for recipe in iter_recipes()
        }
        self._ordered_recipes = list(self._recipes.values())
        self._ordered_recipes.sort(key=lambda r: r.name)

        self._back_button_rect = pygame.Rect(0, 0, 0, 0)
        self._craft_button_rect = pygame.Rect(0, 0, 0, 0)
        self._recipe_buttons: list[dict] = []
        self._selected_recipe_id: str | None = None
        self._message: str | None = None

    def blocks_update(self) -> bool:
        return False

    def blocks_draw(self) -> bool:
        return False

    def _selected_recipe(self) -> SynthesisRecipe | None:
        if self._selected_recipe_id is None:
            return None
        return self._recipes.get(self._selected_recipe_id)

    def _draw_panel_background(self, surface: pygame.Surface, rect: pygame.Rect) -> None:
        surface.fill((35, 35, 60), rect)
        pygame.draw.rect(surface, (90, 90, 140), rect, width=2)

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

        header = self.font.render("Synthesis", True, (235, 235, 245))
        surface.blit(header, (screen_rect.centerx - header.get_width() // 2, 50))

        panel_top = self._back_button_rect.bottom + 30
        material_panel_width = 280
        material_panel_rect = pygame.Rect(60, panel_top, material_panel_width, 420)
        self._draw_panel_background(surface, material_panel_rect)

        title = self.font.render("Materials", True, (230, 230, 240))
        surface.blit(title, (material_panel_rect.left + 16, material_panel_rect.top + 16))

        y = material_panel_rect.top + 16 + title.get_height() + 12
        materials = sorted(
            self.inventory.iter_materials(),
            key=lambda item: material_name(item[0])
        )
        if not materials:
            empty = self.font.render("(None)", True, (200, 200, 210))
            surface.blit(empty, (material_panel_rect.left + 16, y))
            y += empty.get_height() + 8
        else:
            for material_id, qty in materials:
                label = f"{material_name(material_id)} x{qty}"
                label_surf = self.font.render(label, True, (220, 220, 230))
                surface.blit(label_surf, (material_panel_rect.left + 16, y))
                y += label_surf.get_height() + 8

        recipe_panel_left = material_panel_rect.right + 40
        recipe_panel_width = screen_rect.right - recipe_panel_left - 60
        recipe_panel_rect = pygame.Rect(
            recipe_panel_left,
            panel_top,
            recipe_panel_width,
            420,
        )
        self._draw_panel_background(surface, recipe_panel_rect)

        recipe_title = self.font.render("Recipes", True, (230, 230, 240))
        surface.blit(recipe_title, (recipe_panel_rect.left + 16, recipe_panel_rect.top + 16))

        self._recipe_buttons = []
        y = recipe_panel_rect.top + 16 + recipe_title.get_height() + 12
        button_height = self.font.get_height() + 12
        for recipe in self._ordered_recipes:
            rect = pygame.Rect(
                recipe_panel_rect.left + 16,
                y,
                recipe_panel_rect.width - 32,
                button_height,
            )
            craftable = self.inventory.has_materials(recipe.materials)
            fill = (40, 80, 45) if craftable else (80, 40, 40)
            if recipe.recipe_id == self._selected_recipe_id:
                fill = (70, 100, 140)
            surface.fill(fill, rect)
            pygame.draw.rect(surface, (20, 20, 30), rect, width=2)

            label = f"{recipe.name}"
            if not craftable:
                label += " (Missing)"
            label_surf = self.font.render(label, True, (245, 245, 245))
            surface.blit(label_surf, (rect.left + 12, rect.top + 6))

            self._recipe_buttons.append({
                "rect": rect,
                "recipe_id": recipe.recipe_id,
            })
            y += button_height + 8

        selected = self._selected_recipe()
        self._craft_button_rect = pygame.Rect(0, 0, 0, 0)
        details_top = recipe_panel_rect.bottom + 20
        if selected is not None:
            cost_text = ", ".join(
                f"{material_name(mid)} x{qty}" for mid, qty in selected.materials.items()
            ) or "No materials"
            cost_label = self.font.render(f"Cost: {cost_text}", True, (235, 235, 245))
            surface.blit(cost_label, (recipe_panel_rect.left, details_top))
            details_top += cost_label.get_height() + 12

            result = get_item(selected.output_item_id)
            result_label = self.font.render(
                f"Creates: {result.name}",
                True,
                (235, 235, 245),
            )
            surface.blit(result_label, (recipe_panel_rect.left, details_top))
            details_top += result_label.get_height() + 20

            craft_label = self.font.render("Craft Item", True, (0, 0, 0))
            btn_w = craft_label.get_width() + button_padding * 2
            btn_h = craft_label.get_height() + button_padding
            self._craft_button_rect = pygame.Rect(
                recipe_panel_rect.left,
                details_top,
                btn_w,
                btn_h,
            )
            craftable = self.inventory.has_materials(selected.materials)
            fill_color = (200, 200, 200) if craftable else (90, 90, 90)
            surface.fill(fill_color, self._craft_button_rect)
            pygame.draw.rect(surface, (50, 50, 50), self._craft_button_rect, 2)
            surface.blit(
                craft_label,
                craft_label.get_rect(center=self._craft_button_rect.center),
            )

        if self._message:
            msg_label = self.font.render(self._message, True, (250, 220, 120))
            msg_rect = msg_label.get_rect()
            msg_rect.midbottom = (
                screen_rect.centerx,
                screen_rect.bottom - 40,
            )
            surface.blit(msg_label, msg_rect)

    def _attempt_craft(self, recipe: SynthesisRecipe) -> None:
        if not self.inventory.has_materials(recipe.materials):
            self._message = "Missing required materials."
            return
        try:
            self.inventory.spend_materials(recipe.materials)
            try:
                self.inventory.add_item(recipe.output_item_id)
            except ValueError as exc:
                for material_id, qty in recipe.materials.items():
                    if qty > 0:
                        self.inventory.add_material(material_id, qty)
                self._message = str(exc)
                return
        except ValueError as exc:
            self._message = str(exc)
            return
        item = get_item(recipe.output_item_id)
        self._message = f"Created {item.name}!"

    def handle_event(self, event) -> bool:
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.controller.pop()
            return True
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self._back_button_rect.collidepoint(event.pos):
                self.controller.pop()
                return True
            for button in self._recipe_buttons:
                if button["rect"].collidepoint(event.pos):
                    recipe_id = button["recipe_id"]
                    if recipe_id != self._selected_recipe_id:
                        self._selected_recipe_id = recipe_id
                        self._message = None
                    return True
            if self._craft_button_rect and self._craft_button_rect.collidepoint(event.pos):
                selected = self._selected_recipe()
                if selected is None:
                    return True
                self._attempt_craft(selected)
                return True
        return False

    def update(self, dt):
        return None
