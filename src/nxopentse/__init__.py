# the below should be removed, in combination with setuptools in the pyproject.toml
# such that only the imports from the subpackages are available.
# this should make nxopentse much more clean
from .cad import code
from .cae import postprocessing, preprocessing, solving, unversal_file
from .tools import excel, general, vector_arithmetic


# from .cad.code import nx_hello,\
#                     create_point, \
#                     get_all_bodies,\
#                     get_faces_of_type, \
#                     get_all_points,\
#                     get_all_features,\
#                     get_feature_by_name,\
#                     get_all_point_features,\
#                     get_point_with_feature_name, \
#                     create_cylinder, \
#                     create_intersect_feature, \
#                     get_faces_of_body, \
#                     get_area_faces_with_color, \
#                     get_area_faces_with_color, \
#                     create_line, \
#                     delete_feature

# from .cae.postprocessing import PostInput, \
#                             get_solution, \
#                             load_results, \
#                             get_results_units, \
#                             get_result_types, \
#                             delete_companion_result, \
#                             get_sim_result_reference, \
#                             check_post_input, \
#                             check_post_input_identifiers, \
#                             check_unv_file_name, \
#                             get_full_result_names, \
#                             combine_results, \
#                             export_result, \
#                             get_result_paramaters, \
#                             envelope_results, \
#                             envelope_solution, \
#                             get_nodal_value, \
#                             get_nodal_values, \
#                             get_element_nodal_value, \
#                             add_companion_result, \
#                             write_submodel_data_to_file

# from .cae.preprocessing import create_node, \
#                             create_nodal_constraint, \
#                             create_nodal_force_default_name, \
#                             create_nodal_force, \
#                             create_nodal_moment, \
#                             add_solver_set_to_subcase, \
#                             add_load_to_solver_set, \
#                             create_solver_set, \
#                             add_load_to_subcase, \
#                             add_constraint_to_solution, \
#                             add_constraint_to_subcase, \
#                             create_subcase, \
#                             create_solution, \
#                             get_solution, \
#                             set_solution_property, \
#                             get_nodes_in_group, \
#                             create_displacement_field

# from .cae.solving import solve_solution, \
#                             solve_all_solutions, \
#                             solve_dat_file


# from .tools.excel import hello

# from .tools.general import create_full_path

# __add__ = [nx_hello, 
#            create_point, 
#            get_all_bodies, 
#            get_faces_of_type, 
#            get_all_points, 
#            get_all_features, 
#            get_feature_by_name, 
#            get_all_point_features, 
#            get_point_with_feature_name, 
#            create_cylinder, 
#            create_intersect_feature, 
#            get_faces_of_body, 
#            get_area_faces_with_color, 
#            get_area_faces_with_color, 
#            create_line, delete_feature, 
#            PostInput, 
#            get_solution, 
#            load_results, 
#            get_results_units, 
#            get_result_types, 
#            delete_companion_result, 
#            get_sim_result_reference, 
#            check_post_input, 
#            check_post_input_identifiers, 
#            check_unv_file_name, 
#            get_full_result_names, 
#            combine_results, 
#            export_result, 
#            get_result_paramaters, 
#            envelope_results, 
#            envelope_solution, 
#            get_nodal_value, 
#            get_nodal_values, 
#            get_element_nodal_value, 
#            add_companion_result, 
#            write_submodel_data_to_file, 
#            create_node, 
#            create_nodal_constraint, 
#            create_nodal_force_default_name, 
#            create_nodal_force, 
#            create_nodal_moment, 
#            add_solver_set_to_subcase, 
#            add_load_to_solver_set, 
#            create_solver_set, 
#            add_load_to_subcase, 
#            add_constraint_to_solution, 
#            add_constraint_to_subcase, 
#            create_subcase, 
#            create_solution, 
#            get_solution, 
#            set_solution_property, 
#            get_nodes_in_group, 
#            create_displacement_field, 
#            solve_solution, 
#            solve_all_solutions, 
#            solve_dat_file, 
#            hello, 
#            create_full_path]
