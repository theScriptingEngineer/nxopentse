import os
from typing import List, cast, Optional, Union, Dict

import NXOpen
import NXOpen.CAE
import NXOpen.UF

import tkinter as tk
from tkinter import filedialog

from ..tools import create_full_path
from .preprocessing import copy_groups_to_sim_part
from .postprocessing import PostInput, check_post_input, load_results, get_result_types

the_session: NXOpen.Session = NXOpen.Session.GetSession()
the_uf_session: NXOpen.UF.UFSession = NXOpen.UF.UFSession.GetUFSession()
the_ui: NXOpen.UI = NXOpen.UI.GetUI() # type: ignore
the_lw: NXOpen.ListingWindow = the_session.ListingWindow


class ScreenShot(PostInput):
    """
    A class for defining screenshots, inherits from PostInput.

    Attributes
    ----------
    _file_name : str
        The file name of the screenshot.
    _annotation_text : str
        The annotation text to display on the screenshot.
    _template_name : str
        The name of the postview template to apply for the screenshot.
    _group_name : str
        The name of the group to display in the screenshot.
    _component_name : str
        The name of the result component to display on the screenshot.
    _camera_name : str
        The name of the camera to apply for the screenshot.

    Methods
    -------
    need_change_result(other) -> bool
        Determines whether a change in displayed result is required for the screenshot. 
    __repr__()
        Provides a string representation of the screenshot object.
    """
    _file_name: str
    _annotation_text: str
    _template_name: str
    _group_name: str
    _component_name: str
    _camera_name: str

    def need_change_result(self, other) -> bool:
        """
        Checks if the 2 screenshots can be genereated without changing the displayed result.
        If the displayed result does not need to be changed, the generation of screenshots is faster.

        Parameters
        ----------
        other : ScreenShot
            Another instance of the ScreenShot class to compare against.

        Returns
        -------
        bool
            True if both screenshot definitions require a change in displayed result, False otherwise.
        """
        if (self._solution != other._solution):
            return True

        if (self._subcase != other._subcase):
            return True

        if (self._iteration != other._iteration):
            return True

        if (self._resultType != other._resultType):
            return True

        if (self._component_name != other._component_name):
            return True
        
        return False


    def __repr__(self):
        """
        Provides a string representation of the ScreenShot object.

        Returns
        -------
        str
            A string describing the ScreenShot object with its attributes.
        """
        return f"ScreenShot(file_name='{self._file_name}', annotation_text={self._annotation_text}, " \
               f"template_name={self._template_name}, group_name='{self._group_name}', " \
               f"component_name='{self._component_name}', camera_name='{self._camera_name}')"


def sort_screenshots(screenshots: List[ScreenShot]) -> List[ScreenShot]:
    """
    Sorts a list of ScreenShot objects in order to minimize changes in displayed result, for performance reasons.

    The sorting order is determined by the attributes `_solution`, `_subcase`,
    `_iteration`, and `_resultType`, in that sequence.

    Parameters
    ----------
    screenshots : List[ScreenShot]
        A list of ScreenShot objects to be sorted.

    Returns
    -------
    List[ScreenShot]
        The sorted list of ScreenShot objects.
    """
    return sorted(screenshots, key=lambda x: (x._solution, x._subcase, x._iteration, x._resultType))


def check_screenshots(screenshots: List[ScreenShot], sim_part: NXOpen.CAE.SimPart=None) -> None:
    """
    Validates a list of ScreenShot objects against an NX SimPart environment.

    This function ensures that each `ScreenShot` object refers to valid entities
    (groups, templates, components, and cameras) within the specified NX simulation part.
    If `sim_part` is not provided, it defaults to the currently active `.sim` file in the session.

    Parameters
    ----------
    screenshots : List[ScreenShot]
        A list of ScreenShot objects to validate.
    sim_part : NXOpen.CAE.SimPart, optional
        The simulation part (`.sim` file) to validate against. If not provided,
        the currently active `.sim` file in the session is used.

    Raises
    ------
    ValueError
        If `sim_part` is not a valid `.sim` file or if any of the following conditions are not met:
        - The specified group name does not exist or has multiple matches.
        - The template name cannot be found.
        - The component name is invalid or does not exist.
        - The camera name does not exist or has multiple matches.

    Notes
    -----
    - This function is tailored for non-developers, prioritizing simple and clear error messages over full stack traces.
    - Reloads templates before validation to ensure the latest changes are accounted for.
    - Provides detailed feedback in the log window (`the_lw`) for errors and warnings.
    - Testd in SC2312
    """
    if sim_part is None:
        if not isinstance(the_session.Parts.BaseWork, NXOpen.CAE.SimPart):
            raise ValueError("check_screenshots needs to be called on a .sim file!")
        sim_part: NXOpen.CAE.SimPart = cast(NXOpen.CAE.SimPart, the_session.Parts.BaseWork)

    # Raising ValueError with my own message, instead of simply raising which is the proper way to keep the stack trace.
    # This journal is meant for non developers, so I think a simple clear message is more important than a stack trace.
    
    check_post_input(screenshots)

    cae_groups: NXOpen.CAE.CaeGroupCollection = sim_part.CaeGroups
    cameras: NXOpen.Display.CameraCollection = sim_part.Cameras
    # Reload in case template was just created
    the_session.Post.ReloadTemplates()

    for screenshot in screenshots:
        # check the group
        cae_group: List[NXOpen.CAE.CaeGroup] = [x for x in cae_groups if x.Name.lower() == screenshot._group_name.lower()]
        if len(cae_group) == 0:
            the_lw.WriteFullline("Error in input " + screenshot._file_name)
            the_lw.WriteFullline("Group with name " + screenshot._group_name + " not found")
            raise ValueError("Group with name " + screenshot._group_name + " not found")
        elif len(cae_group) != 1:   
            the_lw.WriteFullline("WARNING " + screenshot._file_name)
            the_lw.WriteFullline("FOUND MULTIPLE GROUPS WITH THE NAME " + screenshot._group_name)
        
        # Check the template
        # TemplateSearch throws an error in C# if the template is not found.
        try:
            the_session.Post.TemplateSearch(screenshot._template_name)
        except Exception as e:
            the_lw.WriteFullline("Error in input " + screenshot._file_name)
            the_lw.WriteFullline("Template with name " + screenshot._component_name + " could not be found.")
            raise ValueError("Template with name " + screenshot._template_name + " not found")

        # Check the component name
        try:
            # NXOpen.CAE.Result.Component is a class, not an enum. the __dict__.keys() gets all the attributes by name
            component: NXOpen.CAE.Result.Component = [x for x in NXOpen.CAE.Result.Component.__dict__.keys() if x.lower() == screenshot._group_name.lower()]
        except:
            the_lw.WriteFullline("Error in input " + screenshot._file_name)
            the_lw.WriteFullline("Component with name " + screenshot._component_name + " is not a valid identifier.")
            the_lw.WriteFullline("Component names are case sensitive.")
            the_lw.WriteFullline("Have a look at the options in the post processing navigator in the GUI.")
            the_lw.WriteFullline("Valid identifiers are:")
            for component in NXOpen.CAE.Result.Component.__dict__.keys():
                the_lw.WriteFullline(str(component))
            raise ValueError("Component with name " + screenshot._component_name + " not found")

        # check the camera
        camera: NXOpen.Display.Camera = [x for x in cameras if x.Name.lower() == screenshot._camera_name.lower()]
        if len(camera) == 0:
            the_lw.WriteFullline("Error in input " + screenshot._file_name)
            the_lw.WriteFullline("Camera with name " + screenshot._camera_name + " not found")
            raise ValueError("Camera with name " + screenshot._camera_name + " not found")
        elif len(camera) != 1:   
            the_lw.WriteFullline("WARNING " + screenshot._file_name)
            the_lw.WriteFullline("FOUND MULTIPLE CAMERAS WITH THE NAME " + screenshot._camera_name)


