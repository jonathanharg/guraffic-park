# imports all openGL functions
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GL import shaders

# we will use numpy to store data in arrays
import numpy as np

class Uniform:
    '''
    We create a simple class to handle uniforms, this is not necessary,
    but allow to put all relevant code in one place
    '''
    def __init__(self, name, value=None):
        '''
        Initialise the uniform parameter
        :param name: the name of the uniform, as stated in the GLSL code
        '''
        self.name = name
        self.value = value
        self.location = -1

    def link(self, program):
        '''
        This function needs to be called after compiling the GLSL program to fetch the location of the uniform
        in the program from its name
        :param program: the GLSL program where the uniform is used
        '''
        self.location = glGetUniformLocation(program=program, name=self.name)
        if self.location == -1:
            print('(E) Warning, no uniform {}'.format(self.name))

    def bind_matrix(self, number=1, transpose=True):
        '''
        Call this before rendering to bind the Python matrix to the GLSL uniform mat4.
        You will need different methods for different types of uniform, but for now this will
        do for the PVM matrix
        :param number: the number of matrices sent, leave that to 1 for now
        :param transpose: Whether the matrix should be transposed
        '''
        glUniformMatrix4fv(self.location, number, transpose, self.value)

    def bind_int(self, value=None):
        if value is not None:
            self.value = value
        glUniform1i(self.location, self.value)

    def bind_float(self, value=None):
        if value is not None:
            self.value = value
        glUniform1f(self.location, self.value)

    def bind_texture(self):
        glUniform1i(self.location, 0)

    def bind_vector(self, value=None):
        if value is not None:
            self.value = value
        if value.shape[0] == 2:
            glUniform2fv(self.location, 1, value)
        elif value.shape[0] == 3:
            glUniform3fv(self.location, 1, value)
        elif value.shape[0] == 4:
            glUniform4fv(self.location, 1, value)
        else:
            print('(E) Error in Uniform.bind_vector(): Vector should be of dimension 2,3 or 4, found {}'.format(value.shape[0]))

    def set(self, value):
        '''
        function to set the uniform value (could also access it directly, of course)
        '''
        self.value = value


class Shaders:
    '''
    This is the base class for loading and compiling the GLSL shaders.
    '''
    def __init__(self, vertex_shader = None, fragment_shader = None):
        '''
        Initialises the shaders
        :param vertex_shader: the name of the file containing the vertex shader GLSL code
        :param fragment_shader: the name of the file containing the fragment shader GLSL code
        '''

        # in order to simplify extension of the class in the future, we start storing uniforms in a dictionary.
        self.uniforms = {
            'PVM': Uniform('PVM'),   # project view matrix
            'mode': Uniform('mode',0)  # rendering mode (only for illustration, in general you will want one shader program per mode)
        }

        # load the vertex shader GLSL code
        if vertex_shader is None:
            self.vertex_shader_source = '''
                #version 130
                
                // all input attributes sent via VBOs, one row of each array is sent to 
                // each instance of the vertex shader
                in vec3 position;   // vertex position
                in vec3 normal;    // vertex normal
                in vec3 color;      // vertex color (RGBA)
                
                // the output attribute is interpolated at each location on the face, 
                // and sent to the fragment shader 
                out vec3 vertex_color;  // the output of the shader will be the colour of the vertex
                
                // Uniforms are parameters that are the same for all vertices/fragments
                // ie, model-view matrices, light sources, material, etc.  
                uniform mat4 PVM; // the Perspective-View-Model matrix is received as a Uniform
                uniform int mode; // the rendering mode (only for demo)
                
                // main function of the shader
                void main() {
                    gl_Position = PVM * vec4(position, 1.0f);  // first we transform the position using PVM matrix
                    switch(mode){
                        case 1: vertex_color = color; break;
                        case 2: vertex_color = position; break;
                        case 3: vertex_color = normal; break;
                        default: vertex_color = vec3(0.0f,0.0f,0.0f);
                    }                     
                }
            '''
        else:
            print('Load vertex shader from file: {}'.format(vertex_shader))
            with open(vertex_shader, 'r') as file:
                self.vertex_shader_source = file.read()
            print(self.vertex_shader_source)

        # load the fragment shader GLSL code
        if fragment_shader is None:
            self.fragment_shader_source = '''
                #version 130
                // parameters interpolated from the output of the vertex shader
                in vec3 vertex_color;      // the vertex colour is received from the vertex shader
                
                // main function of the shader
                void main() {                   
                      gl_FragColor = vec4(vertex_color, 1.0f);      // for now, we just apply the colour uniformly
                }
            '''
        else:
            print('Load fragment shader from file: {}'.format(fragment_shader))
            with open(fragment_shader, 'r') as file:
                self.fragment_shader_source = file.read()
            print(self.fragment_shader_source)


    def compile(self):
        '''
        Call this function to compile the GLSL codes for both shaders.
        :return:
        '''
        print('Compiling GLSL shaders...')
        self.program = shaders.compileProgram(
            shaders.compileShader(self.vertex_shader_source, shaders.GL_VERTEX_SHADER),
            shaders.compileShader(self.fragment_shader_source, shaders.GL_FRAGMENT_SHADER)
        )

        # tell OpenGL to use this shader program for rendering
        glUseProgram(self.program)

        # link all uniforms
        for uniform in self.uniforms:
            self.uniforms[uniform].link(self.program)

    def bind(self, P, V, M):
        '''
        Call this function to enable this GLSL Program (you can have multiple GLSL programs used during rendering!)
        :return:
        '''

        # tell OpenGL to use this shader program for rendering
        glUseProgram(self.program)

        # set the PVM matrix uniform
        self.uniforms['PVM'].set( np.matmul(P,np.matmul(V,M)) )

        # and send it to the program
        self.uniforms['PVM'].bind_matrix()

        # bind the mode to the program
        self.uniforms['mode'].bind_int()

    def unbind(self):
        glUseProgram(0)

    def set_mode(self, mode):
        self.uniforms['mode'].set(mode)