from typing import Self

import imgui
import numpy as np
import quaternion

from matutils import scaleMatrix, translationMatrix


class Entity:
    def __init__(
        self,
        position: tuple[float, float, float] = (0.0, 0.0, 0.0),
        scale: float = 1.0,
        rotation=None,
        parent: Self | None = None,
    ) -> None:
        self.position = np.array(position, dtype=np.float32)
        self.scale = scale
        self.parent = parent
        # Note. I use quaternions instead of a matrix to store rotation information
        # This is because I encountered some bugs when trying to implement animations
        # Interpolating between two quaternions is much easier, and allows for smooth animations
        # They also avoid euler angle related gimbal lock issues that I was encountering
        self.rotation = (
            rotation if rotation is not None else np.quaternion(1.0, 0.0, 0.0, 0.0)
        )

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

    # TODO: Make this a property?
    def rotation_matrix(self):
        rotation_matrix = np.identity(4)
        rotation_matrix[:3, :3] = quaternion.as_rotation_matrix(self.rotation)
        return rotation_matrix

    @x.setter
    def x(self, value: float):
        self.position[0] = value  # type: ignore

    @y.setter
    def y(self, value: float):
        self.position[1] = value

    @z.setter
    def z(self, value: float):
        self.position[2] = value

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
            return self.rotation_matrix()
        else:
            return np.matmul(
                self.parent.get_world_rotation_matrix(), self.rotation_matrix()
            )

    def get_world_pose_matrix(self):
        pose_matrix = np.matmul(
            np.matmul(
                self.get_world_translation_matrix(), self.get_world_rotation_matrix()
            ),
            self.get_world_scale_matrix(),
        )

        return pose_matrix

    def debug_menu(self):
        _, self.position = imgui.drag_float3(
            "Position", self.x, self.y, self.z, change_speed=0.1
        )

        angles = quaternion.as_euler_angles(self.rotation)

        z_rot_changed, new_z_rot = imgui.slider_float(
            "Z Rotation", angles[2], -2 * np.pi, 2 * np.pi
        )
        y_rot_changed, new_y_rot = imgui.slider_float(
            "Y Rotation", angles[1], -2 * np.pi, 2 * np.pi
        )
        x_rot_changed, new_x_rot = imgui.slider_float(
            "X Rotation", angles[0], -2 * np.pi, 2 * np.pi
        )

        if x_rot_changed or y_rot_changed or z_rot_changed:
            self.rotation = quaternion.from_euler_angles(
                new_x_rot, new_y_rot, new_z_rot
            )

        _, scale = imgui.drag_float("Scale", self.scale, change_speed=0.1)
        self.scale = scale if scale != 0 else 0.0001
