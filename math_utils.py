"""Various 3D related math utilities"""

import numpy as np
from numpy.typing import ArrayLike, NDArray


def scale_matrix(scale: float) -> NDArray:
    """Generate a scale matrix.

    Args:
        scale (float): The amount to scale by

    Returns:
        NDArray: Scale matrix
    """
    if np.isscalar(scale):
        scale = [scale, scale, scale]

    scale.append(1)
    return np.diag(scale)


def translation_matrix(vec: ArrayLike) -> NDArray:
    """Generate a translation matrix

    Args:
        vec (ArrayLike): The vector to translate by

    Returns:
        NDArray: Translation matrix
    """
    n = len(vec)
    t = np.identity(n + 1, dtype="f")
    t[:n, -1] = vec
    return t


def frustrum_matrix(
    l: float, r: float, t: float, b: float, n: float, f: float
) -> NDArray:
    """Returns a frustrum projection matrix

    Args:
        l (float): Left clipping plane
        r (float): Right clipping plane
        t (float): Top clipping plane
        b (float): Bottom clipping plane
        n (float): Near clipping plane
        f (float): Far clipping plane

    Returns:
        NDArray: A 4x4 orthographic projection matrix
    """
    return np.array([
        [2 * n / (r - l), 0, (r + l) / (r - l), 0],
        [0, -2 * n / (t - b), (t + b) / (t - b), 0],
        [0, 0, -(f + n) / (f - n), -2 * f * n / (f - n)],
        [0, 0, -1, 0],
    ])
