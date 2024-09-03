import os
import math
from typing import List, Optional, cast

import NXOpen
import NXOpen.Features
import NXOpen.GeometricUtilities
import NXOpen.Motion
from .custom_classes import MotionBodyProps


the_session: NXOpen.Session = NXOpen.Session.GetSession()

def create_motionbody(Motionbody: MotionBodyProps) : 
    
    ##basePart1, partLoadStatus1 = the_session.Parts.OpenActiveDisplay(sys.argv[1], NXOpen.DisplayPartOption.AllowAdditional)  #<------------------ Modified code
    workPart = the_session.Parts.Work
    ##displayPart = the_session.Parts.Display
    # ----------------------------------------------
    #   Menu: Insert->Motion Body...
    # ----------------------------------------------
    markId1 = the_session.SetUndoMark(NXOpen.Session.MarkVisibility.Visible, "Start")
    
    linkBuilder1 = workPart.MotionManager.Links.CreateLinkBuilder(NXOpen.Motion.Link.Null)
    
    linkBuilder1.MassProperty.MassType = NXOpen.Motion.LinkMassProperty.MassPropertyType.UserDefined
    
    linkBuilder1.MassProperty.MassExpression.SetFormula(str(Motionbody.mass))  #<------------------ Modified code
    
    linkBuilder1.MassProperty.IxxExpression.SetFormula(str(Motionbody.InertiaMoments[0]))  #<------------------ Modified code
    
    linkBuilder1.MassProperty.IyyExpression.SetFormula(str(Motionbody.InertiaMoments[1]))  #<------------------ Modified code
    
    linkBuilder1.MassProperty.IzzExpression.SetFormula(str(Motionbody.InertiaMoments[2]))  #<------------------ Modified code
    
    linkBuilder1.MassProperty.IxyExpression.SetFormula(str(Motionbody.InertiaProducts[0]))  #<------------------ Modified code
    
    linkBuilder1.MassProperty.IxzExpression.SetFormula(str(Motionbody.InertiaProducts[1]))  #<------------------ Modified code
    
    linkBuilder1.MassProperty.IyzExpression.SetFormula(str(Motionbody.InertiaProducts[2]))  #<------------------ Modified code
    
    try:
        # This expression cannot be modified because it is locked.
        linkBuilder1.MassProperty.AutoMassExpression.SetFormula("0")
    except NXOpen.NXException as ex:
        ex.AssertErrorCode(1050049)
        
    try:
        # This expression cannot be modified because it is locked.
        linkBuilder1.MassProperty.AutoIxxExpression.SetFormula("0")
    except NXOpen.NXException as ex:
        ex.AssertErrorCode(1050049)
        
    try:
        # This expression cannot be modified because it is locked.
        linkBuilder1.MassProperty.AutoIyyExpression.SetFormula("0")
    except NXOpen.NXException as ex:
        ex.AssertErrorCode(1050049)
        
    try:
        # This expression cannot be modified because it is locked.
        linkBuilder1.MassProperty.AutoIzzExpression.SetFormula("0")
    except NXOpen.NXException as ex:
        ex.AssertErrorCode(1050049)
        
    try:
        # This expression cannot be modified because it is locked.
        linkBuilder1.MassProperty.AutoIxyExpression.SetFormula("0")
    except NXOpen.NXException as ex:
        ex.AssertErrorCode(1050049)
        
    try:
        # This expression cannot be modified because it is locked.
        linkBuilder1.MassProperty.AutoIxzExpression.SetFormula("0")
    except NXOpen.NXException as ex:
        ex.AssertErrorCode(1050049)
        
    try:
        # This expression cannot be modified because it is locked.
        linkBuilder1.MassProperty.AutoIyzExpression.SetFormula("0")
    except NXOpen.NXException as ex:
        ex.AssertErrorCode(1050049)
        
    linkBuilder1.InitialVelocity.TranslateExpression.SetFormula("0")
    
    linkBuilder1.InitialVelocity.RotateExpression.SetFormula("0")
    
    linkBuilder1.InitialVelocity.WxExpression.SetFormula("0")
    
    linkBuilder1.InitialVelocity.WyExpression.SetFormula("0")
    
    linkBuilder1.InitialVelocity.WzExpression.SetFormula("0")
    
    the_session.SetUndoMarkName(markId1, "Motion Body Dialog")
    
    unit1 = workPart.UnitCollection.FindObject("MilliMeter")

    # UNNECESSARY NX JOURNAL CODE LINES DELETED (LOOK AT NXJOURNAL_CREATE_MOTIONBODY_V2 FOR THE ORIGINAL LINES)
    #the_session.LogFile.WriteLine(Motionbody.object)
    associativeLine1 = Motionbody.object #workPart.Features.FindObject("LINE(3)")
    
    #associativeLine1 = workPart.Features.FindObject(Motionbody.object)
    line1 = associativeLine1.FindObject("CURVE 1")
    added1 = linkBuilder1.Geometries.Add(line1)
    
    # UNNECESSARY NX JOURNAL CODE LINES DELETED (LOOK AT NXJOURNAL_CREATE_MOTIONBODY_V2 FOR THE ORIGINAL LINES)
    
    expression32 = workPart.Expressions.CreateSystemExpressionWithUnits(str(Motionbody.MassCenter[0]), unit1) #X coordinate of center of mass   #<------------------ Modified code
    
    scalar13 = workPart.Scalars.CreateScalarExpression(expression32, NXOpen.Scalar.DimensionalityType.NotSet, NXOpen.SmartObject.UpdateOption.AfterModeling)
    
    expression33 = workPart.Expressions.CreateSystemExpressionWithUnits(str(Motionbody.MassCenter[1]), unit1) #Y coordinate of center of mass   #<------------------ Modified code
    
    scalar14 = workPart.Scalars.CreateScalarExpression(expression33, NXOpen.Scalar.DimensionalityType.NotSet, NXOpen.SmartObject.UpdateOption.AfterModeling)
    
    expression34 = workPart.Expressions.CreateSystemExpressionWithUnits(str(Motionbody.MassCenter[2]), unit1) #Z coordinate of center of mass   #<------------------ Modified code
    
    scalar15 = workPart.Scalars.CreateScalarExpression(expression34, NXOpen.Scalar.DimensionalityType.NotSet, NXOpen.SmartObject.UpdateOption.AfterModeling)
    
    point5 = workPart.Points.CreatePoint(scalar13, scalar14, scalar15, NXOpen.SmartObject.UpdateOption.AfterModeling)
    
    # UNNECESSARY NX JOURNAL CODE LINES DELETED (LOOK AT NXJOURNAL_CREATE_MOTIONBODY_V2 FOR THE ORIGINAL LINES)
    
    linkBuilder1.MassProperty.MassCenter = point5
    
    # UNNECESSARY NX JOURNAL CODE LINES DELETED (LOOK AT NXJOURNAL_CREATE_MOTIONBODY_V2 FOR THE ORIGINAL LINES)
    
    origin1 = NXOpen.Point3d(float(Motionbody.InertiaCSYS_Origin[0]), float(Motionbody.InertiaCSYS_Origin[1]), float(Motionbody.InertiaCSYS_Origin[2]))         #Origin of coordinate system, float to convert string argv to double  #<------------------ Modified code
    xDirection1 = NXOpen.Vector3d(float(Motionbody.InertiaCSYS_Vector_X[0]), float(Motionbody.InertiaCSYS_Vector_X[1]), float(Motionbody.InertiaCSYS_Vector_X[2]))    #Vector coordinates of X axis, float to convert string argv to double #<------------------ Modified code
    yDirection1 = NXOpen.Vector3d(float(Motionbody.InertiaCSYS_Vector_Y[0]), float(Motionbody.InertiaCSYS_Vector_Y[1]), float(Motionbody.InertiaCSYS_Vector_Y[2]))    #Vector coordinates of Y axis, float to convert string argv to double #<------------------ Modified code
    xform1 = workPart.Xforms.CreateXform(origin1, xDirection1, yDirection1, NXOpen.SmartObject.UpdateOption.AfterModeling, 1.0)
    
    cartesianCoordinateSystem1 = workPart.CoordinateSystems.CreateCoordinateSystem(xform1, NXOpen.SmartObject.UpdateOption.AfterModeling)
    
    linkBuilder1.MassProperty.InertiaCsys = cartesianCoordinateSystem1
    
    globalSelectionBuilder5 = the_session.MotionSession.MotionMethods.GetGlobalSelectionBuilder(workPart)
    
    selectTaggedObjectList5 = globalSelectionBuilder5.Selection
    
    globalSelectionBuilder6 = the_session.MotionSession.MotionMethods.GetGlobalSelectionBuilder(workPart)
    
    selectTaggedObjectList6 = globalSelectionBuilder6.Selection
    
    globalSelectionBuilder7 = the_session.MotionSession.MotionMethods.GetGlobalSelectionBuilder(workPart)
    
    selectTaggedObjectList7 = globalSelectionBuilder7.Selection
    
    linkBuilder1.Name = Motionbody.name #<-------------------------------------------------------------------------- Modified code
    
    markId5 = the_session.SetUndoMark(NXOpen.Session.MarkVisibility.Invisible, "Motion Body")
    
    globalSelectionBuilder8 = the_session.MotionSession.MotionMethods.GetGlobalSelectionBuilder(workPart)
    
    selectTaggedObjectList8 = globalSelectionBuilder8.Selection
    
    globalSelectionBuilder9 = the_session.MotionSession.MotionMethods.GetGlobalSelectionBuilder(workPart)
    
    selectTaggedObjectList9 = globalSelectionBuilder9.Selection
    
    the_session.DeleteUndoMark(markId5, None)
    
    markId6 = the_session.SetUndoMark(NXOpen.Session.MarkVisibility.Invisible, "Motion Body")
    
    linkBuilder1.InitialVelocity.TranslateVector = NXOpen.Direction.Null
    
    linkBuilder1.InitialVelocity.RotateVector = NXOpen.Direction.Null
    
    nXObject1 = linkBuilder1.Commit()
    
    the_session.DeleteUndoMark(markId6, None)
    
    the_session.SetUndoMarkName(markId1, "Motion Body")
    
    linkBuilder1.Destroy()
    
    # UNNECESSARY NX JOURNAL CODE LINES DELETED (LOOK AT NXJOURNAL_CREATE_MOTIONBODY_V2 FOR THE ORIGINAL LINES)
    
    # ----------------------------------------------
    #   Menu: File->Save
    # ----------------------------------------------
    partSaveStatus1 = workPart.Save(NXOpen.BasePart.SaveComponents.TrueValue, NXOpen.BasePart.CloseAfterSave.FalseValue)
    
    partSaveStatus1.Dispose()