def read_screenshot_definitions(file_path: str) -> List[ScreenShot]:
    """
    Reads screenshot definitions from a CSV file and returns a list of `ScreenShot` objects.

    Each line in the file should represent a screenshot definition, with attributes
    separated by commas. The function validates the file content, ensures the correct
    number of attributes, and parses each line into a `ScreenShot` object.

    Parameters
    ----------
    file_path : str
        Path to the CSV file containing screenshot definitions.

    Returns
    -------
    List[ScreenShot]
        A list of `ScreenShot` objects created from the file content.
    
    Raises
    ------
    FileNotFoundError
        If the specified file does not exist.
    ValueError
        If a line in the file does not contain exactly 10 attributes or has invalid data.
    Exception
        If an error occurs during file reading or parsing.

    Notes
    -----
    - Each line in the input file must have exactly 10 comma-separated values:
      `[file_name, annotation_text, template_name, group_name, camera_name, solution, subcase, iteration, resultType, component_name]`.
    - The `subcase` and `iteration` fields are expected to be integers.
    - Commas in names are not allowed to avoid parsing errors.
    - Tested in SC2312
    """
    if (not os.path.exists(file_path)):
        the_lw.WriteFullline("Error: could not find " + file_path)
    
    with open(file_path, 'r') as file:
        csv_string: List[str] = file.readlines()
    
    # the_lw.WriteFullline(csv_string)
    
    screenshots_from_file: List[ScreenShot] = []
    for line in csv_string:
        if line == "" or len(line) == 1: # empty line has length 1...
            continue
        values: List[str] = line.split(",")
        if (len(values) != 10):
            the_lw.WriteFullline("There should be 10 items in each input line, separated by commas. Please check the input and make sure not to use commas in the names.")
            for i in range(len(values)):
                the_lw.WriteFullline("Item " + str(i) + ": " + values[i])
            raise Exception("There should be 10 items in each input line, separated by commas. Please check the input above and make sure not to use commas in the names.")

        entry: ScreenShot = ScreenShot("", "", -1, "")
        entry._file_name = values[0].strip()
        entry._annotation_text = values[1].strip()
        entry._template_name = values[2].strip()
        entry._group_name = values[3].strip()
        entry._camera_name = values[4].strip()
        entry._solution = values[5].strip()
        entry._subcase = int(values[6].strip())
        entry._iteration = int(values[7].strip())
        entry._resultType = values[8].strip()
        entry._component_name = values[9].strip()
        screenshots_from_file.append(entry)

    # Check if the file is empty
    if len(screenshots_from_file) == 0:
        return None
    
    return screenshots_from_file


def display_result(post_input: PostInput, solution_result: NXOpen.CAE.SolutionResult, component_name: str) -> int:
    """
    Displays a specific result in the NX post-processing environment.

    This function sets the result type and component for a postview using the provided
    `PostInput`, `SolutionResult`, and component name. It then creates a postview and
    returns its ID so the user gets a handle for later use.

    Parameters
    ----------
    post_input : PostInput
        The input object containing metadata about the post-processing operation.
    solution_result : NXOpen.CAE.SolutionResult
        The result object associated with the solution to be visualized.
    component_name : str
        The name of the component to be displayed. This name must match an attribute
        in `NXOpen.CAE.Result.Component` exactly (case-sensitive).

    Returns
    -------
    int
        The postview ID created for the displayed result.

    Raises
    ------
    AttributeError
        If `component_name` does not match any valid attribute in `NXOpen.CAE.Result.Component`.
    ValueError
        If the result type cannot be determined or the postview creation fails.

    Notes
    -----
    - The `component_name` must be validated beforehand to ensure it matches a valid
      component in the NX environment.
    - Tested in SC2312
    """
    # Only set the result and the component, the rest is through the template.
    result_type: NXOpen.CAE.ResultType = get_result_types([post_input], [solution_result])[0]
    # Get the component object from the string componentName
    # note this needs to be exact. The check is done when checking the user input.
    component: NXOpen.CAE.Result.Component = getattr(NXOpen.CAE.Result.Component, component_name)
    result_parameters: NXOpen.CAE.ResultParameters = the_session.ResultManager.CreateResultParameters()
    result_parameters.SetGenericResultType(result_type)
    result_parameters.SetResultComponent(component)
    postview_id: int = the_session.Post.CreatePostviewForResult(0, solution_result, False, result_parameters)

    return postview_id


