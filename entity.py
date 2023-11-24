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
        self.__position__ = np.array(position, dtype=np.float32)
        self.__scale__ = scale
        self.children: list[Type["Entity"]] = []
        self.parent = parent

        if parent is not None:
            self.parent.children.append(self)

        self.__cache_world_pose__ = None
        self.__cache_world_translation__ = None
        self.__cache_world_rotation__ = None
        # Note. I use quaternions instead of a matrix to store rotation information
        # This is because I encountered some bugs when trying to implement animations
        # Interpolating between two quaternions is much easier, and allows for smooth animations
        # They also avoid euler angle related gimbal lock issues that I was encountering
        self.__rotation__ = (
            rotation if rotation is not None else np.quaternion(1.0, 0.0, 0.0, 0.0)
        )

        Entity.all_entities.append(self)

    @property
    def position(self):
        return self.__position__

    @position.setter
    def position(self, value):
        self.clear_entity_cache()
        self.__position__ = value

    @property
    def x(self) -> np.float32:
        return self.__position__[0]

    @x.setter
    def x(self, value: float):
        self.clear_entity_cache()
        self.__position__[0] = value  # type: ignore

    @property
    def y(self) -> np.float32:
        return self.__position__[1]

    @y.setter
    def y(self, value: float):
        self.clear_entity_cache()
        self.__position__[1] = value

    @property
    def z(self) -> np.float32:
        return self.__position__[2]

    @z.setter
    def z(self, value: float):
        self.clear_entity_cache()
        self.__position__[2] = value

    @property
    def rotation_matrix(self):
        rotation_matrix = np.identity(4)
        rotation_matrix[:3, :3] = quaternion.as_rotation_matrix(self.__rotation__)
        return rotation_matrix

    @property
    def rotation(self):
        return self.__rotation__

    @rotation.setter
    def rotation(self, value):
        self.clear_entity_cache()
        self.__rotation__ = value

    @property
    def scale(self):
        return self.__scale__

    @scale.setter
    def scale(self, value):
        self.clear_entity_cache()
        self.__scale__ = value

    def clear_entity_cache(self):
        # print(f"MOVED! Clearning cache for {self.__class__.__name__}")
        self.__cache_world_pose__ = None
        self.__cache_world_translation__ = None
        self.__cache_world_rotation__ = None

        for child in self.children:
            child.clear_entity_cache()

    @property
    def forwards(self):
        return np.matmul(
            quaternion.as_rotation_matrix(self.__rotation__), np.array([0, 0, -1])
        )

    @property
    def facing(self):
        forwards = self.forwards
        forwards[1] = 0
        return forwards / np.linalg.norm(forwards)

    def world_translation(self):
        if self.__cache_world_translation__ is not None:
            return self.__cache_world_translation__

        translation_matrix = translationMatrix(self.__position__)

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

        scale_matrix = scaleMatrix(self.__scale__)
        translation_matrix = translationMatrix(self.__position__)
        local_pose_matrix = np.matmul(
            translation_matrix, np.matmul(scale_matrix, self.rotation_matrix)
        )

        if self.parent is not None:
            local_pose_matrix = np.matmul(self.parent.world_pose, local_pose_matrix)

        self.__cache_world_pose__ = local_pose_matrix

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

        parent_name = None
        if self.parent is not None:
            parent_name = (
                self.parent.name
                if hasattr(self.parent, "name")
                else self.parent.__name__
            )

        child_names = list(
            map(lambda c: c.name if hasattr(c, "name") else c.__name__, self.children)
        )

        imgui.text(f"Parent: {parent_name}")
        imgui.text(f"Children: {child_names}")
