import os
import math
from typing import List, Optional, cast

import NXOpen
import NXOpen.Features
import NXOpen.GeometricUtilities

the_session: NXOpen.Session = NXOpen.Session.GetSession()
the_lw: NXOpen.ListingWindow = the_session.ListingWindow


def nx_hello():
    """
    Print a greeting message to the listing window.
    """
    the_lw.WriteFullline("Hello, World!")
    the_lw.WriteFullline("Hello from " + os.path.basename(__file__))


def get_all_bodies(work_part: NXOpen.Part=None) -> List[NXOpen.Body]:
    """
    Get all the bodies in the work part.

    Parameters
    ----------
    work_part : NXOpen.Part, optional
        The part for which to get all bodies. Defaults to work part.
    
    Returns
    -------
    List[NXOpen.Body]
        A list of all the bodies in the work part.

    NOTES
    -----
    Tested in Simcenter 2212
    """
    if work_part is None:
        work_part = the_session.Parts.Work
    all_bodies: List[NXOpen.Body] = []
    for item in work_part.Bodies: # type: ignore
        all_bodies.append(item)
    return all_bodies


def get_faces_of_type(body: NXOpen.Body, face_type: NXOpen.Face.FaceType) -> List[NXOpen.Face]:
    """
    Get all the faces of a specific type from a given body.

    Parameters
    ----------
    body : NXOpen.Body
        The body from which to retrieve the faces.
    face_type : NXOpen.Face.FaceType
        The type of faces to retrieve.

    Returns
    -------
    List[NXOpen.Face]
        A list of faces of the specified type.
    """
    all_faces: List[NXOpen.Face] = body.GetFaces()
    faces_of_type: List[NXOpen.Face] = []
    for i in range(len(all_faces)):
        if all_faces[i].SolidFaceType is face_type:
            faces_of_type.append(all_faces[i])
    return faces_of_type


def get_all_points(work_part: NXOpen.Part=None) -> List[NXOpen.Point]:
    """
    Get all the points in the work part.

    Parameters
    ----------
    work_part : NXOpen.Part, optional
        The part for which to get all bodies. Defaults to work part.

    Returns
    -------
    List[NXOpen.Point]
        A list of all the points in the work part.
    """
    if work_part is None:
        work_part = the_session.Parts.Work
    all_points: List[NXOpen.Point] = []
    for item in work_part.Points: # type: ignore
        all_points.append(item)
    return all_points


def get_all_features(work_part: NXOpen.Part=None) -> List[NXOpen.Features.Feature]:
    """
    Get all the features in the work part.

    Parameters
    ----------
    work_part : NXOpen.Part, optional
        The part for which to get all features. Defaults to work part.

    Returns
    -------
    List[NXOpen.Features.Feature]
        A list of all the features in the work part.
    """
    if work_part is None:
        work_part = the_session.Parts.Work
    all_features: List[NXOpen.Features.Feature] = []
    for item in work_part.Features:
        all_features.append(item)
    return all_features


def get_features_of_type(feature_type: type, work_part: NXOpen.Part=None) -> List[NXOpen.Features.Feature]:
    """
    Get all the features of a specified type in the work part.

    Parameters
    ----------
    feature_type : type
        The type of feature to search for.
    work_part : NXOpen.Part, optional
        The part in which to search for features.

    Returns
    -------
    List[NXOpen.Features.Feature]
        A list of all the features of the specified type in the work part.

    NOTES
    -----
    Tested in Simcenter 2312
    """
    if work_part is None:
        work_part = the_session.Parts.Work
    features: List[NXOpen.Features.Feature] = []
    for item in work_part.Features:
        if type(item) == feature_type:
            features.append(item)
    
    return features


