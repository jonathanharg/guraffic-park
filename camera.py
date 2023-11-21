import imgui
import numpy as np
import pygame
import quaternion
from pygame.event import Event

from entity import Entity
from matutils import rotationMatrixX, rotationMatrixY, translationMatrix


class Camera(Entity):
    """
    Base class for handling the camera.
    """

    def __init__(self, **kwargs):
        self.view_matrix = np.identity(4)
        super().__init__(**kwargs)

    def update(self):
        # Invert the view matrix to give correct camera world coordinates
        self.view_matrix = np.linalg.inv(
            np.matmul(
                self.get_world_translation_matrix(), self.get_world_rotation_matrix()
            )
        )

    def handle_pygame_event(self, event: Event):
        pass


class OrbitCamera(Camera):
    """
    Base class for handling the camera.
    TODO WS2: Implement this class to allow moving the mouse
    """

    def __init__(self, scene):
        self.view_matrix = np.identity(4)
        self.angle = 0.0  # azimuth angle
        self.altitude = 0.0  # zenith angle
        self.distance = 5.0  # distance of the camera to the centre point
        self.center = [0.0, 0.0, 0.0]  # position of the centre
        self.scene = scene
        self.update()  # calculate the view matrix

    def update(self):
        """
        Function to update the camera view matrix from parameters.
        first, we set the point we want to look at as centre of the coordinate system,
        then, we rotate the coordinate system according to phi and psi angles
        finally, we move the camera to the set distance from the point.
        """
        # TODO WS1
        # calculate the translation matrix for the view center (the point we look at)
        translation_0 = translationMatrix(self.center)

        # calculate the rotation matrix from the angles phi (azimuth) and psi (zenith) angles.
        rotation_matrix = np.matmul(
            rotationMatrixX(self.altitude), rotationMatrixY(self.angle)
        )

        # calculate translation for the camera distance to the center point
        translation_matrix = translationMatrix([0.0, 0.0, -self.distance])

        # finally we calculate the view matrix by combining the three matrices
        # The order matters!
        self.view_matrix = np.matmul(
            np.matmul(translation_matrix, rotation_matrix), translation_0
        )

    def debug_menu(self):
        # draw text label inside of current window
        imgui.text("Mode: Orbit")
        imgui.text(
            f"angle: {self.angle:.2f} altitude: {self.altitude:.2f} distance: {self.distance:.2f} center: {self.center}"
        )
        np.set_printoptions(precision=3, suppress=True)
        # imgui.text(f"Rotation Matrix:\n {rotation_matrix}")
        imgui.text(f"View Matrix:\n {self.view_matrix}")
        # imgui.text(f"Translation Matrix:\n {translation_matrix}")
        super().debug_menu()

    def handle_pygame_event(self, event: Event):
        # Ignore mouse events if we're interacting with the GUI
        if imgui.get_io().want_capture_mouse or not self.scene.mouse_locked:
            return

        mods = pygame.key.get_mods()
        mouse_movement = pygame.mouse.get_rel()
        ctrl_shift_or_alt_pressed = mods & (
            pygame.KMOD_ALT | pygame.KMOD_SHIFT | pygame.KMOD_CTRL
        )
        if event.type == pygame.MOUSEBUTTONDOWN and not ctrl_shift_or_alt_pressed:
            if (event.button) == 4:
                self.distance = max(1, self.distance - 1)

            elif event.button == 5:
                self.distance += 1

        elif event.type == pygame.MOUSEMOTION and not ctrl_shift_or_alt_pressed:
            if pygame.mouse.get_pressed()[2]:
                self.center[0] += (
                    float(mouse_movement[0])
                    / self.scene.window_size[0]
                    * self.scene.x_pan_amount
                )
                self.center[1] -= (
                    float(mouse_movement[1])
                    / self.scene.window_size[1]
                    * self.scene.y_pan_amount
                )

            else:
                self.angle -= (
                    float(mouse_movement[0]) / self.scene.window_size[0]
                ) * self.scene.x_sensitivity
                self.altitude -= (
                    float(mouse_movement[1]) / self.scene.window_size[1]
                ) * self.scene.y_sensitivity

                # Clamp the altitude to stop the camera from going upside down
                self.altitude = max(min(self.altitude, np.pi / 2), -np.pi / 2)


class NoclipCamera(Camera):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.move_speed = 10

    def debug_menu(self):
        imgui.text("Mode: Noclip")
        looking_at = np.matmul(
            quaternion.as_rotation_matrix(self.rotation), np.array([0, 0, -1])
        )
        imgui.text(f"looking at: {looking_at}")
        facing = looking_at.copy()
        facing[1] = 0
        facing = facing / np.sqrt(np.sum(facing**2))
        imgui.text(f"facing: {facing}")
        right = np.cross(looking_at, facing)
        imgui.text(f"right: {right} |r| {np.linalg.norm(right)}")

        super().debug_menu()

    def update(self):
        from scene import Scene

        scene = Scene.current_scene

        # Ignore mouse events if we're interacting with the GUI
        if not scene.mouse_locked:
            return super().update()

        mouse_movement = pygame.mouse.get_rel()
        keys_pressed = pygame.key.get_pressed()

        x_angle = float(mouse_movement[0]) * scene.x_sensitivity / 10000
        y_angle = float(mouse_movement[1]) * scene.y_sensitivity / 10000

        looking_at = np.matmul(
            quaternion.as_rotation_matrix(self.rotation), np.array([0, 0, -1])
        )
        # facing = looking_at.copy()
        # facing[1] = 0
        # facing = facing / np.sqrt(np.sum(facing**2))
        right = np.cross(looking_at, np.array([0, -1, 0]))

        x_vector = np.array([0, -1, 0]) * x_angle
        y_vector = right * y_angle
        quat_x = quaternion.from_rotation_vector(x_vector)
        quat_y = quaternion.from_rotation_vector(y_vector)
        self.rotation = quat_x * self.rotation
        self.rotation = quat_y * self.rotation

        direction_vector = np.array([0, 0, 0])  # .transpose()

        if keys_pressed[pygame.K_w]:
            direction_vector[2] -= 1
        if keys_pressed[pygame.K_s]:
            direction_vector[2] += 1
        if keys_pressed[pygame.K_a]:
            direction_vector[0] -= 1
        if keys_pressed[pygame.K_d]:
            direction_vector[0] += 1

        if np.linalg.norm(direction_vector) > 0:
            facing = quaternion.as_rotation_matrix(self.rotation)
            self.position = self.position + np.matmul(
                facing, self.move_speed * scene.delta_time * direction_vector
            )
        return super().update()