def set_post_template(postview_id: int, template_name: str) -> None:
    """
    Sets a post-processing template for a given postview.

    This function applies a specific post-processing template to a postview by searching for
    the template by name and associating it with the provided postview ID.

    Parameters
    ----------
    postview_id : int
        The ID of the postview to which the template will be applied.
    template_name : str
        The name of the template to be applied.

    Returns
    -------
    None

    Raises
    ------
    ValueError
        If the specified template name cannot be found.

    Notes
    -----
    - The template name must exist in the session's template library. If not, the function
    will raise an error during the template search operation.
    - Templates define specific visual settings and layouts for the results in the NX environment.
    - Tested in SC2312
    """
    template_id: int = the_session.Post.TemplateSearch(template_name)
    the_session.Post.PostviewApplyTemplate(postview_id, template_id)


def change_component(postview_id: int, component_name: str) -> None:
    """
    Changes the result component for a given postview.

    This function updates the component displayed in a specific postview by modifying the 
    result parameters associated with it. The postview is then updated to reflect the changes.

    Parameters
    ----------
    postview_id : int
        The ID of the postview to be modified.
    component_name : str
        The name of the component to display. This must match an attribute in 
        `NXOpen.CAE.Result.Component` exactly (case-sensitive).

    Returns
    -------
    None

    Raises
    ------
    AttributeError
        If `component_name` does not match any valid attribute in `NXOpen.CAE.Result.Component`.
    ValueError
        If the postview ID is invalid or the result parameters cannot be updated.

    Notes
    -----
    - The `component_name` must correspond to a valid component in the NX environment.
    - The function fetches the current result and parameters for the specified postview, modifies
    the component, and updates the postview accordingly.
    - Tested in SC2312
    """

    component: NXOpen.CAE.Result.Component = getattr(NXOpen.CAE.Result.Component, component_name)
    result: NXOpen.CAE.Result
    result_parameters: NXOpen.CAE.ResultParameters
    result, result_parameters = the_session.Post.GetResultForPostview(postview_id) # type: ignore
    result_parameters.SetResultComponent(component)
    the_session.Post.PostviewSetResult(postview_id, result_parameters)
    the_session.Post.PostviewUpdate(postview_id)


def display_elements_in_group_via_postgroup(postview_id: int, group_name: str, sim_part: NXOpen.CAE.SimPart=None) -> None:
    """
    Displays elements in a specified group by creating a postgroup on the fly.

    This function leverages NX post-processing to display only the elements in a specified group
    within a given postview. It creates a "PostGroup" based on the element labels in the group
    from the simulation file and applies it to the postview.

    Parameters
    ----------
    postview_id : int
        The ID of the postview where the elements will be displayed.
    group_name : str
        The name of the group containing the elements to be displayed.
    sim_part : NXOpen.CAE.SimPart, optional
        The simulation part containing the group. If not provided, the currently active 
        `.sim` file in the session is used.

    Returns
    -------
    None

    Raises
    ------
    ValueError
        If the function is not called on a `.sim` file or if the specified group cannot be found.
    NXOpen.Exceptions.NXException
        If any operation in the NX session fails (e.g., creating postgroups or applying visibility).

    Notes
    -----
    - NX automatically creates "PostGroups" for groups in the simulation file, but only if the groups 
    contain nodes or elements. This function handles cases where a direct mapping between simulation 
    groups and postgroups is not straightforward.
    - Due to a known bug in NX, `CreateUserGroupFromEntityLabels` only accepts a single label for elements.
    This implementation compensates by adding an extra placeholder label to avoid missing elements.
    - Historical code. Replaced with copy_groups_to_sim_part and display_elements_in_group_using_workaround.
    """

    # NX creates it's own postgroups from the groups in the sim.
    # It only creates a postgroup if either nodes or elements are present in the group.
    # Therefore it's hard to relate the postgroup labels to the group labels in the simfile...

    # however, CreateUserGroupFromEntityLabels has a bug as it only accepts a single label for the elements
    if sim_part is None:
        if not isinstance(the_session.Parts.BaseWork, NXOpen.CAE.SimPart):
            raise ValueError("display_elements_in_group_via_postgroup needs to be called on a .sim file!")
        sim_part: NXOpen.CAE.SimPart = cast(NXOpen.CAE.SimPart, the_session.Parts.BaseWork)
    
    cae_groups: NXOpen.CAE.CaeGroupCollection = sim_part.CaeGroups
    cae_group: NXOpen.CAE.CaeGroup = [x for x in cae_groups if x.Name.lower() == group_name.lower()][0]

    groupItems: List[NXOpen.TaggedObject] = cae_group.GetEntities()
    # one longer, otherwise a single element is missing from each screenshot (bug in NX)
    groupElementLabels: List[int] = [NXOpen.CAE.BaseResultType] * (len(groupItems) + 1)
    groupElementLabels[0] = 0
    for i in range(len(groupItems)):
        if isinstance(groupItems[i], NXOpen.CAE.FEElement):
            groupElementLabels[i + 1] = (cast(NXOpen.CAE.FEElement, groupItems[i])).Label

    userGroupIds: List[int] = [int] * 1
    # This creates a "PostGroup", but there is a bug in CreateUserGroupFromEntityLabels as it accepts only a single label for the elements
    userGroupIds[0] = the_session.Post.CreateUserGroupFromEntityLabels(postview_id, NXOpen.CAE.CaeGroupCollection.EntityType.Element, groupElementLabels) # type: ignore
    the_session.Post.PostviewApplyUserGroupVisibility(postview_id, userGroupIds, NXOpen.CAE.Post.GroupVisibility.ShowOnly) # type: ignore