def get_feature_by_name(name: str, work_part: NXOpen.Part=None) -> Optional[List[NXOpen.Features.Feature]]:
    """
    Get features with the specified name.

    Parameters
    ----------
    name : str
        The name of the feature.
    work_part : NXOpen.Part, optional
        The part in which to search for the feature. Defaults to work part.

    Returns
    -------
    Optional[List[NXOpen.Features.Feature]]
        A list of features with the specified name, or None if no feature is found.
    """
    if work_part is None:
        work_part = the_session.Parts.Work
    all_features: List[NXOpen.Features.Feature] = get_all_features(work_part)
    features: List[NXOpen.Features.Feature] = []
    for feature in all_features:
        if feature.Name == name:
            features.append(feature)
    return features


def get_all_point_features(work_part: NXOpen.Part=None) -> List[NXOpen.Features.PointFeature]:
    """
    Get all the point features in the work part.

    Parameters
    ----------
    work_part : NXOpen.Part, optional
        The part for which to get all features. Defaults to work part.

    Returns
    -------
    List[NXOpen.Features.PointFeature]
        A list of all the point features in the work part.
    """
    if work_part is None:
        work_part = the_session.Parts.Work
    all_features: List[NXOpen.Features.Feature] = get_all_features(work_part)
    all_point_features: list[NXOpen.Features.PointFeature] = []
    for feature in all_features:
        if isinstance(feature, NXOpen.Features.PointFeature):
            all_point_features.append(cast(NXOpen.Features.PointFeature, feature))
    
    return all_point_features


def get_point_with_feature_name(name: str, work_part: NXOpen.Part=None) -> Optional[NXOpen.Point]:
    """
    Get the point associated with the feature name.

    Parameters
    ----------
    name : str
        The name of the feature.

    Parameters
    ----------
    work_part : NXOpen.Part, optional
        The part in which to look the feature. Defaults to work part.
        
    Returns
    -------
    Optional[NXOpen.Point]
        The point associated with the feature name, or None if no point is found.

    NOTES
    -----
    Tested in Simcenter 2212
    """
    if work_part is None:
        work_part = the_session.Parts.Work
    all_point_features: list[NXOpen.Features.PointFeature] = get_all_point_features()
    for point_feature in all_point_features:
        if point_feature.Name == name:
            return cast(NXOpen.Point, point_feature.GetEntities()[0])
    return None


def create_cylinder_between_two_points(point1: NXOpen.Point, point2: NXOpen.Point, diameter: float, length: float, work_part: NXOpen.Part=None) -> NXOpen.Features.Cylinder:
    """
    Create a cylinder between two points.

    Parameters
    ----------
    point1 : NXOpen.Point
        The first point.
    point2 : NXOpen.Point
        The second point.
    diameter : float
        The diameter of the cylinder.
    length : float
        The length of the cylinder.
    work_part : NXOpen.Part, optional
        The part in which to create the cylinder. Defaults to work part.

    Returns
    -------
    NXOpen.Features.Cylinder
        The created cylinder feature.

    NOTES
    -----
    Tested in Simcenter 2212
    """
    if work_part is None:
        work_part = the_session.Parts.Work
    cylinder_builder = work_part.Features.CreateCylinderBuilder(NXOpen.Features.Feature.Null)
    cylinder_builder.BooleanOption.Type = NXOpen.GeometricUtilities.BooleanOperation.BooleanType.Create
    targetBodies1 = [NXOpen.Body.Null] * 1 
    targetBodies1[0] = NXOpen.Body.Null
    cylinder_builder.BooleanOption.SetTargetBodies(targetBodies1)
    cylinder_builder.Diameter.SetFormula(str(diameter))    
    cylinder_builder.Height.SetFormula(str(length))

    origin = NXOpen.Point3d(point1.Coordinates.X, point1.Coordinates.Y, point1.Coordinates.Z)
    vector = NXOpen.Vector3d(point2.Coordinates.X - point1.Coordinates.X, point2.Coordinates.Y - point1.Coordinates.Y, point2.Coordinates.Z - point1.Coordinates.Z)
    direction1 = work_part.Directions.CreateDirection(origin, vector, NXOpen.SmartObject.UpdateOption.WithinModeling) # type: ignore
    axis1 = work_part.Axes.CreateAxis(NXOpen.Point.Null, direction1, NXOpen.SmartObject.UpdateOption.WithinModeling)
    
    cylinder_builder.Axis = axis1

    cylinder_feature: NXOpen.Features.Cylinder = cylinder_builder.Commit()
    cylinder_builder.Destroy()

    return cylinder_feature


