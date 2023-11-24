from typing import Self, Type

import imgui
import numpy as np
import quaternion

from matutils import scaleMatrix, translationMatrix


class Entity:
    all_entities: list[Self] = []

    def __init__(
        self,
        position: tuple[float, float, float] = (0.0, 0.0, 0.0),
        scale: float = 1.0,
        rotation=None,
        parent: Type["Entity"] | None = None,
    ) -> None:
        self.position = np.array(position, dtype=np.float32)
        self.scale = scale
        self.parent = parent
        self.__cache_world_pose__ = None
        self.__cache_world_translation__ = None
        self.__cache_world_rotation__ = None
        # Note. I use quaternions instead of a matrix to store rotation information
        # This is because I encountered some bugs when trying to implement animations
        # Interpolating between two quaternions is much easier, and allows for smooth animations
        # They also avoid euler angle related gimbal lock issues that I was encountering
        self.rotation = (
            rotation if rotation is not None else np.quaternion(1.0, 0.0, 0.0, 0.0)
        )

        Entity.all_entities.append(self)

        # print(f"Creating {self.__class__.__name__}({self.name if hasattr(self, "name") else ""}): {self.position} x{self.scale}")

    @property
    def x(self) -> np.float32:
        return self.position[0]

    @property
    def y(self) -> np.float32:
        return self.position[1]

    @property
    def z(self) -> np.float32:
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

    def world_translation(self):
        if self.__cache_world_translation__ is not None:
            return self.__cache_world_translation__

        translation_matrix = translationMatrix([self.x, self.y, self.z])

        # TODO: This should be parents pose matrix +
        if self.parent is not None:
            translation_matrix = np.matmul(
                self.parent.world_translation(), translation_matrix
            )

        self.__cache_world_translation__ = translation_matrix
        return translation_matrix

    def world_rotation(self):
        if self.__cache_world_rotation__ is not None:
            return self.__cache_world_rotation__

        if self.parent is None:
            self.__cache_world_rotation__ = self.rotation_matrix
            return self.__cache_world_rotation__
        else:
            world_rotation = np.matmul(
                self.parent.world_rotation(), self.rotation_matrix
            )
            self.__cache_world_rotation__ = world_rotation
            return world_rotation

    @property
    def world_pose(self):
        if self.__cache_world_pose__ is not None:
            return self.__cache_world_pose__

        scale_matrix = scaleMatrix(self.scale)
        translation_matrix = translationMatrix(self.position)
        local_pose_matrix = np.matmul(
            translation_matrix, np.matmul(scale_matrix, self.rotation_matrix)
        )

        if self.parent is not None:
            local_pose_matrix = np.matmul(self.parent.world_pose, local_pose_matrix)

        self.__cache_world_pose__ = local_pose_matrix

        return local_pose_matrix

    def clear_matrix_cache(self):
        self.__cache_world_pose__ = None
        self.__cache_world_translation__ = None
        self.__cache_world_rotation__ = None

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
