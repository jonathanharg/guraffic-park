import numpy as np
import pygame
from OpenGL import GL as gl

from BaseModel import DrawModelFromMesh
from blender import load_obj_file
from lightSource import LightSource
from matutils import scaleMatrix, translationMatrix
from scene import Scene
from shaders import FlatShader


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
            print("--> using Flat shading")
            self.bunny.use_textures = True
            self.bunny.bind_shader("flat")

        elif event.key == pygame.K_2:
            print("--> using Texture shading")
            self.bunny.bind_shader("texture")

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


if __name__ == "__main__":
    # initialises the scene object
    # scene = Scene(shaders='gouraud')
    scene = MainScene()

    # starts drawing the scene
    scene.run()
