"""
3D Entity management.
"""

from typing import Self, Type

import imgui
import numpy as np
import quaternion

from math_utils import scale_matrix, translation_matrix


def get_name(entity):
    """Safely get the name of an Entity"""
    if hasattr(entity, "name"):
        return entity.name
    if hasattr(entity, "__name__"):
        return entity.__name__
    if hasattr(entity.__class__, "__name__"):
        return entity.__class__.__name__
    return "Unknown"


class Entity:
    """
    The Entity class. Anything in the 3D world is represented by an Entity.
    An entity has a world position, rotation and scale. Each entity can also have one parent, and many children.
    A parents location, rotation and scale will influence its children.
    """

    all_entities: list[Self] = []

    def __init__(
        self,
        position: tuple[float, float, float] = (0.0, 0.0, 0.0),
        scale: float = 1.0,
        rotation=None,
        parent: Type["Entity"] | None = None,
    ) -> None:
        # Raw position, scale and rotation values aren't publicly accessible. This is so we can cache them.
        self.__position__ = np.array(position, dtype=np.float32)
        self.__scale__ = scale

        self.children: list[Type["Entity"]] = []
        self.parent = parent

        if parent is not None:
            self.parent.children.append(self)

        # We cache all world matrices so they aren't re-calculated unless something changes.
        self.__cache_world_pose__ = None
        self.__cache_world_translation__ = None
        self.__cache_world_rotation__ = None

        # NOTE: I use quaternions instead of a matrix to store rotation information
        # Interpolating between two quaternions is much easier, and allows for smooth animations
        # They also avoid euler angle related gimbal lock issues that I was encountering
        # To learn more about quaternions for 3D rotations, here is a paper I wrote on them https://jonathanharg.dev/projects/ee

        self.__rotation__ = (
            rotation
            if rotation is not None
            else np.quaternion(1.0, 0.0, 0.0, 0.0)  # Equivalent to no rotation
        )

        Entity.all_entities.append(self)

    # We use properties so that the position can be access like usual
    @property
    def position(self):
        return self.__position__

    # Properties mean we can clear the cache if the position is updated
    @position.setter
    def position(self, value):
        self.clear_entity_cache()
        self.__position__ = np.array(value, dtype=np.float32)

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
        """Clear the location, rotation, scale cache for the entity. You should not need to call this outside entity.py"""
        self.__cache_world_pose__ = None
        self.__cache_world_translation__ = None
        self.__cache_world_rotation__ = None

        for child in self.children:
            child.clear_entity_cache()

    @property
    def forwards(self):
        """The forwards vector for this entity. Where the entity is 'looking'"""
        return np.matmul(
            quaternion.as_rotation_matrix(self.__rotation__), np.array([0, 0, -1])
        )

    @property
    def facing(self):
        """The vector this entity is facing. Relative to the upwards direction of the world"""
        forwards = self.forwards
        forwards[1] = 0
        return forwards / np.linalg.norm(forwards)

    def world_translation(self):
        """Get the world translation matrix for this entity."""
        if self.__cache_world_translation__ is not None:
            return self.__cache_world_translation__

        translation = translation_matrix(self.__position__)

        if self.parent is not None:
            translation = np.matmul(self.parent.world_translation(), translation)

        self.__cache_world_translation__ = translation
        return translation

    def world_rotation(self):
        """Get the world rotation matrix for this entity"""
        if self.__cache_world_rotation__ is not None:
            return self.__cache_world_rotation__

        if self.parent is None:
            self.__cache_world_rotation__ = self.rotation_matrix
            return self.__cache_world_rotation__

        world_rotation = np.matmul(self.parent.world_rotation(), self.rotation_matrix)
        self.__cache_world_rotation__ = world_rotation
        return world_rotation

    @property
    def world_pose(self):
        """Get the world pose matrix for this entity"""
        if self.__cache_world_pose__ is not None:
            return self.__cache_world_pose__

        scale = scale_matrix(self.__scale__)
        translation = translation_matrix(self.__position__)
        local_pose_matrix = np.matmul(
            translation, np.matmul(scale, self.rotation_matrix)
        )

        if self.parent is not None:
            local_pose_matrix = np.matmul(self.parent.world_pose, local_pose_matrix)

        self.__cache_world_pose__ = local_pose_matrix

        return local_pose_matrix

    def debug_menu(self):
        """
        Define the debug menu for this class. Uses the ImGui library to construct a UI. Calling this function inside an ImGui context will render this debug menu.
        """
        _, self.position = imgui.drag_float3(
            "Position", self.x, self.y, self.z, change_speed=0.1
        )

        imgui.text(f"Forwards: {self.forwards}")
        imgui.text(f"Facing: {self.facing}")

        angles = quaternion.as_euler_angles(self.rotation)

        # This is slightly buggy due to the nature of quaternions being 4 dimensional. But good enough for debugging/testing
        z_rot_changed, new_z_rot = imgui.slider_angle("Z Rotation", angles[2])
        y_rot_changed, new_y_rot = imgui.slider_angle("Y Rotation", angles[1])
        x_rot_changed, new_x_rot = imgui.slider_angle("X Rotation", angles[0])

        if x_rot_changed or y_rot_changed or z_rot_changed:
            self.rotation = quaternion.from_euler_angles(
                new_x_rot, new_y_rot, new_z_rot
            )

        _, scale = imgui.drag_float("Scale", self.scale, change_speed=0.1)
        self.scale = scale if scale != 0 else 0.0001

        imgui.text(
            f"Parent: {get_name(self.parent) if self.parent is not None else None}"
        )
        imgui.text(f"Children: {list(map(get_name,self.children))}")
