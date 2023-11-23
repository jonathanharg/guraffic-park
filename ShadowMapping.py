import numpy as np
from OpenGL import GL as gl

from BaseModel import DrawModelFromMesh
from framebuffer import Framebuffer
from matutils import frustumMatrix, poseMatrix, scaleMatrix, translationMatrix
from mesh import Mesh
from scene import Scene
from shaders import Shader, PhongShader
from texture import Texture


def normalize(v):
    return v / np.linalg.norm(v)


def lookAt(eye, center, up=np.array([0, 1, 0])):
    f = normalize(center - eye)
    u = normalize(up)

    # Note: the normalization is missing in the official glu manpage: /: /: /
    s = normalize(np.cross(f, u))
    u = np.cross(s, f)

    return np.matmul(
        np.array(
            [
                [s[0], s[1], s[2], 0],
                [u[0], u[1], u[2], 0],
                [-f[0], -f[1], -f[2], 0],
                [0, 0, 0, 1],
            ]
        ),
        translationMatrix(-eye),
    )

class ShadowMappingShader(PhongShader):
    def __init__(self, shadow_map=None):
        super().__init__(name="shadow_mapping")
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

class ShadowMap(Texture):
    def __init__(self, light=None, width=1000, height=1000):
        # In order to call parent constructor I would need to change it to allow for an empty texture object (poor design)
        # Texture.__init__(self, "shadow", img=None, wrap=gl.GL_CLAMP_TO_EDGE, sample=gl.GL_NEAREST, format=gl.GL_DEPTH_COMPONENT, type=gl.GL_FLOAT, target=gl.GL_TEXTURE_2D)

        # we save the light source
        self.light = light

        # we'll just copy and modify the code here
        self.name = "shadow"
        self.format = gl.GL_DEPTH_COMPONENT
        self.type = gl.GL_FLOAT
        self.wrap = gl.GL_CLAMP_TO_EDGE
        self.sample = gl.GL_LINEAR
        self.target = gl.GL_TEXTURE_2D
        self.width = width
        self.height = height

        # create the texture
        self.textureid = gl.glGenTextures(1)

        print("* Creating texture {} at ID {}".format(self.name, self.textureid))

        # initialise the texture memory
        self.bind()
        gl.glTexImage2D(
            self.target,
            0,
            self.format,
            self.width,
            self.height,
            0,
            self.format,
            self.type,
            None,
        )
        self.unbind()

        self.set_wrap_parameter(self.wrap)
        self.set_sampling_parameter(self.sample)
        self.set_shadow_comparison()

        self.fbo = Framebuffer(attachment=gl.GL_DEPTH_ATTACHMENT, texture=self)

        self.V = None

    def render(self, scene, target=[0, 0, 0]):
        # backup the view matrix and replace with the new one
        # self.P = scene.P
        if self.light is not None:
            self.P = frustumMatrix(-1.0, +1.0, -1.0, +1.0, 1.0, 20.0)
            self.V = lookAt(np.array(self.light.position), np.array(target))
            scene.camera.V = self.V

            # update the viewport for the image size
            gl.glViewport(0, 0, self.width, self.height)

            self.fbo.bind()
            scene.draw_shadow_map()
            self.fbo.unbind()

            # reset the viewport to the windows size
            gl.glViewport(0, 0, scene.window_size[0], scene.window_size[1])

            # restore the view matrix
            scene.camera.V = None
            scene.camera.update()
