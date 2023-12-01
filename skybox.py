"""Sky box entity code.
"""

from OpenGL import GL as gl

from cube_map import CubeMap
from material import Material
from mesh import CubeMesh
from model import Model
from shaders import SkyBoxShader


class SkyBox(Model):
    """A sky box object."""

    def __init__(self):
        material = Material(name="skybox", texture=CubeMap(name="skybox/blue-sky"))

        super().__init__(
            scale=700,
            meshes=[CubeMesh(invert=True, material=material)],
            shader=SkyBoxShader(),
            name="Skybox",
        )

    def draw(self):
        gl.glDepthMask(gl.GL_FALSE)
        super().draw()
        gl.glDepthMask(gl.GL_TRUE)
