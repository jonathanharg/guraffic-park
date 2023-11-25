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


class Uniform:
    """
    We create a simple class to handle uniforms, this is not necessary,
    but allow to put all relevant code in one place
    """

    def __init__(self, name, value=None):
        """
        Initialise the uniform parameter
        :param name: the name of the uniform, as stated in the GLSL code
        """
        self.name = name
        self.value = value
        self.location = -1

    def link(self, program):
        """
        This function needs to be called after compiling the GLSL program to fetch the location of the uniform
        in the program from its name
        :param program: the GLSL program where the uniform is used
        """
        self.location = gl.glGetUniformLocation(program=program, name=self.name)
        if self.location == -1:
            pass
            # TODO: FIX THIS
            # print("(E) Warning, no uniform {}".format(self.name))

    def bind_matrix(self, M=None, number=1, transpose=True):
        """
        Call this before rendering to bind the Python matrix to the GLSL uniform mat4.
        You will need different methods for different types of uniform, but for now this will
        do for the PVM matrix
        :param number: the number of matrices sent, leave that to 1 for now
        :param transpose: Whether the matrix should be transposed
        """
        if M is not None:
            self.value = M
        if self.value.shape[0] == 4 and self.value.shape[1] == 4:
            gl.glUniformMatrix4fv(self.location, number, transpose, self.value)
        elif self.value.shape[0] == 3 and self.value.shape[1] == 3:
            gl.glUniformMatrix3fv(self.location, number, transpose, self.value)
        else:
            print(
                "(E) Error: Trying to bind as uniform a matrix of shape {}".format(
                    self.value.shape
                )
            )

    def bind(self, value):
        if value is not None:
            self.value = value

        if isinstance(self.value, int):
            self.bind_int()
        elif isinstance(self.value, float):
            self.bind_float()
        elif isinstance(self.value, np.ndarray):
            if self.value.ndim == 1:
                self.bind_vector()
            elif self.value.ndim == 2:
                self.bind_matrix()
        else:
            print("Wrong value bound: {}".format(type(self.value)))

    def bind_int(self, value=None):
        if value is not None:
            self.value = value
        gl.glUniform1i(self.location, self.value)

    def bind_float(self, value=None):
        if value is not None:
            self.value = value
        gl.glUniform1f(self.location, self.value)

    def bind_vector(self, value=None):
        if value is not None:
            self.value = value
        if value.shape[0] == 2:
            gl.glUniform2fv(self.location, 1, value)
        elif value.shape[0] == 3:
            gl.glUniform3fv(self.location, 1, value)
        elif value.shape[0] == 4:
            gl.glUniform4fv(self.location, 1, value)
        else:
            print(
                "(E) Error in Uniform.bind_vector(): Vector should be of dimension 2,3 or 4, found {}".format(
                    value.shape[0]
                )
            )

    def set(self, value):
        """
        function to set the uniform value (could also access it directly, of course)
        """
        self.value = value


