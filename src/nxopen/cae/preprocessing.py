# should split this file up into a fem/afem and sim functionality file

import os
from typing import List, cast, Optional, Union

import NXOpen
import NXOpen.CAE


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
    physicalPropertyTables: List[NXOpen.CAE.PhysicalPropertyTable] = fem_part.PhysicalPropertyTables.ToArray()
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


def CreateNodalConstraint(node_label: int, dx: float, dy : float, dz: float, rx: float, ry: float, rz: float, constraint_name: str) -> NXOpen.CAE.SimBC:
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
    sim_constraints: List[NXOpen.CAE.SimConstraint] = sim_simulation.Constraints
    sim_constraint: NXOpen.CAE.SimConstraint = [item for item in sim_constraints if item.Name.lower() == constraint_name.lower()]
    sim_bc_builder: NXOpen.CAE.SimBCBuilder
    if len(sim_constraint == 0):
        # no constraint with the given name, thus creating the constrain
        sim_bc_builder = sim_simulation.CreateBcBuilderForConstraintDescriptor("UserDefinedDisplacementConstraint", constraint_name, 0)
    else:
        # a constraint with the given name already exists therefore editing the constraint
        sim_bc_builder = sim_simulation.CreateBcBuilderForBc(sim_constraint)

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
    field_expression6.EditFieldExpression(str(rx), unit_degrees, indep_var_array6, False)
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
    expressions: List[NXOpen.Expression] = [NXOpen.Expression.Null] * 3 
    expressions[0] = expression1
    expressions[1] = expression2
    expressions[2] = expression3
    vector_field_wrapper: NXOpen.Fields.VectorFieldWrapper = field_manager.CreateVectorFieldWrapperWithExpressions(expressions)
    
    property_table.SetVectorFieldWrapperPropertyValue("CartesianMagnitude", vector_field_wrapper)
    property_table.SetTablePropertyWithoutValue("CylindricalMagnitude")
    property_table.SetVectorFieldWrapperPropertyValue("CylindricalMagnitude", NXOpen.Fields.VectorFieldWrapper.Null)
    property_table.SetTablePropertyWithoutValue("SphericalMagnitude")
    property_table.SetVectorFieldWrapperPropertyValue("SphericalMagnitude", NXOpen.Fields.VectorFieldWrapper.Null)
    property_table.SetTablePropertyWithoutValue("DistributionField")
    property_table.SetScalarFieldWrapperPropertyValue("DistributionField", NXOpen.Fields.ScalarFieldWrapper.Null)
    property_table.SetTablePropertyWithoutValue("ComponentsDistributionField")
    property_table.SetVectorFieldWrapperPropertyValue("ComponentsDistributionField", NXOpen.Fields.VectorFieldWrapper.Null)
    
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
        the_lw.WriteFullline("AddLoadToSubcase needs to start from a .sim file. Exiting")
        return
    # we are now sure that basePart is a SimPart
    sim_part: NXOpen.CAE.SimPart = cast(NXOpen.CAE.SimPart, base_part) # explicit casting makes it clear
    sim_simulation: NXOpen.CAE.SimSimulation = sim_part.Simulation

    # get the requested solution if it exists
    sim_solution: NXOpen.CAE.SimSolution = get_solution(solution_name)
    if sim_solution == None:
        # Solution not found
        the_lw.WriteFullline("AddLoadToSubcase: Solution with name " + solution_name + " not found!")
        return
    
    # check if the subcase exists in the given solution
    sim_solution_step: Optional[NXOpen.CAE.SimSolutionStep] = None
    for i in range(sim_solution.StepCount):
        if sim_solution.GetStepByIndex(i).Name.lower() == subcase_name.lower():
            # subcase exists
            sim_solution_step = sim_solution.GetStepByIndex(i)
    
    if sim_solution_step == None:
        the_lw.WriteFullline("AddLoadToSubcase: subcase with name " + subcase_name + " not found in solution " + solution_name + "!")
        return

    # get the requested load if it exists
    sim_load: List[NXOpen.CAE.SimLoad] = [item for item in sim_simulation.Loads if item.Name.lower() == load_name.lower()]
    if len(sim_load) == 0:
        # Load not found
        the_lw.WriteFullline("AddLoadToSubcase: Load with name " + load_name + " not found!")
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
    sim_constraint: List[NXOpen.CAE.SimSolution] = [item for item in sim_simulation.Solutions if item.Name.lower() == solution_name.lower()]
    if len(sim_constraint) == 0:
        # Constraint with the given name not found
        the_lw.WriteFullline("AddConstraintToSolution: constraint with name " + constraint_name + " not found!")
        return

    # add constraint to solution
    sim_solution[0].AddBc(sim_constraint[0])


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
            return sim_solution.GetStepByIndex(i)
    
    # create the subcase with the given name but don't activate it
    return sim_solution[0].CreateStep(0, False, subcase_name)


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
            # default does also not exist. Create it
            bulk_data_property_table = sim_part.ModelingObjectPropertyTables.CreateModelingObjectPropertyTable("Bulk Data Echo Request", "NX NASTRAN - Structural", "NX NASTRAN", "Bulk Data Echo Request1", 1000)

    property_table.SetNamedPropertyTablePropertyValue("Bulk Data Echo Request", bulk_data_property_table)

    # Look for a ModelingObjectPropertyTable with the given name or the default name "Structural Output Requests1"
    output_requests_property_table: List[NXOpen.CAE.ModelingObjectPropertyTable] = [item for item in sim_part.ModelingObjectPropertyTables if item.Name.lower() == output_requests.lower()]
    if len(output_requests_property_table) == 0:
        # did not find ModelinObjectPropertyTable with name "Bulk Data Echo REquest1"
        the_lw.WriteFullline("Warning: could not find Output Requests with name " + output_requests + ". Applying default one.")
        # check if default exists
        output_requests_property_table = [item for item in sim_part.ModelingObjectPropertyTables if item.Name.lower() == "Structural Output Requests1".lower()]
        if len(output_requests_property_table) == 0:
            # default does also not exist. Create it
            output_requests_property_table = sim_part.ModelingObjectPropertyTables.CreateModelingObjectPropertyTable("Structural Output Requests", "NX NASTRAN - Structural", "NX NASTRAN", "Bulk Data Echo Request1", 1001)
            # set Von Mises stress location to corner
            output_requests_property_table.PropertyTable.SetIntegerPropertyValue("Stress - Location", 1)


    property_table.SetNamedPropertyTablePropertyValue("Output Requests", output_requests_property_table)

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
    sim_solutions: List[NXOpen.CAE.SimSolution] = sim_simulation.Solutions.ToArray()

    sim_solution: List[NXOpen.CAE.SimSolution] = [item for item in sim_solutions if item.Name.lower() == solution_name.lower()]
    if len(sim_solution) == 0:
        # solution with the given name not found
        return None
    
    # return the first simSolution with the requested name
    return sim_solution[0]
