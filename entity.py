from typing import Self

import numpy as np

from matutils import scaleMatrix, translationMatrix


class Entity:
    def __init__(
        self,
        position: tuple[float, float, float] = (0.0, 0.0, 0.0),
        scale: float = 1.0,
        rotation=None,
        parent: Self = None,
    ) -> None:
        self.position = position
        self.scale = scale
        self.parent = parent
        self.rotation = rotation if rotation is not None else np.identity(4)

        # print(f"Creating {self.__class__.__name__}({self.name if hasattr(self, "name") else ""}): {self.position} x{self.scale}")

    @property
    def x(self):
        return self.position[0]

    @property
    def y(self):
        return self.position[1]

    @property
    def z(self):
        return self.position[2]

    def x_rot(self):
        return np.arctan2(self.rotation[1, 2], self.rotation[2, 2])

    def y_rot(self):
        return np.arctan2(
            -self.rotation[0, 2],
            np.sqrt(self.rotation[1, 2] ** 2 + self.rotation[2, 2] ** 2),
        )

    def z_rot(self):
        return np.arctan2(self.rotation[0, 1], self.rotation[0, 0])

    @x.setter
    def x(self, value: float):
        self.position = (value, self.y, self.z)

    @y.setter
    def y(self, value: float):
        self.position = (self.x, value, self.z)

    @z.setter
    def z(self, value: float):
        self.position = (self.x, self.y, value)

    # TODO: Clean this up
    def get_world_translation_matrix(self):
        translation_matrix = translationMatrix([self.x, self.y, self.z])

        if self.parent is not None:
            translation_matrix = np.matmul(
                self.parent.get_world_translation_matrix(), translation_matrix
            )

        return translation_matrix

    def get_world_scale_matrix(self):
        scale_matrix = scaleMatrix(self.scale)

        if self.parent is not None:
            scale_matrix = np.matmul(self.parent.get_world_scale_matrix(), scale_matrix)

        return scale_matrix

    def get_world_rotation_matrix(self):
        if self.parent is None:
            return self.rotation
        else:
            return np.matmul(self.parent.get_world_rotation_matrix(), self.rotation)

    def get_world_pose_matrix(self):
        pose_matrix = np.matmul(
            np.matmul(
                self.get_world_translation_matrix(), self.get_world_rotation_matrix()
            ),
            self.get_world_scale_matrix(),
        )

        return pose_matrix
