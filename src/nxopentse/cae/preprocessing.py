# should split this file up into a fem/afem and sim functionality file

import os
from typing import List, cast, Optional, Union, Dict

import NXOpen
import NXOpen.CAE
import NXOpen.UF
import NXOpen.Fields

from ..tools import create_string_attribute


the_session: NXOpen.Session = NXOpen.Session.GetSession()
the_uf_session: NXOpen.UF.UFSession = NXOpen.UF.UFSession.GetUFSession()
the_lw: NXOpen.ListingWindow = the_session.ListingWindow


def hello():
    print("Hello from " + os.path.basename(__file__))


def create_2dmesh_collector(thickness: float, color: int = None) -> Optional[NXOpen.CAE.MeshCollector]:
    """This function creates a 2d mesh collector with the given thickness and label.
       the color of the mesh collector is set as 10 times the label
    
    Parameters
    ----------
    thickness: float
        The thickness to set in the mesh collector
    physical_property_label: int
        The label of the physical property. Needs to be unique and thus cannot already be used in the part.


    Returns
    -------
    NXOpen.CAE.MeshCollector
        Returns the created 2d mesh collector.
    """

    # TODO: make this also work for .fem and .afem

    base_part: NXOpen.BasePart = the_session.Parts.BaseWork
    if not isinstance(NXOpen.CAE.FemPart, base_part):
        the_lw.WriteFullline("create_node needs to start from a .fem file. Exiting")
        return
    
    fem_part: NXOpen.CAE.FemPart = cast(NXOpen.CAE.FemPart, base_part)
    fe_model: NXOpen.CAE.FEModel = fem_part.BaseFEModel
    
    mesh_manager: NXOpen.CAE.MeshManager = cast(NXOpen.CAE.MeshManager, fe_model.MeshManager)
    null_mesh_collector: NXOpen.CAE.MeshCollector = None
    mesh_collector_builder: NXOpen.CAE.MeshCollectorBuilder = mesh_manager.CreateCollectorBuilder(null_mesh_collector, "ThinShell")

    # Get the highest label from the physical properties to then pass as parameter in the creation of a physical property.
    physicalPropertyTables: List[NXOpen.CAE.PhysicalPropertyTable] = [item for item in fem_part.PhysicalPropertyTables]
    max_label = 1
    if len(physicalPropertyTables) != 0:
        max_label = physicalPropertyTables[len(physicalPropertyTables) - 1].Label + 1

    physical_property_table: NXOpen.CAE.PhysicalPropertyTable = fem_part.PhysicalPropertyTables.CreatePhysicalPropertyTable("PSHELL", "NX NASTRAN - Structural", "NX NASTRAN", "PSHELL2", max_label)
    physical_property_table.SetName(str(thickness) + "mm")

    material_manager: NXOpen.CAE.MaterialManager = cast(NXOpen.CAE.MaterialManager, fem_part.MaterialManager) # cast only required because of intellisensse
    physical_materials: List[NXOpen.CAE.PhysicalMaterial] = material_manager.PhysicalMaterials.GetUsedMaterials()
    steel: List[NXOpen.CAE.PhysicalMaterial] = [item for item in physical_materials if item.Name == "Steel"]
    if steel == None:
        steel = material_manager.PhysicalMaterials.LoadFromNxlibrary("Steel")
    else:
        steel = steel[0]

    property_table: NXOpen.CAE.PropertyTable = physical_property_table.PropertyTable
    property_table.SetMaterialPropertyValue("material", False, steel)
    property_table.SetTablePropertyWithoutValue("bending material")
    property_table.SetTablePropertyWithoutValue("transverse shear material")
    property_table.SetTablePropertyWithoutValue("membrane-bending coupling material")

    unit_millimeter: NXOpen.Unit = cast(NXOpen.UnitCollection, fem_part.UnitCollection).FindObject("MilliMeter")
    property_table.SetBaseScalarWithDataPropertyValue("element thickness", str(thickness), unit_millimeter)

    mesh_collector_builder.CollectorName = str(thickness) + "mm"
    mesh_collector_builder.PropertyTable.SetNamedPropertyTablePropertyValue("Shell Property", physical_property_table)

    nx_object: NXOpen.NXObject = mesh_collector_builder.Commit()

    mesh_collector_builder.Destroy()

    # Setting the color of the MeshCollector we just created
    mesh_collector: NXOpen.CAE.MeshCollector = cast(NXOpen.CAE.MeshCollector, nx_object)
    mesh_collector_display_defaults = mesh_collector.GetMeshDisplayDefaults()

    # we set the color as label * 10 to make a distinction between the colors. The maximum color number is 216, therefore we take the modulus to not exceed this numer (eg. 15%4 -> 3)
    if color == None:
        mesh_collector_display_defaults.Color = NXOpen.NXColor.NXColor._Get((max_label * 10) % 216)
    else:
        mesh_collector_display_defaults.Color = NXOpen.NXColor.NXColor._Get(color)

    mesh_collector_display_defaults.Dispose()


def create_node(label: int, x_coordinate: float, y_coordinate: float, z_coordinate: float) -> Optional[NXOpen.CAE.FENode]:
    """This function creates a node with given label and coordinates.
       It is the user responsibility to make sure the label does not already exists in the model!
    
    Parameters
    ----------
    label: int
        The node label
    x_coordinate: float
        The global x-coordinate of the node to be created
    y_coordinate: float
        The global y-coordinate of the node to be created
    z_coordinate: float
        The global z-coordinate of the node to be created

    Returns
    -------
    NXOpen.CAE.FENode
        Returns the created node.
    """

    base_part: NXOpen.BasePart = the_session.Parts.BaseWork
    if not isinstance(NXOpen.CAE.BaseFemPart, base_part):
        the_lw.WriteFullline("create_node needs to start from a .fem or .afem file. Exiting")
        return
    
    base_fem_part: NXOpen.CAE.BaseFemPart = cast(NXOpen.CAE.BaseFemPart, base_part)
    base_fe_model: NXOpen.CAE.FEModel = base_fem_part.BaseFEModel
    node_create_builder: NXOpen.CAE.NodeCreateBuilder = base_fe_model.NodeElementMgr.CreateNodeCreateBuilder()

    node_create_builder.Label = label
    null_nxopen_coordinate_system: NXOpen.CoordinateSystem = None
    node_create_builder.Csys = null_nxopen_coordinate_system
    node_create_builder.SingleOption = True

    node_create_builder.X.Value = x_coordinate
    node_create_builder.Y.Value = y_coordinate
    node_create_builder.Z.Value = z_coordinate

    coordinates: NXOpen.Point3d = NXOpen.Point3d(x_coordinate, y_coordinate, z_coordinate)
    point: NXOpen.Point = base_fem_part.Points.CreatePoint(coordinates)
    node_create_builder.Point = point

    node: NXOpen.NXObject = node_create_builder.Commit()

    node_create_builder.Csys = null_nxopen_coordinate_system
    node_create_builder.DispCsys = null_nxopen_coordinate_system

    node_create_builder.Destroy()

    return cast(NXOpen.CAE.FENode, node)


def create_nodal_constraint(node_label: int, dx: float, dy : float, dz: float, rx: float, ry: float, rz: float, constraint_name: str) -> NXOpen.CAE.SimBC:
    """This function creates a constraint on a node. For free, set the value to -777777
        THis is minus 7, six times. Which equals 42 ;) You got to love the NX developers humor.
    
    Parameters
    ----------
    node_label: int
        The node label to appy the constraint to.
    dx: float
        the displacement in global x-direction.
    dy: float
        the displacement in global y-direction.
    dz: float
        the displacement in global z-direction.
    rx: float
        the rotation in global x-direction.
    ry: float
        the rotation in global y-direction.
    rz: float
        the rotation in global z-direction.
    constraint_name: str
        The name of the constraint for the GUI.

    Returns
    -------
    NXOpen.CAE.SimBC
        Returns the created constraint.

    Notes
    -----
    Tested in SC2212
    Tested in SC2312
    """
    # check if started from a SimPart, returning othwerwise
    base_part: NXOpen.BasePart = the_session.Parts.BaseWork
    if not isinstance(base_part, NXOpen.CAE.SimPart):
        the_lw.WriteFullline("CreateConstraint needs to start from a .sim file. Exiting")
        return
    # we are now sure that basePart is a SimPart
    sim_part: NXOpen.CAE.SimPart = cast(NXOpen.CAE.SimPart, base_part) # explicit casting makes it clear
    
    sim_simulation: NXOpen.CAE.SimSimulation = sim_part.Simulation
    # make the active solution inactive, so bondary condition is not automatically added to active subcase
    sim_simulation.ActiveSolution = NXOpen.CAE.SimSolution.Null

    # check if constaint already exists
    sim_constraints: List[NXOpen.CAE.SimConstraint] = [item for item in sim_simulation.Constraints]
    sim_constraint: List[NXOpen.CAE.SimConstraint] = [item for item in sim_constraints if item.Name.lower() == constraint_name.lower()]
    sim_bc_builder: NXOpen.CAE.SimBCBuilder
    if len(sim_constraint) == 0:
        # no constraint with the given name, thus creating the constrain
        sim_bc_builder = sim_simulation.CreateBcBuilderForConstraintDescriptor("UserDefinedDisplacementConstraint", constraint_name, 0)
    elif len(sim_constraint) == 1:
        the_lw.WriteFullline(f'A constraint with the name {constraint_name} already exists therefore editing the constraint.')
        sim_bc_builder = sim_simulation.CreateBcBuilderForBc(sim_constraint[0])
    else:
        the_lw.WriteFullline(f'Multiple constraints with the name {constraint_name} exist. This function requires unique names and is not case sensitive.')
        raise ValueError(f'Multiple constraints with the name {constraint_name} exist.')

    property_table: NXOpen.CAE.PropertyTable = sim_bc_builder.PropertyTable
    field_expression1: NXOpen.Fields.FieldExpression = property_table.GetScalarFieldPropertyValue("DOF1")
    field_expression2: NXOpen.Fields.FieldExpression = property_table.GetScalarFieldPropertyValue("DOF2")
    field_expression3: NXOpen.Fields.FieldExpression = property_table.GetScalarFieldPropertyValue("DOF3")
    field_expression4: NXOpen.Fields.FieldExpression = property_table.GetScalarFieldPropertyValue("DOF4")
    field_expression5: NXOpen.Fields.FieldExpression = property_table.GetScalarFieldPropertyValue("DOF5")
    field_expression6: NXOpen.Fields.FieldExpression = property_table.GetScalarFieldPropertyValue("DOF6")
    
    unit_millimeter: NXOpen.Unit = cast(NXOpen.Unit, sim_part.UnitCollection.FindObject("MilliMeter"))
    indep_var_array1: List[NXOpen.Fields.FieldVariable] = []
    field_expression1.EditFieldExpression(str(dx), unit_millimeter, indep_var_array1, False)
    property_table.SetScalarFieldPropertyValue("DOF1", field_expression1)

    indep_var_array2: List[NXOpen.Fields.FieldVariable] = []
    field_expression2.EditFieldExpression(str(dy), unit_millimeter, indep_var_array2, False)
    property_table.SetScalarFieldPropertyValue("DOF2", field_expression2)

    indep_var_array3: List[NXOpen.Fields.FieldVariable] = []
    field_expression3.EditFieldExpression(str(dz), unit_millimeter, indep_var_array3, False)
    property_table.SetScalarFieldPropertyValue("DOF3", field_expression3)

    unit_degrees: NXOpen.Unit = cast(NXOpen.Unit, sim_part.UnitCollection.FindObject("Degrees"))
    indep_var_array4: List[NXOpen.Fields.FieldVariable] = []
    field_expression4.EditFieldExpression(str(rx), unit_degrees, indep_var_array4, False)
    property_table.SetScalarFieldPropertyValue("DOF4", field_expression4)

    indep_var_array5: List[NXOpen.Fields.FieldVariable] = []
    field_expression5.EditFieldExpression(str(ry), unit_degrees, indep_var_array5, False)
    property_table.SetScalarFieldPropertyValue("DOF5", field_expression5)

    indep_var_array6: List[NXOpen.Fields.FieldVariable] = []
    field_expression6.EditFieldExpression(str(rz), unit_degrees, indep_var_array6, False)
    property_table.SetScalarFieldPropertyValue("DOF6", field_expression6)

    # select the node via the label to assign the constraint to
    set_manager: NXOpen.CAE.SetManager = sim_bc_builder.TargetSetManager
    
    objects: List[NXOpen.CAE.SetObject] = [NXOpen.CAE.SetObject.Obj] * 1
    objects[0] = NXOpen.CAE.SetObject()
    fe_model_ccurrence: NXOpen.CAE.FEModelOccurrence = sim_part.Simulation.Femodel
    fe_node: NXOpen.CAE.FENode = fe_model_ccurrence.FenodeLabelMap.GetNode(node_label)
    if fe_node is None:
        the_lw.WriteFullline("CreateConstraint: node with label " + str(node_label) + " not found in the model. Constaint not created.")
        return

    objects[0].Obj = fe_node
    objects[0].SubType = NXOpen.CAE.CaeSetObjectSubType.NotSet
    objects[0].SubId = 0
    set_manager.SetTargetSetMembers(0, NXOpen.CAE.CaeSetGroupFilterType.Node, objects)
    
    sim_bc: NXOpen.CAE.SimBC = sim_bc_builder.CommitAddBc()
    sim_bc_builder.Destroy()
    
    return sim_bc


