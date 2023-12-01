"""Classes for loading and managing textures."""

import numpy as np
import pygame
from OpenGL import GL as gl


class ImageWrapper:
    """A wrapper for a pygame image."""

    def __init__(self, name):
        # load the image from file using pyGame
        self.image_data = pygame.image.load(f"./textures/{name}")

    def data(self, image_format=gl.GL_RGB):
        """convert the python image object to a plain byte array for passing to OpenGL"""
        if image_format == gl.GL_RGBA:
            return pygame.image.tostring(self.image_data, "RGBA", 1)
        if image_format == gl.GL_RGB:
            return pygame.image.tostring(self.image_data, "RGB", 1)


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
        image_format=gl.GL_RGBA,
        image_type=gl.GL_UNSIGNED_BYTE,
        target=gl.GL_TEXTURE_2D,
    ):
        self.name = name
        self.format = image_format
        self.type = image_type
        self.wrap = wrap
        self.sample = sample
        self.target = target

        self.texture_id = gl.glGenTextures(1)

        self.bind()

        if img is None:
            img = ImageWrapper(name)

            # load the texture in the buffer
            gl.glTexImage2D(
                self.target,
                0,
                image_format,
                img.image_data.get_width(),
                img.image_data.get_height(),
                0,
                image_format,
                image_type,
                img.data(image_format),
            )
        else:
            # if a data array is provided use this
            gl.glTexImage2D(
                self.target,
                0,
                image_format,
                img.shape[0],
                img.shape[1],
                0,
                image_format,
                image_type,
                img,
            )

        # set what happens for texture coordinates outside [0,1]
        gl.glTexParameteri(self.target, gl.GL_TEXTURE_WRAP_S, wrap)
        gl.glTexParameteri(self.target, gl.GL_TEXTURE_WRAP_T, wrap)

        # set how sampling from the texture is done.
        gl.glTexParameteri(self.target, gl.GL_TEXTURE_MAG_FILTER, sample)
        gl.glTexParameteri(self.target, gl.GL_TEXTURE_MIN_FILTER, sample)

        self.unbind()

    def bind(self):
        gl.glBindTexture(self.target, self.texture_id)

    def unbind(self):
        gl.glBindTexture(self.target, 0)
