import os
import subprocess
from typing import List, cast, Optional, Union

import NXOpen
import NXOpen.CAE
import NXOpen.UF

from ..tools import * # so we can use these


the_session: NXOpen.Session = NXOpen.Session.GetSession()
the_uf_session: NXOpen.UF.UFSession = NXOpen.UF.UFSession.GetUFSession()
the_lw: NXOpen.ListingWindow = the_session.ListingWindow


def solve_solution(solution_name: str):
    """This function solves a solution with the given name, in the active sim file

    Parameters
    ----------
    solution_name: str
        Name of the solution to solve
    """
    base_part: NXOpen.BasePart = the_session.Parts.BaseWork
    if not isinstance(NXOpen.CAE.SimPart, base_part):
        the_lw.WriteFullline("solve_solution needs to start from a .sim file. Exiting")
        return
    
    the_lw.WriteFullline("Solving " + solution_name)
    sim_part: NXOpen.CAE.SimPart = cast(NXOpen.CAE.SimPart, base_part)

    # get the requested solution
    sim_solutions: List[NXOpen.CAE.SimSolution] = [item for item in sim_part.Simulation.Solutions]
    sim_solution: List[NXOpen.CAE.SimSolution] = [item for item in sim_solutions if item.Name.lower() == solution_name.lower()]
    if sim_solution == None:
        the_lw.WriteFullline("Solution with name " + solution_name + " could not be found in " + sim_part.FullPath)
        return
    else:
        sim_solution = sim_solution[0]

    # solve the solution
    chain: List[NXOpen.CAE.SimSolution] = [sim_solution]
    sim_solve_manager: NXOpen.CAE.SimSolveManager = NXOpen.CAE.SimSolveManager.GetSimSolveManager(the_session)
    # Not sure if the following returns a tuple in Python. In C#, additional parameters are returned through pass by reference using the out keyword
    sim_solve_manager.SolveChainOfSolutions(chain, NXOpen.CAE.SimSolution.SolveOption.Solve, NXOpen.CAE.SimSolution.SetupCheckOption.DoNotCheck, NXOpen.CAE.SimSolution.SolveMode.Foreground)

    # user feedback
    the_lw.WriteFullline("Solved solution " + solution_name)
    sim_solve_manager.SolveChainOfSolutions(chain, NXOpen.CAE.SimSolution.SolveOption.Solve, NXOpen.CAE.SimSolution.SetupCheckOption.DoNotCheck, NXOpen.CAE.SimSolution.SolveMode.Foreground)


def solve_all_solutions():
    """This function solves all solutions in the active sim file
    """
    # Note: don't loop over the solutions and solve. This will give a memory access violation error, but will still solve.
    # The error can be avoided by making the simSolveManager a global variable, so it's not on each call.
    base_part: NXOpen.BasePart = the_session.Parts.BaseWork
    if not isinstance(NXOpen.CAE.SimPart, base_part):
        the_lw.WriteFullline("solve_all_solutions needs to start from a .sim file. Exiting")
        return
    the_lw.WriteFullline("Solving all solutions:")
    sim_solve_manager: NXOpen.CAE.SimSolveManager = NXOpen.CAE.SimSolveManager.GetSimSolveManager(the_session)
    sim_solve_manager.SolveAllSolutions(NXOpen.CAE.SimSolution.SolveOption.Solve, NXOpen.CAE.SimSolution.SetupCheckOption.DoNotCheck, NXOpen.CAE.SimSolution.SolveMode.Foreground)


def solve_dat_file(dat_file: str):
    """This function solves a .dat file by directly calling the nastran.exe executable.
        It takes the location of the nastran.exe executable form the environmental variable UGII_NX_NASTRAN.
        By directly calling the nastran executable, a standalone license for the executable is required!
        Running this with a desktop license wil result in an error:
        "Could not check out license for module: Simcenter Nastran Basic"

    Parameters
    ----------
    dat_file: str
        The full path of the .dat file to be solved. 
        If no extension is provided, .dat is assumed.
        If no directory is provided, assumed same as the sim file
    """
    # get the location nastran.exe via the environmental variable
    UGII_NX_NASTRAN: str = the_session.GetEnvironmentVariableValue("UGII_NX_NASTRAN")
    the_lw.WriteFullline(UGII_NX_NASTRAN)

    # process dat file for path and execution
    full_dat_file: str = create_full_path(dat_file, ".dat")

    # change working directory to the location of the .dat file. 
    # So that this is where the solve happens.
    cwd = os.getcwd()
    os.chdir(os.path.dirname(full_dat_file))
    
    # solve the .dat file.
    result = subprocess.run([UGII_NX_NASTRAN, full_dat_file])
    print(result)
    
    # return to original cwd
    os.chdir(cwd)
