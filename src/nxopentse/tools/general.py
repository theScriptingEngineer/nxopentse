import os
from typing import List, cast

import NXOpen
import NXOpen.Assemblies
import NXOpen.CAE
import NXOpen.UF


the_session: NXOpen.Session = NXOpen.Session.GetSession()
the_uf_session: NXOpen.UF.UFSession = NXOpen.UF.UFSession.GetUFSession()
the_lw: NXOpen.ListingWindow = the_session.ListingWindow


def create_full_path(file_name: str, extension: str = ".unv") -> str:
    '''This function takes a filename and adds the .unv extension and path of the part if not provided by the user.
    If the fileName contains an extension, this function leaves it untouched, othwerwise adds .unv as extension.
    If the fileName contains a path, this function leaves it untouched, otherwise adds the path of the BasePart as the path.
    Undefined behaviour if basePart has not yet been saved (eg FullPath not available)

    Parameters
    ----------
    file_name: str
        The filename with or without path and .unv extension.

    Returns
    -------
    str
        A string with .unv extension and path of the basePart if the fileName parameter did not include a path.
    '''

    # TODO: check if base_part is not None, otherwise error

    base_part: NXOpen.BasePart = the_session.Parts.BaseWork

    # check if an extension is included
    if os.path.splitext(file_name)[1] == '':
        file_name = file_name + extension

    # check if path is included in fileName, if not add path of the .sim file
    unv_file_path: str = os.path.dirname(file_name)
    if unv_file_path == '':
        # if the .sim file has never been saved, the next will give an error
        if base_part is None:
            the_lw.WriteFullline('No full path was given and the BasePart is not defined. The latter could be because the part was never saved. Please save the part and try again.')
            raise ValueError('No full path was given and the BasePart is not defined. The latter could be because the part was never saved. Please save the part and try again.')
        file_name = os.path.join(os.path.dirname(base_part.FullPath), file_name)

    return file_name


def indentation(level: int) -> str:
    """
    Helper method to create indentations (eg tabs) with a given length.
    Can be used in print strings in a tree like structure

    Parameters
    ----------
    level: int
        The depth of the indentations.

    Returns
    -------
    str
        The indentation
    
    Notes
    -----
    Tested in SC2306
    """
    indentation: str = ""
    for i in range(level + 1):
        indentation += "\t"
    
    return indentation


def print_component_tree(component: NXOpen.Assemblies.Component, requested_level: int = 0) -> None:
    """
    Prints the component tree for the given component to the listing window.
    Recursive function

    Parameters
    ----------
    component: NXOpen.Assemblies.Component
        The component for whch to print the component tree
    requested_level: int
        Optional parameter used for creating indentations.
    
    Notes
    -----
    Tested in SC2306
    """
    level: int = requested_level
    the_lw.WriteFullline(indentation(level) + "| " + component.JournalIdentifier + " is a compont(instance) of " + component.Prototype.OwningPart.Name + " located in " + component.OwningPart.Name)
    children: List[NXOpen.Assemblies.Component] = component.GetChildren()
    for i in range(len(children) -1, -1, -1):
        print_component_tree(children[i], level + 1)


def print_part_tree(base_part: NXOpen.BasePart, requested_level: int = 0) -> None:
    """
    Prints the part tree for the given BasePart to the listing window.
    Recursive function

    Parameters
    ----------
    base_part: NXOpen.BasePart
        The BasePart to print the tree for.
    requested_level: int
        Optional parameter used for creating indentations.
    
    Notes
    -----
    Tested in SC2306
    """
    level: int = requested_level
    if isinstance(base_part, NXOpen.CAE.SimPart):
        # it's a .sim part
        sim_part: NXOpen.CAE.SimPart = cast(NXOpen.CAE.SimPart, base_part)
        the_lw.WriteFullline(sim_part.Name)

        # both are equal:
        # print_part_tree(sim_part.ComponentAssembly.RootComponent.GetChildren()[0].Prototype.OwningPart)
        print_part_tree(sim_part.FemPart)
    
    elif isinstance(base_part, NXOpen.CAE.AssyFemPart):
        # it's a .afem part
        assy_fem_part: NXOpen.CAE.AssyFemPart = cast(NXOpen.CAE.AssyFemPart, base_part)
        the_lw.WriteFullline(indentation(level) + "| " + assy_fem_part.Name + " located in " + assy_fem_part.FullPath + " linked to part " + assy_fem_part.FullPathForAssociatedCadPart)
        children: List[NXOpen.Assemblies.Component] = cast(NXOpen.Assemblies.ComponentAssembly, assy_fem_part.ComponentAssembly).RootComponent.GetChildren()
        for i in range(len(children) - 1):
            print_part_tree(children[i].Prototype.OwningPart, level + 1)
    
    elif isinstance(base_part, NXOpen.CAE.FemPart):
        # it's a .fem part
        fem_part: NXOpen.CAE.FemPart = cast(NXOpen.CAE.FemPart, base_part)
        # try except since calling femPart.FullPathForAssociatedCadPart on a part which has no cad part results in an error
        try:
            # femPart.MasterCadPart returns the actual part, but is null if the part is not loaded.
            the_lw.WriteFullline(indentation(level) + "| " + fem_part.Name + " which is linked to part " + fem_part.FullPathForAssociatedCadPart)
        except:
            # femPart has no associated cad part
            the_lw.WriteFullline(indentation(level) + "| " + fem_part.Name + " not linked to a part.")
    
    else:
        # it's a .prt part, but can still contain components
        the_lw.WriteFullline(indentation(level) + "| " + base_part.Name + " located in " + base_part.FullPath)
        if cast(NXOpen.Assemblies.ComponentAssembly, base_part.ComponentAssembly).RootComponent == None:
            return
        children: List[NXOpen.Assemblies.Component] = cast(NXOpen.Assemblies.ComponentAssembly, base_part.ComponentAssembly).RootComponent.GetChildren()
        for i in range(len(children)):
            print_part_tree(children[i].Prototype.OwningPart, level + 1)


def create_string_attribute(nx_object: NXOpen.NXObject, title: str, value: str, work_part: NXOpen.BasePart=None) -> None:
    if work_part is None:
        work_part = the_session.Parts.BaseWork
    objects1 = [NXOpen.NXObject.Null] * 1 
    objects1[0] = nx_object
    attribute_manager: NXOpen.AttributeManager = the_session.AttributeManager
    attributePropertiesBuilder1 = attribute_manager.CreateAttributePropertiesBuilder(work_part, objects1, NXOpen.AttributePropertiesBuilder.OperationType.NotSet) # type: ignore
    
    attributePropertiesBuilder1.IsArray = False
    
    attributePropertiesBuilder1.DataType = NXOpen.AttributePropertiesBaseBuilder.DataTypeOptions.String
    
    attributePropertiesBuilder1.Title = title
    
    attributePropertiesBuilder1.StringValue = value
    
    nXObject1 = attributePropertiesBuilder1.Commit()
    
    id1 = the_session.GetNewestUndoMark(NXOpen.Session.MarkVisibility.Visible)
    
    nErrs1 = the_session.UpdateManager.DoUpdate(id1)
    
    attributePropertiesBuilder1.Destroy()    