def create_nodal_force_default_name(node_label: int, fx: float, fy : float, fz: float):
    """This function creates a force on a node using a default name.
    
    Parameters
    ----------
    node_label: int
        The node label to appy the force to.
    fx: float
        the force in global x-direction in Newton.
    fy: float
        the force in global y-direction in Newton.
    fz: float
        the force in global z-direction in Newton.

    Returns
    -------
    NXOpen.CAE.SimBC
        Returns the created force.

    Notes
    -----
    Tested in SC2312
    """
    defaultName: str = "Nodalforce_" + str(node_label)
    nodal_force: NXOpen.CAE.SimBC = create_nodal_force(node_label, fx, fy, fz, defaultName)
    return nodal_force


def create_nodal_force(node_label: int, fx: float, fy: float, fz: float, force_name: str) -> NXOpen.CAE.SimBC:
    """This function creates a force on a node.
    
    Parameters
    ----------
    node_label: int
        The node label to appy the force to.
    fx: float
        the force in global x-direction in Newton.
    fy: float
        the force in global y-direction in Newton.
    fz: float
        the force in global z-direction in Newton.
    force_name: str
        The name of the force for the GUI.

    Returns
    -------
    NXOpen.CAE.SimBC
        Returns the created force.

    Notes
    -----
    Tested in SC2312
    """
    base_part: NXOpen.BasePart = the_session.Parts.BaseWork
    # check if started from a SimPart, returning othwerwise
    if not isinstance(base_part, NXOpen.CAE.SimPart):
        the_lw.WriteFullline("CreateNodalForce needs to start from a .sim file. Exiting")
        return
    # we are now sure that basePart is a SimPart
    sim_part: NXOpen.CAE.SimPart = cast(NXOpen.CAE.SimPart, base_part) # explicit casting makes it clear
    
    sim_simulation: NXOpen.CAE.SimSimulation = sim_part.Simulation
    # make the active solution inactive, so load is not automatically added to active subcase
    sim_simulation.ActiveSolution = NXOpen.CAE.SimSolution.Null

    # check if a nodal force with that name already exists. If it does, update, if not create it
    sim_loads: List[NXOpen.CAE.SimLoad] = sim_part.Simulation.Loads
    sim_load: NXOpen.CAE.SimLoad = [item for item in sim_loads if item.Name.lower() == force_name.lower()]
    if len(sim_load) == 0:
        # load not found
        sim_bc_builder: NXOpen.CAE.SimBCBuilder = sim_simulation.CreateBcBuilderForLoadDescriptor("ComponentForceField", force_name, 0) # overloaded function is unknow to intellisense
    else:
        sim_bc_builder: NXOpen.CAE.SimBCBuilder = sim_simulation.CreateBcBuilderForBc(sim_load[0])
    
    # define the force
    property_table: NXOpen.CAE.PropertyTable = sim_bc_builder.PropertyTable
    set_manager: NXOpen.CAE.SetManager = sim_bc_builder.TargetSetManager
    
    objects: List[NXOpen.CAE.SetObject] = [NXOpen.CAE.SetObject.Obj] * 1
    objects[0] = NXOpen.CAE.SetObject()
    fe_node: NXOpen.CAE.FENode = sim_part.Simulation.Femodel.FenodeLabelMap.GetNode(node_label)
    if fe_node is None:
        the_lw.WriteFullline("CreateNodalForce: node with label " + str(node_label) + " not found in the model. Force not created.")
        return

    objects[0].Obj = fe_node
    objects[0].SubType = NXOpen.CAE.CaeSetObjectSubType.NotSet
    objects[0].SubId = 0
    set_manager.SetTargetSetMembers(0, NXOpen.CAE.CaeSetGroupFilterType.Node, objects)
    
    unit1: NXOpen.Unit = sim_part.UnitCollection.FindObject("Newton")
    expression1: NXOpen.Expression = sim_part.Expressions.CreateSystemExpressionWithUnits(str(fx), unit1)
    expression2: NXOpen.Expression = sim_part.Expressions.CreateSystemExpressionWithUnits(str(fy), unit1)
    expression3: NXOpen.Expression = sim_part.Expressions.CreateSystemExpressionWithUnits(str(fz), unit1)

    field_manager: NXOpen.Fields.FieldManager = cast(NXOpen.Fields.FieldManager, sim_part.FindObject("FieldManager"))
    # property_table.SetTablePropertyWithoutValue("CylindricalMagnitude")
    # property_table.SetVectorFieldWrapperPropertyValue("CylindricalMagnitude", NXOpen.Fields.VectorFieldWrapper.NotSet)
    # property_table.SetTablePropertyWithoutValue("SphericalMagnitude")
    # property_table.SetVectorFieldWrapperPropertyValue("SphericalMagnitude", NXOpen.Fields.VectorFieldWrapper.NotSet)
    # property_table.SetTablePropertyWithoutValue("DistributionField")
    # property_table.SetScalarFieldWrapperPropertyValue("DistributionField", NXOpen.Fields.ScalarFieldWrapper.NotSet)
    # property_table.SetTablePropertyWithoutValue("ComponentsDistributionField")
    # property_table.SetVectorFieldWrapperPropertyValue("ComponentsDistributionField", NXOpen.Fields.VectorFieldWrapper.NotSet)
    expressions: List[NXOpen.Expression] = [NXOpen.Expression.Null] * 3 
    expressions[0] = expression1
    expressions[1] = expression2
    expressions[2] = expression3
    vector_field_wrapper: NXOpen.Fields.VectorFieldWrapper = field_manager.CreateVectorFieldWrapperWithExpressions(expressions)
    
    property_table.SetVectorFieldWrapperPropertyValue("CartesianMagnitude", vector_field_wrapper)
    
    sim_bc: NXOpen.CAE.SimBC = sim_bc_builder.CommitAddBc()
    
    sim_bc_builder.Destroy()

    return sim_bc


def create_nodal_moment(node_label: int, mx: float, my: float, mz: float, moment_name: str) -> NXOpen.CAE.SimBC:
    """This function creates a force on a node.
    
    Parameters
    ----------
    node_label: int
        The node label to appy the force to.
    mx: float
        the moment in global x-direction in NewtonMillimeter.
    my: float
        the moment in global y-direction in NewtonMillimeter.
    mz: float
        the moment in global z-direction in NewtonMillimeter.
    force_name: str
        The name of the force for the GUI.

    Returns
    -------
    NXOpen.CAE.SimBC
        Returns the created force.
    """
    base_part: NXOpen.BasePart = the_session.Parts.BaseWork
    # check if started from a SimPart, returning othwerwise
    if not isinstance(base_part, NXOpen.CAE.SimPart):
        the_lw.WriteFullline("CreateNodalForce needs to start from a .sim file. Exiting")
        return
    # we are now sure that basePart is a SimPart
    sim_part: NXOpen.CAE.SimPart = cast(NXOpen.CAE.SimPart, base_part) # explicit casting makes it clear
    
    sim_simulation: NXOpen.CAE.SimSimulation = sim_part.Simulation
    # make the active solution inactive, so load is not automatically added to active subcase
    sim_simulation.ActiveSolution = NXOpen.CAE.SimSolution.Null

    # check if a nodal force with that name already exists. If it does, update, if not create it
    sim_loads: List[NXOpen.CAE.SimLoad] = sim_part.Simulation.Loads
    sim_load: NXOpen.CAE.SimLoad = [item for item in sim_loads if item.Name.lower() == moment_name.lower()]
    if len(sim_load) == 0:
        # load not found
        sim_bc_builder: NXOpen.CAE.SimBCBuilder = sim_simulation.CreateBcBuilderForLoadDescriptor("ComponentMomentField", moment_name, 0) # overloaded function is unknow to intellisense
    else:
        sim_bc_builder: NXOpen.CAE.SimBCBuilder = sim_simulation.CreateBcBuilderForBc(sim_load[0])
    
    # define the force
    property_table: NXOpen.CAE.PropertyTable = sim_bc_builder.PropertyTable
    set_manager: NXOpen.CAE.SetManager = sim_bc_builder.TargetSetManager
    
    objects: List[NXOpen.CAE.SetObject] = [NXOpen.CAE.SetObject.Obj] * 1
    objects[0] = NXOpen.CAE.SetObject()
    fe_node: NXOpen.CAE.FENode = sim_part.Simulation.Femodel.FenodeLabelMap.GetNode(node_label)
    if fe_node is None:
        the_lw.WriteFullline("CreateNodalMoment: node with label " + str(node_label) + " not found in the model. Moment not created.")
        return

    objects[0].Obj = fe_node
    objects[0].SubType = NXOpen.CAE.CaeSetObjectSubType.NotSet
    objects[0].SubId = 0
    set_manager.SetTargetSetMembers(0, NXOpen.CAE.CaeSetGroupFilterType.Node, objects)
    
    unit1: NXOpen.Unit = sim_part.UnitCollection.FindObject("NewtonMilliMeter")
    expression1: NXOpen.Expression = sim_part.Expressions.CreateSystemExpressionWithUnits(str(mx), unit1)
    expression2: NXOpen.Expression = sim_part.Expressions.CreateSystemExpressionWithUnits(str(my), unit1)
    expression3: NXOpen.Expression = sim_part.Expressions.CreateSystemExpressionWithUnits(str(mz), unit1)

    field_manager: NXOpen.Fields.FieldManager = cast(NXOpen.Fields.FieldManager, sim_part.FindObject("FieldManager"))
    expressions: List[NXOpen.Expression] = [NXOpen.Expression.Null] * 3 
    expressions[0] = expression1
    expressions[1] = expression2
    expressions[2] = expression3
    vector_field_wrapper: NXOpen.Fields.VectorFieldWrapper = field_manager.CreateVectorFieldWrapperWithExpressions(expressions)
    
    property_table.SetVectorFieldWrapperPropertyValue("CartesianMagnitude", vector_field_wrapper)
    
    sim_bc: NXOpen.CAE.SimBC = sim_bc_builder.CommitAddBc()
    
    sim_bc_builder.Destroy()

    return sim_bc


