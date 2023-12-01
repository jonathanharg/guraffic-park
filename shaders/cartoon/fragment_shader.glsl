#version 330 core

in vec3 FragPos;
in vec3 Normal;
in vec2 TexCoords;

out vec4 FragCol;

//=== uniforms
uniform vec3 view_pos;
uniform int has_texture;
uniform sampler2D textureObject; // texture object

// material uniforms
uniform vec3 Ka;    // ambient reflection properties of the material
uniform vec3 Kd;    // diffuse reflection propoerties of the material
uniform vec3 Ks;    // specular properties of the material
uniform float Ns;   // specular exponent

// light source
uniform vec3 light_pos; // light direction
uniform vec3 Ia;    // ambient light properties
uniform vec3 Id;    // diffuse properties of the light source
uniform vec3 Is;    // specular properties of the light source


///=== main shader code
void main() {
    vec3 texval = Kd;
    if(has_texture == 1)
        texval = texture(textureObject, TexCoords).rgb;

    vec3 ambient = Ia*texval;

    vec3 light_direction = normalize(-light_pos);
    float diff = max(dot(Normal, light_direction), 0.0);
    vec3 diffuse = Id * diff * texval;

    vec3 viewDir = normalize(view_pos - FragPos);
    vec3 reflectDir = reflect(-light_direction, Normal);
    float spec = pow(max(dot(viewDir, reflectDir),0.0), Ns);

    vec3 sepcular = Is * spec * Ks;


    vec3 result = ambient + diffuse + sepcular;
    FragCol = vec4(result, 1.0);
}


