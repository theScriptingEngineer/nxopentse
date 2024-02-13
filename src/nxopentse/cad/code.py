import os

import NXOpen


the_session: NXOpen.Session = NXOpen.Session.GetSession()
base_part: NXOpen.BasePart = the_session.Parts.BaseWork
the_lw: NXOpen.ListingWindow = the_session.ListingWindow


def hello():
    print("Hello from " + os.path.basename(__file__))


def nx_hello():
    the_lw.WriteFullline("Hello, World!")
    the_lw.WriteFullline("Hello from " + os.path.basename(__file__))


def create_point(base_part: NXOpen.BasePart, x_co: float, y_co: float, z_co: float, color: int = 134) -> NXOpen.Point:
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
        
    Returns
    -------
    NXOpen.Point3d
        The created point.
    """
    unit_mm: NXOpen.Unit = base_part.UnitCollection.FindObject("Millimeter")
    exp_x: NXOpen.Expression = base_part.Expressions.CreateSystemExpressionWithUnits(str(x_co), unit_mm)
    exp_y: NXOpen.Expression = base_part.Expressions.CreateSystemExpressionWithUnits(str(y_co), unit_mm)
    exp_z: NXOpen.Expression = base_part.Expressions.CreateSystemExpressionWithUnits(str(z_co), unit_mm)

    scalar_x: NXOpen.Scalar = base_part.Scalars.CreateScalarExpression(exp_x, NXOpen.Scalar.DimensionalityType.NotSet, NXOpen.SmartObject.UpdateOption.AfterModeling)
    scalar_y: NXOpen.Scalar = base_part.Scalars.CreateScalarExpression(exp_y, NXOpen.Scalar.DimensionalityType.NotSet, NXOpen.SmartObject.UpdateOption.AfterModeling)
    scalar_z: NXOpen.Scalar = base_part.Scalars.CreateScalarExpression(exp_z, NXOpen.Scalar.DimensionalityType.NotSet, NXOpen.SmartObject.UpdateOption.AfterModeling)

    point: NXOpen.Point = base_part.Points.CreatePoint(scalar_x, scalar_y, scalar_z, NXOpen.SmartObject.UpdateOption.AfterModeling)
    point.Color = color
    point.SetVisibility(NXOpen.SmartObject.VisibilityOption.Visible)
    undo_mark: NXOpen.Session.UndoToMark = the_session.SetUndoMark(NXOpen.Session.MarkVisibility.Visible, "Point")
    the_session.UpdateManager.DoUpdate(undo_mark)

    return point
