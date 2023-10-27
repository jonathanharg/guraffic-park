import numpy as np
import sys

'''
Functions for reading models from blender.
Source:
https://en.wikipedia.org/wiki/Wavefront_.obj_file
'''


class Mesh:
	'''
	Simple class to hold a mesh data. For now we will only focus on vertices, faces (indices of vertices for each face)
	and normals.
	'''
	def __init__(self, vertices, faces=None, normals=None):
		self.vertices = vertices
		self.faces = faces

		if normals is None:
			self.calculate_normals()
		else:
			self.normals = normals
	
	def calculate_normals(self):
		'''
		method to calculate normals from the mesh faces.
		WS3 TODO: Fix this code to calculate the correct normals
		Use the approach discussed in class:
		1. calculate normal for each face using cross product
		2. set each vertex normal as the average of the normals over all faces it belongs to.
		'''
		self.normals = np.zeros((self.vertices.shape[0], 3), dtype='f')

		# === WS3 Calculate normals ===
		for f in range(self.faces.shape[0]):
			# first calculate the face normal using the cross product of the triangle's sides
			a = self.vertices[self.faces[f, 1]] - self.vertices[self.faces[f, 0]]
			b = self.vertices[self.faces[f, 2]] - self.vertices[self.faces[f, 0]]
			face_normal = np.cross(a, b)

			# we normalise the cross product output to make a normal vector
			face_normal /= np.linalg.norm(face_normal)

			# blend normal on all 3 vertices
			for j in range(3):
				self.normals[self.faces[f, j], :] += face_normal

		# and normalise the vectors
		self.normals /= np.linalg.norm(self.normals, axis=1, keepdims=True)
		# === End WS3 ===


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
		# note that indexing in the file starts at 1, so we need to correct to start at zero
		return ( label, [ [np.uint32(i)-1 for i in v.split('/')] for v in fields[1:] ] )

	else:
		print('(E) Unknown line: {}'.format(fields))
		return None


	return (label, [float(token) for token in fields[1:]])


def load_obj_file(file_name):
	'''
	Function for loading a Blender3D object file. minimalistic, and partial,
	but sufficient for this course. You do not really need to worry about it.
	'''
	vlist = []
	tlist = []
	flist = []

	with open(file_name) as objfile:
		for line in objfile:
			data = process_line(line)

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

	print('--> Model loaded: {} vertices, {} texture vectors and {} faces'.format(len(vlist), len(tlist), len(flist)))

	return Mesh(
		vertices=np.array(vlist, dtype='f'),
		faces=np.array(flist, dtype=np.uint32)[:,:,0]
	)
