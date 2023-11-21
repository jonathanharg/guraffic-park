import os
from typing import Self

import imgui

from blender import find_file, load_obj_file
from entity import Entity
from mesh import Mesh
from scene import Scene
from shaders import BaseShaderProgram, FlatShader
from surface import Surface


class Model(Entity):
    untitled_model_count = 0

    def __init__(self, meshes: list[Mesh], name=None, **kwargs) -> None:
        if name is not None:
            self.name = name
        else:
            Model.untitled_model_count += 1
            untitled_model_number = str(Model.untitled_model_count).zfill(3)
            self.name = f"Model.{untitled_model_number}"

        super().__init__(**kwargs)
        self.visible = True
        self.shader: BaseShaderProgram = FlatShader()
        self.surfaces: list[Surface] = []

        for mesh in meshes:
            self.surfaces.append(Surface(mesh, parent=self))

        Scene.current_scene.models.append(self)

    @classmethod
    def from_obj(self, obj_path: str, **kwargs) -> Self:
        file_path = find_file(obj_path, ["models/"])
        name = os.path.basename(file_path)
        meshes = load_obj_file(obj_path)
        print("Creating model from {obj_path}")
        model = Model(meshes, name=name, **kwargs)
        return model

    def draw(self):
        if not self.visible:
            return

        for surface in self.surfaces:
            surface.draw()

    def set_shader(self, shader: BaseShaderProgram):
        # TODO: THIS IS BUSTED
        for surface in self.surfaces:
            surface.shader = shader
            surface.bind_shader(shader.name)

    def debug_menu(self):
        _, self.visible = imgui.checkbox("Visible", self.visible)
        super().debug_menu()
        # clicked_shader, current_shader = imgui.combo("Shader", )
        # shaders = ["flat", "gouraud", "blinn", "texture"]
        # selected = 0
