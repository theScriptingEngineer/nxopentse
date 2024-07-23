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
    """A class for declaring screenshots, inherits from PostInput"""
    _file_name: str
    _annotation_text: str
    _template_name: str
    _group_name: str
    _component_name: str
    _camera_name: str

    def need_change_result(self, other) -> bool:
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
        return f"ScreenShot(file_name='{self._file_name}', annotation_text={self._annotation_text}, " \
               f"template_name={self._template_name}, group_name='{self._group_name}', " \
               f"component_name='{self._component_name}', camera_name='{self._camera_name}')"


def sort_screenshots(screenshots: List[ScreenShot]) -> List[ScreenShot]:
    return sorted(screenshots, key=lambda x: (x._solution, x._subcase, x._iteration, x._resultType))


def check_screenshots(screenshots: List[ScreenShot], sim_part: NXOpen.CAE.SimPart=None) -> None:
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
    template_id: int = the_session.Post.TemplateSearch(template_name)
    the_session.Post.PostviewApplyTemplate(postview_id, template_id)


def change_component(postview_id: int, component_name: str) -> None:
    component: NXOpen.CAE.Result.Component = getattr(NXOpen.CAE.Result.Component, component_name)
    result: NXOpen.CAE.Result
    result_parameters: NXOpen.CAE.ResultParameters
    result, result_parameters = the_session.Post.GetResultForPostview(postview_id) # type: ignore
    result_parameters.SetResultComponent(component)
    the_session.Post.PostviewSetResult(postview_id, result_parameters)
    the_session.Post.PostviewUpdate(postview_id)


def display_elements_in_group_via_postgroup(postview_id: int, group_name: str, sim_part: NXOpen.CAE.SimPart=None) -> None:
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
            the_lw.WriteFullline("A workaround is to create the same group in the sim file and use that in the journal.")
            # display_elements_in_group_via_postgroup(postview_id, group_name)
            raise ValueError("Group " + group_name + " not found in the sim file.")
        else:
            the_session.Post.PostviewApplyUserGroupVisibility(postview_id, usergroups_gids, NXOpen.CAE.Post.GroupVisibility.ShowOnly) # type: ignore


def display_elements_in_group_using_workaround(postview_id: int, group_name: str) -> None:
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
    
    # per for a try catch from a high number down, untill the PostviewApplyUserGroupVisibility does not throw an error
    # this is the last postgroup number.
    usergroup_ids = [None] * 1
    counter: int = len(all_groups) + 100 # cannot be longer than the actual number of groups, but 
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
    
    # technically set_camera should be able to be called on a BasePart
    if base_part is None:
        base_part: NXOpen.CAE.SimPart = cast(NXOpen.CAE.SimPart, the_session.Parts.BaseWork)
    cameras: NXOpen.Display.CameraCollection = base_part.Cameras
    camera: NXOpen.Display.Camera = [x for x in cameras if x.Name.lower() == camera_name.lower()][0]
    camera.ApplyToView(base_part.ModelingViews.WorkView)


def save_view_to_file(file_name: str) -> None:
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
    if sim_part is None:
        if not isinstance(the_session.Parts.BaseWork, NXOpen.CAE.SimPart):
            raise ValueError("map_group_to_postgroup needs to be called on a .sim file!")
        sim_part: NXOpen.CAE.SimPart = cast(NXOpen.CAE.SimPart, the_session.Parts.BaseWork)

    found_post_group: bool = False
    cae_groups: List[NXOpen.CAE.CaeGroup] = sim_part.CaeGroups
    post_groups: List[NXOpen.CAE.CaeGroup] = [x for x in cae_groups if x.Name.startswith("PostGroup")]

    for item in post_groups:
        # only delete the ones with a number at the end (so there is the least change of accidentily deleting an acutal user created group)
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
    the_lw.WriteFullline("                        https:#github.com/theScriptingEngineer/nxopentse                        ")
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