def add_solver_set_to_subcase(solution_name: str, subcase_name: str, solver_set_name: str) -> None:
    """This function adds a given SolverSet to a given solution and subcase.

    Parameters
    ----------
    solution_name: str
        The name of the solution containing the subcase.
    subcase_name: str
        The name of the subcase to add the solver set to.
    solver_set_name: str
        The name of the solver set to add.

    Notes
    -----
    Tested in SC2312
    """
    # check if started from a SimPart, returning othwerwise
    base_part: NXOpen.BasePart = the_session.Parts.BaseWork
    if not isinstance(base_part, NXOpen.CAE.SimPart):
        the_lw.WriteFullline("AddSolverSetToSubcase needs to start from a .sim file. Exiting")
        return
    # we are now sure that basePart is a SimPart
    sim_part: NXOpen.CAE.SimPart = cast(NXOpen.CAE.SimPart, base_part) # explicit casting makes it clear
    sim_simulation: NXOpen.CAE.SimSimulation = sim_part.Simulation

    # get the requested solution if it exists
    sim_solution: NXOpen.CAE.SimSolution = get_solution(solution_name)
    if sim_solution == None:
        # Solution not found
        the_lw.WriteFullline("AddSolverSetToSubcase: Solution with name " + solution_name + " not found!")
        return
    
    # check if the subcase exists in the given solution
    sim_solution_step: Optional[NXOpen.CAE.SimSolutionStep] = None
    for i in range(sim_solution.StepCount):
        if sim_solution.GetStepByIndex(i).Name.lower() == subcase_name.lower():
            # subcase exists
            sim_solution_step = sim_solution.GetStepByIndex(i)
    
    if sim_solution_step == None:
        the_lw.WriteFullline("AddSolverSetToSubcase: subcase with name " + subcase_name + " not found in solution " + solution_name + "!")
        return

    # check if SolverSet exists
    sim_load_set: List[NXOpen.CAE.SimLoadSet] = [item for item in sim_simulation.LoadSets if item.Name.lower() == solver_set_name.lower()]
    if len(sim_load_set) == 0:
        # SolverSet not found
        the_lw.WriteFullline("AddSolverSetToSubcase: solver set with name " + solver_set_name + " not found!")
        return

    simLoad_group: NXOpen.CAE.SimLoadGroup = cast(NXOpen.CAE.SimLoadGroup, sim_solution_step.Find("Loads"))
    # commented code only for reference
    # simBcGroups: List[NXOpen.CAE.SimBcGroup] = simSolutionStep.GetGroups()
    # simLoadGroup: NXOpen.CAE.SimLoadGroup = cast(NXOpen.CAE.SimLoadGroup, simBcGroups[0])
    simLoad_group.AddLoadSet(sim_load_set[0])


def add_load_to_solver_set(solver_set_name: str, load_name: str) -> None:
    """This function adds a load with a given name to a SolverSet with a given name.

    Parameters
    ----------
    solver_set_name: str
        The name of the solver set to add the load to.
    load_name: str
        The name of the load to add to the solver set.

    Notes
    -----
    Tested in SC2312
    """
    # check if started from a SimPart, returning othwerwise
    base_part: NXOpen.BasePart = the_session.Parts.BaseWork
    if not isinstance(base_part, NXOpen.CAE.SimPart):
        the_lw.WriteFullline("AddLoadToSolverSet needs to start from a .sim file. Exiting")
        return
    # we are now sure that basePart is a SimPart
    sim_part: NXOpen.CAE.SimPart = cast(NXOpen.CAE.SimPart, base_part) # explicit casting makes it clear
    sim_simulation: NXOpen.CAE.SimSimulation = sim_part.Simulation

    # check if SolverSet exists
    sim_load_set: List[NXOpen.CAE.SimLoadSet] = [item for item in sim_simulation.LoadSets if item.Name.lower() == solver_set_name.lower()]
    if len(sim_load_set) == 0:
        # SolverSet not found
        the_lw.WriteFullline("AddLoadToSolverSet: solver set with name " + solver_set_name + " not found!")
        return None

    # get the requested load if it exists
    sim_load: List[NXOpen.CAE.SimLoad] = [item for item in sim_simulation.Loads if item.Name.lower() == load_name.lower()]
    if len(sim_load) == 0:
        # Load not found
        the_lw.WriteFullline("AddLoadToSolverSet: Load with name " + load_name + " not found!")
        return

    # add the found load to the found solverSet
    load_set_members: List[NXOpen.CAE.SimLoad] = [NXOpen.CAE.SimLoad] * 1
    load_set_members[0] = sim_load[0]
    sim_load_set[0].AddMemberLoads(load_set_members)


def create_solver_set(solver_set_name: str) -> Optional[NXOpen.CAE.SimLoadSet]:
    """This function creates a SolverSet with the given name.
    Does not create if one with the given name already exists.
    
    Parameters
    ----------
    solver_set_name: str
        The name of the solver set to create
    
    Returns
    -------
    NXOpen.CAE.SimLoadSet or None
        Returns the created solver set if created. None otherwise

    Notes
    -----
    Tested in SC2312
    """
    # check if started from a SimPart, returning othwerwise
    base_part: NXOpen.BasePart = the_session.Parts.BaseWork
    if not isinstance(base_part, NXOpen.CAE.SimPart):
        the_lw.WriteFullline("CreateSolverSet needs to start from a .sim file. Exiting")
        return
    # we are now sure that basePart is a SimPart
    sim_part: NXOpen.CAE.SimPart = cast(NXOpen.CAE.SimPart, base_part) # explicit casting makes it clear
    sim_simulation: NXOpen.CAE.SimSimulation = sim_part.Simulation

    # check if solverSet already exists
    sim_load_sets: List[NXOpen.CAE.SimLoadSet] = [item for item in sim_simulation.LoadSets if item.Name.lower() == solver_set_name.lower()]
    if len(sim_load_sets) != 0:
        # SolverSet already exists
        the_lw.WriteFullline("CreateSolverSet: solver set with name " + solver_set_name + " already exists!")
        return

    null_sim_load_set: Optional[NXOpen.CAE.SimLoadSet] = None
    sim_load_set_builder: NXOpen.CAE.SimLoadSetBuilder = sim_simulation.CreateLoadSetBuilder("StaticLoadSetAppliedLoad", solver_set_name, null_sim_load_set, 0)
    sim_load_set: NXOpen.CAE.SimLoadSet = cast(NXOpen.CAE.SimLoadSet, sim_load_set_builder.Commit())
    
    sim_load_set_builder.Destroy()
    
    return sim_load_set


def add_load_to_subcase(solution_name: str, subcase_name: str, load_name: str) -> None:
    """This function adds a given load to a given solution and subcase.
    
    Parameters
    ----------
    solution_name: str
        The name of the solution containing the subcase.
    subcase_name: str
        The name of the subcase to add the load to.
    load_name: str
        The name of the load to add
    """
    # check if started from a SimPart, returning othwerwise
    base_part: NXOpen.BasePart = the_session.Parts.BaseWork
    if not isinstance(base_part, NXOpen.CAE.SimPart):
        the_lw.WriteFullline("add_load_to_subcase needs to start from a .sim file. Exiting")
        return
    # we are now sure that basePart is a SimPart
    sim_part: NXOpen.CAE.SimPart = cast(NXOpen.CAE.SimPart, base_part) # explicit casting makes it clear
    sim_simulation: NXOpen.CAE.SimSimulation = sim_part.Simulation

    # get the requested solution if it exists
    sim_solution: NXOpen.CAE.SimSolution = get_solution(solution_name)
    if sim_solution == None:
        # Solution not found
        the_lw.WriteFullline("add_load_to_subcase: Solution with name " + solution_name + " not found!")
        return
    
    # check if the subcase exists in the given solution
    sim_solution_step: Optional[NXOpen.CAE.SimSolutionStep] = None
    for i in range(sim_solution.StepCount):
        if sim_solution.GetStepByIndex(i).Name.lower() == subcase_name.lower():
            # subcase exists
            sim_solution_step = sim_solution.GetStepByIndex(i)
    
    if sim_solution_step == None:
        the_lw.WriteFullline("add_load_to_subcase: subcase with name " + subcase_name + " not found in solution " + solution_name + "!")
        return

    # get the requested load if it exists
    sim_load: List[NXOpen.CAE.SimLoad] = [item for item in sim_simulation.Loads if item.Name.lower() == load_name.lower()]
    if len(sim_load) == 0:
        # Load not found
        the_lw.WriteFullline("add_load_to_subcase: Load with name " + load_name + " not found!")
        return
    
    sim_solution_step.AddBc(sim_load[0])


def add_constraint_to_solution(solution_name: str, constraint_name: str) -> None:
    """This function adds a constraint with the given name to the solution with the given name.
    
    Parameters
    ----------
    solution_name: str
        The name of the solution to add the constraint to
    constraint_name: str
        The name of the constraint to add

    Notes
    -----
    Tested in SC2212
    Tested in SC2312
    """
    # check if started from a SimPart, returning othwerwise
    base_part: NXOpen.BasePart = the_session.Parts.BaseWork
    if not isinstance(base_part, NXOpen.CAE.SimPart):
        the_lw.WriteFullline("AddConstraintToSolution needs to start from a .sim file. Exiting")
        return
    # we are now sure that basePart is a SimPart
    sim_sart: NXOpen.CAE.SimPart = cast(NXOpen.CAE.SimPart, base_part) # explicit casting makes it clear
    sim_simulation: NXOpen.CAE.SimSimulation = sim_sart.Simulation

    # get the requested solution if it exists
    sim_solution: NXOpen.CAE.SimSolution = get_solution(solution_name)
    if sim_solution == None:
        # Solution with the given name not found
        the_lw.WriteFullline("AddConstraintToSolution: Solution with name " + solution_name + " not found!")
        return

    # get the requested Constraint if it exists
    sim_constraints: List[NXOpen.CAE.SimConstraint] = [item for item in sim_simulation.Constraints]
    sim_constraint: List[NXOpen.CAE.SimConstraint] = [item for item in sim_constraints if item.Name.lower() == constraint_name.lower()]
    if len(sim_constraint) == 0:
        # Constraint with the given name not found
        the_lw.WriteFullline("AddConstraintToSolution: constraint with name " + constraint_name + " not found!")
        return

    # add constraint to solution
    sim_solution.AddBc(sim_constraint[0])


