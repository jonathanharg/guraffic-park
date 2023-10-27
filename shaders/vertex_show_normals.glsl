# version 130
in vec4 position;	
out vec4 frag_color4;

uniform mat4 PVM; 

void main() {
    gl_Position = PVM * gl_Vertex;
    frag_color4 = gl_color;
}
