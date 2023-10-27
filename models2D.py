from BaseModel import BaseModel
from OpenGL.GL import *
from matutils import *

class TriangleModel(BaseModel):
    '''
    A very simple model for drawing a single triangle. This is only for illustration purpose.
    '''
    def __init__(self, scene, M, color=[1., 1., 1.]):
        BaseModel.__init__(self, scene, M=M, color=color)

        # each row encodes the coordinate for one vertex.
        # given that we are drawing in 2D, the last coordinate is always zero.
        self.vertices = np.array(
            [
                [0.0, 0.0, 0.0],
                [0.0, 1.0, 0.0],
                [1.0, 0.0, 0.0]
            ], 'f')
        self.bind()

class ComplexModel(BaseModel):
    def __init__(self, scene, M):
        BaseModel.__init__(self, scene, M=M)
        self.components = []

    def draw(self, Mp):
        # draw all component primitives
        for component in self.components:
            component.draw(np.matmul(Mp, self.M))

class SquareModel(BaseModel):
    def __init__(self, scene, M, color=[1., 1., 1.]):
        BaseModel.__init__(self, scene, M=M, color=color, primitive=GL_QUADS)
        self.vertices = np.array([
            [0., 0., 0.],
            [1., 0., 0.],
            [1., 1., 0.],
            [0., 1., 0.]
        ], 'f')
        self.bind()

class TreeModel(ComplexModel):
    def __init__(self, scene, M ):
        ComplexModel.__init__(self, scene=scene, M=M)

        # list of simple components
        self.components = [
            SquareModel(scene, M=poseMatrix(position=[-0.125, 0., 0], scale=[0.25,0.5,1.], orientation=0.), color=[0.6, 0.2, 0.2]),
            TriangleModel(scene, M=poseMatrix(position=[0, 0.5, 0], scale=[0.25,0.5,1]), color=[0., 1., 0.]),
            TriangleModel(scene, M=poseMatrix(position=[0, 0.5, 0], scale=[-0.25,0.5,1]), color=[0., 1., 0.]),
            TriangleModel(scene, M=poseMatrix(position=[0, 0.75, 0], scale=[0.25, 0.5, 1]), color=[0., 1., 0.]),
            TriangleModel(scene, M=poseMatrix(position=[0, 0.75, 0], scale=[-0.25, 0.5, 1]), color=[0., 1., 0.]),
            TriangleModel(scene, M=poseMatrix(position=[0, 1.0, 0], scale=[0.25, 0.5, 1]), color=[0., 1., 0.]),
            TriangleModel(scene, M=poseMatrix(position=[0, 1.0, 0], scale=[-0.25, 0.5, 1]), color=[0., 1., 0.]),
        ]