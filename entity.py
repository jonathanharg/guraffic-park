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

    @property
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

    @property
    def forwards(self):
        return np.matmul(
            quaternion.as_rotation_matrix(self.rotation), np.array([0, 0, -1])
        )

    @property
    def facing(self):
        forwards = self.forwards
        forwards[1] = 0
        return forwards / np.linalg.norm(forwards)

    # TODO: Clean this up
    def world_translation(self):
        translation_matrix = translationMatrix([self.x, self.y, self.z])

        # TODO: This should be parents pose matrix +
        if self.parent is not None:
            translation_matrix = np.matmul(
                self.parent.world_translation(), translation_matrix
            )

        return translation_matrix

    # TODO: DO WE NEED THIS TOO?
    def world_rotation(self):
        if self.parent is None:
            return self.rotation_matrix
        else:
            return np.matmul(self.parent.world_rotation(), self.rotation_matrix)

    @property
    def world_pose(self):
        scale_matrix = scaleMatrix(self.scale)
        translation_matrix = translationMatrix(self.position)
        local_pose_matrix = np.matmul(
            translation_matrix, np.matmul(scale_matrix, self.rotation_matrix)
        )

        if self.parent is not None:
            local_pose_matrix = np.matmul(self.parent.world_pose, local_pose_matrix)

        return local_pose_matrix

    def debug_menu(self):
        _, self.position = imgui.drag_float3(
            "Position", self.x, self.y, self.z, change_speed=0.1
        )

        imgui.text(f"Forwards: {self.forwards}")
        imgui.text(f"Facing: {self.facing}")

        angles = quaternion.as_euler_angles(self.rotation)

        z_rot_changed, new_z_rot = imgui.slider_angle("Z Rotation", angles[2])
        y_rot_changed, new_y_rot = imgui.slider_angle("Y Rotation", angles[1])
        x_rot_changed, new_x_rot = imgui.slider_angle("X Rotation", angles[0])

        if x_rot_changed or y_rot_changed or z_rot_changed:
            self.rotation = quaternion.from_euler_angles(
                new_x_rot, new_y_rot, new_z_rot
            )

        _, scale = imgui.drag_float("Scale", self.scale, change_speed=0.1)
        self.scale = scale if scale != 0 else 0.0001
