"""
Functions for reading models from blender. 
Source: 
https://en.wikipedia.org/wiki/Wavefront_.obj_file

Minor changes from workshop code. Some variable renaming and improved file finding.
"""

import os

import numpy as np

from material import Material, MaterialLibrary
from mesh import Mesh


def find_file(name: str, subfolders: list[str] = None) -> str:
    """Find a file in the project directory by name

    Args:
        name (str): Name of the file
        subfolders (list[str], optional): Folders to search. Defaults to "textures/" and "models/".

    Raises:
        FileNotFoundError: Throws if file is not found.

    Returns:
        str: Full file path
    """
    if subfolders is None:
        subfolders = ["textures/", "models/"]

    main_directory = os.path.dirname(__file__)

    # Search in parent directory first
    if os.path.isfile(os.path.join(main_directory, name)):
        return os.path.join(main_directory, name)

    # Then search in the subfolders
    for folder in subfolders:
        if os.path.isfile(os.path.join(main_directory, folder, name)):
            return os.path.join(main_directory, folder, name)

    raise FileNotFoundError(f" (E) File {name} not found!")


def process_line(line):
    """
    Function for reading the Blender3D object file, line by line. Clearly
    minimalistic and slow as it is, but it will do the job nicely for this course.
    """
    label = None
    fields = line.split()

    # If line is empty or its a comment or enables/disables smooth shading
    if len(fields) == 0 or fields[0] == "#" or fields[0] == "s":
        return None

    if fields[0] == "mtllib":
        label = "material library"
        if len(fields) != 2:
            print("(E) Error, material library file name missing")
            return None
        return (label, fields[1])

    if fields[0] == "usemtl":
        label = "material"
        if len(fields) != 2:
            print("(E) Error, material file name missing")
            return None
        return (label, fields[1])

    if fields[0] == "v":
        label = "vertex"
        if len(fields) != 4:
            print("(E) Error, 3 entries expected for vertex")
            return None

    elif fields[0] == "vt":
        label = "vertex texture"
        if len(fields) != 3:
            print("(E) Error, 2 entries expected for vertex texture")
            return None

    elif fields[0] == "f":
        label = "face"
        if len(fields) != 4 and len(fields) != 5:
            print(f"(E) Error, 3 or 4 entries expected for faces (line {line})")
            return None

        # multiple formats for faces lines, eg
        # f 586/1 1860/2 1781/3
        # f vi/ti/ni
        # where vi is the vertex index
        # ti is the texture index
        # ni is the normal index (optional)
        return (label, [[np.uint32(i) for i in v.split("/")] for v in fields[1:]])

    else:
        # print("(E) Unknown line: {}".format(fields))
        return None

    return (label, [float(token) for token in fields[1:]])


def load_material_library(file_name):
    library = MaterialLibrary()
    material = None

    # print("-- Loading material library {}".format(file_name))

    with open(file_name, encoding="utf-8") as mtlfile:
        for line in mtlfile:
            fields = line.split()
            if len(fields) != 0:
                if fields[0] == "newmtl":
                    if material is not None:
                        library.add_material(material)

                    material = Material(fields[1])
                    # print("Found material definition: {}".format(material.name))
                elif fields[0] == "Ka":
                    material.Ka = np.array(fields[1:], "f")
                elif fields[0] == "Kd":
                    material.Kd = np.array(fields[1:], "f")
                elif fields[0] == "Ks":
                    material.Ks = np.array(fields[1:], "f")
                elif fields[0] == "Ns":
                    material.Ns = float(fields[1])
                elif fields[0] == "d":
                    material.d = float(fields[1])
                elif fields[0] == "Tr":
                    material.d = 1.0 - float(fields[1])
                elif fields[0] == "illum":
                    material.illumination = int(fields[1])
                elif fields[0] == "map_Kd":
                    material.texture = fields[1]

    library.add_material(material)

    # print("- Done, loaded {} materials".format(len(library.materials)))

    return library


