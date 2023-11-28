import imgui
import numpy as np
import pygame
import quaternion
from pygame.event import Event

from entity import Entity
from matutils import translation_matrix


class Camera(Entity):
    """
    Base class for handling the camera.
    """

    def __init__(self, **kwargs):
        self.view_matrix = np.identity(4)
        super().__init__(**kwargs)

    def debug_menu(self):
        imgui.text(f"Mode: {self.__class__.__name__}")
        super().debug_menu()

    def update(self):
        # Invert the view matrix to give correct camera world coordinates & rotation
        # This means that the camera position and rotation is considered to be in 3D world space
        self.view_matrix = np.linalg.inv(
            np.matmul(self.world_translation(), self.world_rotation())
        )

    def handle_pygame_event(self, event: Event):
        pass


class FreeCamera(Camera):
    def __init__(self, move_speed=10, **kwargs):
        super().__init__(**kwargs)
        self.move_speed = move_speed

    def debug_menu(self):
        super().debug_menu()

        right = np.cross(self.forwards, self.facing)
        right = right / np.linalg.norm(right)  # Normalise vector
        imgui.text(f"Right: {right}")

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

        # The vector pointing right, relative to the camera. We will rotate looking up/down about this vector
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
        movement_vector = np.array([0, 0, 0])  # .transpose()
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
            self.position = self.position + np.matmul(
                rotation_matrix, self.move_speed * scene.delta_time * movement_vector
            )
        return super().update()


class OrbitCamera(FreeCamera):
    def __init__(self, distance: float = 5.0, **kwargs):
        super().__init__(**kwargs)
        self.distance = distance  # distance of the camera to the centre point

    def update(self):
        # Calculate the view matrix for a regular camera
        super().update()
        # Translate the camera distance units away from the regular camera
        translation = translation_matrix([0.0, 0.0, -self.distance])
        self.view_matrix = np.matmul(translation, self.view_matrix)

    def debug_menu(self):
        super().debug_menu()
        imgui.text(f"Distance: {self.distance}")

    def handle_pygame_event(self, event: Event):
        from scene import Scene

        scene = Scene.current_scene

        # Ignore mouse events if we're interacting with the GUI
        if not scene.mouse_locked:
            return

        if event.type == pygame.MOUSEBUTTONDOWN:
            if (event.button) == 4:
                self.distance = max(1, self.distance - 1)

            elif event.button == 5:
                self.distance += 1
