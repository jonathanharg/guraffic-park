import numpy as np
from OpenGL import GL as gl

from cubeMap import CubeMap
from framebuffer import Framebuffer
from matutils import (
    frustumMatrix,
    poseMatrix,
    rotationMatrixX,
    rotationMatrixY,
    translationMatrix,
)
from mesh import CubeMesh, Mesh
from scene import Scene
from shaders import EnvironmentShader


class EnvironmentMappingTexture(CubeMap):
    def __init__(self, width=200, height=200):
        CubeMap.__init__(self)

        self.done = False

        self.width = width
        self.height = height

        self.fbos = {
            gl.GL_TEXTURE_CUBE_MAP_NEGATIVE_X: Framebuffer(),
            gl.GL_TEXTURE_CUBE_MAP_POSITIVE_X: Framebuffer(),
            gl.GL_TEXTURE_CUBE_MAP_NEGATIVE_Y: Framebuffer(),
            gl.GL_TEXTURE_CUBE_MAP_POSITIVE_Y: Framebuffer(),
            gl.GL_TEXTURE_CUBE_MAP_NEGATIVE_Z: Framebuffer(),
            gl.GL_TEXTURE_CUBE_MAP_POSITIVE_Z: Framebuffer(),
        }

        t = 0.0
        self.views = {
            gl.GL_TEXTURE_CUBE_MAP_NEGATIVE_X: np.matmul(
                translationMatrix([0, 0, t]), rotationMatrixY(-np.pi / 2.0)
            ),
            gl.GL_TEXTURE_CUBE_MAP_POSITIVE_X: np.matmul(
                translationMatrix([0, 0, t]), rotationMatrixY(+np.pi / 2.0)
            ),
            gl.GL_TEXTURE_CUBE_MAP_NEGATIVE_Y: np.matmul(
                translationMatrix([0, 0, t]), rotationMatrixX(+np.pi / 2.0)
            ),
            gl.GL_TEXTURE_CUBE_MAP_POSITIVE_Y: np.matmul(
                translationMatrix([0, 0, t]), rotationMatrixX(-np.pi / 2.0)
            ),
            gl.GL_TEXTURE_CUBE_MAP_NEGATIVE_Z: np.matmul(
                translationMatrix([0, 0, t]), rotationMatrixY(-np.pi)
            ),
            gl.GL_TEXTURE_CUBE_MAP_POSITIVE_Z: translationMatrix([0, 0, t]),
        }

        self.bind()
        for face, fbo in self.fbos.items():
            gl.glTexImage2D(
                face,
                0,
                self.texture_format,
                width,
                height,
                0,
                self.texture_format,
                self.texture_type,
                None,
            )
            fbo.prepare(self, face)
        self.unbind()

    def update(self):
        if self.done:
            return

        self.bind()

        scene = Scene.current_scene

        old_p = scene.projection_matrix

        scene.projection_matrix = frustumMatrix(-1.0, +1.0, -1.0, +1.0, 1.0, 20.0)

        gl.glViewport(0, 0, self.width, self.height)

        for face, fbo in self.fbos.items():
            fbo.bind()
            # scene.camera.V = np.identity(4)
            scene.camera.view_matrix = self.views[face]

            # # scene.draw_reflections()
            # for model in scene.models:
            #     model.draw()

            scene.camera.update()
            fbo.unbind()

        # reset the viewport
        gl.glViewport(0, 0, scene.window_size[0], scene.window_size[1])

        scene.projection_matrix = old_p

        self.unbind()


# class EnvironmentBox(Mesh):
#     def __init__(self, scene, shader=EnvironmentShader(), width=200, height=200):
#         self.done = False
#         self.map = EnvironmentMappingTexture(width, height)

#         super().__init__(
#             scene=scene,
#             mesh=CubeMesh(shader.map),
#             shader=shader,
#             visible=False,
#         )
