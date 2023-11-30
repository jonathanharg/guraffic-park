import numpy as np
import quaternion
from OpenGL import GL as gl

from camera import Camera
from cube_map import CubeMap
from framebuffer import Framebuffer
from scene import Scene
from shaders import EnvironmentShader


class EnvironmentMappingTexture(CubeMap):
    def __init__(self, camera: Camera, width=200, height=200):
        super().__init__()
        self.rendered = False

        self.camera = camera

        self.width = width
        self.height = height

        self.frame_buffers = {
            gl.GL_TEXTURE_CUBE_MAP_NEGATIVE_X: Framebuffer(),
            gl.GL_TEXTURE_CUBE_MAP_POSITIVE_X: Framebuffer(),
            gl.GL_TEXTURE_CUBE_MAP_NEGATIVE_Y: Framebuffer(),
            gl.GL_TEXTURE_CUBE_MAP_POSITIVE_Y: Framebuffer(),
            gl.GL_TEXTURE_CUBE_MAP_NEGATIVE_Z: Framebuffer(),
            gl.GL_TEXTURE_CUBE_MAP_POSITIVE_Z: Framebuffer(),
        }

        self.views = {
            gl.GL_TEXTURE_CUBE_MAP_NEGATIVE_X: quaternion.from_rotation_vector(
                [0, np.pi / 2, 0]
            ),
            gl.GL_TEXTURE_CUBE_MAP_POSITIVE_X: quaternion.from_rotation_vector(
                [0, -np.pi / 2, 0]
            ),
            gl.GL_TEXTURE_CUBE_MAP_POSITIVE_Y: quaternion.from_rotation_vector(
                [-np.pi / 2, 0, 0]
            ),
            gl.GL_TEXTURE_CUBE_MAP_NEGATIVE_Y: quaternion.from_rotation_vector(
                [np.pi / 2, 0, 0]
            ),
            gl.GL_TEXTURE_CUBE_MAP_POSITIVE_Z: quaternion.from_rotation_vector(
                [0, 0, 0]
            ),
            gl.GL_TEXTURE_CUBE_MAP_NEGATIVE_Z: quaternion.from_rotation_vector(
                [0, np.pi, 0]
            ),
        }

        self.bind()
        for face, fbo in self.frame_buffers.items():
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
        if self.rendered:
            return

        self.bind()

        scene = Scene.current_scene

        previous_camera = scene.camera
        scene.camera = self.camera

        gl.glViewport(0, 0, self.width, self.height)

        for face, frame_buffer in self.frame_buffers.items():
            gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
            frame_buffer.bind()
            scene.camera.rotation = self.views[face]
            self.camera.update()

            # # scene.draw_reflections()
            for model in scene.models:
                if model.visible is False:
                    continue
                for mesh in model.meshes:
                    if not isinstance(mesh.shader, EnvironmentShader):
                        mesh.draw()
                # model.draw()

            scene.camera.update()
            frame_buffer.unbind()

        # reset the viewport
        gl.glViewport(0, 0, scene.window_size[0], scene.window_size[1])

        # scene.projection_matrix = old_p
        scene.camera = previous_camera

        self.unbind()
        self.rendered = True


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
