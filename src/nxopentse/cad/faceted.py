import os
import math
from typing import List, Tuple, Optional, cast, Union

import NXOpen
import NXOpen.Features
import NXOpen.GeometricUtilities
import NXOpen.Assemblies

from .code import create_non_timestamp_points
from ..tools.vector_arithmetic import get_angle_between_vectors

the_session: NXOpen.Session = NXOpen.Session.GetSession()
the_uf_session: NXOpen.UF.UFSession = NXOpen.UF.UFSession.GetUFSession()
the_lw: NXOpen.ListingWindow = the_session.ListingWindow

def local_offset_face(face: NXOpen.Face, 
                      offset_distance: float, 
                      is_reverse_direction: bool, 
                      work_part: NXOpen.Part=None # type: ignore
                      ) -> Union[NXOpen.Face, None]:
    """
    Create a local offset of a faceted face with the specified distance.
    
    Parameters
    ----------
    face : NXOpen.Face
        The face to be offset.
    offset_distance : float
        The distance by which to offset the face.
    is_reverse_direction : bool
        Whether to reverse the direction of the offset.
        If True, offsets inward; if False, offsets outward.
    work_part : NXOpen.Part, optional
        The part in which to create the offset. If None, uses the current work part.
    
    Returns
    -------
    Union[NXOpen.Face, None]
        The newly created offset face, or None if the operation fails.
    
    Notes
    -----
    The function uses the facet modeling tools to create a smooth local offset.
    A region distance of "10" is set which is important for the operation but
    not visible in the GUI. The operation is performed as an edit copy.
    
    After committing the operation, the function updates the session to ensure
    the change is visible.
    """
    if work_part is None:
        work_part = the_session.Parts.Work
    
    local_offset_builder = work_part.FacetedBodies.FacetModelingCollection.CreateLocalOffsetBuilder()
    local_offset_builder.OffsetDistance.SetFormula(str(offset_distance))
    local_offset_builder.RegionDistance.SetFormula("10") # this is important, but not in GUI!
    local_offset_builder.ShapeMethod = NXOpen.Facet.LocalOffsetBuilder.ShapeMethodType.Smooth
    local_offset_builder.IsEditCopy = True
    local_offset_builder.IsReverseDirection = is_reverse_direction
    
    facets_face_rule = work_part.FacetSelectionRuleFactory.CreateRuleFaceFacets([face])
    
    rules1 = [None] * 1 
    rules1[0] = facets_face_rule
    local_offset_builder.FacetRegion.AddRules(rules1) # type: ignore
    facets_face_rule.Dispose()
    local_offset_builder.FacetRegion.GetFacets()
    
    # the objext returned by Commit() is an NXOpen.Face.
    try:
        nXObject1 = local_offset_builder.Commit()
        # face.DestroyOwnedFacets()
        id1 = the_session.GetNewestUndoMark(NXOpen.Session.MarkVisibility.Visible)
        the_session.UpdateManager.DoUpdate(id1)
        return nXObject1
    except Exception as e:
        local_offset_builder.Destroy()
        return None


def get_facets_on_face(face: NXOpen.Face, 
                       work_part: NXOpen.Part=None # type: ignore
                       ) -> List[NXOpen.IFacet]:
    '''
    Get all facets on a face.
    Parameters
    ----------
    face : NXOpen.Face
        The face to get the facets from.
    work_part : NXOpen.Part, optional
        The part for in which to get the facets. Defaults to work part.

    Returns
    -------
    List[NXOpen.IFacet]
        The facets on the face.

    Notes
    -----
    This code creates a local offset builder, such that the we can use a selection rule to get the facets on the face.
    This is much more performant. The local offset builder is then destroyed.
    Tested in NX2412

    '''
    if work_part is None:
        work_part = the_session.Parts.Work
    
    local_offset_builder = work_part.FacetedBodies.FacetModelingCollection.CreateLocalOffsetBuilder()
    facets_face_rule = work_part.FacetSelectionRuleFactory.CreateRuleFaceFacets([face])
    
    rules = [None] * 1 
    rules[0] = facets_face_rule
    local_offset_builder.FacetRegion.AddRules(rules) # type: ignore
    facets_face_rule.Dispose()
    facets: List[NXOpen.IFacet] = local_offset_builder.FacetRegion.GetFacets()

    local_offset_builder.Destroy()
    return facets