def create_intersect_feature(body1: NXOpen.Body, body2: NXOpen.Body, work_part: NXOpen.Part=None) -> NXOpen.Features.BooleanFeature:
    """
    Create an intersect feature between two bodies.

    Parameters
    ----------
    body1 : NXOpen.Body
        The first body.
    body2 : NXOpen.Body
        The second body.
    work_part : NXOpen.Part, optional
        The part in which to perform the intersection. Defaults to work part.

    Returns
    -------
    NXOpen.Features.BooleanFeature
        The created intersect feature.

    NOTES
    -----
    Tested in Simcenter 2212
    """
    if work_part is None:
        work_part = the_session.Parts.Work
    boolean_builder = work_part.Features.CreateBooleanBuilderUsingCollector(NXOpen.Features.BooleanFeature.Null)

    # settings
    boolean_builder.Tolerance = 0.01
    boolean_builder.Operation = NXOpen.Features.Feature.BooleanType.Intersect
    boolean_builder.CopyTargets = True
    boolean_builder.CopyTools = True

    # set target
    selection_intent_rule_options = work_part.ScRuleFactory.CreateRuleOptions()
    selection_intent_rule_options.SetSelectedFromInactive(False)

    bodies1 = [NXOpen.Body.Null] * 1
    bodies1[0] = body1
    body_dumb_rule = work_part.ScRuleFactory.CreateRuleBodyDumb(bodies1, True, selection_intent_rule_options)
    
    selection_intent_rule_options.Dispose()
    rules1 = [None] * 1 
    rules1[0] = body_dumb_rule
    sc_collector_1 = work_part.ScCollectors.CreateCollector()
    sc_collector_1.ReplaceRules(rules1, False) # type: ignore
    boolean_builder.TargetBodyCollector = sc_collector_1
    
    # set tool
    selectionIntentRuleOptions2 = work_part.ScRuleFactory.CreateRuleOptions()
    selectionIntentRuleOptions2.SetSelectedFromInactive(False)
    
    bodies2 = [NXOpen.Body.Null] * 1 
    bodies2[0] = body2
    bodyDumbRule2 = work_part.ScRuleFactory.CreateRuleBodyDumb(bodies2, True, selection_intent_rule_options)
    
    selectionIntentRuleOptions2.Dispose()
    rules2 = [None] * 1 
    rules2[0] = bodyDumbRule2
    sc_collector_2= work_part.ScCollectors.CreateCollector()
    sc_collector_2.ReplaceRules(rules2, False) # type: ignore
    boolean_builder.ToolBodyCollector = sc_collector_2

    boolean_feature: NXOpen.Features.BooleanFeature = cast(NXOpen.Features.BooleanFeature, boolean_builder.Commit())
    boolean_builder.Destroy()
    return boolean_feature


def get_faces_of_body(body: NXOpen.Body) -> List[NXOpen.Face]:
    """
    Get all the faces of a body.

    Parameters
    ----------
    body : NXOpen.Body
        The body.

    Returns
    -------
    List[NXOpen.Face]
        A list of all the faces of the body.

    NOTES
    -----
    Tested in Simcenter 2212
    """
    faces: List[NXOpen.Face] = []
    for face in body.GetFaces():
        faces.append(face)
    return faces


def get_faces_with_color(body: NXOpen.Body, color: int) -> List[NXOpen.Face]:
    """
    Get all the faces of a body with a specific color.

    Parameters
    ----------
    body : NXOpen.Body
        The body.
    color : int
        The color.

    Returns
    -------
    List[NXOpen.Face]
        A list of all the faces of the body with the specified color.

    NOTES
    -----
    Tested in Simcenter 2212
    """
    faces: List[NXOpen.Face] = get_faces_of_body(body)
    colored_faces: List[NXOpen.Face] = []
    for face in faces:
        if face.Color == color:
            colored_faces.append(face)
    return colored_faces