def add_constraint_to_subcase(solution_name: str, subcase_name, constraint_name: str) -> None:
    """This function adds a constraint with the given name to subcase witht he given name within the solution with the given name.
    
    Parameters
    ----------
    solution_name: str
        The name of the solution to add the constraint to
    subcase_name: str
        The name of the subcase within the solution to add the constraint to
    constraint_name: str
        The name of the constraint to add

    Notes
    -----
    Tested in SC2212
    """
    # check if started from a SimPart, returning othwerwise
    base_part: NXOpen.BasePart = the_session.Parts.BaseWork
    if not isinstance(base_part, NXOpen.CAE.SimPart):
        the_lw.WriteFullline(add_constraint_to_subcase.__name__ + " needs to start from a .sim file. Exiting")
        return
    # we are now sure that basePart is a SimPart
    sim_sart: NXOpen.CAE.SimPart = cast(NXOpen.CAE.SimPart, base_part) # explicit casting makes it clear
    sim_simulation: NXOpen.CAE.SimSimulation = sim_sart.Simulation

    # get the requested solution if it exists
    sim_solution: NXOpen.CAE.SimSolution = get_solution(solution_name)
    if sim_solution == None:
        # Solution with the given name not found
        the_lw.WriteFullline(add_constraint_to_subcase.__name__ + ": Solution with name " + solution_name + " not found!")
        return

    # check if the subcase exists in the given solution
    sim_solution_step: Optional[NXOpen.CAE.SimSolutionStep] = None
    for i in range(sim_solution.StepCount):
        if sim_solution.GetStepByIndex(i).Name.lower() == subcase_name.lower():
            # subcase exists
            sim_solution_step = sim_solution.GetStepByIndex(i)
    
    if sim_solution_step == None:
        the_lw.WriteFullline(add_constraint_to_subcase.__name__ + ": subcase with name " + subcase_name + " not found in solution " + solution_name + "!")
        return

    # get the requested Constraint if it exists
    sim_constraints: List[NXOpen.CAE.SimConstraint] = [item for item in sim_simulation.Constraints]
    sim_constraint: List[NXOpen.CAE.SimConstraint] = [item for item in sim_constraints if item.Name.lower() == constraint_name.lower()]
    if len(sim_constraint) == 0:
        # Constraint with the given name not found
        the_lw.WriteFullline(add_constraint_to_subcase.__name__ + ": constraint with name " + constraint_name + " not found!")
        return

    # add constraint to solution
    try:
        # don't know how to check for constraintgroup, so just try to create it
        sim_solution_step.CreateConstraintGroup()
    except:
        pass
    sim_solution_step.AddBc(sim_constraint[0])


def create_subcase(solution_name: str, subcase_name: str) -> Optional[NXOpen.CAE.SimSolutionStep]:
    """This function creates a subcase with a given name under the given solution.
    Does not create if already exists.
    
    Parameters
    ----------
    solution_name: str
        The name of the solution to create the subcase under
    subcase_name: str
        The name of the subcase to create
    
    Returns
    -------
    NXOpen.CAE.SimSolutionStep or None
        Returns the created subcase if created. None otherwise

    Notes
    -----
    Tested in SC2212

    """
    # check if started from a SimPart, returning othwerwise
    base_part: NXOpen.BasePart = the_session.Parts.BaseWork
    if not isinstance(base_part, NXOpen.CAE.SimPart):
        the_lw.WriteFullline("CreateSubcase needs to start from a .sim file. Exiting")
        return

    # get the requested solution if it exists
    sim_solution: NXOpen.CAE.SimSolution = get_solution(solution_name)
    if sim_solution == None:
        # Solution not found
        the_lw.WriteFullline("CreateSubcase: Solution with name " + solution_name + " not found!")
        return
    
    # check if the subcase already exists in the given solution
    for i in range(sim_solution.StepCount):
        if sim_solution.GetStepByIndex(i).Name.lower() == subcase_name.lower():
            # subcase already exists
            the_lw.WriteFullline("CreateSubcase: subcase with name " + subcase_name + " already exists in solution " + solution_name + "!")
            the_lw.WriteFullline("Proceeding with the existing one.")
            return sim_solution.GetStepByIndex(i)
    
    # create the subcase with the given name but don't activate it
    return sim_solution.CreateStep(0, False, subcase_name)


def create_solution(solution_name: str, output_requests: str = "Structural Output Requests1", bulk_data_echo_request: str = "Bulk Data Echo Request1") -> Optional[NXOpen.CAE.SimSolution]:
    """This function creates a solution with the given name, updated an existing if one already exists with that name.
    An optional output requests and bulk data echo request can be provided as parameters.
    If not provided or the provided is not found the defaults are applied.
    
    Parameters
    ----------
    solution_name: str
        The name of the solution to create
    optional output_requests: str
        The name of the structural ouput request to set for the solution
    optional bulk_data_echo_request: str
        The name of the bulk data echo request to set for the solution

    Returns
    -------
    NXOpen.CAE.SimSolution or None
        Returns the created subcase if created. The existing one with this name and updated if it exists
    
    Notes
    -----
    Tested with only solution name in SC2212.
    Tested in SC2312 with all parameters.

    """
    # check if started from a SimPart, returning othwerwise
    base_part: NXOpen.BasePart = the_session.Parts.BaseWork
    if not isinstance(base_part, NXOpen.CAE.SimPart):
        the_lw.WriteFullline("CreateSolution needs to start from a .sim file. Exiting")
        return
    # we are now sure that basePart is a SimPart
    sim_part: NXOpen.CAE.SimPart = cast(NXOpen.CAE.SimPart, base_part) # explicit casting makes it clear
    sim_simulation: NXOpen.CAE.SimSimulation = sim_part.Simulation

    sim_solution: NXOpen.CAE.SimSolution = get_solution(solution_name)
    if sim_solution == None:
        # create the solution
        the_lw.WriteFullline("Creating solution " + solution_name)
        sim_solution = sim_simulation.CreateSolution("NX NASTRAN", "Structural", "SESTATIC 101 - Single Constraint", solution_name, NXOpen.CAE.SimSimulation.AxisymAbstractionType.NotSet)


    property_table: NXOpen.CAE.PropertyTable = sim_solution.PropertyTable

    # Look for a ModelingObjectPropertyTable with the given name or the default name "Bulk Data Echo Request1"
    bulk_data_property_table: List[NXOpen.CAE.ModelingObjectPropertyTable] = [item for item in sim_part.ModelingObjectPropertyTables if item.Name.lower() == bulk_data_echo_request.lower()]
    if len(bulk_data_property_table) == 0:
        # did not find ModelinObjectPropertyTable with name "Bulk Data Echo REquest1"
        the_lw.WriteFullline("Warning: could not find Bulk Data Echo Request with name " + bulk_data_echo_request + ". Applying default one.")
        # check if default exists
        bulk_data_property_table: List[NXOpen.CAE.ModelingObjectPropertyTable] = [item for item in sim_part.ModelingObjectPropertyTables if item.Name.lower() == "Bulk Data Echo Request1".lower()]
        if len(bulk_data_property_table) == 0:
            # default does also not exist. Create it and put it in a list such that when setting it, we can use the index
            bulk_data_property_table = [sim_part.ModelingObjectPropertyTables.CreateModelingObjectPropertyTable("Bulk Data Echo Request", "NX NASTRAN - Structural", "NX NASTRAN", "Bulk Data Echo Request1", 1000)]

    property_table.SetNamedPropertyTablePropertyValue("Bulk Data Echo Request", bulk_data_property_table[0])

    # Look for a ModelingObjectPropertyTable with the given name or the default name "Structural Output Requests1"
    output_requests_property_table: List[NXOpen.CAE.ModelingObjectPropertyTable] = [item for item in sim_part.ModelingObjectPropertyTables if item.Name.lower() == output_requests.lower()]
    if len(output_requests_property_table) == 0:
        # did not find ModelinObjectPropertyTable with name "Bulk Data Echo REquest1"
        the_lw.WriteFullline("Warning: could not find Output Requests with name " + output_requests + ". Applying default one.")
        # check if default exists
        output_requests_property_table = [item for item in sim_part.ModelingObjectPropertyTables if item.Name.lower() == "Structural Output Requests1".lower()]
        if len(output_requests_property_table) == 0:
            # default does also not exist. Create it and put it in a list such that when setting it, we can use the index
            output_requests_property_table = [sim_part.ModelingObjectPropertyTables.CreateModelingObjectPropertyTable("Structural Output Requests", "NX NASTRAN - Structural", "NX NASTRAN", "Structural Output Requests1", 1001)]
            # set Von Mises stress location to corner
            output_requests_property_table[0].PropertyTable.SetIntegerPropertyValue("Stress - Location", 1)


    property_table.SetNamedPropertyTablePropertyValue("Output Requests", output_requests_property_table[0])

    return sim_solution


def get_solution(solution_name: str) -> Union[NXOpen.CAE.SimSolution, None]:
    """This function returns the SimSolution object with the given name.
    Returns None if not found, so the user can check and act accordingly

    Parameters
    ----------
    solutionName: int
        The name of the solution to return, case insensitive
    
    Returns
    -------
    NXOpen.CAE.SimSolution or None
        The FIRST solution object with the given name if found, None otherwise
    """
    # check if started from a SimPart, returning othwerwise
    base_part: NXOpen.BasePart = the_session.Parts.BaseWork
    if not isinstance(base_part, NXOpen.CAE.SimPart):
        the_lw.WriteFullline("get_solution needs to start from a .sim file. Exiting")
        return

    sim_part: NXOpen.CAE.SimPart = cast(NXOpen.CAE.SimPart, base_part) # explicit casting makes it clear
    sim_simulation = sim_part.Simulation
    sim_solutions: List[NXOpen.CAE.SimSolution] = [item for item in sim_simulation.Solutions] # no .ToArray() in python

    sim_solution: List[NXOpen.CAE.SimSolution] = [item for item in sim_solutions if item.Name.lower() == solution_name.lower()]
    if len(sim_solution) == 0:
        # solution with the given name not found
        return None
    
    # return the first simSolution with the requested name
    return sim_solution[0]


def set_solution_property(solution_name: str, property_name: str, property_value: Union[str, int]):
    """
    Set a property value for a solution.

    Parameters
    ----------
    solution_name : str
        The name of the solution to set the property for.

    property_name : str
        The name of the property to set.

    property_value : Union[str, int]
        The value to set for the property. It can be either a string or an integer.

    Raises
    ------
    TypeError
        If `property_value` is not a string or an integer.
    
    Examples
    --------
    set_solution_property("MySolution", "sdirectory", "C:\\NXSolveScratch\\")
    set_solution_property("MySolution", "parallel", 8)
    set_solution_property("MySolution", "solver command window", 1)

    Notes
    -----
    Tested in SC2212

    """
    solution = get_solution(solution_name)
    solver_options_property_table: NXOpen.CAE.PropertyTable = solution.SolverOptionsPropertyTable
    if type(property_value) is str:
        solver_options_property_table.SetStringPropertyValue(property_name, property_value)
    if type(property_value) is int:
        solver_options_property_table.SetIntegerPropertyValue(property_name, property_value)


