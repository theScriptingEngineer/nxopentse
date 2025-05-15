import os
import math
from typing import List, Optional, cast

import NXOpen
import NXOpen.Features
import NXOpen.GeometricUtilities
import NXOpen.Assemblies

the_session: NXOpen.Session = NXOpen.Session.GetSession()
the_lw: NXOpen.ListingWindow = the_session.ListingWindow


def get_all_bodies_in_component(component: NXOpen.Assemblies.Component) -> List[NXOpen.Body]:
    """
    Get all the bodies in the given component. (thus not the part)

    Parameters
    ----------
    component : NXOpen.Assemblies.Component
        The component for which to get all bodies.
    
    Returns
    -------
    List[NXOpen.Body]
        A list of all the bodies in the component.

    NOTES
    -----
    The bodies in the component are not the same as the bodies in the part. As a part be be used multiple times in an assembly.
    Tested in Simcenter 2312
    """
    if component is None:
        return []
    all_bodies_in_part: List[NXOpen.Body] = [body for body in component.Prototype.Bodies]
    all_bodies_in_component: List[NXOpen.Body] = [component.FindOccurrence(body) for body in all_bodies_in_part]
    if all_bodies_in_component is None or all_bodies_in_component == [None] * len(all_bodies_in_component):
        # the component doesn't contain any bodies, so we return an empty list
        # this happens for example also when the 'reference set' is set to 'MODEL'
        return []
    return all_bodies_in_component


def get_all_curves_in_component(component: NXOpen.Assemblies.Component) -> List[NXOpen.Curve]:
    """
    Get all the curves in the given component. (thus not the part)

    Parameters
    ----------
    component : NXOpen.Assemblies.Component
        The component for which to get all curves.
    
    Returns
    -------
    List[NXOpen.Curve]
        A list of all the curves in the component.

    NOTES
    -----
    The curves in the component are not the same as the curves in the part. As a part be be used multiple times in an assembly.
    Tested in Simcenter 2312
    """
    if component is None:
        return []
    all_curves_in_part: List[NXOpen.Curve] = [curve for curve in component.Prototype.Curves]
    the_lw.WriteFullline(f'Found {len(all_curves_in_part)} curves in component {component.JournalIdentifier}')
    all_curves_in_component: List[NXOpen.Curve] = [component.FindOccurrence(curve) for curve in all_curves_in_part]
    if all_curves_in_component is None or all_curves_in_component == [None] * len(all_curves_in_part):
        # the component doesn't contain any curves, so we return an empty list
        # this happens for example also when the reference set is set to 'MODEL'
        return []
    return all_curves_in_component


def get_all_points_in_component(component: NXOpen.Assemblies.Component) -> List[NXOpen.Point]:
    """
    Get all the points in the given component. (thus not the part)

    Parameters
    ----------
    component : NXOpen.Assemblies.Component
        The component for which to get all points.
    
    Returns
    -------
    List[NXOpen.Point]
        A list of all the points in the component.

    NOTES
    -----
    The points in the component are not the same as the points in the part. As a part be be used multiple times in an assembly.
    Tested in Simcenter 2312
    """
    if component is None:
        return []
    all_points_in_part: List[NXOpen.Point] = [point for point in component.Prototype.Points]
    all_points_in_component: List[NXOpen.Point] = [component.FindOccurrence(point) for point in all_points_in_part]
    if all_points_in_component is None or all_points_in_component == [None] * len(all_points_in_component):
        # the component doesn't contain any points, so we return an empty list
        # this happens for example also when the 'reference set' is set to 'MODEL'
        return []
    return all_points_in_component


def create_component_from_bodies(bodies: List[NXOpen.Body], 
                                 component_name: str, 
                                 delete_original_bodies:bool=True,
                                 add_defining_objects:bool=True,
                                 work_part: NXOpen.Part=None) -> NXOpen.Assemblies.Component:
    '''
    Create a new component from a list of bodies.

    Parameters
    ----------
    bodies : List[NXOpen.Body]
        The bodies to be used in the new component.
    component_name : str
        The name of the new component.
    delete_original_bodies : bool, optional
        Whether to delete the original bodies. Defaults to True.
    add_defining_objects : bool, optional
        Whether to add the defining objects. Defaults to True.
    work_part : NXOpen.Part, optional
        The part to create the component in. Defaults to work part.

    Returns
    -------
    NXOpen.Assemblies.Component
        The new component.

    NOTES
    -----
    This is based on the GUI funcionality of creating a new component from a set of bodies.
    Tested in Simcenter 2406
    '''
    if work_part is None:
        work_part = the_session.Parts.Work

    file_new: NXOpen.FileNew = the_session.Parts.FileNew()
    file_new.UseBlankTemplate = False
    file_new.ApplicationName = "ModelTemplate"
    file_new.Units = NXOpen.Part.Units.Millimeters
    file_new.TemplateType = NXOpen.FileNewTemplateType.Item
    file_new.TemplatePresentationName = "Model"
    file_new.AllowTemplatePostPartCreationAction(False)
    file_new.TemplateFileName = "model-plain-1-mm-template.prt"
    file_new.NewFileName = os.path.join(os.path.dirname(work_part.FullPath), f'{component_name}.prt')
    if os.path.exists(file_new.NewFileName):
        os.remove(file_new.NewFileName)

    create_new_component_builder: NXOpen.Assemblies.CreateNewComponentBuilder = work_part.AssemblyManager.CreateNewComponentBuilder()
    create_new_component_builder.NewComponentName = component_name
    create_new_component_builder.ReferenceSetName = "MODEL"
    create_new_component_builder.OriginalObjectsDeleted = delete_original_bodies
    create_new_component_builder.DefiningObjectsAdded = add_defining_objects
    for body in bodies:
        create_new_component_builder.ObjectForNewComponent.Add(body)
    
    create_new_component_builder.NewFile = file_new
    component: NXOpen.Assemblies.Component = create_new_component_builder.Commit()
    create_new_component_builder.Destroy()

    return component


def add_parts_to_assembly(parts: List[NXOpen.Part], assembly: NXOpen.Part) -> None:
    """
    Add a part to an assembly.

    Parameters
    ----------
    part : NXOpen.Part
        The part to add to the assembly.
    assembly : NXOpen.Part
        The assembly to add the part to.

    NOTES
    -----
    Tested in Simcenter 2406
    """
    add_component_builder: NXOpen.Assemblies.AddComponentBuilder = assembly.AssemblyManager.CreateAddComponentBuilder()
    add_component_builder.SetCount(1)
    add_component_builder.SetComponentAnchor(NXOpen.Assemblies.ProductInterface.InterfaceObject.Null)
    add_component_builder.SetInitialLocationType(NXOpen.Assemblies.AddComponentBuilder.LocationType.WorkPartAbsolute)
    add_component_builder.ReferenceSet = "Use Model"
    add_component_builder.Layer = -1
    add_component_builder.SetPartsToAdd(parts)
    add_component_builder.ComponentName = assembly.Name

    add_component_builder.Commit()
    add_component_builder.ResetPartsToAdd()
    add_component_builder.Destroy()

