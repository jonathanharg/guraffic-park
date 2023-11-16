# import a bunch of useful matrix functions (for translation, scaling etc)
import numpy as np
import pygame
import imgui
from pygame.event import Event

from matutils import rotationAxisAngle, rotationMatrixX, rotationMatrixY, translationMatrix


class Camera:
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

        # open new window context
        if self.scene.debug_camera:
            _, self.scene.debug_camera = imgui.begin("Camera", True)

            # draw text label inside of current window
            imgui.text("Mode: Orbit")
            imgui.text(f"angle: {self.angle:.2f} altitude: {self.altitude:.2f} distance: {self.distance:.2f} center: {self.center}")
            np.set_printoptions(precision=3, suppress=True)
            imgui.text(f"Rotation Matrix:\n {rotation_matrix}")
            imgui.text(f"View Matrix:\n {self.view_matrix}")
            imgui.text(f"Translation Matrix:\n {translation_matrix}")

            # close current window context
            imgui.end()

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
                self.angle += (
                    float(mouse_movement[0]) / self.scene.window_size[0]
                ) * self.scene.x_sensitivity
                self.altitude -= (
                    float(mouse_movement[1]) / self.scene.window_size[1]
                ) * self.scene.y_sensitivity

                # Clamp the altitude to stop the camera from going upside down
                self.altitude = max(min(self.altitude, np.pi / 2), -np.pi / 2)


class NoclipCamera:
    def __init__(self, scene):
        self.view_matrix = np.identity(4)
        self.angle = 0.0  # azimuth angle
        self.altitude = 0.0  # zenith angle
        self.distance = 5.0  # distance of the camera to the centre point
        self.center = [0.0, 0.0, 0.0]  # position of the centre
        self.scene = scene
        self.rotation_matrix = np.matmul(rotationMatrixX(0), rotationMatrixY(0))
        self.x = 0
        self.y = 0.0
        self.z = -7.5
        self.update()  # calculate the view matrix

    def update(self):
        self.translation_matrix = translationMatrix([self.x,self.y,self.z])
        self.view_matrix = np.matmul(self.rotation_matrix, self.translation_matrix)

        if self.scene.debug_camera:
            # open new window context
            _, self.scene.debug_camera = imgui.begin("Camera", True)

            # draw text label inside of current window
            imgui.text("Mode: Noclip")
            imgui.text(f"x: {self.x:.2f} y: {self.y:.2f} z: {self.z:.2f}")
            np.set_printoptions(precision=3, suppress=True)
            imgui.text(f"Rotation Matrix:\n {self.rotation_matrix}")
            imgui.text(f"View Matrix:\n {self.view_matrix}")
            imgui.text(f"Translation Matrix:\n {self.translation_matrix}")

            # close current window context
            imgui.end()


    def handle_pygame_event(self, event: Event):
        # Ignore mouse events if we're interacting with the GUI
        if imgui.get_io().want_capture_mouse or not self.scene.mouse_locked:
            return
        
        mods = pygame.key.get_mods()
        mouse_movement = pygame.mouse.get_rel()
        ctrl_shift_or_alt_pressed = mods & (
            pygame.KMOD_ALT | pygame.KMOD_SHIFT | pygame.KMOD_CTRL
        )
        keys_pressed = pygame.key.get_pressed()

        if event.type == pygame.MOUSEMOTION and not ctrl_shift_or_alt_pressed:
            x_angle = -(float(mouse_movement[0]) / self.scene.window_size[0]) * self.scene.x_sensitivity
            y_angle = -(float(mouse_movement[1]) / self.scene.window_size[1]) * self.scene.y_sensitivity
            self.rotation_matrix = np.matmul(self.rotation_matrix, rotationAxisAngle([0,1,0], x_angle))
            self.rotation_matrix = np.matmul(rotationAxisAngle([1,0,0], y_angle), self.rotation_matrix)
        
        # test_matrix = self.rotation_matrix
        # test_matrix = np.linalg.inv(self.rotation_matrix)[:3, :3].transpose()
        # relative_forward_vector = np.matmul(test_matrix, [0,0,1])
        # relative_left_vector = np.matmul(test_matrix, [1,0,0])

        if keys_pressed[pygame.K_w]:
            self.z += 8 * self.scene.delta_time
            # self.x += relative_forward_vector[0]
            # self.y += relative_forward_vector[1]
            # self.z += relative_forward_vector[2]
        if keys_pressed[pygame.K_s]:
            self.z -= 8 * self.scene.delta_time
            # self.x -= relative_forward_vector[0]
            # self.y -= relative_forward_vector[1]
            # self.z -= relative_forward_vector[2]
        if keys_pressed[pygame.K_d]:
            self.x -= 8 * self.scene.delta_time
            # self.x -= relative_left_vector[0]
            # self.y -= relative_left_vector[1]
            # self.z -= relative_left_vector[2]
        if keys_pressed[pygame.K_a]:
            self.x += 8 * self.scene.delta_time
            # self.x += relative_left_vector[0]
            # self.y += relative_left_vector[1]
            # self.z += relative_left_vector[2]
