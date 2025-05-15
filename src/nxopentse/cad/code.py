import os
import math
from typing import List, Tuple, Optional, cast, Union

import NXOpen
import NXOpen.UF
import NXOpen.Features
import NXOpen.GeometricUtilities
import NXOpen.Assemblies

from ..tools.vector_arithmetic import dot_product_vector3d

the_session: NXOpen.Session = NXOpen.Session.GetSession()
the_uf_session: NXOpen.UF.UFSession = NXOpen.UF.UFSession.GetUFSession()
the_lw: NXOpen.ListingWindow = the_session.ListingWindow


class MassProps3d:
    '''
    Object to store the mass properties of a body and easily access and compare them.
    '''
    def __init__(
        self,
        surface_area: float = 0.0,
        volume: float = 0.0,
        mass: float = 0.0,
        center_of_mass: Optional[List[float]] = None,
        first_moments: Optional[List[float]] = None,
        moments_of_inertia_wcs: Optional[List[float]] = None,
        moments_of_inertia_centroidal: Optional[List[float]] = None,
        spherical_moment_of_inertia: float = 0.0,
        inertia_products_wcs: Optional[List[float]] = None,
        inertia_products_centroidal: Optional[List[float]] = None,
        principal_axes_wcs: Optional[List[float]] = None,
        principal_moments_centroidal: Optional[List[float]] = None,
        radii_of_gyration_wcs: Optional[List[float]] = None,
        radii_of_gyration_centroidal: Optional[List[float]] = None,
        spherical_radius_of_gyration: float = 0.0,
        density: float = 0.0,
    ):
        self.surface_area = surface_area
        self.volume = volume
        self.mass = mass
        self.center_of_mass = center_of_mass or [0.0, 0.0, 0.0]
        self.first_moments = first_moments or [0.0, 0.0, 0.0]
        self.moments_of_inertia_wcs = moments_of_inertia_wcs or [0.0, 0.0, 0.0]
        self.moments_of_inertia_centroidal = moments_of_inertia_centroidal or [0.0, 0.0, 0.0]
        self.spherical_moment_of_inertia = spherical_moment_of_inertia
        self.inertia_products_wcs = inertia_products_wcs or [0.0, 0.0, 0.0]
        self.inertia_products_centroidal = inertia_products_centroidal or [0.0, 0.0, 0.0]
        self.principal_axes_wcs = principal_axes_wcs or [0.0, 0.0, 0.0]
        self.principal_moments_centroidal = principal_moments_centroidal or [0.0, 0.0, 0.0]
        self.radii_of_gyration_wcs = radii_of_gyration_wcs or [0.0, 0.0, 0.0]
        self.radii_of_gyration_centroidal = radii_of_gyration_centroidal or [0.0, 0.0, 0.0]
        self.spherical_radius_of_gyration = spherical_radius_of_gyration
        self.density = density


    def __str__(self) -> str:
        return (
            f"MassProps3d(\n"
            f"  Surface Area={self.surface_area},\n"
            f"  Volume (0.0 For Thin Shell)={self.volume},\n"
            f"  Mass={self.mass},\n"
            f"  Center Of Mass (COFM), WCS={self.center_of_mass},\n"
            f"  First Moments (centroidal)={self.first_moments},\n"
            f"  Moments Of Inertia, WCS={self.moments_of_inertia_wcs},\n"
            f"  Moments Of Inertia (centroidal)={self.moments_of_inertia_centroidal},\n"
            f"  Spherical Moment Of Inertia={self.spherical_moment_of_inertia},\n"
            f"  Inertia Products, WCS={self.inertia_products_wcs},\n"
            f"  Inertia Products (centroidal)={self.inertia_products_centroidal},\n"
            f"  Principal Axes, WCS={self.principal_axes_wcs},\n"
            f"  Principal Moments (centroidal)={self.principal_moments_centroidal},\n"
            f"  Radii Of Gyration, WCS={self.radii_of_gyration_wcs},\n"
            f"  Radii Of Gyration (centroidal)={self.radii_of_gyration_centroidal},\n"
            f"  Spherical Radius Of Gyration={self.spherical_radius_of_gyration},\n"
            f"  Density={self.density}\n"
            f")"
        )


    def __eq__(self, other) -> bool:
        if not isinstance(other, MassProps3d):
            return False
        return (
            self.surface_area == other.surface_area
            and self.volume == other.volume
            and self.mass == other.mass
            and self.center_of_mass == other.center_of_mass
            and self.first_moments == other.first_moments
            and self.moments_of_inertia_wcs == other.moments_of_inertia_wcs
            and self.moments_of_inertia_centroidal == other.moments_of_inertia_centroidal
            and self.spherical_moment_of_inertia == other.spherical_moment_of_inertia
            and self.inertia_products_wcs == other.inertia_products_wcs
            and self.inertia_products_centroidal == other.inertia_products_centroidal
            and self.principal_axes_wcs == other.principal_axes_wcs
            and self.principal_moments_centroidal == other.principal_moments_centroidal
            and self.radii_of_gyration_wcs == other.radii_of_gyration_wcs
            and self.radii_of_gyration_centroidal == other.radii_of_gyration_centroidal
            and self.spherical_radius_of_gyration == other.spherical_radius_of_gyration
            and self.density == other.density
        )


    def __hash__(self) -> int:
        return hash((
            self.surface_area,
            self.volume,
            self.mass,
            tuple(self.center_of_mass),
            tuple(self.first_moments),
            tuple(self.moments_of_inertia_wcs),
            tuple(self.moments_of_inertia_centroidal),
            self.spherical_moment_of_inertia,
            tuple(self.inertia_products_wcs),
            tuple(self.inertia_products_centroidal),
            tuple(self.principal_axes_wcs),
            tuple(self.principal_moments_centroidal),
            tuple(self.radii_of_gyration_wcs),
            tuple(self.radii_of_gyration_centroidal),
            self.spherical_radius_of_gyration,
            self.density,
        ))


def nx_hello():
    """
    Print a greeting message to the listing window.
    """
    the_lw.WriteFullline("Hello, World!")
    the_lw.WriteFullline("Hello from " + os.path.basename(__file__))


def get_all_bodies_in_part(work_part: NXOpen.Part=None # type: ignore
                           ) -> List[NXOpen.Body]:
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
    all_bodies: List[NXOpen.Body] = [item for item in work_part.Bodies] # type: ignore
    return all_bodies


def get_body_properties(body: NXOpen.Body) -> MassProps3d:
    '''
    Get the properties of a body In METER and KG!!!!

    Parameters
    ----------
    body : NXOpen.Body
        The body to get the properties of.

    Returns
    -------
    MassProps3d
        A MassProps3d object with the properties of the body.

    NOTES
    -----
    This is based on the GUI funcionality of getting the properties of a body.
    Tested in Simcenter 2406
    '''
    # should update the code to use workpart.MeasureManager
    (massProps, Stats) = the_uf_session.Modeling.AskMassProps3d([body.Tag], 1, 1, 4, 0.0, 1, [0.99,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0])
    # Mass properties
    # [0] = Surface Area
    # [1] = Volume (0.0 For Thin Shell)
    # [2] = Mass
    # [3-5] = Center Of Mass (COFM), WCS
    # [6-8] = First Moments (centroidal)
    # [9-11] = Moments Of Inertia, WCS
    # [12-14] = Moments Of Inertia (centroidal)
    # [15] = Spherical Moment Of Inertia
    # [16-18] = Inertia Products, WCS
    # [19-21] = Inertia Products (centroidal)
    # [22-30] = Principal Axes, WCS
    # [31-33] = Principal Moments (centroidal)
    # [34-36] = Radii Of Gyration, WCS
    # [37-39] = Radii Of Gyration (centroidal)
    # [40] = Spherical Radius Of Gyration
    # [41-45] = Unused
    # [46] = Density
    # the_lw.WriteFullline(f"MassProps: {massProps}")

    properties = MassProps3d(massProps[0],
                             massProps[1],
                             massProps[2],
                             massProps[3:6],
                             massProps[6:9],
                             massProps[9:12],
                             massProps[12:15],
                             massProps[15],
                             massProps[16:19],
                             massProps[19:22],
                             massProps[22:31],
                             massProps[31:34],
                             massProps[34:37],
                             massProps[37:40],
                             massProps[40],
                             massProps[46])

    return properties



