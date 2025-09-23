import pygame


class Scene:
    def update(self, dt):
        return None

    def handle_event(self, event) -> bool:
        return False

    def draw(self, surface):
        return None

    def blocks_update(self) -> bool:
        return True

    def blocks_input(self) -> bool:
        return True

    def blocks_draw(self) -> bool:
        return True


class Manager:
    class Controller:
        def __init__(self, manager: "Manager") -> None:
            self._manager = manager

        def replace(self, scene: Scene | None) -> None:
            self._manager.set_scene(scene)

        def push(self, scene: Scene) -> None:
            self._manager.push_scene(scene)

        def pop(self) -> None:
            self._manager.pop_scene()

    def __init__(self, initial_scene: Scene | None = None):
        self._stack: list[Scene] = []
        self._controller = Manager.Controller(self)
        if initial_scene is not None:
            self.set_scene(initial_scene)

    @property
    def controller(self) -> "Manager.Controller":
        return self._controller

    def set_scene(self, scene: Scene | None) -> None:
        self._stack.clear()
        if scene is not None:
            self._stack.append(scene)

    def push_scene(self, scene: Scene) -> None:
        if scene is not None:
            self._stack.append(scene)

    def pop_scene(self) -> None:
        if self._stack:
            self._stack.pop()

    def update(self, dt) -> None:
        if not self._stack:
            return
        start_index = 0
        for idx in range(len(self._stack) - 1, -1, -1):
            if self._stack[idx].blocks_update():
                start_index = idx
                break
        for scene in self._stack[start_index:]:
            scene.update(dt)

    def handle_event(self, event) -> None:
        for scene in reversed(self._stack):
            handled = scene.handle_event(event)
            if handled or scene.blocks_input():
                break

    def draw(self, surface) -> None:
        if not self._stack:
            return
        start_index = 0
        for idx in range(len(self._stack) - 1, -1, -1):
            if self._stack[idx].blocks_draw():
                start_index = idx
                break
        for scene in self._stack[start_index:]:
            scene.draw(surface)


class MainMenu(Scene):
    def __init__(self, font, *, controller: Manager.Controller):
        self.font = font
        self.controller = controller

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

    def handle_event(self, event) -> bool:
        if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
            # Lazy import to avoid circular dependency during module import.
            from core.scenes.battle_scene import BattleScene

            self.controller.replace(
                BattleScene(self.font, controller=self.controller)
            )
            return True
        return False
