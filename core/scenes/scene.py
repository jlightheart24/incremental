import pygame


class Scene:
    def update(self, dt):
        pass

    def handle_event(self, event):
        pass

    def draw(self, surface):
        pass


class Manager:
    def __init__(self, initial_scene: Scene):
        self.current_scene = initial_scene

    def set_scene(self, scene: Scene):
        self.current_scene = scene

    def update(self, dt):
        self.current_scene.update(dt)

    def handle_event(self, event):
        self.current_scene.handle_event(event)

    def draw(self, surface):
        self.current_scene.draw(surface)


class MainMenu(Scene):
    def __init__(self, font, *, change_scene):
        self.font = font
        self.change_scene = change_scene

    def draw(self, surface):
        screen_rect = surface.get_rect()
        surface.fill((30, 30, 30))
        title = self.font.render(
            "Main Menu - Press Enter to Start Battle",
            True,
            (255, 255, 255),
        )
        title_rect = title.get_rect(center=screen_rect.center)
        surface.blit(title, title_rect)

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
            # Lazy import to avoid circular dependency during module import.
            from core.scenes.battle_scene import BattleScene

            self.change_scene(
                BattleScene(self.font, change_scene=self.change_scene)
            )