def get_all_vertices_in_body(body: NXOpen.Body) -> List[NXOpen.Point3d]:
    '''
    Get all the unique vertices in a body.
    Vertices shared by multiple edges are only counted once.

    Parameters
    ----------
    body : NXOpen.Body
        The body to get the vertices of.

    Returns
    -------
    List[NXOpen.Point3d]
        A list of all the unique vertices in the body. 
    '''
    all_edges: List[NXOpen.Edge] = body.GetEdges()
    all_vertices: List[List[float]] = []
    for edge in all_edges:
        vertices: List[NXOpen.Point3d] = edge.GetVertices() # type: ignore a list is retured in Python
        for vertex in vertices:
            all_vertices.append([vertex.X, vertex.Y, vertex.Z])
    # Convert lists to tuples and use a set to remove duplicates
    unique_data = set(tuple(row) for row in all_vertices)

    # Convert back to a list of NXOpen.Point3d
    all_vertices_point3d: List[NXOpen.Point3d] = [NXOpen.Point3d(row[0], row[1], row[2]) for row in unique_data]

    return all_vertices_point3d


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


def get_face_properties(face: NXOpen.Face, 
                        work_part: NXOpen.Part=None # type: ignore
                        ) -> Tuple[float, float, float, NXOpen.Point3d, float, float, NXOpen.Point3d, bool]:
    '''
    Get the properties of a face.

    Parameters
    ----------
    face : NXOpen.Face
        The face for which to get the properties.
    work_part : NXOpen.Part, optional
        The part in which to perform the measurement. Defaults to work part.

    Returns
    -------
    Tuple[float, float, float, NXOpen.Point3d, float, float, NXOpen.Point3d, bool]
        A tuple with the following values:
        - Area (in mm2)
        - Perimeter (in mm)
        - Radius or Diameter (in mm)
        - Center of Gravity (in mm)
        - Minimum Radius of Curvature (in mm)
        - Area Error Estimate (in mm2)
        - Anchor Point (in mm)
        - Is Approximate (bool)

    NOTES
    -----
    '''
    if work_part is None:
        work_part = the_session.Parts.Work
    
    measure_prefs_builder = the_session.Preferences.CreateMeasurePrefsBuilder()
    measure_prefs_builder.InfoUnits = NXOpen.MeasurePrefsBuilder.JaMeasurePrefsInfoUnit.CustomUnit
    measure_prefs_builder.ShowValueOnlyToggle = False
    measure_prefs_builder.ConsoleOutput = False
    
    work_part.MeasureManager.SetPartTransientModification()
    
    sc_collector_1 = work_part.ScCollectors.CreateCollector()
    sc_collector_1.SetMultiComponent()
    
    work_part.MeasureManager.SetPartTransientModification()
    selectionIntentRuleOptions1 = work_part.ScRuleFactory.CreateRuleOptions()
    selectionIntentRuleOptions1.SetSelectedFromInactive(False)
    
    faces1 = [NXOpen.Face.Null] * 1 
    faces1[0] = face
    faceDumbRule1 = work_part.ScRuleFactory.CreateRuleFaceDumb(faces1, selectionIntentRuleOptions1)
    
    selectionIntentRuleOptions1.Dispose()
    rules1 = [None] * 1 
    rules1[0] = faceDumbRule1
    sc_collector_1.ReplaceRules(rules1, False) # type: ignore
    
    work_part.MeasureManager.SetPartTransientModification()
    
    scCollector2 = work_part.ScCollectors.CreateCollector()
    scCollector2.SetMultiComponent()
    
    faceaccuracy1 = measure_prefs_builder.FaceAccuracy
    work_part.MeasureManager.ClearPartTransientModification()
    
    faces = [NXOpen.ISurface.Null] * 1  # type: ignore
    faces[0] = face
    area, perimeter, radiusdiameter, cog, minradiusofcurvature, areaerrorestimate, anchorpoint, isapproximate = the_session.Measurement.GetFaceProperties(faces, 0.98999999999999999, NXOpen.Measurement.AlternateFace.Radius, True)
    
    work_part.MeasureManager.SetPartTransientModification()

    datadeleted1 = the_session.DeleteTransientDynamicSectionCutData()
    
    sc_collector_1.Destroy()
    scCollector2.Destroy()
    
    work_part.MeasureManager.ClearPartTransientModification()

    return area, perimeter, radiusdiameter, cog, minradiusofcurvature, areaerrorestimate, anchorpoint, isapproximate


def get_all_points(work_part: NXOpen.Part=None # type: ignore
                   ) -> List[NXOpen.Point]:
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


def get_all_features(work_part: NXOpen.Part=None # type: ignore
                     ) -> List[NXOpen.Features.Feature]:
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


def get_features_of_type(feature_type: type, 
                         work_part: NXOpen.Part=None # type: ignore
                         ) -> List[NXOpen.Features.Feature]:
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


def get_feature_by_name(name: str, 
                        work_part: NXOpen.Part=None # type: ignore
                        ) -> Optional[List[NXOpen.Features.Feature]]:
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


def get_all_point_features(work_part: NXOpen.Part=None # type: ignore
                           ) -> List[NXOpen.Features.PointFeature]:
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


def get_point_with_feature_name(name: str, 
                                work_part: NXOpen.Part=None # type: ignore
                                ) -> Optional[NXOpen.Point]:
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


def create_cylinder_between_two_points(point1: NXOpen.Point, 
                                       point2: NXOpen.Point, 
                                       diameter: float, 
                                       length: float, 
                                       work_part: NXOpen.Part=None # type: ignore
                                       ) -> NXOpen.Features.Cylinder:
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


def create_intersect_feature(body1: NXOpen.Body, 
                             body2: NXOpen.Body, 
                             work_part: NXOpen.Part=None # type: ignore
                             ) -> NXOpen.Features.BooleanFeature:
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


def get_smallest_face(faces: List[NXOpen.Face], 
                      work_part: NXOpen.Part=None # type: ignore
                      ) -> NXOpen.Face:
    """
    Get the smallest face from a list of faces.

    Parameters
    ----------
    faces : List[NXOpen.Face]
        A list of faces.

    Returns
    -------
    NXOpen.Face
        The smallest face.

    NOTES
    -----
    Tested in Simcenter 2212
    """
    if work_part is None:
        work_part = the_session.Parts.Work
    
    area_unit: NXOpen.Unit = work_part.UnitCollection.FindObject("SquareMilliMeter")
    length_unit: NXOpen.Unit = work_part.UnitCollection.FindObject("MilliMeter")
    
    smallest_face: NXOpen.Face = faces[0]
    smallest_face_area: float = work_part.MeasureManager.NewFaceProperties(area_unit, length_unit, 0.99, [faces[0]]).Area
    
    for face in faces:
        area2 = work_part.MeasureManager.NewFaceProperties(area_unit, length_unit, 0.99, [face]).Area
        if area2 < smallest_face_area:
            smallest_face = face
            smallest_face_area = area2
    
    return smallest_face


