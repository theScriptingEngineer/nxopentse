import NXOpen
import NXOpen.UF
import NXOpen.CAE
from typing import List, cast, Optional, Union


def cross_product_vector3d(vector1: NXOpen.Vector3d, vector2: NXOpen.Vector3d) -> NXOpen.Vector3d:
    """
    Calculate the cross product of two vectors.

    Parameters
    ----------
    vector1 (NXOpen.Vector3d)
        The first vector.
    vector2 (NXOpen.Vector3d)
        The second vector.

    Returns
    -------
    NXOpen.Vector3d
        The cross product of the two vectors.
    
    Notes
    -----
    Tested in SC2306
    """
    x = vector1.Y * vector2.Z - vector2.Y * vector1.Z
    y = vector1.Z * vector2.X - vector2.Z * vector1.X
    z = vector1.X * vector2.Y - vector2.X * vector1.Y
    return NXOpen.Vector3d(x, y, z)


def dot_product_vector3d(vector1: NXOpen.Vector3d, vector2: NXOpen.Vector3d) -> float:
    """
    Calculate the dot product of two vectors.

    Parameters
    ----------
    vector1 (NXOpen.Vector3d): 
        The first vector.
    vector2 (NXOpen.Vector3d): 
        The second vector.

    Returns
    -------
    float: 
        The dot product of the two vectors.
    
    Notes
    -----
    Tested in SC2306
    """
    return vector1.X * vector2.X + vector1.Y * vector2.Y + vector1.Z * vector2.Z