def display_elements_in_group(postview_id: int, group_name: str) -> None:
    """
    Displays elements in a specified group within a postview.

    This function checks for the presence of a specified group in the simulation file and attempts 
    to display its elements in the provided postview. A workaround is applied for certain NX versions 
    due to known API limitations regarding group visibility.

    Parameters
    ----------
    postview_id : int
        The ID of the postview where the group elements will be displayed.
    group_name : str
        The name of the group whose elements are to be displayed.

    Returns
    -------
    None

    Raises
    ------
    ValueError
        If the specified group cannot be found in the simulation file or if a bug in the NX API
        prevents the group from being displayed.

    Notes
    -----
    - If the NX version is v12, a known bug in the NX API prevents groups from being displayed if 
    they are not defined in the simulation file. A workaround is suggested, which involves creating 
    the same group directly in the simulation file.
    - The function checks for user groups associated with the postview. If the group is not found, it raises 
    an error and suggests a workaround to create the group in the simulation file.
    - If the group is found, the function applies the visibility settings to display only the elements of 
    that group in the postview.
    - Historical code. Replaced with copy_groups_to_sim_part and display_elements_in_group_using_workaround.
    """
    nx_version: str = the_session.GetEnvironmentVariableValue("UGII_VERSION") # theSession.BuildNumber only available from version 1926 onwards
    if nx_version == "v12":
        the_lw.WriteFullline("Error: Due to a bug in the NX API, the group " + group_name + " cannot be displayed, because it has not been defined in the sim file.")
        the_lw.WriteFullline("A workaround is to create the same group in the sim file and use that in the journal.")
        # display_elements_in_group_via_postgroup(postview_id, group_name)
        raise ValueError("Group " + group_name + " not found in the sim file.")
    else:
        # The next function only works for Groups created in the .sim file (at least when used like this)
        # And not for groups inherited from the fem or afem file. Also using the JournalIdentifier did not work.
        # Therefore a workaround with a postgroup for these fem or afem groups.
        usergroups_gids = the_session.Post.PostviewGetUserGroupGids(postview_id, [group_name]) # type: ignore single string according docs
        if len(usergroups_gids) == 0:
            the_lw.WriteFullline("Error: Due to a bug in the NX API, the group " + group_name + " cannot be displayed, because it has not been defined in the sim file.")
            the_lw.WriteFullline("A workaround is to create the same group in the sim file. The function copy_groups_to_sim_part can be used for this.")
            # display_elements_in_group_via_postgroup(postview_id, group_name)
            raise ValueError("Group " + group_name + " not found in the sim file.")
        else:
            the_session.Post.PostviewApplyUserGroupVisibility(postview_id, usergroups_gids, NXOpen.CAE.Post.GroupVisibility.ShowOnly) # type: ignore


def display_elements_in_group_using_workaround(postview_id: int, group_name: str) -> None:
    """
    Displays elements in a specified group. If the groups is not found, a check is performed
    to see if a temporary group with suffix "_screenshot_generator_temp" exists. If it does,
    the elements in that group are displayed.
    This is because in some versions of NX (e.g., NX 12), only groups in the .sim file can be displayed
    using 'PostviewApplyUserGroupVisibility'

    Parameters
    ----------
    postview_id : int
        The ID of the postview where the group elements will be displayed.
    group_name : str
        The name of the group whose elements are to be displayed.

    Returns
    -------
    None

    Raises
    ------
    ValueError
        If neither the specified group nor its workaround (temporary group) can be found in the simulation file.

    Notes
    -----
    - The function first attempts to fetch the user group by the given `group_name`. If it is not found,
    it tries to use a temporary group created earlier (with the suffix "_screenshot_generator_temp").
    - If neither group is found, an error is raised.
    - This function is intended to handle cases where groups are not directly available or compatible due to 
    limitations in certain versions of NX (e.g., NX 12).
    - Tested in SC2312
    """
    # this should also work for NX12 (not tested)
    usergroups_gids = the_session.Post.PostviewGetUserGroupGids(postview_id, [group_name]) # type: ignore single string according docs
    if len(usergroups_gids) == 0:
        # the_lw.WriteFullline(f'Using workaround for non-sim group {group_name} using the earlier copied group {group_name + "_screenshot_generator_temp"}')
        usergroups_gids = the_session.Post.PostviewGetUserGroupGids(postview_id, [group_name + "_screenshot_generator_temp"]) # type: ignore single string according docs
        # the_lw.WriteFullline(str(usergroups_gids))
        if len(usergroups_gids) == 0:
            the_lw.WriteFullline(f'Error: Group {group_name + "_screenshot_generator_temp"} not found in the sim file.')
            raise ValueError(f'Group {group_name + "_screenshot_generator_temp"} not found in the sim file.')
        else:
            the_session.Post.PostviewApplyUserGroupVisibility(postview_id, usergroups_gids, NXOpen.CAE.Post.GroupVisibility.ShowOnly) # type: ignore
    else:
        the_session.Post.PostviewApplyUserGroupVisibility(postview_id, usergroups_gids, NXOpen.CAE.Post.GroupVisibility.ShowOnly) # type: ignore