def get_largest_face(faces: List[NXOpen.Face], 
                     work_part: NXOpen.Part=None # type: ignore
                     ) -> NXOpen.Face:
    """
    Get the largest face from a list of faces.

    Parameters
    ----------
    faces : List[NXOpen.Face]
        A list of faces.

    Returns
    -------
    NXOpen.Face
        The largest face.

    NOTES
    -----
    Tested in NX2412
    """
    if work_part is None:
        work_part = the_session.Parts.Work
    
    area_unit: NXOpen.Unit = work_part.UnitCollection.FindObject("SquareMilliMeter")
    length_unit: NXOpen.Unit = work_part.UnitCollection.FindObject("MilliMeter")
    
    largest_face: NXOpen.Face = faces[0]
    largest_face_area: float = work_part.MeasureManager.NewFaceProperties(area_unit, length_unit, 0.99, [faces[0]]).Area
    
    for face in faces:
        area2 = work_part.MeasureManager.NewFaceProperties(area_unit, length_unit, 0.99, [face]).Area
        if area2 > largest_face_area:
            largest_face = face
            largest_face_area = area2
    
    return largest_face


def get_area_faces_with_color(bodies: List[NXOpen.Body], 
                              color: int, 
                              work_part: NXOpen.Part=None # type: ignore
                              ) -> float:
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


def create_point(x_co: float, 
                 y_co: float, 
                 z_co: float, 
                 work_part: NXOpen.Part=None # type: ignore
                 ) -> NXOpen.Features.PointFeature:
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
    scalar_x = work_part.Scalars.CreateScalarExpression(expression_x, NXOpen.Scalar.DimensionalityType.NotSet, NXOpen.SmartObject.UpdateOption.WithinModeling) # type: ignore
    expression_y = work_part.Expressions.CreateSystemExpressionWithUnits(str(y_co), unit_milli_meter)
    scalar_y = work_part.Scalars.CreateScalarExpression(expression_y, NXOpen.Scalar.DimensionalityType.NotSet, NXOpen.SmartObject.UpdateOption.WithinModeling) # type: ignore
    expression_z = work_part.Expressions.CreateSystemExpressionWithUnits(str(z_co), unit_milli_meter)
    scalar_z = work_part.Scalars.CreateScalarExpression(expression_z, NXOpen.Scalar.DimensionalityType.NotSet, NXOpen.SmartObject.UpdateOption.WithinModeling) # type: ignore


    point2 = work_part.Points.CreatePoint(scalar_x, scalar_y, scalar_z, NXOpen.SmartObject.UpdateOption.WithinModeling) # type: ignore
    point2.SetVisibility(NXOpen.SmartObject.VisibilityOption.Visible)
    
    point_feature_builder = work_part.BaseFeatures.CreatePointFeatureBuilder(NXOpen.Features.Feature.Null)
    point_feature_builder.Point = point2
    point_feature: NXOpen.Features.PointFeature = point_feature_builder.Commit()
    
    point_feature_builder.Destroy()

    return point_feature


def create_non_timestamp_point(x_co: float, 
                               y_co: float, 
                               z_co: float, 
                               color: int = 134, 
                               work_part: NXOpen.Part=None # type: ignore
                               ) -> NXOpen.Point:
    """
    Create a point at the specified coordinates.

    Parameters
    ----------
    base_part : NXOpen.BasePart
        The base part where the point will be created.
    x_co : float
        The x-coordinate of the point.
    y_co : float
        The y-coordinate of the point.
    z_co : float
        The z-coordinate of the point.
    color : int, optional
        The color to give the point.
    work_part : NXOpen.Part, optional
        The part in which to create the point. Defaults to work part.
        
    Returns
    -------
    NXOpen.Point3d
        The created point.
    """
    if work_part is None:
        work_part = the_session.Parts.Work
    unit_mm: NXOpen.Unit = work_part.UnitCollection.FindObject("Millimeter")
    exp_x: NXOpen.Expression = work_part.Expressions.CreateSystemExpressionWithUnits(str(x_co), unit_mm)
    exp_y: NXOpen.Expression = work_part.Expressions.CreateSystemExpressionWithUnits(str(y_co), unit_mm)
    exp_z: NXOpen.Expression = work_part.Expressions.CreateSystemExpressionWithUnits(str(z_co), unit_mm)

    scalar_x: NXOpen.Scalar = work_part.Scalars.CreateScalarExpression(exp_x, NXOpen.Scalar.DimensionalityType.NotSet, NXOpen.SmartObject.UpdateOption.WithinModeling) # type: ignore
    scalar_y: NXOpen.Scalar = work_part.Scalars.CreateScalarExpression(exp_y, NXOpen.Scalar.DimensionalityType.NotSet, NXOpen.SmartObject.UpdateOption.WithinModeling) # type: ignore
    scalar_z: NXOpen.Scalar = work_part.Scalars.CreateScalarExpression(exp_z, NXOpen.Scalar.DimensionalityType.NotSet, NXOpen.SmartObject.UpdateOption.WithinModeling) # type: ignore

    point: NXOpen.Point = work_part.Points.CreatePoint(scalar_x, scalar_y, scalar_z, NXOpen.SmartObject.UpdateOption.WithinModeling) # type: ignore
    point.Color = color
    point.SetVisibility(NXOpen.SmartObject.VisibilityOption.Visible)
    undo_mark = the_session.SetUndoMark(NXOpen.Session.MarkVisibility.Visible, "Point")
    the_session.UpdateManager.DoUpdate(undo_mark)

    return point


def create_non_timestamp_points(coordinates: List[List[float]], 
                                color: int = 134, 
                                work_part: NXOpen.Part=None # type: ignore
                                ) -> List[NXOpen.Point]:
    """
    Create points at the specified coordinates.

    Parameters
    ----------
    coordinates : List[List[float]]
        A list with coordinates. Each coordinate is a list with three floats.
    color : int, optional
        The color to give the point.
    work_part : NXOpen.Part, optional
        The part in which to create the point. Defaults to work part.
        
    Returns
    -------
    List[NXOpen.Point3d]
        The created points.

    NOTES
    -----
    This function is much faster than looping over create_point() for each point, because it only updates the part once, after all points are created.
    Tested in Simcenter 2312
    """
    if work_part is None:
        work_part = the_session.Parts.Work
    unit_mm: NXOpen.Unit = work_part.UnitCollection.FindObject("Millimeter")
    points: List[NXOpen.Point] = [NXOpen.Point] * len(coordinates) # type: ignore
    for i in range(len(coordinates)):
        exp_x: NXOpen.Expression = work_part.Expressions.CreateSystemExpressionWithUnits(str(coordinates[i][0]), unit_mm)
        exp_y: NXOpen.Expression = work_part.Expressions.CreateSystemExpressionWithUnits(str(coordinates[i][1]), unit_mm)
        exp_z: NXOpen.Expression = work_part.Expressions.CreateSystemExpressionWithUnits(str(coordinates[i][2]), unit_mm)

        scalar_x: NXOpen.Scalar = work_part.Scalars.CreateScalarExpression(exp_x, NXOpen.Scalar.DimensionalityType.NotSet, NXOpen.SmartObject.UpdateOption.AfterModeling) # type: ignore
        scalar_y: NXOpen.Scalar = work_part.Scalars.CreateScalarExpression(exp_y, NXOpen.Scalar.DimensionalityType.NotSet, NXOpen.SmartObject.UpdateOption.AfterModeling) # type: ignore
        scalar_z: NXOpen.Scalar = work_part.Scalars.CreateScalarExpression(exp_z, NXOpen.Scalar.DimensionalityType.NotSet, NXOpen.SmartObject.UpdateOption.AfterModeling) # type: ignore

        point: NXOpen.Point = work_part.Points.CreatePoint(scalar_x, scalar_y, scalar_z, NXOpen.SmartObject.UpdateOption.AfterModeling) # type: ignore
        point.Color = color
        point.SetVisibility(NXOpen.SmartObject.VisibilityOption.Visible)
        points[i] = point
    undo_mark = the_session.SetUndoMark(NXOpen.Session.MarkVisibility.Visible, "Point")
    the_session.UpdateManager.DoUpdate(undo_mark)

    return points


