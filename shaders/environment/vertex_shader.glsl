#version 130

//=== in attributes are read from the vertex array, one row per instance of the shader
in vec3 position;	// the position attribute contains the vertex position
in vec3 normal;		// store the vertex normal

//=== out attributes are interpolated on the face, and passed on to the fragment shader
out vec3 position_view_space;   // the position of the vertex in view coordinates
out vec3 normal_view_space;     // the normal of the vertex in view coordinates


uniform mat4 PVM; 	// the Perspective-View-Model matrix is received as a Uniform
uniform mat4 VM; 	// the View-Model matrix is received as a Uniform
uniform mat3 VMiT;  // The inverse-transpose of the view model matrix, used for normals

void main(void)
{
    gl_Position = PVM * vec4(position, 1.0f);

    position_view_space = vec3( VM * vec4(position, 1.0f) );
    normal_view_space = normalize(VMiT*normal);
}