def get_nodes_in_group(group_name: str) -> Dict[int, NXOpen.CAE.FENode]:
    """
    Retrieves nodes belonging to a specified group.

    Parameters
    ----------
    group_name : str
       The name of the group whose nodes are to be retrieved (not case sensitive)

    Returns
    -------
    Dict[int, NXOpen.CAE.FENode]
        An ordered dictionary mapping node labels to FENode objects.   

    Raises
    ------
        ValueError: If the group with the specified name is not found or if multiple occurrences are found.

    Notes
    -----
    Tested in SC2212

    """
    work_cae_part: NXOpen.CAE.CaePart = cast(NXOpen.CAE.CaePart, the_session.Parts.BaseWork)
    groups: List[NXOpen.CAE.CaeGroup] = [item for item in work_cae_part.CaeGroups]
    group: List[NXOpen.CAE.CaeGroup] = [item for item in groups if item.Name.strip().lower() == group_name.strip().lower()]
    if len(group) == 0:
        the_lw.WriteFullline(f'Group with name {group_name} not found.')
        raise ValueError(f'Group with name {group_name} not found.')
    elif len(group) != 1:
        the_lw.WriteFullline(f'Multiple occurences of {group_name} found. Note that the names are case insensitive.')
        raise ValueError(f'Multiple occurences of {group_name} found. Note that the names are case insensitive.')
    
    nodes_in_group: Dict[int, NXOpen.CAE.FENode] = {}
    for object in group[0].GetEntities():
        if type(object) == NXOpen.CAE.FENode:
            node = cast(NXOpen.CAE.FENode, object)
            nodes_in_group[node.Label] = node
    
    
    return dict(sorted(nodes_in_group.items()))


def create_displacement_field(field_name: str, file_name: str) -> NXOpen.Fields.FieldTable:
    """
    Creates a displacement field which can be used in an enforced displacement constraint.
    When creating a break-out model or submodel 

    Parameters
    ----------
    field_name : str
       The name to give to the field

    file_name : str
       Full path of the file with the nodal coordinates and displacement values
       
    Returns
    -------
    NXOpen.Fields.FieldTable
        The field just created

    Notes
    -----
    The file with coordinates and displacements can be generated with write_submodel_data_to_file
    Tested in SC2212

    """
    work_sim_part: NXOpen.CAE.SimPart = cast(NXOpen.CAE.SimPart, the_session.Parts.BaseWork)
    field_manager = work_sim_part.FieldManager
    spation_map_builder = field_manager.CreateSpatialMapBuilder(NXOpen.Fields.SpatialMap.Null)

    unit = spation_map_builder.FaceTolerance.Units
    name_variable_1 = field_manager.GetNameVariable("length_1", "Length")
    field_variable_1 = field_manager.CreateDependentVariable(NXOpen.Fields.Field.Null, name_variable_1, unit, NXOpen.Fields.FieldVariable.ValueType.Real)
    name_variable_2 = field_manager.GetNameVariable("length_2", "Length")
    field_variable_2 = field_manager.CreateDependentVariable(NXOpen.Fields.Field.Null, name_variable_2, unit, NXOpen.Fields.FieldVariable.ValueType.Real)
    name_variable_3 = field_manager.GetNameVariable("length_3", "Length")
    field_variable_3 = field_manager.CreateDependentVariable(NXOpen.Fields.Field.Null, name_variable_3, unit, NXOpen.Fields.FieldVariable.ValueType.Real)

    name_variable_4 = field_manager.GetNameVariable("x", "Length")
    field_variable_4 = field_manager.CreateIndependentVariable(NXOpen.Fields.Field.Null, name_variable_4, unit, NXOpen.Fields.FieldVariable.ValueType.Real, False, True, 1e+19, False, True, 9.9999999999999998e-20, False, 2, False, 1.0)
    
    name_variable_5 = field_manager.GetNameVariable("y", "Length")
    field_variable_5 = field_manager.CreateIndependentVariable(NXOpen.Fields.Field.Null, name_variable_5, unit, NXOpen.Fields.FieldVariable.ValueType.Real, False, True, 1e+19, False, True, 9.9999999999999998e-20, False, 2, False, 1.0)
    
    name_variable_6 = field_manager.GetNameVariable("z", "Length")
    field_variable_6 = field_manager.CreateIndependentVariable(NXOpen.Fields.Field.Null, name_variable_6, unit, NXOpen.Fields.FieldVariable.ValueType.Real, False, True, 1e+19, False, True, 9.9999999999999998e-20, False, 2, False, 1.0)

    spatial_map_builder = field_manager.CreateSpatialMapBuilder(NXOpen.Fields.SpatialMap.Null)
    spatial_map_builder.MapType = NXOpen.Fields.SpatialMap.TypeEnum.Global
    spatial_map: NXOpen.Fields.SpatialMap = spatial_map_builder.Commit()

    depVarArray2 = [NXOpen.Fields.FieldVariable.Null] * 3
    depVarArray2[0] = field_variable_1
    depVarArray2[1] = field_variable_2
    depVarArray2[2] = field_variable_3

    indepVarArray2 = [NXOpen.Fields.FieldVariable.Null] * 3 
    indepVarArray2[0] = field_variable_4
    indepVarArray2[1] = field_variable_5
    indepVarArray2[2] = field_variable_6

    import_table_data_builder = field_manager.CreateImportTableDataBuilder(field_name, indepVarArray2, depVarArray2)
    import_table_data_builder.ImportFile = file_name
    field_table: NXOpen.Fields.FieldTable = import_table_data_builder.Commit()
    field_table.ParameterizeIndependentDomain = False
    field_table.DelayedUpdate = False
    field_table.CreateInterpolatorOnCommit = True
    field_table.InterpolationMethod = NXOpen.Fields.FieldEvaluator.InterpolationEnum.Delaunay3dAccurate
    field_table.ValuesOutsideTableInterpolation = NXOpen.Fields.FieldEvaluator.ValuesOutsideTableInterpolationEnum.Constant
    field_table.CreateInterpolator()
    field_table.SetSpatialMap(spatial_map)
    
    import_table_data_builder.Destroy()

    return field_table


def create_linear_acceleration(gx: float, gy: float, gz: float, force_name: str, sim_part: NXOpen.CAE.SimPart=None) -> Optional[NXOpen.CAE.SimBC]:
    """
    Create or edit a linear acceleration load in a SimPart.

    Parameters
    ----------
    gx : float
        The acceleration in the x-direction in mm/s^2.
    gy : float
        The acceleration in the y-direction in mm/s^2.
    gz : float
        The acceleration in the z-direction in mm/s^2.
    forceName : str
        The name of the load to create or edit.

    Returns
    -------
    NXOpen.CAE.SimBC
        The created or edited SimBC object.

    Notes
    -----
    Use create_linear_acceleration(0, 0, -9810, "Gravity") to create a gravity load
    Tested in SC2212

    """
    if sim_part is None:
        sim_part = cast(NXOpen.CAE.SimPart, the_session.Parts.BaseWork)

    sim_simulation = sim_part.Simulation

    # set solution to inactive so load is not automatically added upon creation
    sim_part.Simulation.ActiveSolution = None

    # Check if load already exists
    sim_loads: List[NXOpen.CAE.SimLoad] = [item for item in sim_part.Simulation.Loads]
    sim_load: List[NXOpen.CAE.SimLoad] = [item for item in sim_loads if item.Name.lower() == force_name.lower()]

    if len(sim_load) == 0:
        # no load with the given name, thus creating the load
        sim_bc_builder = sim_simulation.CreateBcBuilderForLoadDescriptor("ComponentGravityField", force_name)
    else:
        # a load with the given name already exists therefore editing the load
        sim_bc_builder = sim_simulation.CreateBcBuilderForBc(sim_load[0])

    propertyTable = sim_bc_builder.PropertyTable
    setManager = sim_bc_builder.TargetSetManager

    objects1 = [NXOpen.CAE.SetObject()]
    objects1[0].Obj = None
    objects1[0].SubType = NXOpen.CAE.CaeSetObjectSubType.Part
    objects1[0].SubId = 0
    setManager.SetTargetSetMembers(0, NXOpen.CAE.CaeSetGroupFilterType.ValueOf(-1), objects1)

    vectorFieldWrapper = propertyTable.GetVectorFieldWrapperPropertyValue("CartesianMagnitude")
    unitMilliMeterPerSquareSecond = sim_part.UnitCollection.FindObject("MilliMeterPerSquareSecond")

    expressionAx = vectorFieldWrapper.GetExpressionByIndex(0)
    sim_part.Expressions.EditWithUnits(expressionAx, unitMilliMeterPerSquareSecond, str(gx))

    expressionAy = vectorFieldWrapper.GetExpressionByIndex(1)
    sim_part.Expressions.EditWithUnits(expressionAy, unitMilliMeterPerSquareSecond, str(gy))

    expressionAz = vectorFieldWrapper.GetExpressionByIndex(2)
    sim_part.Expressions.EditWithUnits(expressionAz, unitMilliMeterPerSquareSecond, str(gz))

    expressions = [expressionAx, expressionAy, expressionAz]
    vectorFieldWrapper.SetExpressions(expressions)

    propertyTable.SetVectorFieldWrapperPropertyValue("CartesianMagnitude", vectorFieldWrapper)
    propertyTable.SetTablePropertyWithoutValue("CylindricalMagnitude")

    propertyTable.SetVectorFieldWrapperPropertyValue("CylindricalMagnitude", None)
    propertyTable.SetTablePropertyWithoutValue("SphericalMagnitude")
    propertyTable.SetVectorFieldWrapperPropertyValue("SphericalMagnitude", None)

    propertyValue1 = [""]
    propertyTable.SetTextPropertyValue("description", propertyValue1)

    sim_bc_builder.DestinationFolder = None

    simBC = sim_bc_builder.CommitAddBc()

    sim_bc_builder.Destroy()

    return simBC


def get_all_fe_elements(base_fem_part: NXOpen.CAE.BaseFemPart=None) -> Dict[int, NXOpen.CAE.FEElement]:
    """
    Get all elements from the model.
    Note that this is the most performant way to do so.

    Parameters
    ----------
    base_fem_part: NXOpen.CAE.BaseFemPart
        The BaseFemPart to get the elements from.

    Returns
    -------
    List[NXOpen.CAE.FEElement]
        A list of all FEElements in the base_fem_part
    
    Notes
    -----
    Tested in SC2306
    """
    if base_fem_part is None:
        base_fem_part = cast(NXOpen.CAE.BaseFemPart,the_session.Parts.Work)
    all_elements: Dict[int, NXOpen.CAE.FEElement] = {}
    fe_element_label_map = base_fem_part.BaseFEModel.FeelementLabelMap
    element_label: int = fe_element_label_map.AskNextElementLabel(0)
    while (element_label > 0):
        all_elements[element_label] = fe_element_label_map.GetElement(element_label)
        element_label = fe_element_label_map.AskNextElementLabel(element_label)
    
    # sort the dict (valid for python 3.7+) even thought the items should be in order from the element label map
    all_elements = dict(sorted(all_elements.items()))
    return all_elements