def create_line_between_two_points(point1: NXOpen.Point, 
                                   point2: NXOpen.Point, 
                                   work_part: NXOpen.Part=None # type: ignore
                                   ) -> NXOpen.Features.AssociativeLine:
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


def create_spline_through_points(points: List[NXOpen.Point], 
                                 work_part: NXOpen.Part=None # type: ignore
                                 ) -> NXOpen.Features.StudioSpline:
    '''
    Create a spline through the given points.

    Parameters
    ----------
    points : List[NXOpen.Point]
        The points through which the spline should go.
    work_part : NXOpen.Part, optional
        The part in which to create the spline. Defaults to work part.

    Returns
    -------
    NXOpen.Features.StudioSpline
        The created spline feature, from which the spline can be retrieved.

    NOTES
    -----
    '''
    if work_part is None:
        work_part = the_session.Parts.Work

    studio_spline_builder_ex: NXOpen.Features.StudioSplineBuilderEx = work_part.Features.CreateStudioSplineBuilderEx(NXOpen.NXObject.Null)
    studio_spline_builder_ex.Degree = 2

    for point in points:
        coordinates1 = NXOpen.Point3d(point.Coordinates.X, point.Coordinates.Y, point.Coordinates.Z)
        point1 = work_part.Points.CreatePoint(coordinates1) # type: ignore
        geometric_constraint_data = studio_spline_builder_ex.ConstraintManager.CreateGeometricConstraintData()
        geometric_constraint_data.Point = point1
        studio_spline_builder_ex.ConstraintManager.Append(geometric_constraint_data)
    
    spline_feature = studio_spline_builder_ex.Commit()
    studio_spline_builder_ex.Destroy()

    return spline_feature
    

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


def create_bounding_box(workPart: NXOpen.Part, bodies: List[NXOpen.Body], sheet_bodies: bool=False) -> NXOpen.Features.ToolingBox:
    '''
    Create a bounding box around the given bodies.
    For sheet bodies, 1mm is added to the box size in all directions, positive and negative. Thus the box size needs to be subtracted by 2mm to get the correct size.

    Parameters
    ----------
    workPart : NXOpen.Part
        The part in which to create the bounding box.
    bodies : List[NXOpen.Body]
        The bodies for which to create the bounding box.
    sheet_bodies : bool, optional
        If the bodies are sheet bodies. Defaults to False.
    
    Returns
    -------
    NXOpen.Features.ToolingBox
        The created bounding box feature.

    NOTES
    -----
    For sheet bodies, 1mm is added to the box size in all directions, positive and negative. Thus the box size needs to be subtracted by 2mm to get the correct size.
    Tested in Simcenter 2312
    '''
    # Initialize the ToolingBoxBuilder.
    toolingBoxBuilder: NXOpen.Features.ToolingBoxBuilder = workPart.Features.ToolingFeatureCollection.CreateToolingBoxBuilder(None)
    toolingBoxBuilder.Type = NXOpen.Features.ToolingBoxBuilder.Types.BoundedBlock
    toolingBoxBuilder.NonAlignedMinimumBox = True
    if sheet_bodies:
        toolingBoxBuilder.XValue.SetFormula("10")
        toolingBoxBuilder.YValue.SetFormula("10")
        toolingBoxBuilder.ZValue.SetFormula("10")
        toolingBoxBuilder.OffsetPositiveX.SetFormula("1")
        toolingBoxBuilder.OffsetNegativeX.SetFormula("1")
        toolingBoxBuilder.OffsetPositiveY.SetFormula("1")
        toolingBoxBuilder.OffsetNegativeY.SetFormula("1")
        toolingBoxBuilder.OffsetPositiveZ.SetFormula("1")
        toolingBoxBuilder.OffsetNegativeZ.SetFormula("1")

    # Minimum required inputs for a bounding box
    matrix = NXOpen.Matrix3x3()
    matrix.Xx = 1.0
    matrix.Xy = 0.0
    matrix.Xz = 0.0
    matrix.Yx = 0.0
    matrix.Yy = 1.0
    matrix.Yz = 0.0
    matrix.Zx = 0.0
    matrix.Zy = 0.0
    matrix.Zz = 1.0
    position = NXOpen.Point3d(0.0, 0.0, 0.0)
    toolingBoxBuilder.SetBoxMatrixAndPosition(matrix, position)

    # Create a list of SelectionIntentRule objects and add bodies one by one
    listRules = []
    for body in bodies:
        tempBodies = [body]
        selectionIntentRuleOptions = workPart.ScRuleFactory.CreateRuleOptions()
        selectionIntentRuleOptions.SetSelectedFromInactive(False)
        bodyDumbRule = workPart.ScRuleFactory.CreateRuleBodyDumb(tempBodies)
        selectionIntentRuleOptions.Dispose()

        listRules.append(bodyDumbRule)

        scCollector = toolingBoxBuilder.BoundedObject
        scCollector.ReplaceRules(listRules, False) # type: ignore

        deselections1 = []
        toolingBoxBuilder.SetSelectedOccurrences(tempBodies, deselections1) # type: ignore

        # Ensure no internal errors when saving
        selectNXObjectList = toolingBoxBuilder.FacetBodies
        empty = []
        selectNXObjectList.Add(empty) # type: ignore

        toolingBoxBuilder.CalculateBoxSize()

    boundingBox = toolingBoxBuilder.Commit()
    boundingBox.SetName("Minimum_Box")
    toolingBoxBuilder.Destroy()

    return boundingBox