class Shader:
    """
    This is the base class for loading and compiling the GLSL shaders.
    """

    shader_count = 0
    compiled_program_ids = {}

    def __init__(self, name, vertex_shader=None, fragment_shader=None):
        """
        Initialises the shaders
        :param vertex_shader: the name of the file containing the vertex shader GLSL code
        :param fragment_shader: the name of the file containing the fragment shader GLSL code
        """

        self.name = name

        if name is None:
            name = "default"

        if vertex_shader is None:
            vertex_shader = f"shaders/{name}/vertex_shader.glsl"

        if fragment_shader is None:
            fragment_shader = f"shaders/{name}/fragment_shader.glsl"

        with open(vertex_shader, "r") as file:
            self.vertex_shader_source = file.read()

        with open(fragment_shader, "r") as file:
            self.fragment_shader_source = file.read()

        # in order to simplify extension of the class in the future, we start storing uniforms in a dictionary.
        self.uniforms = {
            "PVM": Uniform("PVM"),  # projection view model matrix
        }

        self.compiled = False

        # print(f"CHECK: v{gl.glGetString(gl.GL_VERSION)} {bool(gl.glCreateProgram)}")

        # self.compile({})

    def add_uniform(self, name: str):
        if not self.compiled:
            self.compile()

        self.uniforms[name] = Uniform(name)
        if self.program is not None:
            self.uniforms[name].link(self.program)

    def compile(self):
        """
        Call this function to compile the GLSL codes for both shaders.
        :return:
        """
        if self.compiled:
            print("UNECESSARY COMPILE")
            return

        try:
            if self.__class__.__name__ not in Shader.compiled_program_ids:
                self.program = gl.glCreateProgram()
                Shader.shader_count += 1
                print(
                    f"Just compiled a new shader, current total: {Shader.shader_count}"
                )
                gl.glAttachShader(
                    self.program,
                    shaders.compileShader(
                        self.vertex_shader_source, gl.GL_VERTEX_SHADER
                    ),
                )
                gl.glAttachShader(
                    self.program,
                    shaders.compileShader(
                        self.fragment_shader_source, gl.GL_FRAGMENT_SHADER
                    ),
                )
                self.compiled_program_ids[self.__class__.__name__] = self.program
            else:
                self.program = self.compiled_program_ids[self.__class__.__name__]

        except Exception as e:
            raise RuntimeError(f"Error compiling {self.name} shader: {e}") from e

        # self.bind_attributes(attributes)

        gl.glLinkProgram(self.program)

        # tell OpenGL to use this shader program for rendering
        gl.glUseProgram(self.program)

        # link all uniforms
        for uniform in self.uniforms:
            self.uniforms[uniform].link(self.program)

        self.compiled = True

    def bind_attributes(self, attributes):
        if not self.compiled:
            self.compile()
        # bind all shader attributes to the correct locations in the VAO
        for name, location in attributes.items():
            gl.glBindAttribLocation(self.program, location, name)

    def bind(self, model: Type["Model"]):
        """
        Call this function to enable this GLSL Program (you can have multiple GLSL programs used during rendering!)
        """
        if not self.compiled:
            self.compile()

        # tell OpenGL to use this shader program for rendering
        gl.glUseProgram(self.program)

        # projection_matrix = Scene.current_scene.projection_matrix
        # view_matrix = Scene.current_scene.camera.view_matrix

        # # set the PVM matrix uniform
        # self.uniforms["PVM"].bind(
        #     np.matmul(projection_matrix, np.matmul(view_matrix, model.world_pose))
        # )

    def unbind(self):
        gl.glUseProgram(0)


class PhongShader(Shader):
    def __init__(self, name="phong", **kwargs):
        super().__init__(name=name, **kwargs)

        # in order to simplify extension of the class in the future, we start storing uniforms in a dictionary.
        self.uniforms = {
            "PVM": Uniform("PVM"),  # projection view model matrix
            "VM": Uniform("VM"),  # view model matrix (necessary for light computations)
            "VMiT": Uniform(
                "VMiT"
            ),  # inverse-transpose of the view model matrix (for normal transformation)
            "mode": Uniform(
                "mode", 0
            ),  # rendering mode (only for illustration, in general you will want one shader program per mode)
            "alpha": Uniform("alpha", 1.0),
            "Ka": Uniform("Ka"),
            "Kd": Uniform("Kd"),
            "Ks": Uniform("Ks"),
            "Ns": Uniform("Ns"),
            "light": Uniform("light", np.array([0.0, 0.0, 0.0], "f")),
            "Ia": Uniform("Ia"),
            "Id": Uniform("Id"),
            "Is": Uniform("Is"),
            "has_texture": Uniform("has_texture"),
            "textureObject": Uniform("textureObject")
            #'textureObject2': Uniform('textureObject2'),
        }

    def bind(self, model: Type["Model"]):
        """
        Call this function to enable this GLSL Program (you can have multiple GLSL programs used during rendering!)
        """
        projection_matrix = Scene.current_scene.projection_matrix
        view_matrix = Scene.current_scene.camera.view_matrix

        # tell OpenGL to use this shader program for rendering
        gl.glUseProgram(self.program)

        # vm = np.matmul(view_matrix, model.world_pose)

        # # set the PVM matrix uniform
        # self.uniforms["PVM"].bind(np.matmul(projection_matrix, vm))

        # # set the PVM matrix uniform
        # self.uniforms["VM"].bind(vm)

        # # set the PVM matrix uniform
        # self.uniforms["VMiT"].bind(np.linalg.inv(vm)[:3, :3].transpose())

        # # bind the mode to the program
        # self.uniforms["mode"].bind(Scene.current_scene.mode)

        # self.uniforms["alpha"].bind(model.material.alpha)

        # if len(model.textures) > 0:
        #     # bind the texture(s)
        #     self.uniforms["textureObject"].bind(0)
        #     self.uniforms["has_texture"].bind(1)
        # else:
        #     self.uniforms["has_texture"].bind(0)

        # # bind material properties
        # self.bind_material_uniforms(model.material)

        # # bind the light properties
        # self.bind_light_uniforms(Scene.current_scene.light, view_matrix)

    def bind_light_uniforms(self, light, V):
        self.uniforms["light"].bind_vector(unhomog(np.dot(V, homog(light.position))))
        self.uniforms["Ia"].bind_vector(np.array(light.Ia, "f"))
        self.uniforms["Id"].bind_vector(np.array(light.Id, "f"))
        self.uniforms["Is"].bind_vector(np.array(light.Is, "f"))

    def bind_material_uniforms(self, material):
        self.uniforms["Ka"].bind_vector(np.array(material.Ka, "f"))
        self.uniforms["Kd"].bind_vector(np.array(material.Kd, "f"))
        self.uniforms["Ks"].bind_vector(np.array(material.Ks, "f"))
        self.uniforms["Ns"].bind_float(material.Ns)

    def add_uniform(self, name):
        if name in self.uniforms:
            print("(W) Warning re-defining already existing uniform %s" % name)
        self.uniforms[name] = Uniform(name)


