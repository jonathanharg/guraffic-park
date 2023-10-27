# version 130 // required to use OpenGL core standard

//=== 'in' attributes are passed on from the vertex shader's 'out' attributes, and interpolated for each fragment
in vec4 vertex_color;
in vec2 fTexCoord;

//=== 'out' attributes are the output image, usually only one for the colour of each pixel
out vec4 frag_color;

// === uniform here the texture obect to sample from
uniform sampler2D textureObj;
uniform int mode;

///=== main shader code
void main() {
    if(mode == 3){ 
      frag_color = texture2D(textureObj, fTexCoord);
    }
    else {
      frag_color = vertex_color;
    }
}
