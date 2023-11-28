class Material:
    def __init__(
        self,
        name=None,
        Ka=None,
        Kd=None,
        Ks=None,
        Ns=10.0,
        texture=None,
    ):
        self.name = name
        self.Ka = Ka if Ka is not None else [1.0, 1.0, 1.0]
        self.Kd = Kd if Kd is not None else [1.0, 1.0, 1.0]
        self.Ks = Ks if Ks is not None else [1.0, 1.0, 1.0]
        self.Ns = Ns if Ns is not None else [1.0, 1.0, 1.0]
        self.texture = texture
        self.alpha = 1.0


class MaterialLibrary:
    def __init__(self):
        self.materials = []
        self.names = {}

    def add_material(self, material):
        self.names[material.name] = len(self.materials)
        self.materials.append(material)
