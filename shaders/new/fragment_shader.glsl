#version 330 core
out vec4 OutColor;
in vec3 FragPos;
in vec3 FragNormal;
in vec3 FragColor;
in vec2 FragTexCoords;

uniform sampler2D textureObject;
uniform int has_texture;
uniform vec3 light;
uniform vec3 viewPos;

void main(){
    vec3 color = vec3(1.0f);
    if(has_texture == 1)
        color = texture(textureObject, FragTexCoords).rgb;
    
    vec3 ambient = 0.05 * color;
    vec3 lightDirection = normalize(light);
    vec3 normal = normalize(FragNormal);
    float diff = max(dot(lightDirection, normal), 0.0);
    vec3 diffuse = diff * color;

    vec3 viewDirection = normalize(viewPos - FragPos);
    float spec = 0.0;

    vec3 halfwayDir = normalize(lightDirection + viewDirection);
    spec = pow(max(dot(normal, halfwayDir), 0.0), 8.0);
    vec3 specular = vec3(0.3) * spec;
    OutColor = vec4(ambient + diffuse + specular, 1.0);
}