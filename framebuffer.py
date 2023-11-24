from OpenGL import GL as gl


class Framebuffer:
    """
    Basic class to handle rendering to texture using a framebuffer object.
    """

    def __init__(self, attachment=gl.GL_COLOR_ATTACHMENT0, texture=None):
        """
        Initialise the framebuffer
        :param attachment: Which output of the rendering process to save (gl.GL_COLOR_ATTACHMENT0, gl.GL_DEPTH_ATTACHMENT, ...)
        :param texture: (optional) if provided, link the framebuffer to the texture
        """
        self.attachment = attachment
        self.frame_buffer_object = gl.glGenFramebuffers(1)

        if texture is not None:
            self.prepare(texture)

    def bind(self):
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.frame_buffer_object)

    def unbind(self):
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)

    def prepare(self, texture, target=None, level=0):
        """
        Prepare the Framebuffer by linking its output to a texture
        :param texture: The texture object to render to
        :param target: The target of the rendering, if not the default for the texture (use for cube maps)
        :param level: The mipmap level (ignore)
        :return:
        """
        if target is None:
            target = texture.target

        self.bind()
        gl.glFramebufferTexture2D(
            gl.GL_FRAMEBUFFER, self.attachment, target, texture.texture_id, level
        )
        if self.attachment == gl.GL_DEPTH_ATTACHMENT:
            gl.glDrawBuffer(gl.GL_NONE)
            gl.glReadBuffer(gl.GL_NONE)

        self.unbind()
