#version 330 core

//=== in attributes are read from the vertex array, one row per instance of the shader
in vec3 position;	// the position attribute contains the vertex position
in vec3 normal;		// store the vertex normal
in vec3 color; 		// store the vertex colour
in vec2 texCoord;

out vec3 FragPos;
out vec3 Normal;
out vec2 TexCoords;

//=== uniforms
uniform mat4 PVM; 	// the Perspective-View-Model matrix is received as a Uniform
uniform mat4 VM; 	// the View-Model matrix is received as a Uniform
uniform mat3 VMiT;  // The inverse-transpose of the view model matrix, used for normals
uniform mat4 model;


void main() {
    FragPos == vec3(model * vec4(position, 1.0));
    Normal = normalize(VMiT*normal);
    TexCoords = texCoord;

    gl_Position = PVM * vec4(position, 1.0f);
}
