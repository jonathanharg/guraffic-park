import numpy as np
from OpenGL import GL as gl

from framebuffer import Framebuffer
from matutils import frustumMatrix, translationMatrix
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
        self.texture_id = gl.glGenTextures(1)

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