import os
from typing import Self

import imgui
import numpy as np
from OpenGL import GL as gl

from blender import find_file, load_obj_file
from entity import Entity
from matutils import rotationMatrixXYZ
from mesh import Mesh
from shaders import BaseShaderProgram, FlatShader, PhongShader


class Model(Entity):
    untitled_model_count = 0

    # TODO: MAKE THIS HOLD A LIST OF MESHES
    # def __init__(self, meshes: list[Mesh], name=None, **kwargs) -> None:
    def __init__(self, meshes: Mesh, name=None, **kwargs) -> None:
        super().__init__(**kwargs)
        self.visible = True
        self.primitive = gl.GL_TRIANGLES
        self.shader: BaseShaderProgram = FlatShader()
        self.mesh = meshes
        self.vertex_buffer_objects = {}
        self.attributes = {}
        self.vertex_array_object = gl.glGenVertexArrays(1)
        self.index_buffer = None

        if name is not None:
            self.name = name
        else:
            Model.untitled_model_count += 1
            untitled_model_number = str(Model.untitled_model_count).zfill(3)
            self.name = f"Model.{untitled_model_number}"

        if self.mesh.faces.shape[1] == 4:
            self.primitive = gl.GL_QUADS

        self.bind()

        if self.shader is not None:
            self.bind_shader(self.shader)

    @classmethod
    def from_obj(self, obj_path: str, **kwargs) -> Self:
        file_path = find_file(obj_path, ["models/"])
        name = os.path.basename(file_path)
        meshes = load_obj_file(obj_path)
        print("Creating model from {obj_path}")
        model = Model(meshes[0], name=name, **kwargs)
        return model

    def draw(self):
        if not self.visible:
            return

        gl.glBindVertexArray(self.vertex_array_object)

        if self.shader is not None:
            self.shader.bind(self, self.get_pose_matrix())

        for offset, texture in enumerate(self.mesh.textures):
            gl.glActiveTexture(gl.GL_TEXTURE0 + offset)
            texture.bind()

        if self.mesh.faces is not None:
            gl.glDrawElements(
                self.primitive,
                self.mesh.faces.flatten().shape[0],
                gl.GL_UNSIGNED_INT,
                None,
            )
        else:
            gl.glDrawArrays(self.primitive, 0, self.mesh.vertices.shape[0])

        gl.glBindVertexArray(0)
        if self.shader is not None:
            self.shader.unbind()

        with imgui.begin(f"Debug {self.name}"):
            _, self.position = imgui.drag_float3("Position", self.x, self.y, self.z)

            rotation_changed, rotation = imgui.drag_float3(
                "Rotation",
                np.degrees(self.x_rot()),
                np.degrees(self.y_rot()),
                np.degrees(self.z_rot()),
            )
            if rotation_changed:
                self.rotation = rotationMatrixXYZ(
                    np.deg2rad(rotation[0]),
                    np.deg2rad(rotation[1]),
                    np.deg2rad(rotation[2]),
                )

            _, scale = imgui.drag_float("Scale", self.scale)
            self.scale = scale if scale != 0 else 0.0001

            imgui.text(f"Rotation Matrix: {self.rotation}")

    def vbo__del__(self):
        """
        Release all VBO objects when finished.
        """
        for vbo in self.vertex_buffer_objects.items():
            gl.glDeleteBuffers(1, vbo)

        gl.glDeleteVertexArrays(1, self.vertex_array_object.tolist())

    def bind(self):
        """
        This method stores the vertex data in a Vertex Buffer Object (VBO) that can be uploaded
        to the GPU at render time.
        """

        # bind the VAO to retrieve all buffers and rendering context
        gl.glBindVertexArray(self.vertex_array_object)

        if self.mesh.vertices is None:
            print("(W) Warning: No vertex array!")

        # initialise vertex position VBO and link to shader program attribute
        self.initialise_vertex_buffer_object("position", self.mesh.vertices)
        self.initialise_vertex_buffer_object("normal", self.mesh.normals)
        self.initialise_vertex_buffer_object("color", self.mesh.colors)
        self.initialise_vertex_buffer_object("texCoord", self.mesh.texture_coords)
        self.initialise_vertex_buffer_object("tangent", self.mesh.tangents)
        self.initialise_vertex_buffer_object("binormal", self.mesh.binormals)

        # if indices are provided, put them in a buffer too
        if self.mesh.faces is not None:
            self.index_buffer = gl.glGenBuffers(1)
            gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, self.index_buffer)
            gl.glBufferData(
                gl.GL_ELEMENT_ARRAY_BUFFER, self.mesh.faces, gl.GL_STATIC_DRAW
            )

        # finally we unbind the VAO and VBO when we're done to avoid side effects
        gl.glBindVertexArray(0)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, 0)

    def initialise_vertex_buffer_object(self, attribute, data):
        if data is None:
            print(
                f"(W) Warning bind_attribute(): Data array for attribute {attribute} is None!"
            )
            return

        # bind the location of the attribute in the GLSL program to the next index
        # the name of the location must correspond to a 'in' variable in the GLSL vertex shader code
        self.attributes[attribute] = len(self.vertex_buffer_objects)

        # create a buffer object...
        self.vertex_buffer_objects[attribute] = gl.glGenBuffers(1)
        # and bind it
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.vertex_buffer_objects[attribute])

        # enable the attribute
        gl.glEnableVertexAttribArray(self.attributes[attribute])

        # Associate the bound buffer to the corresponding input location in the shader
        # Each instance of the vertex shader will get one row of the array
        # so this can be processed in parallel!
        gl.glVertexAttribPointer(
            index=self.attributes[attribute],
            size=data.shape[1],
            type=gl.GL_FLOAT,
            normalized=False,
            stride=0,
            pointer=None,
        )

        # ... and we set the data in the buffer as the vertex array
        gl.glBufferData(gl.GL_ARRAY_BUFFER, data, gl.GL_STATIC_DRAW)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, 0)

    def bind_shader(self, shader):
        """
        If a new shader is bound, we need to re-link it to ensure attributes are correctly linked.
        """
        # TODO: THIS IS BUSTED
        if self.shader is None or self.shader.name is not shader:
            if isinstance(shader, str):
                self.shader = PhongShader(shader)
            else:
                self.shader = shader

            # bind all attributes and compile the shader
            self.shader.compile(self.attributes)