def add_related_nodes_and_elements(cae_part: NXOpen.CAE.CaePart):
    """
    This function cycles through all cae groups in a CaePart.
    For each group it adds the related nodes and elements for the bodies and faces in the group.
    Practical for repopulating groups after a (partial) remesh.
    Function is idempotent.

    Parameters
    ----------
    fem_part: NXOpen.CAE.FemPart
        The CaePart to perform this operation on.
    
    Notes
    -----
    Tested in SC2306
    """
    cae_groups: List[NXOpen.CAE.CaeGroup] = cae_part.CaeGroups
    for group in cae_groups: # type: ignore
        the_lw.WriteFullline("Processing group " + group.Name)
        seeds_body: List[NXOpen.CAE.CAEBody] = []
        seeds_face: List[NXOpen.CAE.CAEFace] = []

        for tagged_object in group.GetEntities():
            if type(tagged_object) is NXOpen.CAE.CAEBody:
                seeds_body.append(cast(NXOpen.CAE.CAEBody, tagged_object))
            
            elif type(tagged_object) is NXOpen.CAE.CAEFace:
                seeds_face.append(cast(NXOpen.CAE.CAEFace, tagged_object))

        smart_selection_manager: NXOpen.CAE.SmartSelectionManager = cae_part.SmartSelectionMgr

        related_element_method_body: NXOpen.CAE.RelatedElemMethod = smart_selection_manager.CreateRelatedElemMethod(seeds_body, False)
        # related_node_method_body: NXOpen.CAE.RelatedNodeMethod = smart_selection_manager.CreateNewRelatedNodeMethodFromBody(seeds_body, False)
        # comment previous line and uncomment next line for NX version 2007 (release 2022.1) and later
        related_node_method_body: NXOpen.CAE.RelatedElemMethod = smart_selection_manager.CreateNewRelatedNodeMethodFromBodies(seeds_body, False, False)

        group.AddEntities(related_element_method_body.GetElements())
        group.AddEntities(related_node_method_body.GetNodes())

        related_element_method_face: NXOpen.CAE.RelatedElemMethod = smart_selection_manager.CreateRelatedElemMethod(seeds_face, False)
        # related_node_method_face: NXOpen.CAE.RelatedElemMethod = smart_selection_manager.CreateRelatedNodeMethod(seeds_face, False)
        # comment previous line and uncomment next line for NX version 2007 (release 2022.1) and later
        related_node_method_face: NXOpen.CAE.RelatedElemMethod = smart_selection_manager.CreateNewRelatedNodeMethodFromFaces(seeds_face, False, False)

        group.AddEntities(related_element_method_face.GetElements())
        group.AddEntities(related_node_method_face.GetNodes())


def copy_groups_to_sim_part(sim_part: NXOpen.CAE.SimPart=None, groups_in_screenshots: List[str]=[]) -> List[NXOpen.CAE.CaeGroup]:
    if sim_part is None:
        if not isinstance(the_session.Parts.BaseWork, NXOpen.CAE.SimPart):
            raise ValueError("copy_groups_to_sim_part needs to be called on a .sim file!")
        sim_part: NXOpen.CAE.SimPart = cast(NXOpen.CAE.SimPart, the_session.Parts.BaseWork)

    copied_groups: List[NXOpen.CAE.CaeGroup] = []
    sim_groups: List[NXOpen.CAE.CaeGroup] = [item for item in sim_part.CaeGroups]
    for i in range(len(sim_groups)):
        # don't copy the group if it's not used in the screenshots
        if not sim_groups[i].Name in groups_in_screenshots:
            continue
        # dont copy the group if it's a sim group
        if sim_groups[i].OwningComponent is None:
            # the_lw.WriteFullline(f'{i} {sim_groups[i].Name} is a sim group')
            continue
        # skip output groups since these are not user created.
        if sim_groups[i].Name == "OUTPUT GROUP":
            # the_lw.WriteFullline(f'{i} {sim_groups[i].Name} is a sim group')
            continue
        # don't copy the group if it has been copied earlier
        test: List[NXOpen.CAE.CaeGroup] = [item for item in sim_groups if item.Name == sim_groups[i].Name + '_screenshot_generator_temp']
        if len(test) > 0:
            # the_lw.WriteFullline(f'{i} {sim_groups[i].Name} already has a temp group')
            continue
        else:
            enties = sim_groups[i].GetEntities()
            # the_lw.WriteFullline(f'{i} {sim_groups[i].Name} with {len(enties)} entities')
            if len(enties) == 0:
                # the_lw.WriteFullline(f'{i} {sim_groups[i].Name} has no entities')
                continue
            group: NXOpen.CAE.CaeGroup = sim_part.CaeGroups.CreateGroup(sim_groups[i].Name + '_screenshot_generator_temp', sim_groups[i].GetEntities())
            create_string_attribute(group, 'screenshot_generator', 'true')
            copied_groups.append(group)
    
    return copied_groups


def create_force_on_group(group_name: str, fx: float, fy: float, fz: float, force_name: str, group_filter_type: NXOpen.CAE.CaeSetGroupFilterType.GeomEdge) -> NXOpen.CAE.SimBC:
    """This function creates a force on a node.
    
    Parameters
    ----------
    group_name: str
        The name of the group to apply the force to.
    fx: float
        the force in global x-direction in Newton.
    fy: float
        the force in global y-direction in Newton.
    fz: float
        the force in global z-direction in Newton.
    force_name: str
        The name of the force for the GUI.
    group_filter_type: NXOpen.CAE.CaeSetGroupFilterType
        The object type the filter from the group.

    Returns
    -------
    NXOpen.CAE.SimBC
        Returns the created force.

    Notes
    -----
    Tested in SC2312
    """
    base_part: NXOpen.BasePart = the_session.Parts.BaseWork
    # check if started from a SimPart, returning othwerwise
    if not isinstance(base_part, NXOpen.CAE.SimPart):
        the_lw.WriteFullline("CreateNodalForce needs to start from a .sim file. Exiting")
        return
    # we are now sure that basePart is a SimPart
    sim_part: NXOpen.CAE.SimPart = cast(NXOpen.CAE.SimPart, base_part) # explicit casting makes it clear
    
    sim_simulation: NXOpen.CAE.SimSimulation = sim_part.Simulation
    # make the active solution inactive, so load is not automatically added to active subcase
    sim_simulation.ActiveSolution = NXOpen.CAE.SimSolution.Null

    # check if a nodal force with that name already exists. If it does, update, if not create it
    sim_loads: List[NXOpen.CAE.SimLoad] = sim_part.Simulation.Loads
    sim_load: NXOpen.CAE.SimLoad = [item for item in sim_loads if item.Name.lower() == force_name.lower()]
    if len(sim_load) == 0:
        # load not found
        sim_bc_builder: NXOpen.CAE.SimBCBuilder = sim_simulation.CreateBcBuilderForLoadDescriptor("ComponentForceField", force_name, 0) # overloaded function is unknow to intellisense
    else:
        sim_bc_builder: NXOpen.CAE.SimBCBuilder = sim_simulation.CreateBcBuilderForBc(sim_load[0])
        the_lw.WriteFullline(f"A force with the name {force_name} already exists, therefore updating the force.")
    
    # get the group
    groups: List[NXOpen.CAE.CaeGroup] = [item for item in sim_part.CaeGroups if item.Name.lower() == group_name.lower()]
    if len(groups) == 0:
        the_lw.WriteFullline(f"Group {group_name} not found. Exiting")
        return
    elif len(groups) > 1:
        the_lw.WriteFullline(f"Multiple groups with the name {group_name} found. Exiting")
        return
    else:
        group: NXOpen.CAE.CaeGroup = groups[0]

    # define the force
    property_table: NXOpen.CAE.PropertyTable = sim_bc_builder.PropertyTable
    set_manager: NXOpen.CAE.SetManager = sim_bc_builder.TargetSetManager
    set_manager.SetTargetSetGroup(0, group_filter_type, group)
    
    unit1: NXOpen.Unit = sim_part.UnitCollection.FindObject("Newton")
    expression1: NXOpen.Expression = sim_part.Expressions.CreateSystemExpressionWithUnits(str(fx), unit1)
    expression2: NXOpen.Expression = sim_part.Expressions.CreateSystemExpressionWithUnits(str(fy), unit1)
    expression3: NXOpen.Expression = sim_part.Expressions.CreateSystemExpressionWithUnits(str(fz), unit1)

    field_manager: NXOpen.Fields.FieldManager = cast(NXOpen.Fields.FieldManager, sim_part.FindObject("FieldManager"))
    expressions: List[NXOpen.Expression] = [NXOpen.Expression.Null] * 3 
    expressions[0] = expression1
    expressions[1] = expression2
    expressions[2] = expression3
    vector_field_wrapper: NXOpen.Fields.VectorFieldWrapper = field_manager.CreateVectorFieldWrapperWithExpressions(expressions)
    
    property_table.SetVectorFieldWrapperPropertyValue("CartesianMagnitude", vector_field_wrapper)
    
    sim_bc: NXOpen.CAE.SimBC = sim_bc_builder.CommitAddBc()
    
    sim_bc_builder.Destroy()

    return sim_bc


