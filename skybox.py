import numpy as np
from OpenGL import GL as gl

from cubeMap import CubeMap
from material import Material
from mesh import CubeMesh
from model import Model
from scene import Scene
from shaders import Shader


class SkyBoxShader(Shader):
    def __init__(self, name="skybox"):
        super().__init__(name=name)
        self.compile({})
        self.add_uniform("sampler_cube")

    def bind(self, model):
        Shader.bind(self, model)
        
        P = Scene.current_scene.projection_matrix  # get projection matrix from the scene
        V = Scene.current_scene.camera.view_matrix  # get view matrix from the camera


        self.uniforms["PVM"].bind(np.matmul(P, np.matmul(V, model.world_pose)))


class SkyBox(Model):
    def __init__(self):
        material = Material(name="skybox", texture=CubeMap(name="skybox/ame_ash"))
        
        super().__init__(
            scale=100,
            meshes=[CubeMesh(invert= True, material=material)],
            shader=SkyBoxShader(),
        )

    def draw(self):
        gl.glDepthMask(gl.GL_FALSE)
        super().draw()
        gl.glDepthMask(gl.GL_TRUE)
