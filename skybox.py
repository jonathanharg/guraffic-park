import numpy as np
from OpenGL import GL as gl

from cubeMap import CubeMap
from material import Material
from matutils import poseMatrix
from mesh import CubeMesh, Mesh
from shaders import BaseShaderProgram


class SkyBoxShader(BaseShaderProgram):
    def __init__(self, name="skybox"):
        BaseShaderProgram.__init__(self, name=name)
        self.add_uniform("sampler_cube")

    def bind(self, model, M):
        BaseShaderProgram.bind(self, model, M)
        P = model.scene.perspective_matrix  # get projection matrix from the scene
        V = model.scene.camera.view_matrix  # get view matrix from the camera
        Vr = np.identity(4)
        Vr[:3, :3] = V[:3, :3]

        self.uniforms["PVM"].bind(np.matmul(P, np.matmul(V, M)))
        # self.uniforms['PVM'].bind(np.matmul(V, M))


class SkyBox(Mesh):
    def __init__(self):
        material = Material()
        
        super().__init__(
            scale=100,
            # mesh=CubeMesh(texture=CubeMap(name="skybox/ame_ash"), inside=True),
            mesh=CubeMesh(invert= True),
            # shader=SkyBoxShader(),
            # name="skybox",
        )

    def draw(self):
        gl.glDepthMask(gl.GL_FALSE)
        super().draw()
        gl.glDepthMask(gl.GL_TRUE)