def create_force_on_selection_recipe(selection_recipe_name: str, fx: float, fy: float, fz: float, force_name: str, selection_recipe_filter_type: NXOpen.CAE.CaeSetGroupFilterType.GeomEdge) -> NXOpen.CAE.SimBC:
    """This function creates a force on a node.
    
    Parameters
    ----------
    selection_recipe_name: str
        The name of the selection recipe to apply the force to.
    fx: float
        the force in global x-direction in Newton.
    fy: float
        the force in global y-direction in Newton.
    fz: float
        the force in global z-direction in Newton.
    force_name: str
        The name of the force for the GUI.
    group_filter_type: NXOpen.CAE.CaeSetGroupFilterType
        The object type the filter from the group.

    Returns
    -------
    NXOpen.CAE.SimBC
        Returns the created force.

    Notes
    -----
    Tested in SC2312
    """
    base_part: NXOpen.BasePart = the_session.Parts.BaseWork
    # check if started from a SimPart, returning othwerwise
    if not isinstance(base_part, NXOpen.CAE.SimPart):
        the_lw.WriteFullline("CreateNodalForce needs to start from a .sim file. Exiting")
        return
    # we are now sure that basePart is a SimPart
    sim_part: NXOpen.CAE.SimPart = cast(NXOpen.CAE.SimPart, base_part) # explicit casting makes it clear
    
    sim_simulation: NXOpen.CAE.SimSimulation = sim_part.Simulation
    # make the active solution inactive, so load is not automatically added to active subcase
    sim_simulation.ActiveSolution = NXOpen.CAE.SimSolution.Null

    # check if a nodal force with that name already exists. If it does, update, if not create it
    sim_loads: List[NXOpen.CAE.SimLoad] = sim_part.Simulation.Loads
    sim_load: NXOpen.CAE.SimLoad = [item for item in sim_loads if item.Name.lower() == force_name.lower()]
    if len(sim_load) == 0:
        # load not found
        sim_bc_builder: NXOpen.CAE.SimBCBuilder = sim_simulation.CreateBcBuilderForLoadDescriptor("ComponentForceField", force_name, 0) # overloaded function is unknow to intellisense
    else:
        sim_bc_builder: NXOpen.CAE.SimBCBuilder = sim_simulation.CreateBcBuilderForBc(sim_load[0])
        the_lw.WriteFullline(f"A force with the name {force_name} already exists, therefore updating the force.")
    
    # get the group
    selection_recipes: List[NXOpen.CAE.SelectionRecipe] = [item for item in sim_part.SelectionRecipes if item.Name.lower() == selection_recipe_name.lower()]
    if len(selection_recipes) == 0:
        the_lw.WriteFullline(f"Group {selection_recipe_name} not found. Exiting")
        return
    elif len(selection_recipes) > 1:
        the_lw.WriteFullline(f"Multiple groups with the name {selection_recipe_name} found. Exiting")
        return
    else:
        selection_recipe: NXOpen.CAE.SelectionRecipe = selection_recipes[0]
    
    objects = [None] * 1
    objects[0] = NXOpen.CAE.SetObject()
    objects[0].Obj = selection_recipe
    objects[0].SubType = NXOpen.CAE.CaeSetObjectSubType.SelRecipe
    objects[0].SubId = 0

    # define the force
    property_table: NXOpen.CAE.PropertyTable = sim_bc_builder.PropertyTable
    set_manager: NXOpen.CAE.SetManager = sim_bc_builder.TargetSetManager
    set_manager.SetTargetSetMembers(0, selection_recipe_filter_type, objects)
    
    unit1: NXOpen.Unit = sim_part.UnitCollection.FindObject("Newton")
    expression1: NXOpen.Expression = sim_part.Expressions.CreateSystemExpressionWithUnits(str(fx), unit1)
    expression2: NXOpen.Expression = sim_part.Expressions.CreateSystemExpressionWithUnits(str(fy), unit1)
    expression3: NXOpen.Expression = sim_part.Expressions.CreateSystemExpressionWithUnits(str(fz), unit1)

    field_manager: NXOpen.Fields.FieldManager = cast(NXOpen.Fields.FieldManager, sim_part.FindObject("FieldManager"))
    expressions: List[NXOpen.Expression] = [NXOpen.Expression.Null] * 3 
    expressions[0] = expression1
    expressions[1] = expression2
    expressions[2] = expression3
    vector_field_wrapper: NXOpen.Fields.VectorFieldWrapper = field_manager.CreateVectorFieldWrapperWithExpressions(expressions)
    
    property_table.SetVectorFieldWrapperPropertyValue("CartesianMagnitude", vector_field_wrapper)
    
    sim_bc: NXOpen.CAE.SimBC = sim_bc_builder.CommitAddBc()
    
    sim_bc_builder.Destroy()

    return sim_bc


def create_moment_on_group(group_name: str, mx: float, my: float, mz: float, moment_name: str, group_filter_type: NXOpen.CAE.CaeSetGroupFilterType.GeomEdge) -> NXOpen.CAE.SimBC:
    """This function creates a force on a node.
    
    Parameters
    ----------
    group_name: str
        The name of the group to apply the moment to.
    fx: float
        the moment in global x-direction in NewtonMeter.
    fy: float
        the moment in global y-direction in NewtonMeter.
    fz: float
        the moment in global z-direction in NewtonMeter.
    moment_name: str
        The name of the moment for the GUI.
    group_filter_type: NXOpen.CAE.CaeSetGroupFilterType
        The object type the filter from the group.

    Returns
    -------
    NXOpen.CAE.SimBC
        Returns the created moment.

    Notes
    -----
    Tested in SC2312
    """
    base_part: NXOpen.BasePart = the_session.Parts.BaseWork
    # check if started from a SimPart, returning othwerwise
    if not isinstance(base_part, NXOpen.CAE.SimPart):
        the_lw.WriteFullline("CreateNodalForce needs to start from a .sim file. Exiting")
        return
    # we are now sure that basePart is a SimPart
    sim_part: NXOpen.CAE.SimPart = cast(NXOpen.CAE.SimPart, base_part) # explicit casting makes it clear
    
    sim_simulation: NXOpen.CAE.SimSimulation = sim_part.Simulation
    # make the active solution inactive, so load is not automatically added to active subcase
    sim_simulation.ActiveSolution = NXOpen.CAE.SimSolution.Null

    # check if a nodal force with that name already exists. If it does, update, if not create it
    sim_loads: List[NXOpen.CAE.SimLoad] = sim_part.Simulation.Loads
    sim_load: NXOpen.CAE.SimLoad = [item for item in sim_loads if item.Name.lower() == moment_name.lower()]
    if len(sim_load) == 0:
        # load not found
        sim_bc_builder: NXOpen.CAE.SimBCBuilder = sim_simulation.CreateBcBuilderForLoadDescriptor("ComponentMomentField", moment_name, 0) # overloaded function is unknow to intellisense
    else:
        sim_bc_builder: NXOpen.CAE.SimBCBuilder = sim_simulation.CreateBcBuilderForBc(sim_load[0])
        the_lw.WriteFullline(f"A force with the name {moment_name} already exists, therefore updating the force.")
    
    # get the group
    groups: List[NXOpen.CAE.CaeGroup] = [item for item in sim_part.CaeGroups if item.Name.lower() == group_name.lower()]
    if len(groups) == 0:
        the_lw.WriteFullline(f"Group {group_name} not found. Exiting")
        return
    elif len(groups) > 1:
        the_lw.WriteFullline(f"Multiple groups with the name {group_name} found. Exiting")
        return
    else:
        group: NXOpen.CAE.CaeGroup = groups[0]

    # define the force
    property_table: NXOpen.CAE.PropertyTable = sim_bc_builder.PropertyTable
    set_manager: NXOpen.CAE.SetManager = sim_bc_builder.TargetSetManager
    set_manager.SetTargetSetGroup(0, group_filter_type, group)
    
    unit1: NXOpen.Unit = sim_part.UnitCollection.FindObject("NewtonMeter")
    expression1: NXOpen.Expression = sim_part.Expressions.CreateSystemExpressionWithUnits(str(mx), unit1)
    expression2: NXOpen.Expression = sim_part.Expressions.CreateSystemExpressionWithUnits(str(my), unit1)
    expression3: NXOpen.Expression = sim_part.Expressions.CreateSystemExpressionWithUnits(str(mz), unit1)

    field_manager: NXOpen.Fields.FieldManager = cast(NXOpen.Fields.FieldManager, sim_part.FindObject("FieldManager"))
    expressions: List[NXOpen.Expression] = [NXOpen.Expression.Null] * 3 
    expressions[0] = expression1
    expressions[1] = expression2
    expressions[2] = expression3
    vector_field_wrapper: NXOpen.Fields.VectorFieldWrapper = field_manager.CreateVectorFieldWrapperWithExpressions(expressions)
    
    property_table.SetVectorFieldWrapperPropertyValue("CartesianMagnitude", vector_field_wrapper)
    
    sim_bc: NXOpen.CAE.SimBC = sim_bc_builder.CommitAddBc()
    
    sim_bc_builder.Destroy()

    return sim_bc


def create_moment_on_selection_recipe(selection_recipe_name: str, mx: float, my: float, mz: float, moment_name: str, selection_recipe_filter_type: NXOpen.CAE.CaeSetGroupFilterType.GeomEdge) -> NXOpen.CAE.SimBC:
    """This function creates a moment on the specified items in a selection recipe.
    
    Parameters
    ----------
    selection_recipe_name: str
        The name of the selection recipe to apply the force to.
    mx: float
        the moment in global x-direction in NewtonMeter.
    my: float
        the moment in global y-direction in NewtonMeter.
    mz: float
        the moment in global z-direction in NewtonMeter.
    moment_name: str
        The name of the moment for the GUI.
    group_filter_type: NXOpen.CAE.CaeSetGroupFilterType
        The object type the filter from the group.

    Returns
    -------
    NXOpen.CAE.SimBC
        Returns the created moment.

    Notes
    -----
    Untested
    """
    base_part: NXOpen.BasePart = the_session.Parts.BaseWork
    # check if started from a SimPart, returning othwerwise
    if not isinstance(base_part, NXOpen.CAE.SimPart):
        the_lw.WriteFullline("CreateNodalForce needs to start from a .sim file. Exiting")
        return
    # we are now sure that basePart is a SimPart
    sim_part: NXOpen.CAE.SimPart = cast(NXOpen.CAE.SimPart, base_part) # explicit casting makes it clear
    
    sim_simulation: NXOpen.CAE.SimSimulation = sim_part.Simulation
    # make the active solution inactive, so load is not automatically added to active subcase
    sim_simulation.ActiveSolution = NXOpen.CAE.SimSolution.Null

    # check if a nodal force with that name already exists. If it does, update, if not create it
    sim_loads: List[NXOpen.CAE.SimLoad] = sim_part.Simulation.Loads
    sim_load: NXOpen.CAE.SimLoad = [item for item in sim_loads if item.Name.lower() == moment_name.lower()]
    if len(sim_load) == 0:
        # load not found
        sim_bc_builder: NXOpen.CAE.SimBCBuilder = sim_simulation.CreateBcBuilderForLoadDescriptor("ComponentMomentField", moment_name, 0) # overloaded function is unknow to intellisense
    else:
        sim_bc_builder: NXOpen.CAE.SimBCBuilder = sim_simulation.CreateBcBuilderForBc(sim_load[0])
        the_lw.WriteFullline(f"A force with the name {moment_name} already exists, therefore updating the force.")
    
    # get the group
    selection_recipes: List[NXOpen.CAE.SelectionRecipe] = [item for item in sim_part.SelectionRecipes if item.Name.lower() == selection_recipe_name.lower()]
    if len(selection_recipes) == 0:
        the_lw.WriteFullline(f"Group {selection_recipe_name} not found. Exiting")
        return
    elif len(selection_recipes) > 1:
        the_lw.WriteFullline(f"Multiple groups with the name {selection_recipe_name} found. Exiting")
        return
    else:
        selection_recipe: NXOpen.CAE.SelectionRecipe = selection_recipes[0]
    
    objects = [None] * 1
    objects[0] = NXOpen.CAE.SetObject()
    objects[0].Obj = selection_recipe
    objects[0].SubType = NXOpen.CAE.CaeSetObjectSubType.SelRecipe
    objects[0].SubId = 0

    # define the force
    property_table: NXOpen.CAE.PropertyTable = sim_bc_builder.PropertyTable
    set_manager: NXOpen.CAE.SetManager = sim_bc_builder.TargetSetManager
    set_manager.SetTargetSetMembers(0, selection_recipe_filter_type, objects)
    
    unit1: NXOpen.Unit = sim_part.UnitCollection.FindObject("NewtonMeter")
    expression1: NXOpen.Expression = sim_part.Expressions.CreateSystemExpressionWithUnits(str(mx), unit1)
    expression2: NXOpen.Expression = sim_part.Expressions.CreateSystemExpressionWithUnits(str(my), unit1)
    expression3: NXOpen.Expression = sim_part.Expressions.CreateSystemExpressionWithUnits(str(mz), unit1)

    field_manager: NXOpen.Fields.FieldManager = cast(NXOpen.Fields.FieldManager, sim_part.FindObject("FieldManager"))
    expressions: List[NXOpen.Expression] = [NXOpen.Expression.Null] * 3 
    expressions[0] = expression1
    expressions[1] = expression2
    expressions[2] = expression3
    vector_field_wrapper: NXOpen.Fields.VectorFieldWrapper = field_manager.CreateVectorFieldWrapperWithExpressions(expressions)
    
    property_table.SetVectorFieldWrapperPropertyValue("CartesianMagnitude", vector_field_wrapper)
    
    sim_bc: NXOpen.CAE.SimBC = sim_bc_builder.CommitAddBc()
    
    sim_bc_builder.Destroy()

    return sim_bc


