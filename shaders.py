from typing import TYPE_CHECKING, Any, Type

import numpy as np
from OpenGL import GL as gl
from OpenGL.GL import shaders

from matutils import homog, scaleMatrix, translationMatrix, unhomog
from scene import Scene

if TYPE_CHECKING:
    from model import Model


class Singleton(type):
    _instances = {}

    def __call__(self, *args: Any, **kwds: Any) -> Any:
        if self not in self._instances:
            self._instances[self] = super().__call__(*args, **kwds)
        return self._instances[self]


# class Uniform:
#     """
#     We create a simple class to handle uniforms, this is not necessary,
#     but allow to put all relevant code in one place
#     """

#     def __init__(self, name, value=None):
#         """
#         Initialise the uniform parameter
#         :param name: the name of the uniform, as stated in the GLSL code
#         """
#         self.name = name
#         self.value = value
#         self.location = -1

#     def link(self, program):
#         """
#         This function needs to be called after compiling the GLSL program to fetch the location of the uniform
#         in the program from its name
#         :param program: the GLSL program where the uniform is used
#         """
#         self.location = gl.glGetUniformLocation(program=program, name=self.name)
#         if self.location == -1:
#             pass
#             # TODO: FIX THIS
#             # print("(E) Warning, no uniform {}".format(self.name))

#     def bind_matrix(self, M=None, number=1, transpose=True):
#         """
#         Call this before rendering to bind the Python matrix to the GLSL uniform mat4.
#         You will need different methods for different types of uniform, but for now this will
#         do for the PVM matrix
#         :param number: the number of matrices sent, leave that to 1 for now
#         :param transpose: Whether the matrix should be transposed
#         """
#         if M is not None:
#             self.value = M
#         if self.value.shape[0] == 4 and self.value.shape[1] == 4:
#             gl.glUniformMatrix4fv(self.location, number, transpose, self.value)
#         elif self.value.shape[0] == 3 and self.value.shape[1] == 3:
#             gl.glUniformMatrix3fv(self.location, number, transpose, self.value)
#         else:
#             print(
#                 "(E) Error: Trying to bind as uniform a matrix of shape {}".format(
#                     self.value.shape
#                 )
#             )

#     def bind(self, value):
#         if value is not None:
#             self.value = value

#         if isinstance(self.value, int):
#             self.bind_int()
#         elif isinstance(self.value, float):
#             self.bind_float()
#         elif isinstance(self.value, np.ndarray):
#             if self.value.ndim == 1:
#                 self.bind_vector()
#             elif self.value.ndim == 2:
#                 self.bind_matrix()
#         else:
#             print("Wrong value bound: {}".format(type(self.value)))

#     def bind_int(self, value=None):
#         if value is not None:
#             self.value = value
#         gl.glUniform1i(self.location, self.value)

#     def bind_float(self, value=None):
#         if value is not None:
#             self.value = value
#         gl.glUniform1f(self.location, self.value)

#     def bind_vector(self, value=None):
#         if value is not None:
#             self.value = value
#         if value.shape[0] == 2:
#             gl.glUniform2fv(self.location, 1, value)
#         elif value.shape[0] == 3:
#             gl.glUniform3fv(self.location, 1, value)
#         elif value.shape[0] == 4:
#             gl.glUniform4fv(self.location, 1, value)
#         else:
#             print(
#                 "(E) Error in Uniform.bind_vector(): Vector should be of dimension 2,3 or 4, found {}".format(
#                     value.shape[0]
#                 )
#             )

#     def set(self, value):
#         """
#         function to set the uniform value (could also access it directly, of course)
#         """
#         self.value = value


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

        with open(vertex_shader, "r") as file:
            self.vertex_shader_source = file.read()

        with open(fragment_shader, "r") as file:
            self.fragment_shader_source = file.read()

        self.uniforms = {}

        self.compiled = False

    # def add_uniform(self, name: str):
    #     if not self.compiled:
    #         self.compile()

    #     self.uniforms[name] = Uniform(name)
    #     if self.program_id is not None:
    #         self.uniforms[name].link(self.program_id)

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

        # link all uniforms
        for uniform in self.uniforms:
            self.uniforms[uniform].link(self.program_id)

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
            unit = len(model.textures)
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
