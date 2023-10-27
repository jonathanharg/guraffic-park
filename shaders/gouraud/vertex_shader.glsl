#version 130		// required to use OpenGL core standard

//=== in attributes are read from the vertex array, one row per instance of the shader
in vec3 position;	// the position attribute contains the vertex position
in vec4 color; 		// store the vertex colour
in vec3 normal;		// store the vertex normal
in vec2 texcoord;	// store the texture coordinates

//=== out attributes are interpolated on the face, and passed on to the fragment shader
out vec4 vertex_color;  // the output of the shader will be the colour of the vertex
out vec2 fTexCoord;	// pass on the texture coordinates
out vec3 frag_normal;

//=== uniforms 
uniform mat4 PVM; 	// the Perspective-View-Model matrix is received as a Uniform
uniform mat4 VMiT;
uniform int mode;	// the rendering mode (better to code different shaders!)
uniform vec3 Ka; 
uniform vec3 Kd; 
uniform vec3 Ks;
uniform float Ns;  

void main() {
    gl_Position = PVM * vec4(position, 1.0f);  	// first we transform the position using PVM matrix
    fTexCoord = texcoord;
    frag_normal = normalize(vec3(VMiT*vec4(normal, 1.0f)));

    vec3 K = (Ka+Ks+Ks)*Ns;

    switch(mode){
	case 0: vertex_color = color; break;
	case 1: vertex_color = vec4(normal,1.0f); break;
	case 2: vertex_color = vec4(texcoord,1.0f,1.0f); break;
	default: vertex_color = vec4(0.0f,0.0f,0.0f,1.0f);
    }
}
