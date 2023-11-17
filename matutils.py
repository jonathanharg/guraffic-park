import numpy as np


def scaleMatrix(scale):
    if np.isscalar(scale):
        scale = [scale, scale, scale]

    scale.append(1)
    return np.diag(scale)


def translationMatrix(t):
    n = len(t)
    T = np.identity(n + 1, dtype="f")
    T[:n, -1] = t
    return T


def rotationMatrixZ(angle):
    c = np.cos(angle)
    s = np.sin(angle)
    R = np.identity(4)
    R[0, 0] = c
    R[0, 1] = s
    R[1, 0] = -s
    R[1, 1] = c
    return R


def rotationMatrixX(angle):
    c = np.cos(angle)
    s = np.sin(angle)
    R = np.identity(4)
    R[1, 1] = c
    R[1, 2] = s
    R[2, 1] = -s
    R[2, 2] = c
    return R


def rotationMatrixY(angle):
    c = np.cos(angle)
    s = np.sin(angle)
    R = np.identity(4)
    R[0, 0] = c
    R[0, 2] =- s
    R[2, 0] = s
    R[2, 2] = c
    return R

def rotationMatrixXYZ(x_angle, y_angle, z_angle):
    x = rotationMatrixX(x_angle)
    y = rotationMatrixY(y_angle)
    z = rotationMatrixZ(z_angle)
    R = np.matmul(z, np.matmul(y, x))
    return R

def rotationAxisAngle(u, angle):
    c = np.cos(angle)
    s = np.sin(angle)
    R = np.identity(4)
    # u = np.linalg.norm(u)

    x = 0
    y = 1
    z = 2

    R[0, 0] = c + (u[x] ^ 2) * (1 - c)
    R[0, 1] = u[y] * u[x] * (1 - c) + u[z] * s
    R[0, 2] = u[z] * u[x] * (1 - c) - u[y] * s

    R[1, 0] = u[x] * u[y] * (1 - c) - u[z] * s
    R[1, 1] = c + (u[y] ^ 2) * (1 - c)
    R[1, 2] = u[z] * u[y] * (1 - c) + u[x] * s

    R[2, 0] = u[x] * u[z] * (1 - c) + u[y] * s
    R[2, 1] = u[x] * u[z] * (1 - c) - u[x] * s
    R[2, 2] = c + (u[z] ^ 2) * (1 - c)
    return R


def poseMatrix(position=[0, 0, 0], orientation=0, scale=1):
    """
    Returns a combined TRS matrix for the pose of a model.
    :param position: the position of the model
    :param orientation: the model orientation (for now assuming a rotation around the Z axis)
    :param scale: the model scale, either a scalar for isotropic scaling, or vector of scale factors
    :return: the 4x4 TRS matrix
    """
    # apply the position and orientation of the object
    R = rotationMatrixZ(orientation)
    T = translationMatrix(position)

    # ... and the scale factor
    S = scaleMatrix(scale)
    return np.matmul(np.matmul(T, R), S)


def orthoMatrix(l, r, t, b, n, f):
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
    return np.array(
        [
            [2.0 / (r - l), 0.0, 0.0, (r + l) / (r - l)],
            [0.0, -2.0 / (t - b), 0.0, (t + b) / (t - b)],
            [0.0, 0.0, 2.0 / (f - n), (f + n) / (f - n)],
            [0.0, 0.0, 0.0, 1.0],
        ]
    )


def frustumMatrix(l, r, t, b, n, f):
    return np.array(
        [
            [2 * n / (r - l), 0, (r + l) / (r - l), 0],
            [0, -2 * n / (t - b), (t + b) / (t - b), 0],
            [0, 0, -(f + n) / (f - n), -2 * f * n / (f - n)],
            [0, 0, -1, 0],
        ]
    )


# Homogeneous coordinates helpers
def homog(v):
    return np.hstack([v, 1])


def unhomog(vh):
    return vh[:-1] / vh[-1]


def matmul(L):
    R = L[0]
    for M in L[1:]:
        R = np.matmul(R, M)
    return R