def trim_body_with_plane(body: NXOpen.Body, 
                         plane: NXOpen.DatumPlane, 
                         work_part: NXOpen.Part=None # type: ignore
                         ) -> NXOpen.Features.TrimBody:
    if work_part is None:
        work_part = the_session.Parts.Work
    trim_body_2_builder = work_part.Features.CreateTrimBody2Builder(NXOpen.Features.TrimBody2.Null)
    
    scCollector1 = work_part.ScCollectors.CreateCollector()
    selectionIntentRuleOptions1 = work_part.ScRuleFactory.CreateRuleOptions()
    selectionIntentRuleOptions1.SetSelectedFromInactive(False)
    
    bodies = [NXOpen.Body.Null] * 1 
    bodies[0] = body
    bodyFeatureRule1 = work_part.ScRuleFactory.CreateRuleBodyDumb(bodies, False, selectionIntentRuleOptions1)
    
    selectionIntentRuleOptions1.Dispose()
    rules1 = [None] * 1 
    rules1[0] = bodyFeatureRule1
    scCollector1.ReplaceRules(rules1, False) # type: ignore
    
    trim_body_2_builder.TargetBodyCollector = scCollector1

    selectionIntentRuleOptions2 = work_part.ScRuleFactory.CreateRuleOptions()
    selectionIntentRuleOptions2.SetSelectedFromInactive(False)
    faces1 = [NXOpen.DatumPlane.Null] * 1 
    faces1[0] = plane
    faceDumbRule1 = work_part.ScRuleFactory.CreateRuleFaceDatum(faces1, selectionIntentRuleOptions2)
    
    selectionIntentRuleOptions2.Dispose()
    rules2 = [None] * 1 
    rules2[0] = faceDumbRule1
    trim_body_2_builder.BooleanTool.FacePlaneTool.ToolFaces.FaceCollector.ReplaceRules(rules2, False)

    trim_body_feature = trim_body_2_builder.Commit()
    trim_body_2_builder.Destroy()
    return trim_body_feature


def create_datum_plane_on_planar_face(face: NXOpen.Face, 
                                      work_part: NXOpen.Part=None # type: ignore
                                      ) -> NXOpen.Features.DatumPlaneFeature:
    '''
    Create a datum plane on a planar face.

    Parameters
    ----------
    face : NXOpen.Face
        The face on which to create the datum plane.
    work_part : NXOpen.Part, optional
        The part in which to create the datum plane. Defaults to work part.

    Returns
    -------
    NXOpen.Features.DatumPlaneFeature
        The created datum plane feature, from which the datum plane can be retrieved.

    NOTES
    -----
    '''
    if work_part is None:
        work_part = the_session.Parts.Work

    datum_plane_builder = work_part.Features.CreateDatumPlaneBuilder(NXOpen.Features.Feature.Null)
    plane = datum_plane_builder.GetPlane()
    plane.SetMethod(NXOpen.PlaneTypes.MethodType.Point)
    plane.SetUpdateOption(NXOpen.SmartObject.UpdateOption.WithinModeling)

    scalar1 = work_part.Scalars.CreateScalar(0.5, NXOpen.Scalar.DimensionalityType.NotSet, NXOpen.SmartObject.UpdateOption.WithinModeling) # type: ignore
    scalar2 = work_part.Scalars.CreateScalar(0.5, NXOpen.Scalar.DimensionalityType.NotSet, NXOpen.SmartObject.UpdateOption.WithinModeling) # type: ignore
    point = work_part.Points.CreatePoint(face, scalar1, scalar2, NXOpen.SmartObject.UpdateOption.WithinModeling) # type: ignore
    
    geom = [NXOpen.NXObject.Null] * 1 
    geom[0] = point
    plane.SetGeometry(geom)
    
    plane.SetAlternate(NXOpen.PlaneTypes.AlternateType.One)
    plane.Evaluate()
    plane.RemoveOffsetData()
    plane.Evaluate()
    
    datum_plane_feature = datum_plane_builder.CommitFeature()
    datum_plane_builder.Destroy()

    return datum_plane_feature


def get_axes_of_coordinate_system(coordinate_system_feature: NXOpen.Features.DatumCsys, 
                                  work_part: NXOpen.Part=None # type: ignore
                                  ) -> List[NXOpen.DatumAxis]:
    '''
    Get the axes of a coordinate system.

    Parameters
    ----------
    coordinate_system_feature : NXOpen.Features.DatumCsys
        The coordinate system feature for which to get the axes.
    work_part : NXOpen.Part, optional
        The part in which to get the axes. Defaults to work part.

    Returns
    -------
    List[NXOpen.DatumAxis]
        A list of the axes of the coordinate system.

    NOTES
    -----
    '''
    if work_part is None:
        work_part = the_session.Parts.Work
    builder: NXOpen.Features.DatumCsysBuilder =  work_part.Features.CreateDatumCsysBuilder(coordinate_system_feature)
    axis: List[NXOpen.DatumAxis] = []
    for item in builder.GetCommittedObjects():
        # the_lw.WriteFullline(f'Committed object: {item.JournalIdentifier} of type {type(item)}')
        if type(item) is NXOpen.DatumAxis:
            axis.append(item)
    
    return axis


def create_datum_axis(vector: NXOpen.Vector3d, 
                      point: NXOpen.Point3d=None,  # type: ignore
                      work_part: NXOpen.Part=None # type: ignore
                      ) -> NXOpen.Features.DatumAxisFeature:
    '''
    Create a datum axis. through a point with a given vector.

    Parameters
    ----------
    vector : NXOpen.Vector3d
        The vector of the axis.
    point : NXOpen.Point3d, optional
        The point through which the axis should go. Defaults to the origin.
    work_part : NXOpen.Part, optional
        The part in which to create the datum axis. Defaults to work part.

    Returns
    -------
    NXOpen.Features.DatumAxisFeature
        The created datum axis feature, from which the datum axis can be retrieved.

    NOTES
    -----
    '''
    if work_part is None:
        work_part = the_session.Parts.Work

    datum_axis_builder = work_part.Features.CreateDatumAxisBuilder(NXOpen.Features.Feature.Null)
    if point is None:
        origin_1 = NXOpen.Point3d(0.0, 0.0, 0.0)
    else:
        origin_1 = point

    direction_1 = work_part.Directions.CreateDirection(origin_1, vector, NXOpen.SmartObject.UpdateOption.WithinModeling) # type: ignore
    
    datum_axis_builder.Point = work_part.Points.CreatePoint(origin_1) # type: ignore
    datum_axis_builder.Vector = direction_1
    
    datum_axis = datum_axis_builder.Commit()
    datum_axis_builder.Destroy()

    return datum_axis


def create_bisector_datum_plane(datum_plane1: NXOpen.DatumPlane, 
                                datum_plane2: NXOpen.DatumPlane, 
                                work_part: NXOpen.Part=None # type: ignore
                                ) -> NXOpen.Features.DatumPlaneFeature:
    '''
    Create a datum plane bisecting two datum planes.

    Parameters
    ----------
    datum_plane1 : NXOpen.DatumPlane
        The first datum plane.
    datum_plane2 : NXOpen.DatumPlane
        The second datum plane.
    work_part : NXOpen.Part, optional
        The part in which to create the datum plane. Defaults to work part.

    Returns
    -------
    NXOpen.Features.DatumPlaneFeature
        The created datum plane feature, from which the datum plane can be retrieved.

    NOTES
    -----
    '''
    if work_part is None:
        work_part = the_session.Parts.Work

    datum_plane_builder = work_part.Features.CreateDatumPlaneBuilder(NXOpen.Features.Feature.Null)
    plane = datum_plane_builder.GetPlane()
    plane.SetUpdateOption(NXOpen.SmartObject.UpdateOption.WithinModeling)
    plane.SetMethod(NXOpen.PlaneTypes.MethodType.Center)
    
    geom = [NXOpen.NXObject.Null] * 2 
    geom[0] = datum_plane1
    geom[1] = datum_plane2
    plane.SetGeometry(geom)
    
    plane.SetAlternate(NXOpen.PlaneTypes.AlternateType.One)
    plane.Evaluate()
    plane.RemoveOffsetData()
    plane.Evaluate()
    
    datum_plane_builder.ResizeDuringUpdate = True
    
    datum_plane_feature = datum_plane_builder.CommitFeature()
    datum_plane_builder.Destroy()

    return datum_plane_feature


