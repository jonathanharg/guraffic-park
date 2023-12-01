#version 130

in vec3 normal_view_space;
in vec3 position_view_space;
out vec4 final_color;

uniform samplerCube sampler_cube;
uniform mat3 VT;

void main(void)
{
	vec3 normal_view_space_normalized = normalize(normal_view_space);
	vec3 reflected = reflect(normalize(-position_view_space), normal_view_space_normalized);

	final_color = texture(sampler_cube, normalize(reflect(VT*reflected, vec3(1,0,0))));
}
