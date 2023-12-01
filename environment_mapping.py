"""
Environment Mapping Texture.
"""

import numpy as np
import quaternion
from OpenGL import GL as gl

from camera import Camera
from cube_map import CubeMap
from framebuffer import Framebuffer
from scene import Scene
from shaders import EnvironmentShader


class EnvironmentMappingTexture(CubeMap):
    """Generate an environment map for reflections."""

    def __init__(self, camera: Camera, width=200, height=200):
        """Create an EnvironmentMap.

        Args:
            camera (Camera): The camera to use for the reflection cubemap.
            width (int, optional): Width of the reflection map. Defaults to 200.
            height (int, optional): Height of the reflection map. Defaults to 200.
        """
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

        # Rotate the camera to the correct axis
        self.views = {
            gl.GL_TEXTURE_CUBE_MAP_NEGATIVE_X: quaternion.from_rotation_vector([
                0, np.pi / 2, 0
            ]),
            gl.GL_TEXTURE_CUBE_MAP_POSITIVE_X: quaternion.from_rotation_vector([
                0, -np.pi / 2, 0
            ]),
            gl.GL_TEXTURE_CUBE_MAP_POSITIVE_Y: quaternion.from_rotation_vector([
                -np.pi / 2, 0, 0
            ]),
            gl.GL_TEXTURE_CUBE_MAP_NEGATIVE_Y: quaternion.from_rotation_vector([
                np.pi / 2, 0, 0
            ]),
            gl.GL_TEXTURE_CUBE_MAP_POSITIVE_Z: quaternion.from_rotation_vector([
                0, 0, 0
            ]),
            gl.GL_TEXTURE_CUBE_MAP_NEGATIVE_Z: quaternion.from_rotation_vector([
                0, np.pi, 0
            ]),
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
        """Update the environment map. If you want to update the environment map after it has already been rendered, set `self.rendered` to `False` first"""
        # Don't re-render the map unless necessary
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
                    # Don't draw models with reflections, because they will not have an environment map, and appear black.
                    if not isinstance(mesh.shader, EnvironmentShader):
                        mesh.draw()

            scene.camera.update()
            frame_buffer.unbind()

        # reset the viewport
        gl.glViewport(0, 0, scene.window_size[0], scene.window_size[1])

        scene.camera = previous_camera

        self.unbind()
        self.rendered = True