def get_facets_on_body(body: NXOpen.Body, 
                       work_part: NXOpen.Part=None # type: ignore
                       ) -> List[NXOpen.IFacet]:
    '''
    Get all facets on a face.
    Parameters
    ----------
    face : NXOpen.Face
        The face to get the facets from.
    work_part : NXOpen.Part, optional
        The part for in which to get the facets. Defaults to work part.

    Returns
    -------
    List[NXOpen.IFacet]
        The facets on the face.

    Notes
    -----
    This code creates a local offset builder, such that the we can use a selection rule to get the facets on the face.
    This is much more performant. The local offset builder is then destroyed.
    Tested in NX2412

    '''
    if work_part is None:
        work_part = the_session.Parts.Work
    
    local_offset_builder = work_part.FacetedBodies.FacetModelingCollection.CreateLocalOffsetBuilder()
    facets_face_rule = work_part.FacetSelectionRuleFactory.CreateRuleBodyFacets([body])
    
    rules = [None] * 1 
    rules[0] = facets_face_rule
    local_offset_builder.FacetRegion.AddRules(rules) # type: ignore
    facets_face_rule.Dispose()
    facets: List[NXOpen.IFacet] = local_offset_builder.FacetRegion.GetFacets()

    local_offset_builder.Destroy()
    return facets


def get_average_normal(facets: Union[List[NXOpen.ConvergentFacet], List[NXOpen.IFacet]]) -> NXOpen.Vector3d:
    '''
    Get the average normal of a list of facets.

    Parameters
    ----------
    facets : List[NXOpen.ConvergentFacet]
        The facets to get the average normal from.

    Returns
    -------
    NXOpen.Vector3d
        The average normal of the facets.

    Notes
    -----
    Is slow
    Tested in NX2412    
    '''
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    for i in range(len(facets)):
        if i % 1000 == 0:
            the_uf_session.Ui.SetStatus(f'Calculating average normal for facet {i} of {len(facets)}')
        normal = facets[i].GetUnitNormal()
        x += normal.X
        y += normal.Y
        z += normal.Z
    
    vector: NXOpen.Vector3d = NXOpen.Vector3d(x / len(facets), y / len(facets), z / len(facets))

    return vector
    

def get_facets_angle_above(facets: Union[List[NXOpen.ConvergentFacet], 
                                         List[NXOpen.IFacet]], 
                                         vector: NXOpen.Vector3d, 
                                         limit_angle: float) ->  Union[List[NXOpen.ConvergentFacet], List[NXOpen.IFacet]]:
    '''
    Get all facets for which the angle between the normal and the vector is above a limit.

    Parameters
    ----------
    facets : List[NXOpen.IFacet]
        The facets to check.
    vector : NXOpen.Vector3d
        The vector to check against.
    limit_angle : float
        The angle in degrees.

    Returns
    -------
    List[NXOpen.ConvergentFacet]
        The facets that are above the angle.
    '''
    facets_above: List[NXOpen.ConvergentFacet] = []
    for facet in facets:
        normal: NXOpen.Vector3d = facet.GetUnitNormal()
        angle: float = get_angle_between_vectors(vector, normal)
        if angle > limit_angle:
            facets_above.append(facet)
    
    return facets_above


