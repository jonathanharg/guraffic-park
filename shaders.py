# imports all openGL functions
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GL import shaders
from matutils import *
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

    def bind_matrix(self, M=None, number=1, transpose=True):
        '''
        Call this before rendering to bind the Python matrix to the GLSL uniform mat4.
        You will need different methods for different types of uniform, but for now this will
        do for the PVM matrix
        :param number: the number of matrices sent, leave that to 1 for now
        :param transpose: Whether the matrix should be transposed
        '''
        if M is not None:
            self.value = M
        if self.value.shape[0] == 4 and self.value.shape[1] == 4:
            glUniformMatrix4fv(self.location, number, transpose, self.value)
        elif self.value.shape[0] == 3 and self.value.shape[1] == 3:
            glUniformMatrix3fv(self.location, number, transpose, self.value)
        else:
            print('(E) Error: Trying to bind as uniform a matrix of shape {}'.format(self.value.shape))

    def bind(self, value=None):
        if value is not None:
            self.value = value

        if self.value is None:
            print('(E) Error in Uniform.bind(): Invalid value: None')

        if isinstance(self.value, int):
            self.bind_int()

        elif isinstance(self.value, float):
            self.bind_float()

        elif isinstance(self.value, np.ndarray):
            if len(self.value.shape) == 1 or self.value.shape[1] == 1:
                self.bind_vector()
            else:
                self.bind_matrix()
        else:
            print('(E) Error in Uniform.bind() (Uniform: {}): Invalid value type {}'.format(self.name, type(value)))
            raise

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

        if self.value.shape[0] == 2:
            glUniform2fv(self.location, 1, self.value)

        elif self.value.shape[0] == 3:
            glUniform3fv(self.location, 1, self.value)

        elif self.value.shape[0] == 4:
            glUniform4fv(self.location, 1, self.value)

        else:
            print('(E) Error in Uniform.bind_vector(): Vector should be of dimension 2,3 or 4, found {}'.format(self.value.shape[0]))

    def set(self, value):
        '''
        function to set the uniform value (could also access it directly, of course)
        '''
        self.value = value


class Shaders:
    '''
    This is the base class for loading and compiling the GLSL shaders.
    '''
    def __init__(self, name=None, vertex_shader = None, fragment_shader = None):
        '''
        Initialises the shaders
        :param vertex_shader: the name of the file containing the vertex shader GLSL code
        :param fragment_shader: the name of the file containing the fragment shader GLSL code
        '''

        # in order to simplify extension of the class in the future, we start storing uniforms in a dictionary.
        self.uniforms = {
            'PVM': Uniform('PVM'),   # project view model matrix
            'VM': Uniform('VM'),     # view model matrix (necessary for light computations)
            'VMiT': Uniform('VMiT'),  # inverse-transpose of the view model matrix (for normal transformation)
            'mode': Uniform('mode',0),  # rendering mode (only for illustration, in general you will want one shader program per mode)
            'Ka': Uniform('Ka'),
            'Kd': Uniform('Kd'),
            'Ks': Uniform('Ks'),
            'Ns': Uniform('Ns'),
            'light': Uniform('light', np.array([0.,0.,0.], 'f')),
            'Ia': Uniform('Ia'),
            'Id': Uniform('Id'),
            'Is': Uniform('Is'),
        }

        self.name = name
        if name is not None:
            vertex_shader = 'shaders/{}/vertex_shader.glsl'.format(name)
            fragment_shader = 'shaders/{}/fragment_shader.glsl'.format(name)

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


    def add_uniform(self,name):
        self.uniforms[name] = Uniform(name)

    def compile(self):
        '''
        Call this function to compile the GLSL codes for both shaders.
        :return:
        '''
        print('Compiling GLSL shaders...')
        try:
            self.program = shaders.compileProgram(
                shaders.compileShader(self.vertex_shader_source, shaders.GL_VERTEX_SHADER),
                shaders.compileShader(self.fragment_shader_source, shaders.GL_FRAGMENT_SHADER)
            )
        except RuntimeError as error:
            print('(E) An error occured while compiling {} shader:\n {}\n... forwarding exception...'.format(self.name, error)),
            raise error


        # tell OpenGL to use this shader program for rendering
        glUseProgram(self.program)

        # link all uniforms
        for uniform in self.uniforms:
            self.uniforms[uniform].link(self.program)

    def bind(self, P, V, M, mode, light, material):
        '''
        Call this function to enable this GLSL Program (you can have multiple GLSL programs used during rendering!)
        '''

        # tell OpenGL to use this shader program for rendering
        glUseProgram(self.program)

        # set the PVM matrix uniform
        self.uniforms['PVM'].set(np.matmul(P,np.matmul(V,M)))

        # set the VM matrix uniform
        self.uniforms['VM'].set(np.matmul(V,M))

        # set the VMiT matrix uniform
        self.uniforms['VMiT'].set(np.linalg.inv(np.matmul(V,M))[:3,:3].transpose())

        # set the mode to the program
        self.uniforms['mode'].set(mode)

        # set material properties
        self.set_material_uniforms(material)

        # set the light properties
        self.set_light_uniforms(light,V)

        # bind everything
        for uniform in self.uniforms.values():
            uniform.bind()


    def set_light_uniforms(self, light, V):
        self.uniforms['light'].set(unhomog(np.dot(V, homog(light.position))))
        self.uniforms['Ia'].set(np.array(light.Ia, 'f'))
        self.uniforms['Id'].set(np.array(light.Id, 'f'))
        self.uniforms['Is'].set(np.array(light.Is, 'f'))

    def set_material_uniforms(self, material):
        self.uniforms['Ka'].set(np.array(material.Ka, 'f'))
        self.uniforms['Kd'].set(np.array(material.Kd, 'f'))
        self.uniforms['Ks'].set(np.array(material.Ks, 'f'))
        self.uniforms['Ns'].set(material.Ns)

    def unbind(self):
        glUseProgram(0)

    def set_mode(self, mode):
        self.uniforms['mode'].set(mode)

class FlatShader(Shaders):
    def __init__(self):
        Shaders.__init__(self, name='flat')

class GouraudShader(Shaders):
    def __init__(self):
        Shaders.__init__(self, name='gouraud')

class PhongShader(Shaders):
    def __init__(self):
        Shaders.__init__(self, name='phong')

class BlinnShader(Shaders):
    def __init__(self):
        Shaders.__init__(self, name='blinn')

