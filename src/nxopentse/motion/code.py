import os
import math
from typing import List, Optional, cast

import NXOpen
import NXOpen.Features
import NXOpen.GeometricUtilities

the_session: NXOpen.Session = NXOpen.Session.GetSession()

def create_simfile(motion_file_full_path: str):
    """
    Creates a motion simulation file with a specified name.

    Parameters
    ----------
    motion_file_full_path : str
        the full path of the motion simulation file

    Returns
    -------


    NOTES
    -----
    """
     # ----------------------------------------------
    #   Menu: File->New...
    # ----------------------------------------------
    markId1 = the_session.SetUndoMark(NXOpen.Session.MarkVisibility.Visible, "Start")
    
    fileNew1 = the_session.Parts.FileNew()
    
    the_session.SetUndoMarkName(markId1, "New Dialog")
    
    markId2 = the_session.SetUndoMark(NXOpen.Session.MarkVisibility.Invisible, "New")
    
    the_session.DeleteUndoMark(markId2, None)
    
    markId3 = the_session.SetUndoMark(NXOpen.Session.MarkVisibility.Invisible, "New")
    
    fileNew1.TemplateFileName = "Simcenter 3D Motion"
    
    fileNew1.UseBlankTemplate = True
    
    fileNew1.ApplicationName = "MotionTemplate"
    
    fileNew1.Units = NXOpen.Part.Units.Millimeters
    
    fileNew1.RelationType = ""
    
    fileNew1.UsesMasterModel = "No"
    
    fileNew1.TemplateType = NXOpen.FileNewTemplateType.Item
    
    fileNew1.TemplatePresentationName = ""
    
    fileNew1.ItemType = ""
    
    fileNew1.Specialization = ""
    
    fileNew1.SetCanCreateAltrep(False)
    
    fileNew1.NewFileName = str(motion_file_full_path) #Make path and name of motion file an argument
    
    fileNew1.MasterFileName = ""
    
    fileNew1.MakeDisplayedPart = True
    
    fileNew1.DisplayPartOption = NXOpen.DisplayPartOption.AllowAdditional
    
    nXObject1 = fileNew1.Commit()
    
    workPart = the_session.Parts.Work
    displayPart = the_session.Parts.Display
    the_session.DeleteUndoMark(markId3, None)
    
    fileNew1.Destroy()
    
    workPart.ModelingViews.WorkView.Fit()
    
    the_session.ApplicationSwitchImmediate("UG_APP_MECHANISMS")
    
    globalSelectionBuilder1 = the_session.MotionSession.MotionMethods.GetGlobalSelectionBuilder(workPart)
    
    the_session.MotionSession.InitializeSimulation(workPart)
    
    baseTemplateManager1 = the_session.XYPlotManager.TemplateManager
    
    envValue1 = the_session.GetEnvironmentVariableValue("TEMPLATE_GENERATOR_ENABLE")
    
    # ----------------------------------------------
    #   Menu: File->Save
    # ----------------------------------------------
    partSaveStatus1 = workPart.Save(NXOpen.BasePart.SaveComponents.TrueValue, NXOpen.BasePart.CloseAfterSave.FalseValue)
    
    partSaveStatus1.Dispose()

    # return point_feature


