"""Base class for a PyGame based OpenGL scene."""

from collections import deque
from typing import TYPE_CHECKING, Self, Type

import imgui
import numpy as np
import pygame
from imgui.integrations.pygame import PygameRenderer
from OpenGL import GL as gl

from camera import Camera, FreeCamera, OrbitCamera
from entity import Entity
from light import Light
from math_utils import frustrum_matrix

if TYPE_CHECKING:
    from model import Model


class Scene:
    """
    This is the main class for drawing an OpenGL scene using the PyGame library
    """

    current_scene: Self = None  # type: ignore

    def update_viewport(self):
        """Update the viewport if the window size, fov, or clipping planes are changed."""
        pygame.display.set_mode(
            self.window_size, pygame.OPENGL | pygame.DOUBLEBUF | pygame.RESIZABLE
        )
        gl.glViewport(0, 0, self.window_size[0], self.window_size[1])

        aspect_ratio = self.window_size[1] / self.window_size[0]

        # TODO: This should be in the camera class
        right = self.near_clipping * np.tan(self.fov * np.pi / 360.0)
        left = -right
        top = -right * aspect_ratio
        bottom = right * aspect_ratio

        self.projection_matrix = frustrum_matrix(
            left, right, top, bottom, self.near_clipping, self.far_clipping
        )

    def __init__(self, width=960, height=720):
        """Initialises the scene"""
        Scene.current_scene = self
        self.window_size = (width, height)
        self.wireframe = False
        self.fov = 90.0
        self.projection_matrix = None
        self.near_clipping = 0.5
        self.far_clipping = 1700.0
        self.x_sensitivity = 3
        self.y_sensitivity = 3
        self.fps_max = 300
        self.frame_times = deque(maxlen=100)
        self.clock: pygame.time.Clock = None
        self.delta_time = 0
        self.mouse_locked = True
        self.running = False

        pygame.init()

        # # TODO: REMOVE THIS, IT BUGS OUT IMGUI
        # pygame.display.gl_set_attribute(
        #     pygame.GL_CONTEXT_PROFILE_MASK, pygame.GL_CONTEXT_PROFILE_CORE
        # )
        # pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MAJOR_VERSION, 3)
        # pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MINOR_VERSION, 3)
        # pygame.display.gl_set_attribute(
        #     pygame.GL_CONTEXT_FLAGS, pygame.GL_CONTEXT_FORWARD_COMPATIBLE_FLAG
        # )
        # # TODO: REMOVE THIS, IT BUGS OUT IMGUI

        pygame.display.set_caption("Guraffic Park")
        pygame.display.set_icon(pygame.image.load("./textures/logo.png"))
        pygame.display.set_mode(
            self.window_size, pygame.OPENGL | pygame.DOUBLEBUF | pygame.RESIZABLE
        )

        # Stops the mouse from being able to leave the window
        pygame.event.set_grab(True)
        pygame.mouse.set_visible(False)

        # Center the mouse
        pygame.mouse.set_pos((self.window_size[0] / 2, self.window_size[1] / 2))

        # Print numpy matrices to a reasonable degree of accuracy for debugging
        np.set_printoptions(precision=3, suppress=True)

        # Create the GUI context
        imgui.create_context()
        self.imgui_impl = PygameRenderer()

        io = imgui.get_io()
        io.fonts.add_font_default()
        io.display_size = self.window_size

        self.update_viewport()

        # this selects the background color
        gl.glClearColor(0.0, 0.0, 0.0, 1.0)

        # enable back face culling (see lecture on clipping and visibility
        # TODO: UNCOMMENT

        # enable the vertex array capability
        # TODO: ONLY DISABLE THIS WHEN DEBUGING WITH RENDERDOC
        gl.glEnableClientState(gl.GL_VERTEX_ARRAY)

        # enable depth test for clean output (see lecture on clipping & visibility for an explanation
        gl.glEnable(gl.GL_DEPTH_TEST)

        # initialises the camera object
        self.orbit_camera = OrbitCamera()
        self.free_camera = FreeCamera()
        self.reflection_camera = Camera()
        self.camera = self.free_camera
        self.light = Light()

        # This will maintain a list of models to draw in the scene,
        self.models: list[Type["Model"]] = []

    def draw(self):
        """Draw all models in the scene"""
        # first we need to clear the scene, we also clear the depth buffer to handle occlusions
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)

        # ensure that the camera view matrix is up to date
        self.camera.update()

        # then we loop over all models in the list and draw them
        for model in self.models:
            model.draw()

        pygame.display.flip()

    def keyboard(self, event):
        """Method to process keyboard events.
        :param event: the event object that was raised
        """
        if event.key == pygame.K_q:
            self.running = False

        if event.key == pygame.K_ESCAPE and self.mouse_locked:
            # Allow the mouse to leave the window
            self.mouse_locked = False
            pygame.event.set_grab(False)
            pygame.mouse.set_visible(True)
            self.mouse_locked = False

    def run(self):
        """Method to handle PyGame events for user interaction."""
        # check whether the window has been closed
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            self.imgui_impl.process_event(event)

            if event.type == pygame.VIDEORESIZE:
                self.window_size = (event.w, event.h)
                self.update_viewport()

            if event.type == pygame.KEYDOWN:
                self.keyboard(event)

            self.camera.handle_pygame_event(event)

            if self.mouse_locked:
                # Re-center the mouse after every frame to stop it escaping
                pygame.mouse.set_pos((self.window_size[0] / 2, self.window_size[1] / 2))
            else:
                if (
                    not imgui.get_io().want_capture_mouse
                ) and pygame.mouse.get_pressed()[0]:
                    # We've clicked on the 3D scene and not the UI so grab the mouse
                    pygame.event.set_grab(True)
                    pygame.mouse.set_visible(False)
                    self.mouse_locked = True

    def debug_menu(self):
        """Define the debug menu for this class. Uses the ImGui library to construct a UI. Calling this function inside an ImGui context will render this debug menu."""

    def start(self):
        """Draws the scene in a loop until exit."""
        self.running = True
        self.clock = pygame.time.Clock()

        while self.running:
            # Calculate frame time
            self.delta_time = self.clock.tick(self.fps_max) / 1000
            self.frame_times.append(self.clock.get_time())

            self.run()

            # Generate GUI
            self.imgui_impl.process_inputs()
            imgui.new_frame()
            self.debug_menu()

            gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)

            self.draw()

            # Render GUI
            imgui.render()
            self.imgui_impl.render(imgui.get_draw_data())

            for entity in Entity.all_entities:
                entity.clear_entity_cache()
            pygame.display.flip()
