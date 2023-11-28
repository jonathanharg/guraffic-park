#version 330 core

in vec3 fragment_texCoord;
out vec4 final_color;

uniform samplerCube sampler_cube;

void main(void)
{
	final_color = texture(sampler_cube, fragment_texCoord);
}
