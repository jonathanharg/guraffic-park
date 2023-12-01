import os
from typing import Self, Type

import imgui

from blender import find_file, load_obj_file
from entity import Entity
from mesh import Mesh
from scene import Scene
from shaders import (
    EnvironmentShader,
    FlatShader,
    NewShader,
    PhongShader,
    Shader,
    ShadowMappingShader,
    SkyBoxShader,
    TextureShader,
)


class Model(Entity):
    untitled_model_count = 0

    def __init__(
        self,
        meshes: list[Type[Mesh]],
        name=None,
        shader: Shader = PhongShader(),
        **kwargs,
    ) -> None:
        # TODO: FIX issue if the model is loaded multiple times
        if name is not None:
            self.name = name
        else:
            Model.untitled_model_count += 1
            untitled_model_number = str(Model.untitled_model_count).zfill(3)
            self.name = f"Model.{untitled_model_number}"

        super().__init__(**kwargs)
        self.visible = True
        self.shader = shader
        self.meshes = meshes

        for mesh in self.meshes:
            mesh.parent = self
            # mesh.shader = shader
            mesh.bind_shader(self.shader)

        Scene.current_scene.models.append(self)

    @classmethod
    def from_obj(self, obj_path: str, **kwargs) -> Self:
        file_path = find_file(obj_path, ["models/"])
        if "name" not in kwargs:
            kwargs["name"] = os.path.basename(file_path)
        meshes = load_obj_file(obj_path)
        print(f"Creating model from {obj_path}")
        model = Model(meshes, **kwargs)
        return model

    def draw(self):
        if not self.visible:
            return

        for mesh in self.meshes:
            mesh.draw()

    def set_shader(self, shader: Shader):
        self.shader = shader
        for mesh in self.meshes:
            mesh.bind_shader(shader)

    def debug_menu(self):
        super().debug_menu()
        _, self.visible = imgui.checkbox("Visible", self.visible)

        ALL_SHADERS = [
            Shader,
            PhongShader,
            FlatShader,
            NewShader,
            TextureShader,
            SkyBoxShader,
            EnvironmentShader,
            ShadowMappingShader,
        ]

        current_shader = ALL_SHADERS.index(type(self.shader))
        shader_changed, selected_index = imgui.combo(
            "Shader", current_shader, [shader.__name__ for shader in ALL_SHADERS]
        )

        if shader_changed:
            self.set_shader(ALL_SHADERS[selected_index]())

        # clicked_shader, current_shader = imgui.combo("Shader", )
        # shaders = ["flat", "gouraud", "blinn", "texture"]
        # selected = 0