def bisector_multiple_planes(planes: List[NXOpen.Features.DatumPlaneFeature]) -> List[NXOpen.Features.DatumPlaneFeature]:
    '''
    Create bisector planes between each pair of planes in the list.

    Parameters
    ----------
    planes : List[NXOpen.Features.DatumPlaneFeature]
        The list of datum planes.

    Returns
    -------
    List[NXOpen.Features.DatumPlaneFeature]
        The list of datum plane features, from which the datum planes can be retrieved.

    NOTES
    -----
    '''
    new_planes: List[NXOpen.DatumPlane] = []
    for i in range(len(planes) - 1):
        new_planes.append(create_bisector_datum_plane(planes[i].DatumPlane, planes[i + 1].DatumPlane))
    
    return_planes = [item for item in planes]
    for i in range(len(new_planes)):
        return_planes.insert(2 * i + 1, new_planes[i])
    
    return return_planes


def split_body_with_planes(body: NXOpen.Body, 
                           planes: List[NXOpen.Features.DatumPlaneFeature], 
                           work_part: NXOpen.Part=None # type: ignore
                           ) -> NXOpen.Features.SplitBody:
    """
    Split a body using multiple datum plane features.
    
    Creates a split body feature that divides the target body along the specified datum planes.
    
    Parameters
    ----------
    body : NXOpen.Body
        The body to be split.
    planes : List[NXOpen.Features.DatumPlaneFeature]
        List of datum plane features to use as cutting tools.
    work_part : NXOpen.Part, optional
        The part in which to perform the operation. If None, uses the current work part.
    
    Returns
    -------
    NXOpen.Features.SplitBody
        The created split body feature.
    
    Notes
    -----
    The function extracts the DatumPlane objects from the provided DatumPlaneFeature objects
    and uses them as cutting tools. The function creates and configures the necessary 
    selection collectors for both the target body and the cutting planes.
    """
    if work_part is None:
        work_part = the_session.Parts.Work

    split_body_builder = work_part.Features.CreateSplitBodyBuilder(NXOpen.Features.SplitBody.Null)

    scCollector1 = work_part.ScCollectors.CreateCollector()
    
    selectionIntentRuleOptions1 = work_part.ScRuleFactory.CreateRuleOptions()
    
    selectionIntentRuleOptions1.SetSelectedFromInactive(False)
    
    bodies1 = [NXOpen.Body.Null] * 1 
    bodies1[0] = body
    bodyDumbRule1 = work_part.ScRuleFactory.CreateRuleBodyDumb(bodies1, True, selectionIntentRuleOptions1)
    
    selectionIntentRuleOptions1.Dispose()
    rules1 = [None] * 1 
    rules1[0] = bodyDumbRule1
    scCollector1.ReplaceRules(rules1, False) # type: ignore
    
    split_body_builder.TargetBodyCollector = scCollector1

    datum_planes = []
    for plane in planes:
        datum_planes.append(plane.DatumPlane)

    selectionIntentRuleOptions2 = work_part.ScRuleFactory.CreateRuleOptions()
    selectionIntentRuleOptions2.SetSelectedFromInactive(False)

    faceDumbRule1 = work_part.ScRuleFactory.CreateRuleFaceDatum(datum_planes, selectionIntentRuleOptions2)
    
    selectionIntentRuleOptions2.Dispose()
    rules2 = [None] * 1 
    rules2[0] = faceDumbRule1
    split_body_builder.BooleanTool.FacePlaneTool.ToolFaces.FaceCollector.ReplaceRules(rules2, False)
    
    selectionIntentRuleOptions3 = work_part.ScRuleFactory.CreateRuleOptions()
    
    selectionIntentRuleOptions3.SetSelectedFromInactive(False)

    split_body_feature = split_body_builder.Commit()
    split_body_builder.Destroy()

    return split_body_feature


def create_datum_at_distance(plane: NXOpen.DatumPlane, 
                             distance: float, 
                             work_part: NXOpen.Part=None # type: ignore
                             ) -> NXOpen.Features.DatumPlaneFeature:
    """
    Create a new datum plane at a specified distance from an existing datum plane.
    
    Parameters
    ----------
    plane : NXOpen.DatumPlane
        The reference datum plane from which to create the offset plane.
    distance : float
        The distance at which to create the new datum plane from the reference plane.
    work_part : NXOpen.Part, optional
        The part in which to create the datum plane. If None, uses the current work part.
    
    Returns
    -------
    NXOpen.Features.DatumPlaneFeature
        The created datum plane feature.
    
    Notes
    -----
    The function creates a datum plane using the Distance method, which positions
    the new plane parallel to the reference plane at the specified distance.
    The plane is not flipped and the positive side of the plane is preserved (not reversed).
    """
    if work_part is None:
        work_part = the_session.Parts.Work

    datum_plane_builder = work_part.Features.CreateDatumPlaneBuilder(NXOpen.Features.Feature.Null)
    _plane = datum_plane_builder.GetPlane()
    _plane.SetMethod(NXOpen.PlaneTypes.MethodType.Distance)
    _plane.SetFlip(False)
    _plane.SetReverseSide(False)

    geom = [NXOpen.NXObject.Null] * 1 
    geom[0] = plane
    _plane.SetGeometry(geom)

    expression = _plane.Expression
    expression.RightHandSide = str(distance)
    _plane.SetAlternate(NXOpen.PlaneTypes.AlternateType.One)
    _plane.Evaluate()

    datum_plane_feature = datum_plane_builder.CommitFeature()
    datum_plane_builder.Destroy()

    return datum_plane_feature


def get_distance_between_planes(plane1: NXOpen.DatumPlane, plane2: NXOpen.DatumPlane) -> float:
    """
    Calculate the shortest distance between two datum planes.
    
    Parameters
    ----------
    plane1 : NXOpen.DatumPlane
        The first datum plane.
    plane2 : NXOpen.DatumPlane
        The second datum plane.
    
    Returns
    -------
    float
        The shortest distance between the two planes.
    
    Notes
    -----
    The function calculates the distance by:
    1. Finding the vector between the origins of the two planes
    2. Computing the dot product of this vector with the normal of the first plane
    3. Dividing by the magnitude of the normal vector
    4. Taking the absolute value of the result
    """
    diff = NXOpen.Vector3d(plane2.Origin.X - plane1.Origin.X, plane2.Origin.Y - plane1.Origin.Y, plane2.Origin.Z - plane1.Origin.Z)
    magnitude = math.sqrt(plane1.Normal.X**2 + plane1.Normal.Y**2 + plane1.Normal.Z**2)
    distance = abs(dot_product_vector3d(diff, plane1.Normal)) / magnitude
    return distance