def color_facets(face, 
                 facets:  Union[List[NXOpen.ConvergentFacet], List[NXOpen.IFacet]], 
                 color: List[float], 
                 work_part: NXOpen.Part=None # type: ignore
                 ) -> None:
    '''
    Color all facets of a face with a specified color.
    Parameters
    ----------
    face : NXOpen.Face
        The face to color.
    facets : List[NXOpen.IFacet]
        The facets to color.
    color : List[float]
        The color to apply as a list of 3 floats. The floats are RGB and in the range [0, 1].
    work_part : NXOpen.Part, optional
        The part for in which to color the facets. Defaults to work part.

    Notes
    -----
    Tested in NX2412

    '''
    if work_part is None:
        work_part = the_session.Parts.Work
    
    # check color input
    if len(color) != 3:
        raise ValueError('Color must be a list of 3 floats in color_facets()')

    paintFacetBodyBuilder1 = work_part.FacetedBodies.FacetModelingCollection.CreatePaintFacetBodyBuilder()
    
    work_part.ModelingViews.WorkView.RenderingStyle = NXOpen.View.RenderingStyleType.FaceAnalysis

    bodies1 = [NXOpen.DisplayableObject.Null] * 1
    # divideface1 = work_part.Features.FindObject("DIVIDE_FACE(21)")
    # face1 = divideface1.FindObject("FACE 2 {(100.2164615155374,220.3901982842945,282.2413496499244) UNPARAMETERIZED_FEATURE(1)}")
    # bodies1[0] = face1
    # face2 = divideface1.FindObject("FACE 1 {(104.3980077791817,217.9869375772173,300.7258673395449) UNPARAMETERIZED_FEATURE(1)}")
    # bodies1[1] = face2
    bodies1[0] = face
    paintFacetBodyBuilder1.PaintBodiesBackgroundColor(bodies1)

    bodies2 = []
    paintFacetBodyBuilder1.SetupBodyColorData(bodies2)

    paintbrushcolor1 = [None] * 3
    paintbrushcolor1[0] = color[0] # type: ignore
    paintbrushcolor1[1] = color[1] # type: ignore
    paintbrushcolor1[2] = color[2] # type: ignore
    paintFacetBodyBuilder1.SetPaintBrushColor(paintbrushcolor1) # type: ignore

    select_facets_rule = work_part.FacetSelectionRuleFactory.CreateRuleSingleFacet(facets)
    facetCollector1 = paintFacetBodyBuilder1.FacetCollector
    
    rules1 = [None] * 1 
    rules1[0] = select_facets_rule
    facetCollector1.AddRules(rules1) # type: ignore
    
    select_facets_rule.Dispose()
    paintFacetBodyBuilder1.PaintSelectedFacets()
    
    facetCollector1.RemoveAllFacets()

    nXObject1 = paintFacetBodyBuilder1.Commit()
    paintFacetBodyBuilder1.Destroy()


def create_points_on_facets(facets:  Union[List[NXOpen.ConvergentFacet], List[NXOpen.IFacet]], 
                            color: int = 134, 
                            work_part: NXOpen.Part=None # type: ignore
                            ) -> List[NXOpen.Point]:
    # TODO: remove double points
    if work_part is None:
        work_part = the_session.Parts.Work

    points: List[List[float]] = []

    for i in range(len(facets)):
        if i % 1000 == 0:
            the_uf_session.Ui.SetStatus(f'Obtaining vertices from facet {i} of {len(facets)}')
        if not points.__contains__([facets[i].Vertex0.X, facets[i].Vertex0.Y, facets[i].Vertex0.Z]):
            points.append([facets[i].Vertex0.X, facets[i].Vertex0.Y, facets[i].Vertex0.Z])
        if not points.__contains__([facets[i].Vertex1.X, facets[i].Vertex1.Y, facets[i].Vertex1.Z]):
            points.append([facets[i].Vertex1.X, facets[i].Vertex1.Y, facets[i].Vertex1.Z])
        if not points.__contains__([facets[i].Vertex2.X, facets[i].Vertex2.Y, facets[i].Vertex2.Z]):
            points.append([facets[i].Vertex2.X, facets[i].Vertex2.Y, facets[i].Vertex2.Z])
    
    the_uf_session.Ui.SetStatus(f'Finished processing {len(facets)} facets. Creating {len(points)} points...')
    return create_non_timestamp_points(points, color)


