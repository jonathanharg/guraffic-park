import pygame
from OpenGL import GL as gl
import numpy as np

from camera import Camera
from lightSource import LightSource
from matutils import frustumMatrix


class Scene:
    """
    This is the main class for drawing an OpenGL scene using the PyGame library
    """

    def update_viewport(self):
        pygame.display.set_mode(self.window_size, pygame.OPENGL | pygame.DOUBLEBUF | pygame.RESIZABLE)
        gl.glViewport(0, 0, self.window_size[0], self.window_size[1])

        aspect_ratio =  self.window_size[1] / self.window_size[0] 

        right = self.near_clipping * np.tan(self.fov * np.pi / 360.0)
        left = -right
        top = -right * aspect_ratio
        bottom = right * aspect_ratio

        # to start with, we use an orthographic projection; change this.
        # self.P = frustumMatrix(left, right, top, bottom, near, far)
        self.perspective_matrix = frustumMatrix(left, right, top, bottom, self.near_clipping, self.far_clipping)

    def __init__(self, width=960, height=720):
        """
        Initialises the scene
        """

        self.window_size = (width, height)
        self.wireframe = False
        self.fov = 90.0
        self.perspective_matrix = None
        self.near_clipping = 0.5
        self.far_clipping = 1000.0

        pygame.init()

        self.update_viewport()

        # this selects the background color
        gl.glClearColor(0.886, 0.91, 0.941, 1.0)

        # enable back face culling (see lecture on clipping and visibility
        gl.glEnable(gl.GL_CULL_FACE)
        # depending on your model, or your projection matrix, the winding order may be inverted,
        # Typically, you see the far side of the model instead of the front one
        # uncommenting the following line should provide an easy fix.
        # glCullFace(GL_FRONT)

        # enable the vertex array capability
        gl.glEnableClientState(gl.GL_VERTEX_ARRAY)

        # enable depth test for clean output (see lecture on clipping & visibility for an explanation
        gl.glEnable(gl.GL_DEPTH_TEST)

        # set the default shader program (can be set on a per-mesh basis)
        self.shaders = "flat"


        # initialises the camera object
        self.camera = Camera()

        # initialise the light source
        self.light = LightSource(self, position=[5.0, 5.0, 5.0])

        # rendering mode for the shaders
        self.mode = 1  # initialise to full interpolated shading

        # This class will maintain a list of models to draw in the scene,
        self.models = []

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

        # flag to switch wireframe rendering
        elif event.key == pygame.K_0:
            if self.wireframe:
                print("--> Rendering using colour fill")
                gl.glPolygonMode(gl.GL_FRONT_AND_BACK, gl.GL_FILL)
                self.wireframe = False
            else:
                print("--> Rendering using colour wireframe")
                gl.glPolygonMode(gl.GL_FRONT_AND_BACK, gl.GL_LINE)
                self.wireframe = True

    def pygameEvents(self):
        """
        Method to handle PyGame events for user interaction.
        """
        # check whether the window has been closed
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            elif event.type == pygame.VIDEORESIZE:
                self.window_size = (event.w, event.h)
                self.update_viewport()

            # keyboard events
            elif event.type == pygame.KEYDOWN:
                self.keyboard(event)

            elif event.type == pygame.MOUSEBUTTONDOWN:
                mods = pygame.key.get_mods()
                if event.button == 4:
                    # pass
                    # TODO: WS2
                    if mods & pygame.KMOD_CTRL:
                        self.light.position *= 1.1
                        self.light.update()
                    else:
                        self.camera.distance = max(1, self.camera.distance - 1)

                elif event.button == 5:
                    # pass
                    # TODO: WS2
                    if mods & pygame.KMOD_CTRL:
                        self.light.position *= 0.9
                        self.light.update()
                    else:
                        self.camera.distance += 1

            elif event.type == pygame.MOUSEMOTION:
                if pygame.mouse.get_pressed()[0]:
                    if self.mouse_mvt is not None:
                        self.mouse_mvt = pygame.mouse.get_rel()
                        # TODO: WS2
                        self.camera.center[0] -= (
                            float(self.mouse_mvt[0]) / self.window_size[0]
                        )
                        self.camera.center[1] -= (
                            float(self.mouse_mvt[1]) / self.window_size[1]
                        )
                    else:
                        self.mouse_mvt = pygame.mouse.get_rel()

                elif pygame.mouse.get_pressed()[2]:
                    if self.mouse_mvt is not None:
                        self.mouse_mvt = pygame.mouse.get_rel()
                        # TODO: WS2
                        self.camera.phi -= (
                            float(self.mouse_mvt[0]) / self.window_size[0]
                        )
                        self.camera.psi -= (
                            float(self.mouse_mvt[1]) / self.window_size[1]
                        )
                    else:
                        self.mouse_mvt = pygame.mouse.get_rel()
                else:
                    self.mouse_mvt = None

    def run(self):
        """
        Draws the scene in a loop until exit.
        """

        # We have a classic program loop
        self.running = True
        while self.running:
            self.pygameEvents()

            # first we need to clear the scene, we also clear the depth buffer to handle occlusions
            gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)

            # otherwise, continue drawing
            self.draw()
            pygame.display.flip()
