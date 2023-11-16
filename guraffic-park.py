import imgui
import numpy as np
import pygame
from OpenGL import GL as gl

from BaseModel import DrawModelFromMesh
from blender import load_obj_file
from lightSource import LightSource
from matutils import scaleMatrix, translationMatrix
from scene import Scene
from shaders import FlatShader
from camera import NoclipCamera, Camera


class MainScene(Scene):
    def __init__(self):
        Scene.__init__(self)

        self.light = LightSource(self, position=[5.0, 3.0, 5.0])

        # ldn = load_obj_file("models/london.obj")
        # self.add_models_list([DrawModelFromMesh(scene=self, M=translationMatrix([0,0,0]),mesh=mesh,shader=FlatShader(),) for mesh in ldn])

        meshes = load_obj_file("models/scene.obj")
        self.add_models_list(
            [
                DrawModelFromMesh(
                    scene=self,
                    M=scaleMatrix([0.5, 0.5, 0.5]),
                    mesh=mesh,
                    shader=FlatShader(),
                )
                for mesh in meshes
            ]
        )

        table = load_obj_file("models/quad_table.obj")
        self.table = [
            DrawModelFromMesh(
                scene=self,
                M=translationMatrix([0, -3, +0]),
                mesh=mesh,
                shader=FlatShader(),
            )
            for mesh in table
        ]

        bunny = load_obj_file("models/bunny_world.obj")
        self.bunny = DrawModelFromMesh(
            scene=self,
            M=np.matmul(translationMatrix([0, +1, 0]), scaleMatrix([0.5, 0.5, 0.5])),
            mesh=bunny[0],
            shader=FlatShader(),
        )

        box = load_obj_file("models/fluid_border.obj")
        self.box = [
            DrawModelFromMesh(
                scene=self,
                M=translationMatrix([0, +1, 0]),
                mesh=mesh,
                shader=FlatShader(),
            )
            for mesh in box
        ]

    def keyboard(self, event):
        """
        Process additional keyboard events for this demo.
        """
        Scene.keyboard(self, event)

        if event.key == pygame.K_1:
            print("Number 1 detected")
            
        #     print("--> using Flat shading")
        #     self.bunny.use_textures = True
        #     self.bunny.bind_shader("flat")

        # elif event.key == pygame.K_2:
        #     print("--> using Texture shading")
        #     self.bunny.bind_shader("texture")

    def draw(self):
        """
        Draw all models in the scene
        :return: None
        """
        self.camera.update()

        # then we loop over all models in the list and draw them
        for model in self.models:
            model.draw()

        # also all models from the table
        for model in self.table:
            model.draw()

        # and for the box
        for model in self.box:
            model.draw()

        # for the bunny (it consists of a single mesh).
        self.bunny.draw()

        if self.show_imgui_demo:
            self.show_imgui_demo = imgui.show_demo_window(True)

        with imgui.begin("Scene", ):
            imgui.text("Press ESC to interact with the menu")
            imgui.text(f"FPS: {self.clock.get_fps():.2f}")
            imgui.text(f"Frametime: {self.clock.get_time():.2f}ms")

            (fov_changed, self.fov) = imgui.slider_float("FOV", self.fov, 30, 150)
            if fov_changed:
                self.update_viewport()

            _, self.wireframe = imgui.checkbox("Wireframe", self.wireframe)
            if self.wireframe:
                gl.glPolygonMode(gl.GL_FRONT_AND_BACK, gl.GL_LINE)
            else:
                gl.glPolygonMode(gl.GL_FRONT_AND_BACK, gl.GL_FILL)

            clicked_noclip_checkbox, self.noclip = imgui.checkbox("Noclip", self.noclip)
            if clicked_noclip_checkbox:
                if self.noclip:
                    self.camera = NoclipCamera(self)
                else:
                    self.camera = Camera(self)
            
            if imgui.button("Debug camera"):
                self.debug_camera = True

            if imgui.button("Open ImGui Demo"):
                self.show_imgui_demo = True


if __name__ == "__main__":
    # initialises the scene object
    # scene = Scene(shaders='gouraud')
    scene = MainScene()

    # starts drawing the scene
    scene.run()
