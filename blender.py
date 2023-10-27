import numpy as np

from material import Material,MaterialLibrary
from mesh import Mesh

'''
Functions for reading models from blender. 
Source: 
https://en.wikipedia.org/wiki/Wavefront_.obj_file
'''

def process_line(line):
	'''
	Function for reading the Blender3D object file, line by line. Clearly
	minimalistic and slow as it is, but it will do the job nicely for this course.
	'''
	label = None
	fields = line.split()
	if len(fields) == 0:
		return None

	if fields[0] == '#':
		label = 'comment'
		return (label, fields[1:])

	elif fields[0] == 'v':
		label = 'vertex'
		if len(fields) != 4:
			print('(E) Error, 3 entries expected for vertex')
			return None

	elif fields[0] == 'vt':
		label = 'vertex texture'
		if len(fields) != 3:
			print('(E) Error, 2 entries expected for vertex texture')
			return None

	elif fields[0] == 'mtllib':
		label = 'material library'
		if len(fields) != 2:
			print('(E) Error, material library file name missing')
			return None
		else:
			return (label, fields[1])

	elif fields[0] == 'usemtl':
		label = 'material'
		if len(fields) != 2:
			print('(E) Error, material file name missing')
			return None
		else:
			return (label, fields[1])

	# check this
	elif fields[0] == 's':
		label = 's???'
		return None

	elif fields[0] == 'f':
		label = 'face'
		if len(fields) != 4 and len(fields) != 5:
			print('(E) Error, 3 or 4 entries expected for faces\n{}'.format(line))
			return None


		# multiple formats for faces lines, eg
		# f 586/1 1860/2 1781/3
		# f vi/ti/ni
		# where vi is the vertex index
		# ti is the texture index
		# ni is the normal index (optional)
		return ( label, [ [np.uint32(i) for i in v.split('/')] for v in fields[1:] ] )

	else:
		print('(E) Unknown line: {}'.format(fields))
		return None

	return (label, [float(token) for token in fields[1:]])


def load_material_library(file_name):
	library = MaterialLibrary()
	material = None

	print('-- Loading material library {}'.format(file_name))

	mtlfile = open(file_name)
	for line in mtlfile:
		fields = line.split()
		if len(fields) != 0:
			if fields[0] == 'newmtl':
				if material is not None:
					library.add_material(material)

				material = Material(fields[1])
				print('Found material definition: {}'.format(material.name))
			elif fields[0] == 'Ka':
				material.Ka = np.array(fields[1:], 'f')
			elif fields[0] == 'Kd':
				material.Kd = np.array(fields[1:], 'f')
			elif fields[0] == 'Ks':
				material.Ks = np.array(fields[1:], 'f')
			elif fields[0] == 'Ns':
				material.Ns = float(fields[1])
			elif fields[0] == 'd':
				material.d = float(fields[1])
			elif fields[0] == 'Tr':
				material.d = 1.0 - float(fields[1])
			elif fields[0] == 'illum':
				material.illumination = int(fields[1])
			elif fields[0] == 'map_Kd':
				material.texture = fields[1]

	library.add_material(material)

	print('- Done, loaded {} materials'.format(len(library.materials)))

	return library


def load_obj_file(file_name):
	'''
	Function for loading a Blender3D object file. minimalistic, and partial,
	but sufficient for this course. You do not really need to worry about it.
	'''
	print('Loading mesh(es) from Blender file: {}'.format(file_name))

	vlist = []
	tlist = []
	flist = []
	mlist = []

	# each mesh in the file uses continuous vertex indexing, we will store them as separate mesh.
	voffset = 1

	# list of meshes, indexed by the material name
	meshes = []

	# current material object
	material = None

	with open(file_name) as objfile:
		line_nb = 0 # count line number for easier error locating

		# loop over all lines in the file
		for line in objfile:
			# process the line
			data = process_line(line)

			line_nb += 1 # increment line

			# skip empty lines
			if data is None:
				continue

			elif data[0] == 'vertex':
				vlist.append(data[1])

			elif data[0] == 'normal':
				vlist.append(data[1])

			elif data[0] == 'vertex texture':
				tlist.append(data[1])

			elif data[0] == 'face':
				flist.append(data[1])
				mlist.append(material)

			elif data[0] == 'material library':
				library = load_material_library('models/{}'.format(data[1]))

			# material indicate a new mesh in the file, so we store the previous one if not empty and start
			# a new one.
			elif data[0] == 'material':
				material = library.names[data[1]]
				print('[l.{}] Loading mesh with material: {}'.format(line_nb, data[1]))

	print('File read. Found {} vertices and {} faces.'.format(len(vlist), len(flist)))
	return create_meshes_from_blender( vlist, flist, mlist, library )


def create_meshes_from_blender( vlist, flist, mlist, library ):
	fstart = 0
	material = None
	meshes = []

	# we start by putting all vertices in one array
	varray = np.array(vlist, dtype='f')

	for f in range(len(flist)):
		if material is None:
			material = mlist[f]

		elif material != mlist[f]:  # new mesh is denoted by change in material
			farray = np.array(flist[fstart:f], dtype=np.uint32)[:, :, 0]
			vmax = np.max(farray.flatten())
			vmin = np.min(farray.flatten())-1

			#print('+++ vertices ID in range [{},{}] and vstart={} / vmax={}'.format(np.min(farray.flatten()), np.max(farray.flatten()), vstart, vmax))

			meshes.append(
				Mesh(
					vertices=varray[vmin:vmax,:],
					faces=farray - vmin - 1,
					material=library.materials[material]
				)
			)

			# start the next mesh
			fstart = f

	farray = np.array(flist[fstart:], dtype=np.uint32)[:, :, 0]
	vmax = np.max(farray.flatten())
	vmin = np.min(farray.flatten())-1

	meshes.append(
		Mesh(
			vertices=varray[vmin:vmax,:],
			faces=farray - vmin - 1,
			material=library.materials[material]
		)
	)

	print('--- Created {} mesh(es) from Blender file.'.format(len(meshes)))
	return meshes