def get_distance_to_plane(point: Union[NXOpen.Point, NXOpen.Point3d], plane: NXOpen.DatumPlane) -> float:
    """
    Calculate the shortest distance from a point to a datum plane.
    
    Parameters
    ----------
    point : Union[NXOpen.Point3d, NXOpen.Point]
        The point for which to calculate distance. Can be either a Point3d or Point object.
    plane : NXOpen.DatumPlane
        The datum plane to which the distance is calculated.
    
    Returns
    -------
    float
        The shortest distance from the point to the plane.
    
    Raises
    ------
    ValueError
        If the point parameter is neither a Point3d nor a Point object.
    
    Notes
    -----
    The function calculates the distance by:
    1. Creating a vector from the plane's origin to the point
    2. Computing the dot product of this vector with the plane's normal vector
    3. Dividing by the magnitude of the normal vector
    4. Taking the absolute value of the result
    """
    if type(point) is NXOpen.Point3d:
        diff = NXOpen.Vector3d(point.X - plane.Origin.X, point.Y - plane.Origin.Y, point.Z - plane.Origin.Z)
    elif type(point) is NXOpen.Point:
        diff = NXOpen.Vector3d(point.Coordinates.X - plane.Origin.X, point.Coordinates.Y - plane.Origin.Y, point.Coordinates.Z - plane.Origin.Z)
    else:
        raise ValueError(f'Invalid type for point {type(point)}')

    magnitude = math.sqrt(plane.Normal.X**2 + plane.Normal.Y**2 + plane.Normal.Z**2)
    distance = abs(dot_product_vector3d(diff, plane.Normal)) / magnitude
    return distance


def divide_face_with_curve(face: NXOpen.Face, 
                curve_feature: NXOpen.Features.CurveFeature, 
                name: str = None,  # type: ignore
                work_part: NXOpen.Part = None  # type: ignore
                ) -> NXOpen.Features.Divideface:
    """
    Divide a face using a curve feature.
    
    Creates a divide face feature by projecting a curve onto the selected face.
    The projection uses the face normal as the projection direction.
    
    Parameters
    ----------
    face : NXOpen.Face
        The face to be divided.
    curve_feature : NXOpen.Features.CurveFeature
        The curve feature used to divide the face.
    name : str, optional
        Name to assign to the created feature. If None, the default name is used.
    work_part : NXOpen.Part, optional
        The part in which to create the feature. If None, uses the current work part.
    
    Returns
    -------
    NXOpen.Features.Divideface
        The created divide face feature.
    
    Notes
    -----
    The function sets an offset distance formula of "5" and uses the face normal
    as the projection direction. It creates a section containing only curves for
    the dividing operation.
    """

    if work_part is None:
        work_part = the_session.Parts.Work
    divideface_builder: NXOpen.Features.DivideCurveBuilder = work_part.Features.CreateDividefaceBuilder(NXOpen.Features.Feature.Null)
    divideface_builder.SelectDividingObject.OffsetDistance.SetFormula("5")

    projection_options = divideface_builder.ProjectionOption
    projection_options.ProjectVector = NXOpen.Direction.Null
    projection_options.ProjectDirectionMethod = NXOpen.GeometricUtilities.ProjectionOptions.DirectionType.FaceNormal

    sc_collector: NXOpen.ScCollector = work_part.ScCollectors.CreateCollector()
    selectionIntentRuleOptions1 = work_part.ScRuleFactory.CreateRuleOptions()
    # body1 = work_part.Bodies.FindObject("UNPARAMETERIZED_FEATURE(1)")
    # faceBodyRule1 = work_part.ScRuleFactory.CreateRuleFaceBody(body1, selectionIntentRuleOptions1)
    face_dumb_rule = work_part.ScRuleFactory.CreateRuleFaceDumb([face])
    
    selectionIntentRuleOptions1.Dispose()
    rules1 = [None] * 1 
    rules1[0] = face_dumb_rule
    sc_collector.ReplaceRules(rules1, False) # type: ignore
    divideface_builder.FacesToDivide = sc_collector

    selectionIntentRuleOptions2 = work_part.ScRuleFactory.CreateRuleOptions()
    selectionIntentRuleOptions2.SetSelectedFromInactive(False)
    features1 = [NXOpen.Features.Feature.Null] * 1 
    #curveOnSurface1 = work_part.Features.FindObject("CURVE_ON_SURFACE(9)")
    features1[0] = curve_feature # curveOnSurface1
    curveFeatureRule1 = work_part.ScRuleFactory.CreateRuleCurveFeature(features1, NXOpen.DisplayableObject.Null, selectionIntentRuleOptions2)

    section2 = work_part.Sections.CreateSection(0.0094999999999999998, 0.01, 0.5) # type: ignore
    section2.SetAllowedEntityTypes(NXOpen.Section.AllowTypes.OnlyCurves)
    rules2 = [None] * 1 
    rules2[0] = curveFeatureRule1
    helpPoint1 = NXOpen.Point3d(139.82176736068584, 223.5488245492476, 426.99427887357456)
    section2.AddToSection(rules2, NXOpen.NXObject.Null, NXOpen.NXObject.Null, NXOpen.NXObject.Null, helpPoint1, NXOpen.Section.Mode.Create, False)
    divideface_builder.SelectDividingObject.DividingObjectsList.Add(section2)

    feature = divideface_builder.CommitFeature()
    divideface_builder.Destroy()

    if name is not None:
        feature.SetName(name)
    
    return feature


def pattern_geometry(body: NXOpen.Body, 
                     dir: Union[NXOpen.DatumAxis, NXOpen.Vector3d], 
                     total_number: int, 
                     distance_per_copy: float, 
                     work_part: NXOpen.Part=None # type: ignore
                     ):
    """
    Create a linear pattern of geometry along a specified direction.
    
    Parameters
    ----------
    body : NXOpen.Body
        The body to be patterned.
    dir : Union[NXOpen.DatumAxis, NXOpen.Vector3d]
        The direction along which to pattern the body.
        Can be either a datum axis or a vector.
    total_number : int
        Total number of instances (including the original) to create.
    distance_per_copy : float
        Distance between consecutive instances of the pattern.
    work_part : NXOpen.Part, optional
        The part in which to create the pattern. If None, uses the current work part.
    
    Returns
    -------
    NXOpen.Features.PatternGeometry
        The created pattern geometry feature.
    
    Raises
    ------
    ValueError
        If the provided direction is neither a DatumAxis nor a Vector3d.
    
    Notes
    -----
    When using a Vector3d for direction, the function temporarily creates
    a point at the origin to establish the direction vector.
    """
    if work_part is None:
        work_part = the_session.Parts.Work
    
    patternGeometryBuilder1 = work_part.Features.CreatePatternGeometryBuilder(NXOpen.Features.PatternGeometry.Null)
    patternGeometryBuilder1.PatternService.RectangularDefinition.XSpacing.NCopies.SetFormula(str(total_number))
    patternGeometryBuilder1.PatternService.RectangularDefinition.XSpacing.PitchDistance.SetFormula(str(distance_per_copy))
    
    if type(dir) is NXOpen.Vector3d:
        point_feature = create_point(0.0, 0.0, 0.0)
        point = point_feature.GetEntities()[0]
        direction2 = work_part.Directions.CreateDirection(point, dir) # type: ignore
        delete_feature(point_feature)
    elif type(dir) is NXOpen.DatumAxis:
        # datumAxis1 = work_part.Datums.FindObject("DATUM_CSYS(2) Z axis")
        direction2 = work_part.Directions.CreateDirection(dir, NXOpen.Sense.Forward, NXOpen.SmartObject.UpdateOption.WithinModeling) # type: ignore
    else:
        raise ValueError('Invalid type for direction in pattern_geometry()')
    
    patternGeometryBuilder1.PatternService.RectangularDefinition.XDirection = direction2

    added1 = patternGeometryBuilder1.GeometryToPattern.Add(body)

    pattern_geometry_feature = patternGeometryBuilder1.Commit()
    patternGeometryBuilder1.Destroy()

    return pattern_geometry_feature