def map_group_to_postgroup(postview_id: int, sim_part: NXOpen.CAE.SimPart=None) -> Dict[str, int]:
    """
    Maps simulation groups to postgroups in a postview.

    This function attempts to map simulation groups (from the .sim file) to postgroups in a postview. It considers
    groups that contain nodes or elements and attempts to find the corresponding postgroup IDs. A workaround is 
    applied for earlier versions of NX (eg. NX12 and earlier) where postgroup numbering may be dependent on the number of postviews already 
    created. The function does not currently return a mapping but sets up the postgroup visibility for the given postview.

    Parameters
    ----------
    postview_id : int
        The ID of the postview where the postgroup visibility will be applied.
    sim_part : NXOpen.CAE.SimPart, optional
        The simulation part containing the groups. If not provided, the currently active `.sim` file in the session is used.

    Returns
    -------
    Dict[str, int]
        A dictionary mapping the group names to their respective postgroup IDs. This is a placeholder for future functionality.

    Raises
    ------
    ValueError
        If the function is called on a non-simulation file or if the simulation part cannot be accessed.
    NXOpen.Exceptions.NXException
        If the postgroup visibility update or mapping fails due to issues in the NX session.

    Notes
    -----
    - This function is not yet fully functional for mapping group names to postgroup IDs. The part that performs
    the actual mapping is still to be implemented.
    - The `PostviewApplyUserGroupVisibility` method is used to attempt to identify valid postgroup IDs, and the 
    last valid postgroup number is determined by incrementing and then decrementing a counter.
    - NX versions such as NX12 may have different behavior for postgroup numbering based on the session's history of postviews.
    - The function attempts to handle groups that have either nodes or elements, and works with groups created in the 
    simulation part.
    """

    # this function is just for future reference, as it is not used in the journal
    # the numbering of the postgroups is not the same as the numbering of the groups in the sim file
    # and also depends on the number of postviews already created
    # In NX12 the postgroup number would also depend on how many postview were already created in the session.
    # NX2212 does not seem to have this issue anymore.
    if sim_part is None:
        if not isinstance(the_session.Parts.BaseWork, NXOpen.CAE.SimPart):
            raise ValueError("map_group_to_postgroup needs to be called on a .sim file!")
        sim_part: NXOpen.CAE.SimPart = cast(NXOpen.CAE.SimPart, the_session.Parts.BaseWork)

    the_session.Post.UpdateUserGroupsFromSimPart() # type: ignore
    all_groups: List[NXOpen.CAE.CaeGroup] = [group for group in sim_part.CaeGroups] # type: ignore
    # the postgroups are all groups with either nodes or elements or both
    all_groups_with_nodes_or_elements: List[NXOpen.CAE.CaeGroup] = []
    flag: bool = False
    for group in all_groups:
        for item in group.GetEntities():
            if flag:
                flag = False
                break
            if isinstance(item, NXOpen.CAE.FEElement) or isinstance(item, NXOpen.CAE.FENode):
                all_groups_with_nodes_or_elements.append(group)
                flag = True
    
    # perform a try catch from a high number down, untill the PostviewApplyUserGroupVisibility does not throw an error
    # this is the last postgroup number.
    usergroup_ids = [None] * 1
    # in certain NX versions the postgroup number is dependent on the number of postviews already created (Eg NX12).
    # this approach can fail if the postgroup numbering has increased by more than 100 due to the creation of postviews.
    counter: int = len(all_groups) + 100 
    while True:
        usergroup_ids[0] = counter
        try:
            the_session.Post.PostviewApplyUserGroupVisibility(postview_id, usergroup_ids, NXOpen.CAE.Post.GroupVisibility.ShowOnly) # type: ignore
            break
        except:
            counter -= 1
     # counter is now the index of the last postgroup.
     # still to implement the mapping.
     # theoretically the postgroup number should be the same as the index in all_groups_with_nodes_or_elements, but see earlier comment for NX12
      

def create_annotation(postview_id: int, annotation_text: str, sim_part: NXOpen.CAE.SimPart=None) -> NXOpen.CAE.PostAnnotation:
    """
    Creates a user-defined annotation in a postview.

    This function allows the creation of an annotation in a postview within a simulation part. It sets the name, 
    type, and location of the annotation, and applies various visual properties such as the background box and color.

    Parameters
    ----------
    postview_id : int
        The ID of the postview where the annotation will be created.
    annotation_text : str
        The text to be displayed in the annotation.
    sim_part : NXOpen.CAE.SimPart, optional
        The simulation part in which the annotation will be created. If not provided, the function uses the 
        currently active simulation part in the session.

    Returns
    -------
    NXOpen.CAE.PostAnnotation
        The created annotation object.

    Raises
    ------
    ValueError
        If the function is called outside of a valid `.sim` file.
    NXOpen.Exceptions.NXException
        If there are issues creating or drawing the annotation in the session.

    Notes
    -----
    - The annotation is created with a default name "AnnotationName" and placed at a fixed coordinate (0.5, 0.05).
    - The background box for the annotation is drawn with a translucent fill color, and the box's color is set 
    based on the simulation part's color palette (using index 0).
    - Tested in SC2312
    """

    if sim_part is None:
        if not isinstance(the_session.Parts.BaseWork, NXOpen.CAE.SimPart):
            raise ValueError("create_annotation needs to be called on a .sim file!")
        sim_part: NXOpen.CAE.SimPart = cast(NXOpen.CAE.SimPart, the_session.Parts.BaseWork)

    post_annotation_builder: NXOpen.CAE.PostAnnotationBuilder = the_session.Post.CreateAnnotationBuilder(postview_id)
    post_annotation_builder.SetName("AnnotationName")
    post_annotation_builder.SetAnnotationType(NXOpen.CAE.PostAnnotationBuilder.Type.Userloc)
    post_annotation_builder.SetCoordinate(0.5, 0.05)

    post_annotation_builder.SetUsertext([annotation_text]) # single string according docs, but actually requires a list of str

    post_annotation = post_annotation_builder.CommitAnnotation()
    post_annotation.DrawBox = True
    post_annotation.BoxTranslucency = False
    post_annotation.BoxFill = True
    post_annotation.BoxColor = sim_part.Colors.Find(0)
    post_annotation.Draw()

    post_annotation_builder.Dispose()

    return post_annotation


