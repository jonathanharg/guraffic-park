#version 330 core

in vec3 position;
out vec3 fragment_texCoord;

uniform mat4 PVM;

void main(void)
{
	fragment_texCoord = position;
	gl_Position = PVM * vec4(position, 1.0);
}
