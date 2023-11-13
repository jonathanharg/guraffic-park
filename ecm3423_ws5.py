import numpy as np
from OpenGL import GL as gl

from BaseModel import BaseModel
from blender import Mesh, load_obj_file
from matutils import poseMatrix
from scene import Scene


class DrawModelFromObjFile(BaseModel):
    """
    Base class for all models, inherit from this to create new models
    """

    def __init__(self, scene, M, file):
        """
        Initialises the model data
        """

        BaseModel.__init__(self, scene=scene, M=M),

        # load all data from the blender file
        mesh = load_obj_file(file)

        # initialises the vertices of the shape
        self.vertices = mesh.vertices

        # initialises the faces of the shape
        self.indices = mesh.faces[:, :]

        # initialise the normals per vertex
        self.normals = mesh.normals

        if self.indices.shape[1] == 3:
            self.primitive = gl.GL_TRIANGLES

        elif self.indices.shape[1] == 4:
            self.primitive = gl.GL_QUADS

        else:
            print(
                "(E) Error in DrawModelFromObjFile.__init__(): index array must have 3 (triangles) or 4 (quads) columns, found {}!".format(
                    self.indices.shape[1]
                )
            )
            raise

        # default vertex colors to one (white)
        self.vertex_colors = np.ones((self.vertices.shape[0], 3), dtype="f")

        if self.normals is None:
            print("(W) No normal array was provided.")
            print("--> setting to zero.")
            self.normals = np.zeros(self.vertices.shape, dtype="f")

        # and bind the data to a vertex array
        self.bind()


class ColorTestModel(BaseModel):
    """
    Draws a simple square to test the different colour rendering modes
    """

    def __init__(self, scene, M, color=[1.0, 1.0, 1.0]):
        BaseModel.__init__(self, scene, M=M, color=color, primitive=gl.GL_QUADS)
        # we draw a simple square
        self.vertices = np.array(
            [[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [1.0, 1.0, 0.0], [0.0, 1.0, 0.0]], "f"
        )

        # set the color for each vertex
        self.vertex_colors = np.array(
            [[1.0, 1.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]], "f"
        )

        # set the normals for each vertex
        self.normals = np.array(
            [[0.0, 0.0, 1.0], [0.0, 0.0, 1.0], [0.0, 0.0, 1.0], [0.0, 0.0, 1.0]], "f"
        )

        self.bind()


# === WS5: Drawing a Sphere ===
class SphereModel(BaseModel):
    """
    Class for drawing a sphere on the fly.
    WS5.
    """

    def __init__(self, scene, M=poseMatrix(), nvert=10, nhoriz=20):
        BaseModel.__init__(self, scene, M=M, primitive=gl.GL_TRIANGLES)

        # we calculate the number of vertices given the number
        # of horizontal and vertical slices
        n = (nvert - 1) * nhoriz + 2

        # and initialise a vertex array (note this needs to be
        # an array of floats!)
        self.vertices = np.zeros((n, 3), "f")

        # we then calculate the angular slices, vertically and horizontally
        vslice = np.pi / nvert
        hslice = 2.0 * np.pi / nhoriz

        # and we set the first and last vertices as the top and bottom poles.
        self.vertices[0, :] = [0.0, 1.0, 0.0]  # ,0,0,0]
        self.vertices[-1, :] = [0.0, -1.0, 0.0]  # ,nvert,0,n-1]

        print("nvert={}, vslice={}".format(nvert, vslice))
        print("nhoriz={}, hslice={}".format(nhoriz, hslice))

        # we then loop over all longitudes to set strips of vertices
        for i in range(nvert - 1):
            # caculate coordinates from longitude and latitude
            y = np.cos((i + 1) * vslice)
            r = np.sin((i + 1) * vslice)
            # print('i={}, y={}, r={}'.format(i,y,r))

            # and go around the circle
            for j in range(nhoriz):
                v = 1 + i * nhoriz + j
                self.vertices[v, 0] = r * np.cos(j * hslice)
                self.vertices[v, 1] = y
                self.vertices[v, 2] = r * np.sin(j * hslice)

        # This was the easy part!
        # we then need to calculate the indices of the triangular faces on
        # the sphere.
        # It is a bit more difficult, but if you go one step at a time with the
        # help of pen and paper, it isn't too hard.

        # first we calculate the number of faces (note that the poles have
        # no triangle).
        nfaces = nhoriz * 2 + (nvert - 2) * (nhoriz) * 2
        self.indices = np.zeros((nfaces, 3), dtype=np.uint32)
        k = 0

        # we do the top and bottom crowns of the sphere first: they are peculiar
        # because all faces in the top and bottom link to one of the poles.
        for i in range(nhoriz - 1):
            # top, all faces link to the north pole
            self.indices[k, 0] = 0
            self.indices[k, 1] = i + 1
            self.indices[k, 2] = i + 2
            k += 1

            # bottom, all faces link to the south pole
            lastrow = n - nhoriz - 2
            self.indices[k, 0] = lastrow + i + 2
            self.indices[k, 1] = lastrow + i + 1
            self.indices[k, 2] = n - 1
            k += 1

        # last triangle at the top, joining the circle
        self.indices[k, :] = [0, nhoriz, 1]

        # last triangle at the bottom, joining the circle
        self.indices[k + 1, :] = [lastrow + 1, n - 2, n - 1]
        k += 2

        # now that we have taken care of the special cases, we can draw the rest
        # of the faces in a large double loop.
        # Note that you could fix this loop to handle all special cases,
        # but it makes the code more complicated.
        for j in range(1, nvert - 1):
            for i in range(nhoriz - 1):
                # we calculate the index of the previous row
                lastrow = nhoriz * (j - 1) + 1
                # and the current row index
                row = nhoriz * j + 1

                # and we set the first triangle
                self.indices[k, 0] = row + i
                self.indices[k, 1] = row + i + 1
                self.indices[k, 2] = lastrow + i
                k += 1

                # and the second. The ordering is important for back-face cullimg.
                self.indices[k, 0] = row + i + 1
                self.indices[k, 1] = lastrow + i + 1
                self.indices[k, 2] = lastrow + i
                k += 1

            # last two triangles on this row, closing the loop
            self.indices[k, :] = [row + nhoriz - 1, row, lastrow + nhoriz - 1]
            k += 1
            self.indices[k, :] = [row, lastrow, lastrow + nhoriz - 1]
            k += 1

        # we then create a mesh from those faces and vertices
        mesh = Mesh(vertices=self.vertices, faces=self.indices)

        self.vertices = mesh.vertices
        self.indices = mesh.faces
        self.normals = mesh.normals

        self.bind()


# === End WS5 ===

if __name__ == "__main__":
    # initialises the scene object
    scene = Scene()

    scene.add_models_list(
        [
            # ColorTestModel(scene, M=poseMatrix(position=[-2, 0., 0])),
            # DrawModelFromObjFile(scene=scene, M=poseMatrix(), file='models/bunny_world.obj'),
            SphereModel(scene, M=poseMatrix(position=[+2.0, 0.0, 0.0]))
        ]
    )

    # starts drawing the scene
    scene.run()
