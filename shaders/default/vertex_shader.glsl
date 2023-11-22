#version 130

in vec3 position;   // vertex position
uniform mat4 PVM; // the Perspective-View-Model matrix is received as a Uniform

// main function of the shader
void main() {
    gl_Position = PVM * vec4(position, 1.0f);  // first we transform the position using PVM matrix
}