def create_cartesian_formula_field(variable_name: str, variable_type: str, unit: NXOpen.Unit, formula: str, field_name: str, work_part: NXOpen.CAE.CaePart=None) -> NXOpen.Fields.SpatialMap:
    """This function creates a field (spatial map) in which the value of a given variable is calculated based on a formula.
        This formula can depend on the global coordinates x, y and z.

    Parameters
    ----------
    variable_name: str
        The name of the dependent domain, as displayed in the 'Name' column of the 'Dependent Domain' section in the GUI (e.g. 'pressure')
    variable_type: str
        The name of the dependent domain, as displayed in the Pulldown of the 'Dependent Domain' section in the GUI (e.g. 'Pressure')
    unit: NXOpen.Unit
        The unit of the variable. (e.g. work_part.UnitCollection.FindObject("PressureNewtonPerSquareMilliMeter"))
    formula: str
        The formula as provided in the 'Definition' section in the GUI (e.g. 'ug_val(x) * 10')
    field_name: str
        The name of the field.
    work_part: NXOpen.CAE.CaePart (Optional)
        The part to create the field in. If None, the work part is used.

    Returns
    -------
    NXOpen.CAE.SimBC
        Returns the created moment.

    Notes
    -----
    Tested in SC2312
    """
    if work_part is None:
        work_part = the_session.Parts.BaseWork
    
    # check if field does not already exist
    field_manager = work_part.FieldManager
    try:
        field_manager.FindObject(field_name)
        the_lw.WriteFullline(f"ERROR: Field {field_name} already exists. Field {field_name} not created")
        return None
    except:
        pass
    
    # the dependent domain
    try:
        name_variable = field_manager.GetNameVariable(variable_name, variable_type)
    except:
        the_lw.WriteFullline(f"ERROR: Variable {variable_name} of type {variable_type} not found. Exiting")
        return None
    field_variable = field_manager.CreateDependentVariable(NXOpen.Fields.Field.Null, name_variable, unit, NXOpen.Fields.FieldVariable.ValueType.Real)
    field_expression = field_manager.CreateSubFieldExpression(field_variable)
    
    spatial_map_builder = field_manager.CreateSpatialMapBuilder(NXOpen.Fields.SpatialMap.Null)
    spatial_map_builder.CoordSystem = NXOpen.CoordinateSystem.Null
    spatial_map_builder.FitSurfaceCoordinateSystem = NXOpen.CoordinateSystem.Null
    spatial_map_builder.MapType = NXOpen.Fields.SpatialMap.TypeEnum.Global

    # the 'independent domain'
    unit_milli_meter = work_part.UnitCollection.FindObject("MilliMeter")
    name_variable_x = field_manager.GetNameVariable("x", "Length")
    field_variable_x = field_manager.CreateIndependentVariable(NXOpen.Fields.Field.Null, name_variable_x, unit_milli_meter, NXOpen.Fields.FieldVariable.ValueType.Real, False, True, 1e+19, False, True, 9.9999999999999998e-20, False, 2, False, 1.0)
    name_variable_y = field_manager.GetNameVariable("y", "Length")
    field_variable_y = field_manager.CreateIndependentVariable(NXOpen.Fields.Field.Null, name_variable_y, unit_milli_meter, NXOpen.Fields.FieldVariable.ValueType.Real, False, True, 1e+19, False, True, 9.9999999999999998e-20, False, 2, False, 1.0)
    name_variable_z = field_manager.GetNameVariable("z", "Length")
    field_variable_z = field_manager.CreateIndependentVariable(NXOpen.Fields.Field.Null, name_variable_z, unit_milli_meter, NXOpen.Fields.FieldVariable.ValueType.Real, False, True, 1e+19, False, True, 9.9999999999999998e-20, False, 2, False, 1.0)
    spatial_map: NXOpen.Fields.SpatialMap = spatial_map_builder.Commit()
    
    # the fomula section
    indep_var_array = [NXOpen.Fields.FieldVariable.Null] * 3
    indep_var_array[0] = field_variable_x
    indep_var_array[1] = field_variable_y
    indep_var_array[2] = field_variable_z
    dep_exp_rray = [NXOpen.Fields.FieldExpression.Null] * 1 
    dep_exp_rray[0] = field_expression
    field_manager.CreateFieldFormula(field_name, indep_var_array, dep_exp_rray)
    field_expression.EditFieldExpression(formula, unit, indep_var_array, False)
    
    spatial_map: NXOpen.Fields.SpatialMap = spatial_map_builder.Commit()    
    spatial_map_builder.Destroy()

    return spatial_map


def create_pressure_on_group(group_name: str, pressure: float, force_name: str, group_filter_type: NXOpen.CAE.CaeSetGroupFilterType.GeomEdge) -> NXOpen.CAE.SimBC:
    """This function creates a force on a node.
    
    Parameters
    ----------
    group_name: str
        The name of the group to apply the pressure to.
    pressure: float
        The magnitude of the pressure in Newton per square meter (Pascals).
    force_name: str
        The name of the force for the GUI.
    group_filter_type: NXOpen.CAE.CaeSetGroupFilterType
        The object type the filter from the group.

    Returns
    -------
    NXOpen.CAE.SimBC
        Returns the created force.

    Notes
    -----
    Tested in SC2312
    """
    base_part: NXOpen.BasePart = the_session.Parts.BaseWork
    # check if started from a SimPart, returning othwerwise
    if not isinstance(base_part, NXOpen.CAE.SimPart):
        the_lw.WriteFullline("create_pressure_on_group needs to start from a .sim file. Exiting")
        return
    # we are now sure that basePart is a SimPart
    sim_part: NXOpen.CAE.SimPart = cast(NXOpen.CAE.SimPart, base_part) # explicit casting makes it clear
    
    sim_simulation: NXOpen.CAE.SimSimulation = sim_part.Simulation
    # make the active solution inactive, so load is not automatically added to active subcase
    sim_simulation.ActiveSolution = NXOpen.CAE.SimSolution.Null

    # check if a nodal force with that name already exists. If it does, update, if not create it
    sim_loads: List[NXOpen.CAE.SimLoad] = sim_part.Simulation.Loads
    sim_load: NXOpen.CAE.SimLoad = [item for item in sim_loads if item.Name.lower() == force_name.lower()]
    if len(sim_load) == 0:
        # load not found
        sim_bc_builder: NXOpen.CAE.SimBCBuilder = sim_simulation.CreateBcBuilderForLoadDescriptor("2D3DFaceNormalPressure", force_name, 0) # overloaded function is unknow to intellisense
    else:
        sim_bc_builder: NXOpen.CAE.SimBCBuilder = sim_simulation.CreateBcBuilderForBc(sim_load[0])
        the_lw.WriteFullline(f"A force with the name {force_name} already exists, therefore updating the force.")
    
    # get the group
    groups: List[NXOpen.CAE.CaeGroup] = [item for item in sim_part.CaeGroups if item.Name.lower() == group_name.lower()]
    if len(groups) == 0:
        the_lw.WriteFullline(f"Group {group_name} not found. Exiting")
        return
    elif len(groups) > 1:
        the_lw.WriteFullline(f"Multiple groups with the name {group_name} found. Exiting")
        return
    else:
        group: NXOpen.CAE.CaeGroup = groups[0]

    # define the force
    property_table: NXOpen.CAE.PropertyTable = sim_bc_builder.PropertyTable
    set_manager: NXOpen.CAE.SetManager = sim_bc_builder.TargetSetManager
    set_manager.SetTargetSetGroup(0, group_filter_type, group)
    
    unit_pascal: NXOpen.Unit = sim_part.UnitCollection.FindObject("Pascals")
    expression: NXOpen.Expression = sim_part.Expressions.CreateSystemExpressionWithUnits(str(pressure), unit_pascal)

    field_manager: NXOpen.Fields.FieldManager = cast(NXOpen.Fields.FieldManager, sim_part.FindObject("FieldManager"))
    scalar_field_wrapper: NXOpen.Fields.VectorFieldWrapper = field_manager.CreateScalarFieldWrapperWithExpression(expression)
    
    property_table.SetScalarFieldWrapperPropertyValue("TotalPressure", scalar_field_wrapper)
    
    sim_bc: NXOpen.CAE.SimBC = sim_bc_builder.CommitAddBc()
    
    sim_bc_builder.Destroy()

    return sim_bc


def set_field_in_pressure_load(load_name: str, field_name: str) -> NXOpen.CAE.SimBC:
    '''
    This function sets the field in a pressure load.

    Parameters
    ----------
    load_name: str
        The name of the pressure load to apply the field to.
    field_name: str
        The name of the field to apply as the pressure value.

    Returns
    -------
    NXOpen.CAE.SimBC
        Returns the created force.

    Notes
    -----
    Tested in SC2312
    Note the unit will be taken from the pressure field. Take care that the unit is correct.

    '''
    base_part: NXOpen.BasePart = the_session.Parts.BaseWork
    # check if started from a SimPart, returning othwerwise
    if not isinstance(base_part, NXOpen.CAE.SimPart):
        the_lw.WriteFullline("create_pressure_on_group needs to start from a .sim file. Exiting")
        return
    # we are now sure that basePart is a SimPart
    sim_part: NXOpen.CAE.SimPart = cast(NXOpen.CAE.SimPart, base_part) # explicit casting makes it clear
    sim_simulation = sim_part.Simulation
    
    sim_loads: List[NXOpen.CAE.SimLoad] = [item for item in sim_part.Simulation.Loads if item.Name.lower() == load_name.lower()]
    if len(sim_loads) == 0:
        the_lw.WriteFullline(f"Load {load_name} not found. Exiting")
        return
    elif len(sim_loads) > 1:
        the_lw.WriteFullline(f"Multiple loads with the name {load_name} found. Exiting")
        return
    sim_load = sim_loads[0]
    sim_bc_builder = sim_simulation.CreateBcBuilderForBc(sim_load)

    # check if field exists
    field_manager = sim_part.FieldManager
    # FindObject throws an exception if the object is not found
    try: 
        field = field_manager.FindObject(field_name)
    except:
        the_lw.WriteFullline(f"ERROR: Field {field_name} not found.")
        return None
    
    property_table = sim_bc_builder.PropertyTable
    scalar_field_wrapper = property_table.GetScalarFieldWrapperPropertyValue("TotalPressure")
    try:
        scalar_field_wrapper.SetField(field, 1.0)
        property_table.SetScalarFieldWrapperPropertyValue("TotalPressure", scalar_field_wrapper)
    except:
        the_lw.WriteFullline(f"ERROR: Field {field_name} not set in pressure load {load_name}. Is the field compatible with the pressure load?")
        return None

    sim_bc = sim_bc_builder.CommitAddBc()
    sim_bc_builder.Destroy()

    return sim_bc
