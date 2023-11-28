import numpy as np

from entity import Entity


class DirectionalLight(Entity):
    """
    Base class for maintaining a light source in the scene. Inheriting from Sphere allows to visualize the light
    source position easily.
    """

    def __init__(
        self,
        ambient_illumination=(0.2, 0.2, 0.2),
        diffuse_illumination=(0.9, 0.9, 0.9),
        specular_illumination=(1.0, 1.0, 1.0),
    ):
        """
        :param scene: The scene in which the light source exists.
        :param position: the position of the light source
        :param Ia: The ambiant illumination it provides (may not be dependent on the light source itself)
        :param Id: The diffuse illumination
        :param Is: The specular illumination
        """
        self.ambient_illumination = np.array(ambient_illumination, dtype=np.float32)
        self.diffuse_illumination = np.array(diffuse_illumination, dtype=np.float32)
        self.specular_illumination = np.array(specular_illumination, dtype=np.float32)
        super().__init__(position=(0, 0, -1))

    def debug_menu(self):
        return super().debug_menu()