def load_obj_file(file_name):
    """
    Function for loading a Blender3D object file. minimalistic, and partial,
    but sufficient for this course. You do not really need to worry about it.
    """
    vertices = []  # list of vertices
    vertex_textures = []  # list of texture vectors
    faces = []  # list of polygonal faces
    material_names = []  # list of material names

    line_no_list = []
    mesh_id = 0
    mesh_list = []

    # current material object
    material = None

    file = find_file(file_name, ["models/"])

    with open(file, encoding="utf-8") as obj_file:
        line_no = 0  # count line number for easier error locating

        # loop over all lines in the file
        for line in obj_file:
            # process the line
            data = process_line(line)

            line_no += 1  # increment line

            # skip empty lines
            if data is None:
                continue

            if data[0] == "vertex":
                vertices.append(data[1])

            elif data[0] == "normal":
                vertices.append(data[1])

            elif data[0] == "vertex texture":
                vertex_textures.append(data[1])

            elif data[0] == "face":
                if len(data[1]) == 3:
                    faces.append(data[1])
                    mesh_list.append(mesh_id)
                    material_names.append(material)
                    line_no_list.append(line_no)
                else:
                    # converts quads into pairs of  triangles
                    face1 = [data[1][0], data[1][1], data[1][2]]
                    faces.append(face1)
                    mesh_list.append(mesh_id)
                    material_names.append(material)
                    line_no_list.append(line_no)

                    face2 = [data[1][0], data[1][2], data[1][3]]
                    faces.append(face2)
                    mesh_list.append(mesh_id)
                    material_names.append(material)
                    line_no_list.append(line_no)

            elif data[0] == "material library":
                library_path = find_file(data[1], ["models/"])
                library = load_material_library(library_path)

            # material indicate a new mesh in the file, so we store the previous one if not empty and start
            # a new one.
            elif data[0] == "material":
                material = library.names[data[1]]
                mesh_id += 1

    return create_meshes_from_blender(
        vertices,
        faces,
        material_names,
        vertex_textures,
        library,
        mesh_list,
    )


def create_meshes_from_blender(
    vertices, faces, material_names, vertex_textures, library, mesh_list
):
    start_face = 0
    mesh_id = 1
    meshes = []

    # we start by putting all vertices in one array
    vertex_array = np.array(vertices, dtype="f")

    # and all texture vectors
    texture_array = np.array(vertex_textures, dtype="f")

    material = material_names[start_face]

    for face in range(len(faces)):
        if mesh_id != mesh_list[face]:  # new mesh is denoted by change in material
            # print(
            #     "Creating new mesh %i, faces %i-%i, line %i, with material %i: %s"
            #     % (
            #         mesh_id,
            #         fstart,
            #         f,
            #         lnlist[fstart],
            #         mlist[fstart],
            #         library.materials[mlist[fstart]].name,
            #     )
            # )
            try:
                mesh = create_mesh(
                    vertex_array,
                    texture_array,
                    faces,
                    start_face,
                    face,
                    library,
                    material,
                )
                meshes.append(mesh)
            except Exception as e:
                print("(W) could not load mesh!")
                print(e)
                raise

            mesh_id = mesh_list[face]

            # start the next mesh
            start_face = face
            material = material_names[start_face]

    # add the last mesh
    try:
        meshes.append(
            create_mesh(
                vertex_array,
                texture_array,
                faces,
                start_face,
                len(faces),
                library,
                material,
            )
        )
    except:
        print("(W) could not load mesh!")
        raise

    # print("--- Created {} mesh(es) from Blender file.".format(len(meshes)))
    return meshes


def create_mesh(varray, tarray, flist, fstart, f, library, material):
    # select faces for this mesh
    farray = np.array(flist[fstart:f], dtype=np.uint32)

    # and vertices
    vmax = np.max(farray[:, :, 0].flatten())
    vmin = np.min(farray[:, :, 0].flatten()) - 1

    # fix blender texture intexing
    textures = fix_blender_textures(tarray, farray, varray)
    if textures is not None:
        textures = textures[vmin:vmax, :]

    return Mesh(
        vertices=varray[vmin:vmax, :],
        faces=farray[:, :, 0] - vmin - 1,
        material=library.materials[material],
        texture_coords=textures,
    )


def fix_blender_textures(textures, faces, vertices):
    """
    Corrects the indexing of textures in Blender file for OpenGL.
    Blender allows for multiple indexing of vertices and textures, which is not supported by OpenGL.
    This function ensures that indexing is consistent.
    :param textures: Original Blender texture UV values
    :param faces: Blender faces multiple-index
    :return: a new texture array indexed according to vertices.
    """
    # (OpenGL, unlike Blender, does not allow for multiple indexing!)

    if faces.shape[2] == 1:
        # print(
        #     "(W) No texture indices provided, setting texture coordinate array as None!"
        # )
        return None

    new_textures = np.zeros((vertices.shape[0], 2), dtype="f")

    for f in range(faces.shape[0]):
        for j in range(faces.shape[1]):
            new_textures[faces[f, j, 0] - 1, :] = textures[faces[f, j, 1] - 1, :]

    return new_textures
