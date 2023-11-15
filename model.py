from entity import Entity


class Model(Entity):
    def __init__(self, position: tuple[float, float, float] = (0, 0, 0)) -> None:
        super().__init__(position)
        self.visible = True