def local_offset_facets(facets: List[NXOpen.IFacet], 
                        offset_distance: float, 
                        is_reverse_direction: bool, 
                        regenerate_offset_mesh: bool = False, 
                        edit_a_copy: bool = True, 
                        smooth_edge: bool = True, 
                        work_part: NXOpen.Part=None # type: ignore
                        ) -> Union[NXOpen.Face, None]:
    '''
    Create a local offset of a list of facets.

    Parameters
    ----------
    facets : List[NXOpen.IFacet]
        The facets to offset.
    offset_distance : float
        The distance to offset the facets.
    is_reverse_direction : bool
        If True, the offset is in the opposite direction.
    regenerate_offset_mesh : bool, optional
        If True, the offset mesh is regenerated. Defaults to False.
    edit_a_copy : bool, optional
        If True, a copy of the facets is created. Defaults to True.
    smooth_edge : bool, optional
        If True, the edges are smoothed. Defaults to True.
    work_part : NXOpen.Part, optional
        The part for in which to create the offset. Defaults to work part.

    Returns
    -------
    NXOpen.Face
        The created offset face.

    Notes
    -----
    Note that this function returns a face, but it still creates a feature in the part.
    Tested in NX2412
    '''
    if work_part is None:
        work_part = the_session.Parts.Work
    
    local_offset_builder = work_part.FacetedBodies.FacetModelingCollection.CreateLocalOffsetBuilder()
    local_offset_builder.OffsetDistance.SetFormula(str(offset_distance))
    local_offset_builder.RegionDistance.SetFormula("10") # this is important, but not in GUI!
    # local_offset_builder.ShapeMethod = NXOpen.Facet.LocalOffsetBuilder.ShapeMethodType.Smooth
    local_offset_builder.IsReverseDirection = is_reverse_direction
    local_offset_builder.IsRegenerateOffsetMesh = regenerate_offset_mesh
    local_offset_builder.IsEditCopy = edit_a_copy
    local_offset_builder.IsSmoothEdge = smooth_edge

    facets_face_rule = work_part.FacetSelectionRuleFactory.CreateRuleSingleFacet(facets)
    
    rules1 = [None] * 1 
    rules1[0] = facets_face_rule
    local_offset_builder.FacetRegion.AddRules(rules1) # type: ignore
    facets_face_rule.Dispose()
    
    # the objext returned by Commit() is an NXOpen.Face.
    try:
        nXObject1 = local_offset_builder.Commit()
        # face.DestroyOwnedFacets()
        id1 = the_session.GetNewestUndoMark(NXOpen.Session.MarkVisibility.Visible)
        the_session.UpdateManager.DoUpdate(id1)
        return nXObject1
    except Exception as e:
        local_offset_builder.Destroy()
        return None


def smooth_facet_body(body: NXOpen.Body, 
                      smooth_factor: int, 
                      number_of_iterations: int, 
                      work_part: NXOpen.Part=None # type: ignore
                      ) -> None:
    if work_part is None:
        work_part = the_session.Parts.Work
    smooth_facet_body_builder = work_part.FacetedBodies.CreateSmoothFacetBodyBuilder()
    smooth_facet_body_builder.SmoothFactor = smooth_factor
    smooth_facet_body_builder.NumberOfIterations = number_of_iterations
    smooth_facet_body_builder.IsEditCopy = True

    bodies = [NXOpen.NXObject.Null] * 1 
    # body1 = work_part.Bodies.FindObject("UNPARAMETERIZED_FEATURE(36)")
    bodies[0] = body
    bodyFacetsRule1 = work_part.FacetSelectionRuleFactory.CreateRuleBodyFacets(bodies)
    
    facetCollector1 = smooth_facet_body_builder.FacetCollector
    
    rules1 = [None] * 1 
    rules1[0] = bodyFacetsRule1
    facetCollector1.AddRules(rules1) # type: ignore
    
    bodyFacetsRule1.Dispose()
    
    nXObject1 = smooth_facet_body_builder.Commit()
    smooth_facet_body_builder.Destroy()
    
    # id1 = the_session.GetNewestUndoMark(NXOpen.Session.MarkVisibility.Visible)
    # nErrs1 = the_session.UpdateManager.DoUpdate(id1)
