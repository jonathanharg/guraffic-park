
from entity import Entity


class Light(Entity):
    """
    Base class for maintaining a light source in the scene. Inheriting from Sphere allows to visualize the light
    source position easily.
    """

    def __init__(
        self,
        scene,
        Ia=[0.2, 0.2, 0.2],
        Id=[0.9, 0.9, 0.9],
        Is=[1.0, 1.0, 1.0],
        **kwargs
    ):
        """
        :param scene: The scene in which the light source exists.
        :param position: the position of the light source
        :param Ia: The ambiant illumination it provides (may not be dependent on the light source itself)
        :param Id: The diffuse illumination
        :param Is: The specular illumination
        :param visible: Whether the light should be represented as a sphere in the scene (default: False)
        """

        super().__init__(**kwargs)
        self.Ia = Ia
        self.Id = Id
        self.Is = Is
