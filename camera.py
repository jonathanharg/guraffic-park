# pygame is just used to create a window with the operating system on which to draw.
import pygame

# imports all openGL functions
from OpenGL.GL import *
from OpenGL.GLU import *

# we will use numpy to store data in arrays
import numpy as np

# import a bunch of useful matrix functions (for translation, scaling etc)
from matutils import *


class Camera:
    '''
    Base class for handling the camera.
    '''


    def __init__(self, size):
        self.size = size
        self.V = np.identity(4)
        self.V[2,3] = -5.0
        self.phi = 0.
        self.psi = 0.
        self.distance = 5.
        self.center = [0.,0.,0.]
        #self.update()

    def update(self):
        # we change the origin of the coordinate system
        D = -translationMatrix(self.center)

        # we rotate around both X and Y axes by the set angles
        R = np.matmul(rotationMatrixX(self.psi), rotationMatrixY(self.phi))

        # we move the camera away from the origin, looking back. 
        T = translationMatrix([0., 0., -self.distance])

        # note the order of the matrices. It is important!
        self.V = np.matmul(np.matmul(T, R), D)