def get_area_faces_with_color(bodies: List[NXOpen.Body], color: int, work_part: NXOpen.Part=None) -> float:
    """
    Get the total area of faces with a specific color in a list of bodies.

    Parameters
    ----------
    bodies : List[NXOpen.Body]
        The list of bodies.
    color : int
        The color.

    Returns
    -------
    float
        The total area of faces, for all the bodies, (in mm2), with the specified color.

    NOTES
    -----
    Tested in Simcenter 2212
    """
    if work_part is None:
        work_part = the_session.Parts.Work
    area_unit: NXOpen.Unit = work_part.UnitCollection.FindObject("SquareMilliMeter")
    length_unit: NXOpen.Unit = work_part.UnitCollection.FindObject("MilliMeter")
    area: float = 0.0
    for body in bodies:
        faces: List[NXOpen.Face] = get_faces_with_color(body, color)    
        area += work_part.MeasureManager.NewFaceProperties(area_unit, length_unit, 0.99, faces).Area
    return area


def create_point(x_co: float, y_co: float, z_co: float, work_part: NXOpen.Part=None) -> NXOpen.Features.PointFeature:
    """
    Creates an point at the specified coordinates.

    Parameters
    ----------
    x_co : float
        The x-coordinate of the point in global coordinates in millimeter.
    y_co : float
        The y-coordinate of the point in global coordinates in millimeter.
    z_co : float
        The z-coordinate of the point in global coordinates in millimeter.
    work_part : NXOpen.Part, optional
        The part in which to create the point. Defaults to work part.

    Returns
    -------
    NXOpen.Features.PointFeature
        The point feature. Use the GetEntities() method to get the point.

    NOTES
    -----
    Tested in Simcenter 2306
    """
    if work_part is None:
        work_part = the_session.Parts.Work

    unit_milli_meter = work_part.UnitCollection.FindObject("MilliMeter")
    expression_x = work_part.Expressions.CreateSystemExpressionWithUnits(str(x_co), unit_milli_meter)
    scalar_x = work_part.Scalars.CreateScalarExpression(expression_x, NXOpen.Scalar.DimensionalityType.NotSet, NXOpen.SmartObject.UpdateOption.WithinModeling)
    expression_y = work_part.Expressions.CreateSystemExpressionWithUnits(str(y_co), unit_milli_meter)
    scalar_y = work_part.Scalars.CreateScalarExpression(expression_y, NXOpen.Scalar.DimensionalityType.NotSet, NXOpen.SmartObject.UpdateOption.WithinModeling)
    expression_z = work_part.Expressions.CreateSystemExpressionWithUnits(str(z_co), unit_milli_meter)
    scalar_z = work_part.Scalars.CreateScalarExpression(expression_z, NXOpen.Scalar.DimensionalityType.NotSet, NXOpen.SmartObject.UpdateOption.WithinModeling)


    point2 = work_part.Points.CreatePoint(scalar_x, scalar_y, scalar_z, NXOpen.SmartObject.UpdateOption.WithinModeling)
    point2.SetVisibility(NXOpen.SmartObject.VisibilityOption.Visible)
    
    point_feature_builder = work_part.BaseFeatures.CreatePointFeatureBuilder(NXOpen.Features.Feature.Null)
    point_feature_builder.Point = point2
    point_feature: NXOpen.Features.PointFeature = point_feature_builder.Commit()
    
    point_feature_builder.Destroy()

    return point_feature


