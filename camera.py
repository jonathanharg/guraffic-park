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
        self.V[2,3] = -5.0 # we translate the camera five units back, looking at the origin
        self.phi = 0.
        self.psi = 0.
        self.distance = 5.
        self.center = [0.,0.,0.]

    def update(self):
        T0 = translationMatrix(self.center)
        R = np.matmul(rotationMatrixX(self.psi), rotationMatrixY(self.phi))
        T = translationMatrix([0., 0., -self.distance])
        self.V = np.matmul(np.matmul(T, R), T0)