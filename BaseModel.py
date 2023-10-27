# imports all openGL functions
from OpenGL.GL import *

# and we import a bunch of helper functions
from matutils import *


class BaseModel:
    '''
    Base class for all models, implementing the basic draw function for triangular meshes.
    Inherit from this to create new models.
    '''

    def __init__(self, scene, M, color=[1.,1.,1.], primitive=GL_TRIANGLES):
        '''
        Initialises the model data
        '''

        print('+ Initializing {}'.format(self.__class__.__name__))

        self.scene = scene

        self.primitive = primitive

        # store the object's color
        self.color = color
        self.vertices = None
        self.indices = None
        self.normals = None
        self.vertex_colors = None

        self.vbos = {}
        self.attributes = {}

        # store the position of the model in the scene, ...
        self.M = M

    def initialise_vbo(self, name, data):
        print('Initialising VBO for attribute {}'.format(name))

        # bind the GLSL program to find the attribute locations
        #glUseProgram(self.scene.shaders.program)

        # bind the location of the attribute in the GLSL program to the next index
        # the name of the location must correspond to a 'in' variable in the GLSL vertex shader code
        self.attributes[name] = len(self.vbos)
        glBindAttribLocation(self.scene.shaders.program, self.attributes[name], name)
        print('Binding attribute {} to location {}'.format(name,self.attributes[name]))

        if data is None:
            print('(W) Warning in {}.bind_attribute(): Data array for attribute {} is None!'.format(
                self.__class__.__name__, name))
            return

        # create a buffer object...
        self.vbos[name] = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbos[name])

        # enable the attribute
        glEnableVertexAttribArray(self.attributes[name])

        # Associate the bound buffer to the corresponding input location in the shader
        # Each instance of the vertex shader will get one row of the array
        # so this can be processed in parallel!
        glVertexAttribPointer(index=self.attributes[name], size=data.shape[1], type=GL_FLOAT, normalized=False,
                              stride=0, pointer=None)

        # ... and we set the data in the buffer as the vertex array
        glBufferData(GL_ARRAY_BUFFER, data, GL_STATIC_DRAW)


        # unbind the buffer to avoid side effects
        #glBindBuffer(GL_ARRAY_BUFFER, 0)


    def bind_all_attributes(self):
        '''
        bind all VBOs to the corresponding attributes in the shader program. Call this before rendering.
        '''
        for attribute in self.vbos:
            # bind the buffer corresponding to the attribute
            glBindBuffer(GL_ARRAY_BUFFER,self.vbos[attribute])

            # enable the attribute
            glEnableVertexAttribArray(self.attributes[attribute])


    def bind(self):
        '''
        This method stores the vertex data in a Vertex Buffer Object (VBO) that can be uploaded
        to the GPU at render time.
        '''

        # We use a Vertex Array Object to pack all buffers for rendering in the GPU (see lecture on OpenGL)
        self.vao = glGenVertexArrays(1)

        # bind the VAO to retrieve all buffers and rendering context
        glBindVertexArray(self.vao)

        if self.vertices is None:
            print('(W) Warning in {}.bind(): No vertex array!'.format(self.__class__.__name__))

        # initialise vertex position VBO and link to shader program attribute
        self.initialise_vbo('position', self.vertices)
        self.initialise_vbo('normal', self.normals)
        self.initialise_vbo('color', self.vertex_colors)

        # if indices are provided, put them in a buffer too
        if self.indices is not None:
            self.index_buffer = glGenBuffers(1)
            glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.index_buffer)
            glBufferData(GL_ELEMENT_ARRAY_BUFFER, self.indices, GL_STATIC_DRAW)

        glBindVertexArray(0)
        glBindBuffer(GL_ARRAY_BUFFER,0)

    def draw(self, Mp):
        '''
        Draws the model using OpenGL functions
        :return:
        '''

        if self.vertices is None:
            print('(W) Warning in {}.draw(): No vertex array!'.format(self.__class__.__name__))

        # setup the shader program and provide it the Model, View and Projection matrices to use
        # for rendering this model
        self.scene.shaders.bind(
            M=np.matmul(Mp, self.M),
            V=self.scene.camera.V,
            P=self.scene.P
        )

        # bind the Vertex Array Object so that all buffers are bound correctly and the following operations affect them
        glBindVertexArray(self.vao)

        # check whether the data is stored as vertex array or index array
        if self.indices is not None:
            # draw the data in the buffer using the index array
            glDrawElements(self.primitive, self.indices.flatten().shape[0], GL_UNSIGNED_INT, None )
        else:
            # draw the data in the buffer using the vertex array ordering only.
            glDrawArrays(self.primitive, 0, self.vertices.shape[0])

        # unbind the shader to avoid side effects
        glBindVertexArray(0)

def __del__(self):
    '''
    Release all VBO objects when finished.
    '''
    for vbo in self.vbos.items():
        glDeleteBuffers(1,vbo)