class FlatShader(PhongShader):
    def __init__(self):
        super().__init__(name="flat")


class GouraudShader(PhongShader):
    def __init__(self):
        super().__init__(name="gouraud")


class BlinnShader(PhongShader):
    def __init__(self):
        super().__init__(name="blinn")


class TextureShader(PhongShader):
    def __init__(self):
        super().__init__(name="texture")


class SkyBoxShader(Shader):
    def __init__(self, name="skybox"):
        super().__init__(name=name)
        # self.compile()
        self.add_uniform("sampler_cube")

    def bind(self, model):
        Shader.bind(self, model)

        P = (
            Scene.current_scene.projection_matrix
        )  # get projection matrix from the scene
        V = Scene.current_scene.camera.view_matrix  # get view matrix from the camera

        self.uniforms["PVM"].bind(np.matmul(P, np.matmul(V, model.world_pose)))


class EnvironmentShader(Shader):
    def __init__(self, name="environment", map=None):
        super().__init__(name=name)
        self.compile()
        self.add_uniform("sampler_cube")
        self.add_uniform("VM")
        self.add_uniform("VMiT")
        self.add_uniform("VT")

        self.map = map

    def bind(self, model):
        if self.map is not None:
            # self.map.update(model.scene)
            unit = len(model.textures)
            gl.glActiveTexture(gl.GL_TEXTURE0)
            self.map.bind()
            # self.uniforms["sampler_cube"].bind(0)

        gl.glUseProgram(self.program)

        projection_matrix = (
            Scene.current_scene.projection_matrix
        )  # get projection matrix from the scene
        view_matrix = (
            Scene.current_scene.camera.view_matrix
        )  # get view matrix from the camera

        vm = np.matmul(view_matrix, model.world_pose)

        # set the PVM matrix uniform
        self.uniforms["PVM"].bind(np.matmul(projection_matrix, vm))

        # set the PVM matrix uniform
        self.uniforms["VM"].bind(vm)

        # set the PVM matrix uniform
        self.uniforms["VMiT"].bind(np.linalg.inv(vm)[:3, :3].transpose())

        self.uniforms["VT"].bind(view_matrix.transpose()[:3, :3])


class ShadowMappingShader(PhongShader):
    def __init__(self, shadow_map=None):
        super().__init__(name="shadow_mapping")
        self.compile({})
        self.add_uniform("shadow_map")
        # self.add_uniform('old_map')
        self.add_uniform("shadow_map_matrix")
        self.shadow_map = shadow_map

    def bind(self, model):
        super().bind(model)
        self.uniforms["shadow_map"].bind(1)

        gl.glActiveTexture(gl.GL_TEXTURE1)
        self.shadow_map.bind()

        # gl.glActiveTexture(gl.GL_TEXTURE2)
        # self.shadow_map.bind()

        gl.glActiveTexture(gl.GL_TEXTURE0)

        # setup the shadow map matrix
        VsT = np.linalg.inv(Scene.current_scene.camera.view_matrix)
        self.SM = np.matmul(self.shadow_map.view_matrix, VsT)
        self.SM = np.matmul(self.shadow_map.projection_matrix, self.SM)
        self.SM = np.matmul(translationMatrix([1, 1, 1]), self.SM)
        self.SM = np.matmul(scaleMatrix(0.5), self.SM)
        self.uniforms["shadow_map_matrix"].bind(self.SM)
