import numpy as np

from matutils import scaleMatrix, translationMatrix


class Entity:
    def __init__(
        self,
        position: tuple[float, float, float] = (0.0, 0.0, 0.0),
        scale: float = 1.0,
        rotation=None,
    ) -> None:
        self.position = position
        self.scale = scale
        # self.enable_shadow_casting = True
        self.rotation = rotation if rotation is not None else np.identity(4)

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

    def get_translation_matrix(self):
        return translationMatrix([self.x, self.y, self.z])

    def get_scale_matrix(self):
        return scaleMatrix(self.scale)

    def get_pose_matrix(self):
        return np.matmul(
            np.matmul(self.get_translation_matrix(), self.rotation),
            self.get_scale_matrix(),
        )