def set_camera(camera_name: str, base_part: NXOpen.BasePart=None) -> None:
    """
    Sets the camera view for the specified base part.

    This function applies a camera view to the work view of a given (sim) part or the currently active simulation part. 
    It locates the camera by name and then applies it to the part's work view, updating the view accordingly.

    Parameters
    ----------
    camera_name : str
        The name of the camera to be applied to the work view.
    base_part : NXOpen.BasePart, optional
        The base part in which the camera view will be applied. If not provided, the function uses the 
        currently active base part in the session.

    Returns
    -------
    None

    Raises
    ------
    ValueError
        If no camera with the specified name exists in the part.

    Notes
    -----
    - The function searches for the camera by name in the part's camera collection and applies the camera to the
    active work view.
    - The camera's name comparison is case-insensitive.
    - Tested in SC2312
    """
    # technically set_camera should be able to be called on a BasePart
    if base_part is None:
        base_part: NXOpen.BasePart = the_session.Parts.BaseWork
    cameras: NXOpen.Display.CameraCollection = base_part.Cameras
    camera: NXOpen.Display.Camera = [x for x in cameras if x.Name.lower() == camera_name.lower()][0]
    camera.ApplyToView(base_part.ModelingViews.WorkView)


def save_view_to_file(file_name: str) -> None:
    """
    Saves the current view of the model to a file in TIFF format.

    This function exports the current view of the model to an image file in TIFF format. If the specified file already exists, 
    it is deleted to ensure that the new image overwrites the previous one. The image export options are set to enhance edges, 
    make the background transparent, and save in the TIFF file format.

    Parameters
    ----------
    file_name : str
        The name of the file to save the view as. The function will append the `.tif` extension if it is not already included. 
        If no path is provided, the file will be saved in the current directory.

    Returns
    -------
    None

    Raises
    ------
    FileNotFoundError
        If the file path is invalid or the file cannot be created.
        
    IOError
        If an error occurs during the image export process.

    Notes
    -----
    - The function currently only supports saving images in TIFF format.
    - If the file already exists, it will be deleted and overwritten with the new image.
    - Tested in SC2312
    """
    # TODO: add options for file formats other than .tiff
    # check if fileName contains a path. If not save with the .sim file
    file_path_without_extension: str = create_full_path(file_name, "") # should be in line with imageExportBuilder.FileFormat
    file_path_with_extension: str = file_path_without_extension + "tif"

    # delete existing file to mimic overwriting
    if (os.path.exists(file_path_with_extension)):
        os.remove(file_path_without_extension)
    
    image_export_builder: NXOpen.Gateway.ImageExportBuilder = the_ui.CreateImageExportBuilder()
    try:
        # Options
        image_export_builder.EnhanceEdges = True
        image_export_builder.RegionMode = False
        image_export_builder.FileFormat = NXOpen.Gateway.ImageExportBuilder.FileFormats.Tiff # should be in line with the fileName
        image_export_builder.FileName = file_path_without_extension # NX adds the extension for the specific file format
        image_export_builder.BackgroundOption = NXOpen.Gateway.ImageExportBuilder.BackgroundOptions.Transparent
        # Commit the builder
        image_export_builder.Commit()
    except Exception as e:
        the_lw.WriteFullline(str(e))
    finally:
        image_export_builder.Destroy()


def delete_post_groups(sim_part: NXOpen.CAE.SimPart=None) -> None:
    """
    Deletes automatically created post groups from a .sim file.

    This function searches for groups within the given `SimPart` that have names starting with "PostGroup" and deletes 
    those that have a numeric suffix (i.e., automatically generated post groups). The function ensures that user-created groups 
    are not accidentally deleted by checking for a numeric suffix.

    Parameters
    ----------
    sim_part : NXOpen.CAE.SimPart, optional
        The CAE SimPart to search for post groups. If no `SimPart` is provided, the function uses the currently active work part.

    Returns
    -------
    None

    Raises
    ------
    ValueError
        If the function is called with a part that is not a `.sim` file.

    Notes
    -----
    - This function marks the deleted post groups for removal and performs an update to apply the changes.
    - The function only deletes post groups with names that contain a numeric suffix to avoid deleting user-created groups.
    - Tested in SC2312
    """

    if sim_part is None:
        if not isinstance(the_session.Parts.BaseWork, NXOpen.CAE.SimPart):
            raise ValueError("delete_post_groups needs to be called on a .sim file!")
        sim_part: NXOpen.CAE.SimPart = cast(NXOpen.CAE.SimPart, the_session.Parts.BaseWork)

    found_post_group: bool = False
    cae_groups: List[NXOpen.CAE.CaeGroup] = sim_part.CaeGroups
    post_groups: List[NXOpen.CAE.CaeGroup] = [x for x in cae_groups if x.Name.startswith("PostGroup")]

    for item in post_groups:
        # only delete the ones with a number at the end (so there is the least chance of accidentily deleting an acutal user created group)
        if item.Name[9:].isdigit():
            the_session.UpdateManager.AddObjectsToDeleteList([cast(NXOpen.NXObject, item)])
            found_post_group = True
    
    if found_post_group:
        undo_mark_id = the_session.SetUndoMark(NXOpen.Session.MarkVisibility.Invisible, "deletePostGroup")
        the_session.UpdateManager.DoUpdate(undo_mark_id)
        the_lw.WriteFullline("Removed automatically created PostGroups")


