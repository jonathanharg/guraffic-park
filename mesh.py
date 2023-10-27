from material import Material
import numpy as np

class Mesh:
    '''
    Simple class to hold a mesh data. For now we will only focus on vertices, faces (indices of vertices for each face)
    and normals.
    '''
    def __init__(self, vertices, faces=None, normals=None, material=Material()):
        '''
        Initialises a mesh object.
        :param vertices: A numpy array containing all vertices
        :param faces: [optional] An int array containing the vertex indices for all faces.
        :param normals: [optional] An array of normal vectors, calculated from the faces if not provided.
        :param material: [optional] An object containing the material information for this object
        '''
        self.vertices = vertices
        self.faces = faces
        self.material = material

        print('Creating mesh')
        print('- {} vertices, {} faces'.format(self.vertices.shape[0], self.faces.shape[0]))
        print('- {} vertices per face'.format(self.faces.shape[1]))
        print('- vertices ID in range [{},{}]'.format(np.min(self.faces.flatten()), np.max(self.faces.flatten())))

        if normals is None:
            if faces is None:
                print('(W) Warning: the current code only calculates normals using the face vector of indices, which was not provided here.')
            else:
                self.calculate_normals()
        else:
            self.normals = normals

    def calculate_normals(self):
        '''
        method to calculate normals from the mesh faces.
        Use the approach discussed in class:
        1. calculate normal for each face using cross product
        2. set each vertex normal as the average of the normals over all faces it belongs to.
        '''

        self.normals = np.zeros((self.vertices.shape[0], 3), dtype='f')

        # seen in WS4
        for f in range(self.faces.shape[0]):
            # first calculate the face normal using the cross product of the triangle's sides
            a = self.vertices[self.faces[f, 1]] - self.vertices[self.faces[f, 0]]
            b = self.vertices[self.faces[f, 2]] - self.vertices[self.faces[f, 0]]
            face_normal = np.cross(a, b)

            # blend normal on all 3 vertices
            for j in range(3):
                self.normals[self.faces[f, j], :] += face_normal

        # finally we need to normalise the vectors
        self.normals /= np.linalg.norm(self.normals, axis=1, keepdims=True)