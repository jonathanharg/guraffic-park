import os
from typing import Self, Type

import imgui

from blender import find_file, load_obj_file
from entity import Entity
from mesh import Mesh
from scene import Scene
from shaders import (
    CartoonShader,
    EnvironmentShader,
    FlatShader,
    PhongShader,
    Shader,
    ShadowMappingShader,
    SkyBoxShader,
    TextureShader,
)


class Model(Entity):
    """A model in the 3D world. Represents a collection of meshes
    that should be treated as the same object.
    """

    untitled_model_count = 0

    def __init__(
        self,
        meshes: list[Type[Mesh]],
        name=None,
        shader: Shader = CartoonShader(),
        **kwargs,
    ) -> None:
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
            mesh.bind_shader(self.shader)

        Scene.current_scene.models.append(self)

    @classmethod
    def from_obj(self, obj_name: str, **kwargs) -> Self:
        """Load a Wavefront obj file.

        Args:
            obj_name (str): The name of the obj file

        Returns:
            Self: Model
        """
        file_path = find_file(obj_name, ["models/"])
        if "name" not in kwargs:
            kwargs["name"] = os.path.basename(file_path)
        meshes = load_obj_file(obj_name)
        print(f"Creating model from {obj_name}")
        model = Model(meshes, **kwargs)
        return model

    def draw(self):
        """Draw the model to the window."""
        if not self.visible:
            return

        for mesh in self.meshes:
            mesh.draw()

    def set_shader(self, shader: Shader):
        """Update the model shader"""
        self.shader = shader
        for mesh in self.meshes:
            mesh.bind_shader(shader)

    def debug_menu(self):
        """Define the debug menu for this class. Uses the ImGui library to construct a UI. Calling this function inside an ImGui context will render this debug menu."""
        super().debug_menu()
        _, self.visible = imgui.checkbox("Visible", self.visible)

        all_shaders = [
            CartoonShader,
            SkyBoxShader,
            EnvironmentShader,
            ShadowMappingShader,
        ]

        current_shader = all_shaders.index(type(self.shader))
        shader_changed, selected_index = imgui.combo(
            "Shader", current_shader, [shader.__name__ for shader in all_shaders]
        )

        if shader_changed:
            self.set_shader(all_shaders[selected_index]())