def print_message() -> None:
    the_lw.WriteFullline("##################################################################################################")
    the_lw.WriteFullline("##################################################################################################")
    the_lw.WriteFullline("##################################################################################################")
    the_lw.WriteFullline("THE SOFTWARE IS PROVIDED 'AS IS', WITHOUT WARRANTY OF ANY KIND, EXPRESS OR")
    the_lw.WriteFullline("IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,")
    the_lw.WriteFullline("FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE")
    the_lw.WriteFullline("AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER")
    the_lw.WriteFullline("LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,")
    the_lw.WriteFullline("OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE")
    the_lw.WriteFullline("SOFTWARE.")
    the_lw.WriteFullline("##################################################################################################")
    the_lw.WriteFullline("##################################################################################################")
    the_lw.WriteFullline("##################################################################################################")
    the_lw.WriteFullline("                        You have just experienced the power of scripting                          ")
    the_lw.WriteFullline("                             brought to you by theScriptingEngineer                               ")
    the_lw.WriteFullline("                                   www.theScriptingEngineer.com                                   ")
    the_lw.WriteFullline("                                  More journals can be found at:                                  ")
    the_lw.WriteFullline("                        https://github.com/theScriptingEngineer/nxopentse                        ")
    the_lw.WriteFullline("##################################################################################################")
    the_lw.WriteFullline("##################################################################################################")
    the_lw.WriteFullline("##################################################################################################")
    the_lw.WriteFullline("                                          Learn NXOpen at                                         ")
    the_lw.WriteFullline("https://www.udemy.com/course/simcenter3d-basic-nxopen-course/?referralCode=4ABC27CFD7D2C57D220B%20")
    the_lw.WriteFullline("https://www.udemy.com/course/siemens-nx-beginner-nxopen-course-python/?referralCode=DEE8FAB445765802FEDC")
    the_lw.WriteFullline("##################################################################################################")
    the_lw.WriteFullline("##################################################################################################")
    the_lw.WriteFullline("##################################################################################################")


