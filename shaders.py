from typing import TYPE_CHECKING, Any, Type

import numpy as np
from OpenGL import GL as gl
from OpenGL.GL import shaders

from matutils import (
    make_homogeneous,
    make_unhomogeneous,
    scale_matrix,
    translation_matrix,
)
from scene import Scene

if TYPE_CHECKING:
    from model import Model


class Singleton(type):
    _instances = {}

    def __call__(cls, *args: Any, **kwds: Any) -> Any:
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwds)
        return cls._instances[cls]


class Shader:
    """
    This is the base class for loading and compiling the GLSL shaders.
    """

    compiled_program_ids = {}

    def __init__(self, program_name, vertex_shader=None, fragment_shader=None):
        """
        Initialises the shaders
        :param vertex_shader: the name of the file containing the vertex shader GLSL code
        :param fragment_shader: the name of the file containing the fragment shader GLSL code
        """

        self.program_name = program_name
        self.program_id = 0

        if program_name is None:
            program_name = "default"

        if vertex_shader is None:
            vertex_shader = f"shaders/{program_name}/vertex_shader.glsl"

        if fragment_shader is None:
            fragment_shader = f"shaders/{program_name}/fragment_shader.glsl"

        with open(vertex_shader, "r", encoding="utf-8") as file:
            self.vertex_shader_source = file.read()

        with open(fragment_shader, "r", encoding="utf-8") as file:
            self.fragment_shader_source = file.read()

        self.compiled = False

    def compile(self):
        """
        Call this function to compile the GLSL codes for both shaders.
        :return:
        """
        if self.compiled:
            print("UNECESSARY COMPILE")
            return

        try:
            if self.program_name not in Shader.compiled_program_ids:
                self.program_id = gl.glCreateProgram()
                print(f"Compiling {self.program_name} shader")
                gl.glAttachShader(
                    self.program_id,
                    shaders.compileShader(
                        self.vertex_shader_source, gl.GL_VERTEX_SHADER
                    ),
                )
                gl.glAttachShader(
                    self.program_id,
                    shaders.compileShader(
                        self.fragment_shader_source, gl.GL_FRAGMENT_SHADER
                    ),
                )
                self.compiled_program_ids[self.program_name] = self.program_id
            else:
                self.program_id = self.compiled_program_ids[self.program_name]

        except Exception as e:
            raise RuntimeError(
                f"Error compiling {self.program_name} shader: {e}"
            ) from e

        # self.bind_attributes(attributes)

        gl.glLinkProgram(self.program_id)

        # tell OpenGL to use this shader program for rendering
        gl.glUseProgram(self.program_id)

        self.compiled = True

    def bind_attributes(self, attributes):
        if not self.compiled:
            self.compile()
        # bind all shader attributes to the correct locations in the VAO
        for name, location in attributes.items():
            gl.glBindAttribLocation(self.program_id, location, name)

    def bind(self, model: Type["Model"]):
        """
        Call this function to enable this GLSL Program (you can have multiple GLSL programs used during rendering!)
        """
        if not self.compiled:
            self.compile()

        # tell OpenGL to use this shader program for rendering
        gl.glUseProgram(self.program_id)

    def unbind(self):
        gl.glUseProgram(0)


class PhongShader(Shader):
    def __init__(self):
        super().__init__(program_name="phong")


class NewShader(Shader):
    def __init__(self):
        super().__init__(program_name="new")


class FlatShader(Shader):
    def __init__(self):
        super().__init__(program_name="flat")


class GouraudShader(Shader):
    def __init__(self):
        super().__init__(program_name="gouraud")


class BlinnShader(Shader):
    def __init__(self):
        super().__init__(program_name="blinn")


class TextureShader(Shader):
    def __init__(self):
        super().__init__(program_name="texture")


class SkyBoxShader(Shader):
    def __init__(self, name="skybox"):
        super().__init__(program_name=name)
        # self.compile()
        # self.add_uniform("sampler_cube")


class EnvironmentShader(Shader):
    def __init__(self, name="environment", map=None):
        super().__init__(program_name=name)
        self.map = map

    def bind(self, model):
        if self.map is not None:
            # self.map.update(model.scene)
            # unit = len(model.textures)
            gl.glActiveTexture(gl.GL_TEXTURE0)
            self.map.bind()
            # self.uniforms["sampler_cube"].bind(0)

        gl.glUseProgram(self.program_id)


class ShadowMappingShader(Shader):
    def __init__(self, shadow_map=None):
        super().__init__(program_name="shadow_mapping")
        self.compile()
        # self.add_uniform("shadow_map")
        ##### self.add_uniform('old_map')
        # self.add_uniform("shadow_map_matrix")
        self.shadow_map = shadow_map

    def bind(self, model):
        super().bind(model)
        # self.uniforms["shadow_map"].bind(1)

        gl.glActiveTexture(gl.GL_TEXTURE1)
        self.shadow_map.bind()

        # gl.glActiveTexture(gl.GL_TEXTURE2)
        # self.shadow_map.bind()

        gl.glActiveTexture(gl.GL_TEXTURE0)
