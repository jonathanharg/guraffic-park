#version 130		// required to use OpenGL core standard
in vec3 position;	// the position attribute contains the vertex position
in vec4 color; 		// store the vertex colour
in vec3 normal;
in vec2 texcoord;
out vec4 vertex_color;  // the output of the shader will be the colour of the vertex
out vec2 fTexCoord;
uniform mat4 PVM; 	// the Perspective-View-Model matrix is received as a Uniform
uniform int mode;

void main() {
    gl_Position = PVM * vec4(position, 1.0f);  	// first we transform the position using PVM matrix
    fTexCoord = texcoord;

    switch(mode){
	case 0: vertex_color = color; break;
	case 1: vertex_color = vec4(normal,1.0f); break;
	case 2: vertex_color = vec4(texcoord,1.0f,1.0f);	break;
	default: vertex_color = vec4(0.0f,0.0f,0.0f,1.0f);
    }
}