def subtract_bodies(target: NXOpen.Body, 
                    tool: NXOpen.Body, 
                    retain_tool: bool=False, 
                    retain_target: bool=True, 
                    work_part: NXOpen.Part=None # type: ignore
                    ) -> NXOpen.Features.BooleanFeature:
    """
    Perform a Boolean subtraction between two bodies.
    
    Subtracts the tool body from the target body using a Boolean operation.
    
    Parameters
    ----------
    target : NXOpen.Body
        The body from which to subtract.
    tool : NXOpen.Body
        The body to subtract from the target.
    retain_tool : bool, default=False
        Whether to keep the tool body after the operation.
    retain_target : bool, default=True
        Whether to keep the target body after the operation.
    work_part : NXOpen.Part, optional
        The part in which to perform the operation. If None, uses the current work part.
    
    Returns
    -------
    NXOpen.Features.BooleanFeature
        The created Boolean feature representing the subtraction operation.
    
    Notes
    -----
    The function uses a tolerance of 0.01 units for the Boolean operation.
    It creates and configures the necessary selection collectors for both
    the target and tool bodies.
    """
    if work_part is None:
        work_part = the_session.Parts.Work
    
    boolean_builder: NXOpen.Features.BooleanBuilder = work_part.Features.CreateBooleanBuilderUsingCollector(NXOpen.Features.BooleanFeature.Null)
    boolean_builder.Tolerance = 0.01
    boolean_builder.Operation = NXOpen.Features.Feature.BooleanType.Subtract
    boolean_builder.RetainTarget = retain_target
    boolean_builder.RetainTool = retain_tool

    # Select the target
    sc_collector_target = work_part.ScCollectors.CreateCollector()
    selection_intent_rule_options_target = work_part.ScRuleFactory.CreateRuleOptions()
    selection_intent_rule_options_target.SetSelectedFromInactive(False)

    target_bodies = [NXOpen.Body.Null] * 1 
    # brep1 = work_part.Features.FindObject("UNPARAMETERIZED_FEATURE(31)")
    target_bodies[0] = target # brep1
    bodyFeatureRule1 = work_part.ScRuleFactory.CreateRuleBodyDumb(target_bodies, False, selection_intent_rule_options_target)
    
    selection_intent_rule_options_target.Dispose()
    rules1 = [None] * 1
    rules1[0] = bodyFeatureRule1
    sc_collector_target.ReplaceRules(rules1, False) # type: ignore
    
    boolean_builder.TargetBodyCollector = sc_collector_target

    # Select the tool
    sc_collector_tool = work_part.ScCollectors.CreateCollector()
    selection_intent_rule_options_tool = work_part.ScRuleFactory.CreateRuleOptions()
    selection_intent_rule_options_tool.SetSelectedFromInactive(False)
    
    tool_bodies = [NXOpen.Body.Null] * 1 
    # brep2 = work_part.Features.FindObject("UNPARAMETERIZED_FEATURE(30)")
    tool_bodies[0] = tool # brep2
    bodyFeatureRule2 = work_part.ScRuleFactory.CreateRuleBodyDumb(tool_bodies, True, selection_intent_rule_options_tool)
    
    selection_intent_rule_options_tool.Dispose()
    rules2 = [None] * 1 
    rules2[0] = bodyFeatureRule2
    sc_collector_tool.ReplaceRules(rules2, False) # type: ignore
    
    boolean_builder.ToolBodyCollector = sc_collector_tool

    boolean_feature: NXOpen.Features.BooleanFeature = boolean_builder.Commit()
    boolean_builder.Destroy()

    return boolean_feature


def subtract_features(target: NXOpen.Features.Feature, 
                      tool: NXOpen.Features.Feature, 
                      work_part: NXOpen.Part=None,  # type: ignore
                      retain_tool: bool=False) -> NXOpen.Features.BooleanFeature:
    """
    Perform a Boolean subtraction between two features.
    
    Subtracts the tool feature from the target feature using a Boolean operation.
    
    Parameters
    ----------
    target : NXOpen.Features.Feature
        The feature from which to subtract.
    tool : NXOpen.Features.Feature
        The feature to subtract from the target.
    work_part : NXOpen.Part, optional
        The part in which to perform the operation. If None, uses the current work part.
    retain_tool : bool, default=False
        Whether to keep the tool feature after the operation.
    
    Returns
    -------
    NXOpen.Features.BooleanFeature
        The created Boolean feature representing the subtraction operation.
    
    Notes
    -----
    The function uses a tolerance of 0.01 units for the Boolean operation.
    Unlike subtract_bodies, this function works with Feature objects rather than Body objects.
    It creates and configures the necessary selection collectors for both features.
    """
    if work_part is None:
        work_part = the_session.Parts.Work
    
    boolean_builder: NXOpen.Features.BooleanBuilder = work_part.Features.CreateBooleanBuilderUsingCollector(NXOpen.Features.BooleanFeature.Null)
    boolean_builder.Tolerance = 0.01
    boolean_builder.Operation = NXOpen.Features.Feature.BooleanType.Subtract
    boolean_builder.RetainTool = retain_tool

    # Select the target
    sc_collector_target = work_part.ScCollectors.CreateCollector()
    selection_intent_rule_options_target = work_part.ScRuleFactory.CreateRuleOptions()
    selection_intent_rule_options_target.SetSelectedFromInactive(False)

    features1 = [NXOpen.Features.Feature.Null] * 1 
    # brep1 = work_part.Features.FindObject("UNPARAMETERIZED_FEATURE(31)")
    features1[0] = target # brep1
    bodyFeatureRule1 = work_part.ScRuleFactory.CreateRuleBodyFeature(features1, True, NXOpen.DisplayableObject.Null, selection_intent_rule_options_target)
    
    selection_intent_rule_options_target.Dispose()
    rules1 = [None] * 1
    rules1[0] = bodyFeatureRule1
    sc_collector_target.ReplaceRules(rules1, False) # type: ignore
    
    boolean_builder.TargetBodyCollector = sc_collector_target


    # Select the tool
    sc_collector_tool = work_part.ScCollectors.CreateCollector()
    selection_intent_rule_options_tool = work_part.ScRuleFactory.CreateRuleOptions()
    selection_intent_rule_options_tool.SetSelectedFromInactive(False)
    
    features2 = [NXOpen.Features.Feature.Null] * 1 
    # brep2 = work_part.Features.FindObject("UNPARAMETERIZED_FEATURE(30)")
    features2[0] = tool # brep2
    bodyFeatureRule2 = work_part.ScRuleFactory.CreateRuleBodyFeature(features2, False, NXOpen.DisplayableObject.Null, selection_intent_rule_options_tool)
    
    selection_intent_rule_options_tool.Dispose()
    rules2 = [None] * 1 
    rules2[0] = bodyFeatureRule2
    sc_collector_tool.ReplaceRules(rules2, False) # type: ignore
    
    boolean_builder.ToolBodyCollector = sc_collector_tool

    boolean_feature: NXOpen.Features.BooleanFeature = boolean_builder.Commit()
    boolean_builder.Destroy()

    return boolean_feature
