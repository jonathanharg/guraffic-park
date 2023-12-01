"""Classes for OpenGL Materials and Wavefront Material Libraries"""


class Material:
    """Defines a material for a mesh."""

    def __init__(
        self,
        name=None,
        Ka: list[float] = None,
        Kd: list[float] = None,
        Ks: list[float] = None,
        Ns=10.0,
        texture=None,
    ):
        """Create a new Material.

        Args:
            name (str, optional): The name of the material. Defaults to None.
            Ka (list[float], optional): The material ambient. Defaults to None.
            Kd (list[float], optional): The material diffuse. Defaults to None.
            Ks (list[float], optional): The material specular. Defaults to None.
            Ns (float, optional): _description_. Defaults to 10.0.
            texture (Texture, optional): The image texture. Defaults to None.
        """
        self.name = name
        self.Ka = Ka if Ka is not None else [1.0, 1.0, 1.0]
        self.Kd = Kd if Kd is not None else [1.0, 1.0, 1.0]
        self.Ks = Ks if Ks is not None else [1.0, 1.0, 1.0]
        self.Ns = Ns if Ns is not None else [1.0, 1.0, 1.0]
        self.texture = texture


class MaterialLibrary:
    """A material library for an Wavefront file. Symbolic representation of a `.mtl`."""

    def __init__(self):
        self.materials = []
        self.names = {}

    def add_material(self, material):
        """Add a material to the material library"""
        self.names[material.name] = len(self.materials)
        self.materials.append(material)