def create_screen_shots() -> None:
    """
    Automatically generates screenshots of post-processing results using definitions provided in a .csv file.

    The .csv file should be formatted as follows:
    FileName, AnnotationText, TemplateName, GroupName, CameraName, Solution, Subcase, Iteration, ResultType, ComponentName

    Example:
    screenshot1.tif, Text displayed on top of screenshot1, Template 1, Group 1, TopView, Solution 1, 1, 1, Stress - Element-Nodal, VonMises

    The script runs from the .sim file and uses the data in the .csv file to generate screenshots. Each row in the file corresponds 
    to a different screenshot and its associated settings.

    Parameters
    ----------
    None

    Returns
    -------
    None

    Notes
    -----
    - FileName: Specifies the file name (with or without path) for the screenshot. If no path is provided, it is saved in the 
      location of the .sim file.
    - AnnotationText: Text to be displayed on top of the screenshot.
    - TemplateName: Name of the PostView template to apply for displaying results.
    - GroupName: Name of the CaeGroup to display. The name is not case-sensitive.
    - CameraName: Name of the camera (as seen in the GUI) used to orient the screenshot view.
    - Solution: The name of the solution to display.
    - Subcase: The subcase number (starting from 1).
    - Iteration: The iteration number (starting from 1). Defaults to 1 for results without iterations.
    - ResultType: The type of result (e.g., "Stress - Element-Nodal", "Displacement - Nodal").
    - ComponentName: Name of the result component (case-sensitive) such as Scalar, VonMises, or Displacement components.

    - The user needs to manually ensure that the camera view is saved before generating the screenshot, otherwise, unexpected results may occur.

    - A manually edited template.xml file may be required:
        * Delete specific entries under the <ResultOptions> tag:
            - <LoadCase>0</LoadCase>
            - <Iteration>0</Iteration>
            - <SubIteration>-1</SubIteration>
            - <Result>[Displacement][Nodal]</Result>
            - <Component>Magnitude</Component>

    It is advised to update the group visibility with the following (assuming there are less than 1000 groups in the model).
    Note that other types might exist (like <Num3DGroups>). Adjust accordingly.
            <GroupVisibilities>
                <Num1DGroups>1000</Num1DGroups>
                <Visibilities1DGroups>1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1</Visibilities1DGroups>
                <Num2DGroups>1000</Num2DGroups>
                <Visibilities2DGroups>1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1</Visibilities2DGroups>
            </GroupVisibilities>

    Post processing XML template files are located under the location where UGII_CAE_POST_TEMPLATE_USER_DIR is pointing to.
    This can be found in the log file.
    If you also set UGII_CAE_POST_TEMPLATE_EDITOR to for example notepad++.exe,
    you can directly edit by right-clicking the template in the NX GUI
    
    """
    the_lw.Open()

    # user feedback
    base_part: NXOpen.BasePart = the_session.Parts.BaseWork
    if not isinstance(base_part, NXOpen.CAE.SimPart):
        the_lw.WriteFullline("ScreenshotGenerator needs to be started from a .sim file!")
        return

    root = tk.Tk()
    root.withdraw()

    # file_paths is a tuple with all the selected files (user can select multiple files)
    file_paths = filedialog.askopenfilenames(title = "Select input file", filetypes = (("csv files (*.csv)","*.csv"),))

    if file_paths == '':
        # user pressed cancel
        return

    # read the input file into an array of ScreenShot
    # it's user input, so errors can occur
    screenshots: List[ScreenShot] = []
    for file_path in list(file_paths):
        try:
            screenshots.extend(read_screenshot_definitions(file_path))
        except Exception as e:
            the_lw.WriteFullline("Failed to parse file " + file_path + ". Please check the screenshot definitions in the file.")
            the_lw.WriteFullline(str(e))
            return
    
    # check for empty file
    if len(screenshots) == 0:
        the_lw.WriteFullline(f"The file(s) {file_paths} is empty.")
        return
    
    # check input and catch errors so that the user doesn't get a error pop-up in SC
    try:
        check_screenshots(screenshots)
    except Exception as e:
        the_lw.WriteFullline("The following error occured while checking the screenshot definitions:")
        the_lw.WriteFullline(str(e))
        return

    # PostviewGetUserGroupGids only works with groups created in the .sim file
    # the workaround is to create a postgroup with the same elements using the function CreateUserGroupFromEntityLabels
    # however, the latter only accepts a single label for the element
    # there are 2 possible workaourns:
    # 1. Get the postgroup index from the sim group and use that in the PostviewApplyUserGroupVisibility, however, the index is not the same as the group number
    #    because only groups which have nodes or elements are converted to postgroups
    # 2. Copy all non-sim groups to the sim part and use the PostviewApplyUserGroupVisibility
    
    # implement workaround 2
    sim_part: NXOpen.CAE.SimPart = cast(NXOpen.CAE.SimPart, base_part)
    # improve performance by only copying the groups used in the screenshots
    groups_in_screenshots: List[str] = [screenshot._group_name for screenshot in screenshots]
    copied_groups: List[NXOpen.CAE.CaeGroup] = copy_groups_to_sim_part(sim_part, groups_in_screenshots)
    the_session.Post.UpdateUserGroupsFromSimPart(sim_part) # type: ignore
    # now if a group is not found using PostviewGetUserGroupGids, get the group which has been copied to the sim part
    
    # sort for performance in NX
    # we don't put requirements on the order of the screen shots,
    # only changing the group to display is very fast, compared to changing the result.
    # Sorting minimizes the amount of switches between solutions and subcases and thus improves performance
    screenshots = sort_screenshots(screenshots)

    # load all results before the loop
    solutionResults: List[NXOpen.CAE.SolutionResult] = load_results(screenshots, sim_part=sim_part)

    # Keep track of all original CaeGroups, so the (possible) Created PostGroups can be tracked and deleted
    # Without accidentaly deleting user groups which might start with PostGroup.
    sim_part: NXOpen.CAE.SimPart = cast(NXOpen.CAE.SimPart, base_part)
    cae_groups_original: NXOpen.CAE.CaeGroupCollection = sim_part.CaeGroups

    postview_id: int = -1
    # process the screenshots
    # using a for loop with index, so I can compare the current to the previous screenshot
    the_lw.WriteFullline("Generated " + str(len(screenshots)) + " screenshots with the following input:")
    for i in range(len(screenshots)):
        the_lw.WriteFullline(str(screenshots[i]))

        # set the result to be displayed
        # don't change if not required (but need to always display the first time):
        if i != 0:
            if screenshots[i].need_change_result(screenshots[i - 1]):
                postview_id = display_result(screenshots[i], solutionResults[i], screenshots[i]._component_name)
        else:
            postview_id = display_result(screenshots[i], solutionResults[i], screenshots[i]._component_name)

        # set the post template (do this before setting the group, as the template might have group visibility still in it)
        # no need to set if it hasn't changed, but displaying another solution removes the template settings so also need to set the template after changing the solution.
        # Note that you need to delete de definition of the 'result to display' from the template xml file! 
        # Otherwise applying the template changes the displayed result.
        if i != 0:
            if screenshots[i]._template_name != screenshots[i - 1]._template_name or screenshots[i]._solution != screenshots[i - 1]._solution:
                set_post_template(postview_id, screenshots[i]._template_name)
            else:
                set_post_template(postview_id, screenshots[i]._template_name)
        else:
            set_post_template(postview_id, screenshots[i]._template_name)

        # Removing the <component> tag, makes NX used the default component (eg. Magnitude for Displacement, Von-Mises for stress, ...)
        # Therefore setting the correct component again after applying the template
        # postview_id = display_result(screenshots[i], solutionResults[i], screenshots[i]._component_name)
        change_component(postview_id, screenshots[i]._component_name)

        # Set the group to display, using the workaround described earlier
        display_elements_in_group_using_workaround(postview_id, screenshots[i]._group_name)

        # Create the annotation but only if one given.
        post_annotation: NXOpen.CAE.PostAnnotation = None
        if not (screenshots[i]._annotation_text == "" or screenshots[i]._annotation_text == None):
            post_annotation = create_annotation(postview_id, screenshots[i]._annotation_text, sim_part)
        
        # Position the result in the view with the camera.
        # Cameras are created in the GUI
        set_camera(screenshots[i]._camera_name, sim_part)

        # Save the screenshot to file.
        save_view_to_file(screenshots[i]._file_name)

        # Clean up annotations, otherwise annotations pile up
        if post_annotation != None:
            post_annotation.Delete()
    
    # the following line does not contain the newly creates postgroups (contrary to C#)
    # cae_groups: NXOpen.CAE.CaeGroupCollection = sim_part.CaeGroups
    # Therefore deleting all created PostGroups
    delete_post_groups(sim_part)

    # Delete all copied groups.
    # use the name, in case a crash has happend at some point
    # for group in copied_groups:
    #     the_session.UpdateManager.AddObjectsToDeleteList([group])
    # undo_mark_id = the_session.SetUndoMark(NXOpen.Session.MarkVisibility.Invisible, "deleteCopiedGroups")
    # the_session.UpdateManager.DoUpdate(undo_mark_id)

    sim_groups: List[NXOpen.CAE.CaeGroup] = [item for item in sim_part.CaeGroups]
    for group in sim_groups:
        if group.Name.endswith('_screenshot_generator_temp'):
            the_session.UpdateManager.AddObjectsToDeleteList([group])
    undo_mark_id = the_session.SetUndoMark(NXOpen.Session.MarkVisibility.Invisible, "deleteCopiedGroups")
    the_session.UpdateManager.DoUpdate(undo_mark_id)

    print_message()
