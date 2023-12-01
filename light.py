"""
Contains the class for a 3D light entity.
"""

import imgui
import numpy as np

from entity import Entity


class Light(Entity):
    """
    Base class for maintaining a light source in the scene. By default lights are
    rendered as directional lights, which are infinitely far away (like the sun).
    The position of the light represents its direction.
    """

    def __init__(
        self,
        ambient_illumination=(0.2, 0.2, 0.2),
        diffuse_illumination=(0.5, 0.5, 0.5),
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
        ambient_changed, ambient_values = imgui.slider_float3(
            "Ambient",
            self.ambient_illumination[0],
            self.ambient_illumination[1],
            self.ambient_illumination[2],
            min_value=0.0,
            max_value=1.0,
        )
        diffuse_changed, diffuse_values = imgui.slider_float3(
            "Diffuse",
            self.diffuse_illumination[0],
            self.diffuse_illumination[1],
            self.diffuse_illumination[2],
            min_value=0.0,
            max_value=1.0,
        )
        specular_changed, specular_values = imgui.slider_float3(
            "Specular",
            self.specular_illumination[0],
            self.specular_illumination[1],
            self.specular_illumination[2],
            min_value=0.0,
            max_value=1.0,
        )

        if ambient_changed:
            self.ambient_illumination = np.array(ambient_values, dtype=np.float32)

        if diffuse_changed:
            self.diffuse_illumination = np.array(diffuse_values, dtype=np.float32)

        if specular_changed:
            self.specular_illumination = np.array(specular_values, dtype=np.float32)

        return super().debug_menu()
