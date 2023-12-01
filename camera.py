"""All of the various types of 3D cameras. Includes a base Camera,
free camera (first person camera) and an orbit camera.
"""

import imgui
import numpy as np
import pygame
import quaternion
from pygame.event import Event

from entity import Entity
from math_utils import translation_matrix


class Camera(Entity):
    """Base class for handling the camera."""

    def __init__(self, **kwargs):
        self.view_matrix = np.identity(4)
        super().__init__(**kwargs)

    def debug_menu(self):
        # Bad practice to import outside the top level, but necessary to avoid circular imports.
        from scene import Scene

        # Camera switcher
        scene = Scene.current_scene
        cameras = [scene.free_camera, scene.orbit_camera]

        current_camera = cameras.index(scene.camera)

        camera_changed, selected_index = imgui.combo(
            "Camera Mode",
            current_camera,
            [cam.__class__.__name__ for cam in cameras],
        )

        if camera_changed:
            scene.camera = cameras[selected_index]
        super().debug_menu()

    def update(self):
        """Update the camera view matrix"""
        # Invert the view matrix to give correct camera world coordinates & rotation
        # This means that the camera position and rotation will match 3D world space
        self.view_matrix = np.linalg.inv(
            np.matmul(self.world_translation(), self.world_rotation())
        )

    def handle_pygame_event(self, event: Event):
        pass


class FreeCamera(Camera):
    """A FreeCamera (first person camera), that can be aimed
    using the mouse and moved using W A S D.
    """

    def __init__(self, move_speed=10, **kwargs):
        """Create a FreeCamera.

        Args:
            move_speed (int, optional): Speed the camera moves in world space. Defaults to 10.
        """
        super().__init__(**kwargs)
        self.move_speed = move_speed

    def debug_menu(self):
        super().debug_menu()

        _, self.move_speed = imgui.slider_float(
            "Movement Speed", self.move_speed, 0.0, 1000.0
        )

    def update(self):
        from scene import Scene

        scene = Scene.current_scene

        # Ignore mouse events if we're interacting with the GUI
        if not scene.mouse_locked:
            return super().update()

        #
        # Mouse based movement
        #
        mouse_movement = pygame.mouse.get_rel()

        x_angle = float(mouse_movement[0]) * scene.x_sensitivity / 10000
        y_angle = float(mouse_movement[1]) * scene.y_sensitivity / 10000

        # The vector pointing right, relative to the camera.
        # We will rotate looking up/down about this vector
        right = np.cross(self.forwards, np.array([0, -1, 0]))
        right = right / np.linalg.norm(right)  # Normalise vector

        x_rotation_vector = np.array([0, -x_angle, 0])
        y_rotation_vector = right * y_angle

        x_quaternion_rotation = quaternion.from_rotation_vector(x_rotation_vector)
        y_quaternion_rotation = quaternion.from_rotation_vector(y_rotation_vector)

        self.rotation = y_quaternion_rotation * self.rotation
        self.rotation = x_quaternion_rotation * self.rotation

        #
        # Keyboard based movement
        #
        movement_vector = np.array([0, 0, 0])
        keys_pressed = pygame.key.get_pressed()
        shift_pressed = pygame.key.get_mods() & pygame.KMOD_SHIFT

        if keys_pressed[pygame.K_w]:
            movement_vector[2] -= 1
        if keys_pressed[pygame.K_s]:
            movement_vector[2] += 1
        if keys_pressed[pygame.K_a]:
            movement_vector[0] -= 1
        if keys_pressed[pygame.K_d]:
            movement_vector[0] += 1
        if keys_pressed[pygame.K_SPACE] and not shift_pressed:
            movement_vector[1] += 1
        if keys_pressed[pygame.K_SPACE] and shift_pressed:
            movement_vector[1] -= 1

        if np.linalg.norm(movement_vector) > 0:
            rotation_matrix = quaternion.as_rotation_matrix(self.rotation)
            self.position += np.matmul(
                rotation_matrix, self.move_speed * scene.delta_time * movement_vector
            )
        return super().update()


class OrbitCamera(Camera):
    def __init__(self, distance: float = 5.0, **kwargs):
        """Create and OrbitCamera.

        Args:
            distance (float, optional): Distance of the camera to the centre point. Defaults to 5.0.
        """
        super().__init__(**kwargs)
        self.distance = distance

    def update(self):
        # Calculate the view matrix for a regular camera
        from scene import Scene

        scene = Scene.current_scene

        # Ignore mouse events if we're interacting with the GUI
        if scene.mouse_locked:
            #
            # Mouse based movement
            #
            mouse_movement = pygame.mouse.get_rel()

            x_angle = float(mouse_movement[0]) * scene.x_sensitivity / 10000
            y_angle = float(mouse_movement[1]) * scene.y_sensitivity / 10000

            # The vector pointing right, relative to the camera. We will rotate looking up/down about this vector
            right = np.cross(self.forwards, np.array([0, -1, 0]))
            right = right / np.linalg.norm(right)  # Normalise vector

            x_rotation_vector = np.array([0, -x_angle, 0])
            y_rotation_vector = right * y_angle

            x_quaternion_rotation = quaternion.from_rotation_vector(x_rotation_vector)
            y_quaternion_rotation = quaternion.from_rotation_vector(y_rotation_vector)

            self.rotation = y_quaternion_rotation * self.rotation
            self.rotation = x_quaternion_rotation * self.rotation

        # Translate the camera distance units away from the regular camera
        translation = translation_matrix([0.0, 0.0, -self.distance])

        super().update()

        self.view_matrix = np.matmul(translation, self.view_matrix)

    def debug_menu(self):
        super().debug_menu()
        _, self.distance = imgui.slider_float("Distance", self.distance, 0.0, 50.0)

    def handle_pygame_event(self, event: Event):
        from scene import Scene

        scene = Scene.current_scene

        # Ignore mouse events if we're interacting with the GUI
        if not scene.mouse_locked:
            return

        # Use scroll to zoom in and out
        if event.type == pygame.MOUSEBUTTONDOWN:
            if (event.button) == 4:
                self.distance = max(1, self.distance - 1)

            elif event.button == 5:
                self.distance += 1
