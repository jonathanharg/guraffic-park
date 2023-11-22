import numpy as np
from OpenGL import GL as gl
from entity import Entity
from material import Material
from shaders import Shader, FlatShader, PhongShader
from texture import Texture


class Mesh(Entity):
    """
    Simple class to hold a mesh data. For now we will only focus on vertices, faces (indices of vertices for each face)
    and normals.
    """

    def __init__(
        self,
        vertices=None,
        faces=None,
        normals=None,
        texture_coords=None,
        material=Material(),
        shader: Shader = PhongShader(),
        **kwargs
    ):
        """
        Initialises a mesh object.
        :param vertices: A numpy array containing all vertices
        :param faces: [optional] An int array containing the vertex indices for all faces.
        :param normals: [optional] An array of normal vectors, calculated from the faces if not provided.
        :param material: [optional] An object containing the material information for this object
        """
        super().__init__(**kwargs)
        self.vertices = vertices
        self.faces = faces
        self.material = material
        self.colors = None
        self.texture_coords = texture_coords
        self.textures = []
        self.tangents = None
        self.binormals = None
        self.primitive = gl.GL_TRIANGLES
        self.shader= shader
        self.vertex_buffer_objects = {}
        self.attributes = {}
        self.vertex_array_object = gl.glGenVertexArrays(1)
        self.index_buffer = None

        if normals is None:
            if faces is None:
                print(
                    "(W) Warning: the current code only calculates normals using the face vector of indices, which was not provided here."
                )
            else:
                self.calculate_normals()
        else:
            self.normals = normals

        if material.texture is not None:
            self.textures.append(Texture(material.texture))
        
        # Assume if one uses quads, they all do
        if self.faces.shape[1] == 4:
            self.primitive = gl.GL_QUADS

        self.bind()
        self.bind_shader(self.shader)


    def calculate_normals(self):
        """
        method to calculate normals from the mesh faces.
        Use the approach discussed in class:
        1. calculate normal for each face using cross product
        2. set each vertex normal as the average of the normals over all faces it belongs to.
        """

        self.normals = np.zeros((self.vertices.shape[0], 3), dtype="f")
        if self.texture_coords is not None:
            self.tangents = np.zeros((self.vertices.shape[0], 3), dtype="f")
            self.binormals = np.zeros((self.vertices.shape[0], 3), dtype="f")

        for f in range(self.faces.shape[0]):
            # first calculate the face normal using the cross product of the triangle's sides
            a = self.vertices[self.faces[f, 1]] - self.vertices[self.faces[f, 0]]
            b = self.vertices[self.faces[f, 2]] - self.vertices[self.faces[f, 0]]
            face_normal = np.cross(a, b)

            # tangent
            if self.texture_coords is not None:
                txa = (
                    self.texture_coords[self.faces[f, 1], :]
                    - self.texture_coords[self.faces[f, 0], :]
                )
                txb = (
                    self.texture_coords[self.faces[f, 2], :]
                    - self.texture_coords[self.faces[f, 2], :]
                )
                face_tangent = txb[0] * a - txa[0] * b
                face_binormal = -txb[1] * a + txa[1] * b

            # blend normal on all 3 vertices
            for j in range(3):
                self.normals[self.faces[f, j], :] += face_normal
                if self.texture_coords is not None:
                    self.tangents[self.faces[f, j], :] += face_tangent
                    self.binormals[self.faces[f, j], :] += face_binormal

        # finally we need to normalize the vectors
        self.normals /= np.linalg.norm(self.normals, axis=1, keepdims=True)
        if self.texture_coords is not None:
            self.tangents /= np.linalg.norm(self.tangents, axis=1, keepdims=True)
            self.binormals /= np.linalg.norm(self.binormals, axis=1, keepdims=True)

    
    def draw(self):
        gl.glBindVertexArray(self.vertex_array_object)

        self.shader.bind(self)

        for offset, texture in enumerate(self.textures):
            gl.glActiveTexture(gl.GL_TEXTURE0 + offset)
            texture.bind()

        if self.faces is not None:
            gl.glDrawElements(
                self.primitive,
                self.faces.flatten().shape[0],
                gl.GL_UNSIGNED_INT,
                None,
            )
        else:
            gl.glDrawArrays(self.primitive, 0, self.vertices.shape[0])

        gl.glBindVertexArray(0)
        self.shader.unbind()
    
    
    def vbo__del__(self):
        """
        Release all VBO objects when finished.
        """
        for vbo in self.vertex_buffer_objects.items():
            gl.glDeleteBuffers(1, vbo)

        gl.glDeleteVertexArrays(1, self.vertex_array_object.tolist())

    def bind(self):
        """
        This method stores the vertex data in a Vertex Buffer Object (VBO) that can be uploaded
        to the GPU at render time.
        """

        # bind the VAO to retrieve all buffers and rendering context
        gl.glBindVertexArray(self.vertex_array_object)

        if self.vertices is None:
            print("(W) Warning: No vertex array!")

        # initialise vertex position VBO and link to shader program attribute
        self.initialise_vertex_buffer_object("position", self.vertices)
        self.initialise_vertex_buffer_object("normal", self.normals)
        self.initialise_vertex_buffer_object("color", self.colors)
        self.initialise_vertex_buffer_object("texCoord", self.texture_coords)
        self.initialise_vertex_buffer_object("tangent", self.tangents)
        self.initialise_vertex_buffer_object("binormal", self.binormals)

        # if indices are provided, put them in a buffer too
        if self.faces is not None:
            self.index_buffer = gl.glGenBuffers(1)
            gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, self.index_buffer)
            gl.glBufferData(
                gl.GL_ELEMENT_ARRAY_BUFFER, self.faces, gl.GL_STATIC_DRAW
            )

        # finally we unbind the VAO and VBO when we're done to avoid side effects
        gl.glBindVertexArray(0)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, 0)

    def initialise_vertex_buffer_object(self, attribute, data):
        if data is None:
            return

        # bind the location of the attribute in the GLSL program to the next index
        # the name of the location must correspond to a 'in' variable in the GLSL vertex shader code
        self.attributes[attribute] = len(self.vertex_buffer_objects)

        # create a buffer object...
        self.vertex_buffer_objects[attribute] = gl.glGenBuffers(1)
        # and bind it
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.vertex_buffer_objects[attribute])

        # enable the attribute
        gl.glEnableVertexAttribArray(self.attributes[attribute])

        # Associate the bound buffer to the corresponding input location in the shader
        # Each instance of the vertex shader will get one row of the array
        # so this can be processed in parallel!
        gl.glVertexAttribPointer(
            index=self.attributes[attribute],
            size=data.shape[1],
            type=gl.GL_FLOAT,
            normalized=False,
            stride=0,
            pointer=None,
        )

        # ... and we set the data in the buffer as the vertex array
        gl.glBufferData(gl.GL_ARRAY_BUFFER, data, gl.GL_STATIC_DRAW)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, 0)
    
    # @property
    # def shader_new(self):
    #     return self.shader
    
    # @shader_new.setter
    # def shader(self, value: Shader):
    #     value.compile(self.attributes)
    #     self.shader = value


    def bind_shader(self, shader: Shader):
        """
        If a new shader is bound, we need to re-link it to ensure attributes are correctly linked.
        """
        # TODO: THIS IS BUSTED
        if self.shader.name is not shader:
            if isinstance(shader, str):
                self.shader = PhongShader(shader)
            else:
                self.shader = shader

            # bind all attributes and compile the shader
            self.shader.bind_attributes(self.attributes)


class CubeMesh(Mesh):
    def __init__(self,invert = False, **kwargs):
        vertices = np.array(
            [
                [-1.0, -1.0, -1.0],  # 0
                [+1.0, -1.0, -1.0],  # 1
                [-1.0, +1.0, -1.0],  # 2
                [+1.0, +1.0, -1.0],  # 3
                [-1.0, -1.0, +1.0],  # 4
                [-1.0, +1.0, +1.0],  # 5
                [+1.0, -1.0, +1.0],  # 6
                [+1.0, +1.0, +1.0],  # 7
            ],
            dtype="f",
        )

        faces = np.array(
            [
                # back
                [1, 0, 2],
                [1, 2, 3],
                # right
                [2, 0, 4],
                [2, 4, 5],
                # left
                [1, 3, 7],
                [1, 7, 6],
                # front
                [5, 4, 6],
                [5, 6, 7],
                # bottom
                [0, 1, 4],
                [4, 1, 6],
                # top
                [2, 5, 3],
                [5, 7, 3],
            ],
            dtype=np.uint32,
        )

        if invert:
            faces = faces[:, np.argsort([0, 2, 1])]

        super().__init__(vertices,faces, **kwargs)
