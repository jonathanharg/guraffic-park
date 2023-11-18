import numpy as np
from OpenGL import GL as gl

from matutils import poseMatrix
from mesh import Mesh
from shaders import PhongShader
from texture import Texture


class BaseModel:
    """
    Base class for all models, implementing the basic draw function for triangular meshes.
    Inherit from this to create new models.
    """

    def __init__(
        self,
        scene,
        M=poseMatrix(),
        mesh=Mesh(),
        color=[1.0, 1.0, 1.0],
        primitive=gl.GL_TRIANGLES,
        visible=True,
    ):
        """
        Initialises the model data
        """
        # if this flag is set to False, the model is not rendered
        self.visible = visible
        # store the scene reference
        self.scene = scene
        # store the type of primitive to draw
        self.primitive = primitive
        # # store the object's color (deprecated now that we have per-vertex colors)
        # self.color = color
        # store the shader program for rendering this model
        self.shader = None

        # mesh data
        self.mesh = mesh
        if self.mesh.textures == 1:
            self.mesh.textures.append(Texture("lena.bmp"))

        # TODO: Fix this
        self.name = "self.mesh.name"
        # self.vertices = None
        # self.indices = None
        # self.normals = None
        # self.vertex_colors = None
        # self.textureCoords = None
        # self.textures = []

        # dict of VBOs
        self.vertex_buffer_objects = {}

        # dict of attributes
        self.attributes = {}

        # store the position of the model in the scene, ...
        self.position_matrix = M

        # We use a Vertex Array Object to pack all buffers for rendering in the GPU (see lecture on OpenGL)
        self.vertex_array_object = gl.glGenVertexArrays(1)

        # this buffer will be used to store indices, if using shared vertex representation
        self.index_buffer = None

    def initialise_vertex_buffer_object(self, property, data):
        if data is None:
            # TODO: FIX THIS
            # print(
            #     "(W) Warning in {}.bind_attribute(): Data array for attribute {} is None!".format(
            #         self.__class__.__name__, property
            #     )
            # )
            return

        # bind the location of the attribute in the GLSL program to the next index
        # the name of the location must correspond to a 'in' variable in the GLSL vertex shader code
        self.attributes[property] = len(self.vertex_buffer_objects)

        # create a buffer object...
        self.vertex_buffer_objects[property] = gl.glGenBuffers(1)
        # and bind it
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.vertex_buffer_objects[property])

        # enable the attribute
        gl.glEnableVertexAttribArray(self.attributes[property])

        # Associate the bound buffer to the corresponding input location in the shader
        # Each instance of the vertex shader will get one row of the array
        # so this can be processed in parallel!
        gl.glVertexAttribPointer(
            index=self.attributes[property],
            size=data.shape[1],
            type=gl.GL_FLOAT,
            normalized=False,
            stride=0,
            pointer=None,
        )

        # ... and we set the data in the buffer as the vertex array
        gl.glBufferData(gl.GL_ARRAY_BUFFER, data, gl.GL_STATIC_DRAW)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, 0)

    def bind_shader(self, shader):
        """
        If a new shader is bound, we need to re-link it to ensure attributes are correctly linked.
        """
        if self.shader is None or self.shader.name is not shader:
            if isinstance(shader, str):
                self.shader = PhongShader(shader)
            else:
                self.shader = shader

            # bind all attributes and compile the shader
            self.shader.compile(self.attributes)

    def bind(self):
        """
        This method stores the vertex data in a Vertex Buffer Object (VBO) that can be uploaded
        to the GPU at render time.
        """

        # bind the VAO to retrieve all buffers and rendering context
        gl.glBindVertexArray(self.vertex_array_object)

        if self.mesh.vertices is None:
            print(
                "(W) Warning in {}.bind(): No vertex array!".format(
                    self.__class__.__name__
                )
            )

        # initialise vertex position VBO and link to shader program attribute
        self.initialise_vertex_buffer_object("position", self.mesh.vertices)
        self.initialise_vertex_buffer_object("normal", self.mesh.normals)
        self.initialise_vertex_buffer_object("color", self.mesh.colors)
        self.initialise_vertex_buffer_object("texCoord", self.mesh.texture_coords)
        self.initialise_vertex_buffer_object("tangent", self.mesh.tangents)
        self.initialise_vertex_buffer_object("binormal", self.mesh.binormals)

        # if indices are provided, put them in a buffer too
        if self.mesh.faces is not None:
            self.index_buffer = gl.glGenBuffers(1)
            gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, self.index_buffer)
            gl.glBufferData(
                gl.GL_ELEMENT_ARRAY_BUFFER, self.mesh.faces, gl.GL_STATIC_DRAW
            )

        # finally we unbind the VAO and VBO when we're done to avoid side effects
        gl.glBindVertexArray(0)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, 0)

    def draw(self, Mp=poseMatrix()):
        """
        Draws the model using OpenGL functions.
        :param Mp: The model matrix of the parent object, for composite objects.
        :param shaders: the shader program to use for drawing
        """

        if not self.visible:
            return

        if self.mesh.vertices is None:
            print(
                "(W) Warning in {}.draw(): No vertex array!".format(
                    self.__class__.__name__
                )
            )

        # bind the Vertex Array Object so that all buffers are bound correctly and following operations affect them
        gl.glBindVertexArray(self.vertex_array_object)

        # setup the shader program and provide it the Model, View and Projection matrices to use
        # for rendering this model
        if self.shader is not None:
            self.shader.bind(model=self, M=np.matmul(Mp, self.position_matrix))

        # print('---> object {} rendered using shader {}'.format(self.name, self.shader.name))

        # bind all textures. Note that your shader needs to handle each one with a sampler object.
        for unit, tex in enumerate(self.mesh.textures):
            gl.glActiveTexture(gl.GL_TEXTURE0 + unit)
            tex.bind()

        # check whether the data is stored as vertex array or index array
        if self.mesh.faces is not None:
            # draw the data in the buffer using the index array
            gl.glDrawElements(
                self.primitive,
                self.mesh.faces.flatten().shape[0],
                gl.GL_UNSIGNED_INT,
                None,
            )
        else:
            # draw the data in the buffer using the vertex array ordering only.
            gl.glDrawArrays(self.primitive, 0, self.mesh.vertices.shape[0])

        # unbind the shader to avoid side effects
        gl.glBindVertexArray(0)
        if self.shader is not None:
            self.shader.unbind()

    def vbo__del__(self):
        """
        Release all VBO objects when finished.
        """
        for vbo in self.vertex_buffer_objects.items():
            gl.glDeleteBuffers(1, vbo)

        gl.glDeleteVertexArrays(1, self.vertex_array_object.tolist())


class DrawModelFromMesh(BaseModel):
    """
    Base class for all models, inherit from this to create new models
    """

    def __init__(self, scene, M, mesh, name=None, shader=None, visible=True):
        """
        Initialises the model data
        """

        BaseModel.__init__(self, scene=scene, M=M, mesh=mesh, visible=visible)

        if name is not None:
            self.name = name

        # and we check which primitives we need to use for drawing
        if self.mesh.faces.shape[1] == 3:
            self.primitive = gl.GL_TRIANGLES

        elif self.mesh.faces.shape[1] == 4:
            self.primitive = gl.GL_QUADS

        else:
            print(
                "(E) Error in DrawModelFromObjFile.__init__(): index array must have 3 (triangles) or 4 (quads) columns, found {}!".format(
                    self.indices.shape[1]
                )
            )

        self.bind()

        if shader is not None:
            self.bind_shader(shader)
