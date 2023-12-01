from typing import Any

from OpenGL import GL as gl
from OpenGL.GL import shaders

from scene import Scene


class Singleton(type):
    """A singleton class. Only one instance of this class can ever exist.
    If a second instance is ever created, it returns a pointer to the first instance.
    """

    _instances = {}

    def __call__(cls, *args: Any, **kwds: Any) -> Any:
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwds)
        return cls._instances[cls]


class Shader(metaclass=Singleton):
    """This is the base class for loading and compiling the GLSL shaders.
    Each shader can only have one instance. The shader can be shared across models/meshes.
    """

    current_shader: int = 0

    def __init__(self, program_name, vertex_shader=None, fragment_shader=None):
        """
        Initialises the shaders
        :param vertex_shader: the name of the file containing the vertex shader GLSL code
        :param fragment_shader: the name of the file containing the fragment shader GLSL code
        """

        self.program_name = program_name
        self.program_id = 0

        if program_name is None:
            program_name = "cartoon"

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
        """Call this function to compile the GLSL codes for both shaders.
        :return:
        """
        if self.compiled:
            return

        try:
            self.program_id = gl.glCreateProgram()
            print(f"Compiling {self.program_name} shader")
            gl.glAttachShader(
                self.program_id,
                shaders.compileShader(self.vertex_shader_source, gl.GL_VERTEX_SHADER),
            )
            gl.glAttachShader(
                self.program_id,
                shaders.compileShader(
                    self.fragment_shader_source, gl.GL_FRAGMENT_SHADER
                ),
            )

        except Exception as e:
            raise RuntimeError(
                f"Error compiling {self.program_name} shader: {e}"
            ) from e

        gl.glLinkProgram(self.program_id)
        self.compiled = True

    def bind_attributes(self, attributes):
        """Bind attributes to the VAO"""
        if not self.compiled:
            self.compile()
        # bind all shader attributes to the correct locations in the VAO
        for name, location in attributes.items():
            gl.glBindAttribLocation(self.program_id, location, name)

    def bind(self):
        """Bind the shader"""
        if not self.compiled:
            self.compile()

        # Binding shaders is costly, dont bind unless we need to
        if Shader.current_shader != self.program_id:
            gl.glUseProgram(self.program_id)
            Shader.current_shader = self.program_id


class CartoonShader(Shader):
    def __init__(self):
        super().__init__(program_name="cartoon")


class SkyBoxShader(Shader):
    def __init__(self, name="skybox"):
        super().__init__(program_name=name)


class EnvironmentShader(Shader):
    def __init__(self, name="environment"):
        super().__init__(program_name=name)

    def bind(self):
        if Scene.current_scene.environment is not None:
            gl.glActiveTexture(gl.GL_TEXTURE0)
            Scene.current_scene.environment.bind()

        super().bind()