def create_line_between_two_points(point1: NXOpen.Point, point2: NXOpen.Point, work_part: NXOpen.Part=None) -> NXOpen.Features.AssociativeLine:
    """
    Create a line between two points.

    Parameters
    ----------
    point1 : NXOpen.Point
        The first point.
    point2 : NXOpen.Point
        The second point.
    work_part : NXOpen.Part, optional
        The part for in which to create the line. Defaults to work part.

    Returns
    -------
    NXOpen.Features.AssociativeLine
        The created line feature.

    NOTES
    -----
    Tested in Simcenter 2212
    """
    # Implementation of create_line function is missing in the provided code.
    # Please provide the implementation or remove the function if not needed.
    if work_part is None:
        work_part = the_session.Parts.Work
    associative_line_builder = work_part.BaseFeatures.CreateAssociativeLineBuilder(NXOpen.Features.AssociativeLine.Null)
    # cannot use point directly, but need to create a new point
    associative_line_builder.StartPoint.Value = work_part.Points.CreatePoint(point1, NXOpen.Xform.Null, NXOpen.SmartObject.UpdateOption.WithinModeling) # type: ignore
    associative_line_builder.EndPoint.Value = work_part.Points.CreatePoint(point2, NXOpen.Xform.Null, NXOpen.SmartObject.UpdateOption.WithinModeling) # type: ignore
    associative_line_builder.StartPointOptions = NXOpen.Features.AssociativeLineBuilder.StartOption.Point
    associative_line_builder.EndPointOptions = NXOpen.Features.AssociativeLineBuilder.EndOption.Point

    associative_line_builder.Limits.StartLimit.LimitOption = NXOpen.GeometricUtilities.CurveExtendData.LimitOptions.AtPoint
    associative_line_builder.Limits.StartLimit.Distance.SetFormula("0")
    distance_between_points = math.sqrt((point2.Coordinates.X-point1.Coordinates.X)**2 + \
                                        (point2.Coordinates.Y-point1.Coordinates.Y)**2 + \
                                        (point2.Coordinates.Z-point1.Coordinates.Z)**2)
    associative_line_builder.Limits.EndLimit.LimitOption = NXOpen.GeometricUtilities.CurveExtendData.LimitOptions.AtPoint
    # times 1.2 to make sure the line is long enough
    associative_line_builder.Limits.EndLimit.LimitOption = NXOpen.GeometricUtilities.CurveExtendData.LimitOptions.Value
    associative_line_builder.Limits.EndLimit.Distance.SetFormula(str(distance_between_points))

    associative_line_feature = associative_line_builder.Commit()
    associative_line_builder.Destroy()
    return cast(NXOpen.Features.AssociativeLine, associative_line_feature)


def delete_feature(feature_to_delete: NXOpen.Features.Feature) -> None:
    """
    Delete a feature.

    Parameters
    ----------
    feature_to_delete : NXOpen.Features.Feature
        The first point.

    NOTES
    -----
    Tested in Simcenter 2212
    """
    the_session.UpdateManager.AddObjectsToDeleteList([feature_to_delete])
    id1 = the_session.NewestVisibleUndoMark
    the_session.UpdateManager.DoUpdate(id1)


def get_named_datum_planes(cad_part: NXOpen.Part) -> List[NXOpen.DatumPlane]:
    """
    Searches the part for all datum planes with a name and returns them.
    Naming a datum plane is done by right-clicking on the plane in the GUI and selecting rename.

    Parameters
    ----------
    cad_part: NXOpen.Part
        The part for which to return the named datum planes.

    Returns
    -------
    List[NXOpen.DatumPlane]
        A list with the named datum planes.
    
    Notes
    -----
    Tested in SC2306
    """
    named_datum_planes: List[NXOpen.DatumPlane] = []
    for item in cad_part.Datums: # type: ignore
        # cad_part.Datums.ToArray() will also contain datum axis (if present)
        if type(item) is NXOpen.DatumPlane:
            # item is a datum plane. Now check if it has a name.
            # Note Feature.Name and not Name
            if cast(NXOpen.DatumPlane, item).Feature.Name != "":
                named_datum_planes.append(cast(NXOpen.DatumPlane, item))
    
    return named_datum_planes

