
class Entity:
    def __init__(self, position: tuple[float, float, float] = (0,0,0)) -> None:
        self.position = position
    
    @property
    def x(self):
        return self.position[0]
    
    @property
    def y(self):
        return self.position[1]
    
    @property
    def z(self):
        return self.position[2]
    
    @x.setter
    def x(self, value: float):
        self.position = (value, self.y, self.z)
    
    @y.setter
    def y(self, value: float):
        self.position = (self.x, value, self.z)
    
    @z.setter
    def z(self, value: float):
        self.position = (self.x, self.y, value)