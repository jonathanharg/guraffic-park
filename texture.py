import numpy as np
import pygame
from OpenGL import GL as gl


class ImageWrapper:
    def __init__(self, name):
        # load the image from file using pyGame - any other image reading function could be used here.
        # print("Loading image: texture/{}".format(name))
        self.img = pygame.image.load("./textures/{}".format(name))

    def width(self):
        return self.img.get_width()

    def height(self):
        return self.img.get_height()

    def data(self, format=gl.GL_RGB):
        # convert the python image object to a plain byte array for passsing to OpenGL
        if format == gl.GL_RGBA:
            return pygame.image.tostring(self.img, "RGBA", 1)
        elif format == gl.GL_RGB:
            return pygame.image.tostring(self.img, "RGB", 1)


class Texture:
    """
    Class to handle texture loading.
    """

    def __init__(
        self,
        name,
        img=None,
        wrap=gl.GL_REPEAT,
        sample=gl.GL_NEAREST,
        format=gl.GL_RGBA,
        type=gl.GL_UNSIGNED_BYTE,
        target=gl.GL_TEXTURE_2D,
    ):
        self.name = name
        self.format = format
        self.type = type
        self.wrap = wrap
        self.sample = sample
        self.target = target

        self.textureid = gl.glGenTextures(1)

        self.bind()

        if img is None:
            img = ImageWrapper(name)

            # load the texture in the buffer
            gl.glTexImage2D(
                self.target,
                0,
                format,
                img.width(),
                img.height(),
                0,
                format,
                type,
                img.data(format),
            )
        else:
            # if a data array is provided use this
            gl.glTexImage2D(
                self.target, 0, format, img.shape[0], img.shape[1], 0, format, type, img
            )

        # set what happens for texture coordinates outside [0,1]
        gl.glTexParameteri(self.target, gl.GL_TEXTURE_WRAP_S, wrap)
        gl.glTexParameteri(self.target, gl.GL_TEXTURE_WRAP_T, wrap)

        # set how sampling from the texture is done.
        gl.glTexParameteri(self.target, gl.GL_TEXTURE_MAG_FILTER, sample)
        gl.glTexParameteri(self.target, gl.GL_TEXTURE_MIN_FILTER, sample)

        self.unbind()

    def set_shadow_comparison(self):
        self.set_parameter(gl.GL_TEXTURE_COMPARE_MODE, gl.GL_COMPARE_REF_TO_TEXTURE)

    def set_parameter(self, param, value):
        self.bind()
        gl.glTexParameteri(self.target, param, value)
        self.unbind()

    def set_wrap_parameter(self, wrap=gl.GL_REPEAT):
        self.wrap = wrap
        self.bind()
        gl.glTexParameteri(self.target, gl.GL_TEXTURE_WRAP_S, wrap)
        gl.glTexParameteri(self.target, gl.GL_TEXTURE_WRAP_T, wrap)
        self.unbind()

    def set_sampling_parameter(self, sample=gl.GL_NEAREST):
        self.sample = sample
        self.bind()
        gl.glTexParameteri(self.target, gl.GL_TEXTURE_MAG_FILTER, sample)
        gl.glTexParameteri(self.target, gl.GL_TEXTURE_MIN_FILTER, sample)
        self.unbind()

    def set_data_from_image(self, data, width=None, height=None):
        if isinstance(data, np.ndarray):
            width = data.shape[0]
            height = data.shape[1]

        self.bind()

        # load the texture in the buffer
        gl.glTexImage2D(
            self.target, 0, self.format, width, height, 0, self.format, self.type, data
        )

        self.unbind()

    def bind(self):
        gl.glBindTexture(self.target, self.textureid)

    def unbind(self):
        gl.glBindTexture(self.target, 0)
