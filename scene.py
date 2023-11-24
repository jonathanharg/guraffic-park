import cProfile
import pstats
import stat
from typing import TYPE_CHECKING, Self, Type

import imgui
import numpy as np
import pygame
from imgui.integrations.pygame import PygameRenderer
from OpenGL import GL as gl

from camera import Camera
from entity import Entity
from matutils import frustumMatrix
from shaders import ALL_SHADERS

if TYPE_CHECKING:
    from model import Model


class Scene:
    """
    This is the main class for drawing an OpenGL scene using the PyGame library
    """

    current_scene: Self = None  # type: ignore

    def update_viewport(self):
        pygame.display.set_mode(
            self.window_size, pygame.OPENGL | pygame.DOUBLEBUF | pygame.RESIZABLE
        )
        gl.glViewport(0, 0, self.window_size[0], self.window_size[1])

        aspect_ratio = self.window_size[1] / self.window_size[0]

        # TODO: Move this into camera class
        right = self.near_clipping * np.tan(self.fov * np.pi / 360.0)
        left = -right
        top = -right * aspect_ratio
        bottom = right * aspect_ratio

        # to start with, we use an orthographic projection; change this.
        # self.P = frustumMatrix(left, right, top, bottom, near, far)
        self.projection_matrix = frustumMatrix(
            left, right, top, bottom, self.near_clipping, self.far_clipping
        )

    def __init__(self, width=960, height=720):
        """
        Initialises the scene
        """
        Scene.current_scene = self
        self.window_size = (width, height)
        self.wireframe = False
        self.fov = 90.0
        self.projection_matrix = None
        self.near_clipping = 0.5
        self.far_clipping = 1000.0
        self.x_sensitivity = 3
        self.y_sensitivity = 3
        self.fps_max = 300
        self.clock = pygame.time.Clock()
        self.delta_time = 0
        self.mouse_locked = True
        self.show_imgui_demo = False
        self.running = False

        pygame.init()

        # # TODO: REMOVE THIS, IT BUGS OUT IMGUI
        pygame.display.gl_set_attribute(
            pygame.GL_CONTEXT_PROFILE_MASK, pygame.GL_CONTEXT_PROFILE_CORE
        )
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MAJOR_VERSION, 3)
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MINOR_VERSION, 3)
        pygame.display.gl_set_attribute(
            pygame.GL_CONTEXT_FLAGS, pygame.GL_CONTEXT_FORWARD_COMPATIBLE_FLAG
        )
        # # TODO: REMOVE THIS, IT BUGS OUT IMGUI

        pygame.display.set_mode(
            self.window_size, pygame.OPENGL | pygame.DOUBLEBUF | pygame.RESIZABLE
        )
        # Stops the mouse from being able to leave the window
        pygame.event.set_grab(True)
        pygame.mouse.set_visible(False)
        # Increase key repeat window, Makes WASD movement smoother
        pygame.key.set_repeat(0)
        # Center the mouse
        pygame.mouse.set_pos((self.window_size[0] / 2, self.window_size[1] / 2))

        # Print numpy matrices to a reasonable degree of accuracy for debugging
        np.set_printoptions(precision=3, suppress=True)

        imgui.create_context()
        self.imgui_impl = PygameRenderer()

        io = imgui.get_io()
        io.fonts.add_font_default()
        io.display_size = self.window_size

        self.update_viewport()

        # this selects the background color
        gl.glClearColor(0.0, 0.0, 0.0, 1.0)

        # enable back face culling (see lecture on clipping and visibility
        gl.glEnable(gl.GL_CULL_FACE)
        # depending on your model, or your projection matrix, the winding order may be inverted,
        # Typically, you see the far side of the model instead of the front one
        # uncommenting the following line should provide an easy fix.
        # gl.glCullFace(gl.GL_FRONT)

        # enable the vertex array capability
        # TODO: ONLY DISABLE THIS WHEN DEBUGING WITH RENDERDOC
        # gl.glEnableClientState(gl.GL_VERTEX_ARRAY)

        # enable depth test for clean output (see lecture on clipping & visibility for an explanation
        gl.glEnable(gl.GL_DEPTH_TEST)

        # set the default shader program (can be set on a per-mesh basis)
        self.shaders = "flat"

        # initialises the camera object
        self.camera = Camera()

        # initialise the light source
        # self.light = LightSource(self, position=[5.0, 5.0, 5.0])

        # rendering mode for the shaders
        self.mode = 1  # initialise to full interpolated shading

        # This class will maintain a list of models to draw in the scene,
        self.models: list[Type["Model"]] = []

    def add_model(self, model):
        """
        This method just adds a model to the scene.
        :param model: The model object to add to the scene
        :return: None
        """

        # bind the default shader to the mesh
        # model.bind_shader(self.shaders)

        # and add to the list
        self.models.append(model)

    def add_models_list(self, models_list):
        """
        This method just adds a model to the scene.
        :param model: The model object to add to the scene
        :return: None
        """
        for model in models_list:
            self.add_model(model)

    def draw(self, framebuffer=False):
        """
        Draw all models in the scene
        :return: None
        """

        # first we need to clear the scene, we also clear the depth buffer to handle occlusions
        if not framebuffer:
            gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)

            # ensure that the camera view matrix is up to date
            self.camera.update()

        # then we loop over all models in the list and draw them
        for model in self.models:
            model.draw()

        # once we are done drawing, we display the scene
        # Note that here we use double buffering to avoid artefacts:
        # we draw on a different buffer than the one we display,
        # and flip the two buffers once we are done drawing.
        if not framebuffer:
            pygame.display.flip()

    def keyboard(self, event):
        """
        Method to process keyboard events. Check Pygame documentation for a list of key events
        :param event: the event object that was raised
        """
        if event.key == pygame.K_q:
            self.running = False

        if event.key == pygame.K_ESCAPE and self.mouse_locked:
            self.mouse_locked = False
            pygame.event.set_grab(False)  # Allow the mouse to leave the window
            pygame.mouse.set_visible(True)
            self.mouse_locked = False

    def run(self):
        """
        Method to handle PyGame events for user interaction.
        """
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

            if event.type == pygame.MOUSEBUTTONDOWN:
                mods = pygame.key.get_mods()
                if event.button == 4:
                    if mods & pygame.KMOD_CTRL:
                        self.light.position *= 1.1
                        self.light.update()
                elif event.button == 5:
                    if mods & pygame.KMOD_CTRL:
                        self.light.position *= 0.9
                        self.light.update()

            if self.mouse_locked:
                pygame.mouse.set_pos(
                    (self.window_size[0] / 2, self.window_size[1] / 2)
                )  # Re-center the mouse after every frame
            else:
                if (
                    not imgui.get_io().want_capture_mouse
                ) and pygame.mouse.get_pressed()[0]:
                    # We've clicked on the 3d scene and not the UI
                    # Stops the mouse from being able to leave the window
                    pygame.event.set_grab(True)
                    pygame.mouse.set_visible(False)
                    self.mouse_locked = True

    def debug_menu(self):
        pass

    def start(self):
        """
        Draws the scene in a loop until exit.
        """

        # with cProfile.Profile() as pr:
        # We have a classic program loop
        self.running = True
        while self.running:
            self.delta_time = self.clock.tick(self.fps_max) / 1000
            self.run()
            self.imgui_impl.process_inputs()
            imgui.new_frame()
            self.debug_menu()

            gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)

            self.draw()

            imgui.render()
            self.imgui_impl.render(imgui.get_draw_data())

            for entity in Entity.all_entities:
                entity.clear_entity_cache()
            pygame.display.flip()

        # stats = pstats.Stats(pr)
        # stats.sort_stats(pstats.SortKey.TIME)
        # stats.dump_stats(filename='last_run.prof')
