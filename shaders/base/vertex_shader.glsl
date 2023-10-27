#version 130		// required to use OpenGL core standard

//=== in attributes are read from the vertex array, one row per instance of the shader
in vec3 position;	// the position attribute contains the vertex position
in vec4 color; 		// store the vertex colour

//=== out attributes are interpolated on the face, and passed on to the fragment shader
out vec4 vertex_color;  // the output of the shader will be the colour of the vertex

//=== uniforms 
uniform mat4 PVM; 	// the Perspective-View-Model matrix is received as a Uniform


///=== main shader code
void main() {
    gl_Position = PVM * vec4(position, 1.0f);  	// first we transform the position using PVM matrix
    vertex_color = color;		// at this stage, the colour simply passed on.  
}
