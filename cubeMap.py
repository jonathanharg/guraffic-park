from OpenGL import GL as gl

from texture import ImageWrapper, Texture

class CubeMap(Texture):
    """
    Class for handling a cube map texture.

    """

    def __init__(
        self,
        name=None,
        files=None,
        wrap=gl.GL_CLAMP_TO_EDGE,
        sample=gl.GL_LINEAR,
        texture_format=gl.GL_RGBA,
        texture_type=gl.GL_UNSIGNED_BYTE,
    ):
        """
        Initialise the cube map texture object
        :param name: If a name is provided, the function will load the faces of the cube from files on the disk in a
        folder of this name
        :param files: If provided, a dictionary containing for each cube face ID the file name to load the texture from
        :param wrap: Which texture wrapping method to use. Default is gl.GL_CLAMP_TO_EDGE which is best for cube maps
        :param sample: Which sampling to use, default is gl.GL_LINEAR
        :param format: The pixel format of the image and texture (gl.GL_RGBA). Do not change.
        :param type: The data format for the texture. Default is gl.GL_UNSIGNED_BYTE (should not be changed)
        """
        self.name = name
        self.texture_format = texture_format
        self.texture_type = texture_type
        self.wrap = wrap
        self.sample = sample
        self.target = gl.GL_TEXTURE_CUBE_MAP  # we set the texture target as a cube map

        # This dictionary contains the file name for each face, if loading from disk (otherwise ignored)
        self.files = {
            gl.GL_TEXTURE_CUBE_MAP_NEGATIVE_X: "left.bmp",
            gl.GL_TEXTURE_CUBE_MAP_POSITIVE_Z: "back.bmp",
            gl.GL_TEXTURE_CUBE_MAP_POSITIVE_X: "right.bmp",
            gl.GL_TEXTURE_CUBE_MAP_NEGATIVE_Z: "front.bmp",
            gl.GL_TEXTURE_CUBE_MAP_POSITIVE_Y: "top.bmp",
            gl.GL_TEXTURE_CUBE_MAP_NEGATIVE_Y: "bottom.bmp",
        }

        # generate the texture.
        self.texture_id = gl.glGenTextures(1)

        # bind the texture
        self.bind()

        # if name is provided, load cube faces from images on disk
        if name is not None:
            self.set(name, files)

        # set what happens for texture coordinates outside [0,1]
        gl.glTexParameteri(self.target, gl.GL_TEXTURE_WRAP_S, wrap)
        gl.glTexParameteri(self.target, gl.GL_TEXTURE_WRAP_T, wrap)

        # set how sampling from the texture is done.
        gl.glTexParameteri(self.target, gl.GL_TEXTURE_MAG_FILTER, sample)
        gl.glTexParameteri(self.target, gl.GL_TEXTURE_MIN_FILTER, sample)

        # unbind the texture
        self.unbind()

    def set(self, name:str , files=None):
        """
        Load the cube's faces from images on the disk
        :param name: The folder in which the images are.
        :param files: A dictionary containing the file name for each face.
        """

        if files is not None:
            self.files = files

        for key, value in self.files.items():
            img = ImageWrapper(f"{name}/{value}")

            # convert the python image object to a plain byte array for passsing to OpenGL
            gl.glTexImage2D(
                key,
                0,
                self.texture_format,
                img.width(),
                img.height(),
                0,
                self.texture_format,
                self.texture_type,
                img.data(self.texture_format),
            )

    def update(self, scene):
        """
        Used to update the texture, does not do anything at the moment, but could be extended for the environment mapping.
        """
        pass
