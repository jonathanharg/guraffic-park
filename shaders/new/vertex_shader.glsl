#version 330 core
in vec3 aPos;
in vec3 aNormal;
in vec3 aColor;
in vec2 aTexCoords;

out vec3 FragPos;
out vec3 FragNormal;
out vec3 FragColor;
out vec2 FragTexCoords;

uniform mat4 PVM;

void main(){
    FragPos = aPos;
    FragNormal = aNormal;
    FragColor = aColor;
    FragTexCoords = aTexCoords;
    gl_Position = PVM * vec4(FragPos, 1.0);
}