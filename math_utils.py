import numpy as np


def scale_matrix(scale):
    if np.isscalar(scale):
        scale = [scale, scale, scale]

    scale.append(1)
    return np.diag(scale)


def translation_matrix(vec):
    n = len(vec)
    t = np.identity(n + 1, dtype="f")
    t[:n, -1] = vec
    return t


def rotation_matrix_z(angle):
    c = np.cos(angle)
    s = np.sin(angle)
    r = np.identity(4)
    r[0, 0] = c
    r[0, 1] = s
    r[1, 0] = -s
    r[1, 1] = c
    return r


def rotation_matrix_x(angle):
    c = np.cos(angle)
    s = np.sin(angle)
    r = np.identity(4)
    r[1, 1] = c
    r[1, 2] = s
    r[2, 1] = -s
    r[2, 2] = c
    return r


def rotation_matrix_y(angle):
    c = np.cos(angle)
    s = np.sin(angle)
    r = np.identity(4)
    r[0, 0] = c
    r[0, 2] = -s
    r[2, 0] = s
    r[2, 2] = c
    return r


def rotation_matrix_xyz(x_angle, y_angle, z_angle):
    x = rotation_matrix_x(x_angle)
    y = rotation_matrix_y(y_angle)
    z = rotation_matrix_z(z_angle)
    r = np.matmul(z, np.matmul(y, x))
    return r


def rotation_axis_angle(u, angle):
    c = np.cos(angle)
    s = np.sin(angle)
    r = np.identity(4)
    # u = np.linalg.norm(u)

    x = 0
    y = 1
    z = 2

    r[0, 0] = c + (u[x] ^ 2) * (1 - c)
    r[0, 1] = u[y] * u[x] * (1 - c) + u[z] * s
    r[0, 2] = u[z] * u[x] * (1 - c) - u[y] * s

    r[1, 0] = u[x] * u[y] * (1 - c) - u[z] * s
    r[1, 1] = c + (u[y] ^ 2) * (1 - c)
    r[1, 2] = u[z] * u[y] * (1 - c) + u[x] * s

    r[2, 0] = u[x] * u[z] * (1 - c) + u[y] * s
    r[2, 1] = u[x] * u[z] * (1 - c) - u[x] * s
    r[2, 2] = c + (u[z] ^ 2) * (1 - c)
    return r


def pose_matrix(position=None, orientation=0, scale=1):
    """
    Returns a combined TRS matrix for the pose of a model.
    :param position: the position of the model
    :param orientation: the model orientation (for now assuming a rotation around the Z axis)
    :param scale: the model scale, either a scalar for isotropic scaling, or vector of scale factors
    :return: the 4x4 TRS matrix
    """
    position = position if position is not None else [0, 0, 0]
    # apply the position and orientation of the object
    r = rotation_matrix_z(orientation)
    t = translation_matrix(position)

    # ... and the scale factor
    s = scale_matrix(scale)
    return np.matmul(np.matmul(t, r), s)


def orthogonal_matrix(l, r, t, b, n, f):
    """
    Returns an orthographic projection matrix
    :param l: left clip plane
    :param r: right clip plane
    :param t: top clip plane
    :param b: bottom clip plane
    :param n: near clip plane
    :param f: far clip plane
    :return: A 4x4 orthographic projection matrix
    """
    return np.array([
        [2.0 / (r - l), 0.0, 0.0, (r + l) / (r - l)],
        [0.0, -2.0 / (t - b), 0.0, (t + b) / (t - b)],
        [0.0, 0.0, 2.0 / (f - n), (f + n) / (f - n)],
        [0.0, 0.0, 0.0, 1.0],
    ])


def frustrum_matrix(l, r, t, b, n, f):
    return np.array([
        [2 * n / (r - l), 0, (r + l) / (r - l), 0],
        [0, -2 * n / (t - b), (t + b) / (t - b), 0],
        [0, 0, -(f + n) / (f - n), -2 * f * n / (f - n)],
        [0, 0, -1, 0],
    ])


# Homogeneous coordinates helpers
def make_homogeneous(v):
    return np.hstack([v, 1])


def make_unhomogeneous(vh):
    return vh[:-1] / vh[-1]
