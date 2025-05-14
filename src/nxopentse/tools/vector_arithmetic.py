import NXOpen
import NXOpen.UF
import NXOpen.CAE
from typing import List, cast, Optional, Union

import math

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


def get_angle_between_vectors(vector1: NXOpen.Vector3d, vector2: NXOpen.Vector3d) -> float:
    '''
    Calculate the angle between two vectors (radians).

    Parameters
    ----------
    vector1 (NXOpen.Vector3d): 
        The first vector.
    vector2 (NXOpen.Vector3d):
        The second vector.

    Returns
    -------
    float:
        The angle between the two vectors in radians.
    '''
    angle: float = math.acos(dot_product_vector3d(vector1, vector2))
    return angle * 180 / 3.14159265358979323846


def create_vector(point1: Union[NXOpen.Point, NXOpen.Point3d], point2: Union[NXOpen.Point, NXOpen.Point3d]) -> NXOpen.Vector3d:
    """
    Create a vector from two points.

    Parameters
    ----------
    point1 (Union[NXOpen.Point, NXOpen.Point3d]): 
        The first point.
    point2 (Union[NXOpen.Point, NXOpen.Point3d]): 
        The second point.

    Returns
    -------
    NXOpen.Vector3d: 
        The vector from vector1 to vector2.
    
    Notes
    -----
    """
    if isinstance(point1, NXOpen.Point) and isinstance(point2, NXOpen.Point):
        return NXOpen.Vector3d(point2.Coordinates.X - point1.Coordinates.X, point2.Coordinates.Y - point1.Coordinates.Y, point2.Coordinates.Z - point1.Coordinates.Z)
    elif isinstance(point1, NXOpen.Point3d) and isinstance(point2, NXOpen.Point3d):
        return NXOpen.Vector3d(point2.X - point1.X, point2.Y - point1.Y, point2.Z - point1.Z)
    elif isinstance(point1, NXOpen.Point) and isinstance(point2, NXOpen.Point3d):
        return NXOpen.Vector3d(point2.X - point1.Coordinates.X, point2.Y - point1.Coordinates.Y, point2.Z - point1.Coordinates.Z)
    elif isinstance(point1, NXOpen.Point3d) and isinstance(point2, NXOpen.Point):
        return NXOpen.Vector3d(point2.Coordinates.X - point1.X, point2.Coordinates.Y - point1.Y, point2.Coordinates.Z - point1.Z)
    else:
        raise ValueError(f'Invalid types for point1 {type(point1)} and point2 {type(point2)}')


def distance_between_points(point1: Union[NXOpen.Point, NXOpen.Point3d], point2: Union[NXOpen.Point, NXOpen.Point3d]) -> float:
    """
    Calculate the distance between two points.

    Parameters
    ----------
    point1 : NXOpen.Point or NXOpen.Point3d
        The first point.
    point2 : NXOpen.Point or NXOpen.Point3d
        The second point.

    Returns
    -------
    float
        The distance between the two points.

    NOTES
    -----
    Tested in NX2412
    """
    if isinstance(point1, NXOpen.Point) and isinstance(point2, NXOpen.Point):
        return ((point1.Coordinates.X - point2.Coordinates.X) ** 2 + (point1.Coordinates.Y - point2.Coordinates.Y) ** 2 + (point1.Coordinates.Z - point2.Coordinates.Z) ** 2) ** 0.5
    elif isinstance(point1, NXOpen.Point3d) and isinstance(point2, NXOpen.Point3d):
        return ((point1.X - point2.X) ** 2 + (point1.Y - point2.Y) ** 2 + (point1.Z - point2.Z) ** 2) ** 0.5
    elif isinstance(point1, NXOpen.Point) and isinstance(point2, NXOpen.Point3d):
        return ((point1.Coordinates.X - point2.X) ** 2 + (point1.Coordinates.Y - point2.Y) ** 2 + (point1.Coordinates.Z - point2.Z) ** 2) ** 0.5
    elif isinstance(point1, NXOpen.Point3d) and isinstance(point2, NXOpen.Point):
        return ((point1.X - point2.Coordinates.X) ** 2 + (point1.Y - point2.Coordinates.Y) ** 2 + (point1.Z - point2.Coordinates.Z) ** 2) ** 0.5
    else:
        raise ValueError(f'Invalid types for point1 {type(point1)} and point2 {type(point2)}')


def get_closest_point(point: Union[NXOpen.Point, NXOpen.Point3d], points: Union[List[NXOpen.Point], List[NXOpen.Point3d]]) -> Union[NXOpen.Point, NXOpen.Point3d]:
    '''
    Get the point closest to a given point from a list of points.

    Parameters
    ----------
    point: NXOpen.Point3d
        The point to get the closest point to.
    points: List[NXOpen.Point3d]
        The list of points to search

    Returns
    -------
    Union[NXOpen.Point, NXOpen.Point3d]
        The closest point to the given point in the list of points. The type is the same as the type of point in the list.

    NOTES
    -----
    Should be extended to handle point and point3d iso only point3d
    Tested in NX2412
    '''
    closest_point = points[0]
    closest_distance = distance_between_points(point, points[0])
    for p in points:
        d = distance_between_points(point, p)
        if d < closest_distance:
            closest_distance = d
            closest_point = p
    
    return closest_point
