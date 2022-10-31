# ---LICENSE----------------------
"""
    Copyright 2022 Travel Modelling Group, Department of Civil Engineering, University of Toronto

    This file is part of the TMG Toolbox.

    The TMG Toolbox is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    The TMG Toolbox is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with the TMG Toolbox.  If not, see <http://www.gnu.org/licenses/>.
"""

# ---METADATA---------------------
"""
Toll-Based Road Assignment

    Authors: David King, Eric Miller

    Latest revision by: dKingII
    
    Executes a multi-class road assignment which allows for the generalized penalty of road tolls.
    
    V 1.0.0

    V 1.1.0 Added link volume attributes for increased resolution of analysis.

    V 1.1.1 Updated to allow for multi-threaded matrix calcs in 4.2.1+

    V 2.0.0 Refactored to work with XTMF2/TMGToolbox2 on 2021-10-21 by williamsDiogu      

    V 2.0.1 Updated to receive JSON object parameters from XTMX2

    V 2.0.2 Updated to receive JSON file parameters from Python API call

"""
import inro.modeller as _m
import multiprocessing

_m.InstanceType = object
_m.ListType = list
_m.TupleType = object

_trace = _m.logbook_trace
_MODELLER = _m.Modeller()  # Instantiate Modeller once.
_util = _MODELLER.module("tmg2.utilities.general_utilities")
EMME_VERSION = _util.get_emme_version(tuple)

matrix_calc_tool = _MODELLER.tool("inro.emme.matrix_calculation.matrix_calculator")
network_calculation_tool = _MODELLER.tool("inro.emme.network_calculation.network_calculator")
traffic_assignment_tool = _MODELLER.tool("inro.emme.traffic_assignment.sola_traffic_assignment")
extra_parameter_tool = _MODELLER.tool("inro.emme.traffic_assignment.set_extra_function_parameters")
delete_matrix = _MODELLER.tool("inro.emme.data.matrix.delete_matrix")


class AssignTraffic(_m.Tool()):
    version = "2.0.2"
    tool_run_msg = ""
    # For progress reporting, enter the integer number of tasks here
    number_of_tasks = 4
    # Tool Input Parameters
    #    Only those parameters necessary for Modeller and/or XTMF to dock with
    #    need to be placed here. Internal parameters (such as lists and dicts)
    #    get initialized during construction (__init__)
    # Parameters can takes in a json file name depending on entry point(either through XTMF or api calls )
    parameters = _m.Attribute(str)
    number_of_processors = _m.Attribute(int)

    def __init__(self):
        self._tracker = _util.progress_tracker(self.number_of_tasks)
        self.scenario = _MODELLER.scenario
        self.number_of_processors = multiprocessing.cpu_count()
        self._traffic_util = _util.assign_traffic_util()

    def page(self):
        pb = _m.ToolPageBuilder(
            self,
            title="Multi-Class Road Assignment",
            description="Cannot be called from Modeller.",
            runnable=False,
            branding_text="XTMF",
        )
        return pb.render()

    def __call__(self, parameters):
        scenario = _util.load_scenario(parameters["scenario_number"])
        try:
            self._execute(scenario, parameters)
        except Exception as e:
            raise Exception(_util.format_reverse_stack())

    def run_xtmf(self, parameters):
        scenario = _util.load_scenario(parameters["scenario_number"])

        try:
            self._execute(scenario, parameters)
        except Exception as e:
            raise Exception(_util.format_reverse_stack())

    def _execute(self, scenario, parameters):
        """
        Definition of common names:
            - matrix_name (type(str)): e.g. cost_matrix, demand_matrix etc.
            - matrix_id (type(str)): e.g. mf0, mf2 etc.
                Note - matrix id expects either of ms, mo, md, or mf, before the number.
            - temp_matrix_list: keeps track (by appending to it) of all temporary matrices
                created and deletes them with the help of a temp_matrix_manager() at the at
                the end of each run (including when code catches an error)
            - temp_attributes_list: keeps track of all temporary attributes created and deletes
                them at the at the end of each run (including when code catches an error)
        """
        load_input_matrix_list = self._traffic_util.load_input_matrices(parameters, "demand_matrix")
        load_output_matrix_dict = self._traffic_util.load_output_matrices(
            parameters,
            matrix_name=["cost_matrix", "time_matrix", "toll_matrix"],
        )
        with _trace(
            name="%s (%s v%s)" % (parameters["run_title"], self.__class__.__name__, self.version),
            attributes=self._traffic_util.load_atts(scenario, parameters, self.__MODELLER_NAMESPACE__),
        ):
            self._tracker.reset()
            with _util.temporary_matrix_manager() as temp_matrix_list:
                demand_matrix_list = self._traffic_util.init_input_matrices(load_input_matrix_list, temp_matrix_list)
                cost_matrix_list = self._traffic_util.init_output_matrices(
                    load_output_matrix_dict,
                    temp_matrix_list,
                    matrix_name="cost_matrix",
                    description="",
                )
                time_matrix_list = self._traffic_util.init_output_matrices(
                    load_output_matrix_dict,
                    temp_matrix_list,
                    matrix_name="time_matrix",
                    description="",
                )
                toll_matrix_list = self._traffic_util.init_output_matrices(
                    load_output_matrix_dict,
                    temp_matrix_list,
                    matrix_name="toll_matrix",
                    description="",
                )
                peak_hour_matrix_list = self._traffic_util.init_temp_peak_hour_matrix(parameters, temp_matrix_list)
                self._tracker.complete_subtask()

                with _util.temporary_attribute_manager(scenario) as temp_attribute_list:
                    time_attribute_list = self._traffic_util.create_time_attribute_list(
                        scenario, demand_matrix_list, temp_attribute_list
                    )
                    cost_attribute_list = self._traffic_util.create_cost_attribute_list(
                        scenario, demand_matrix_list, temp_attribute_list
                    )
                    transit_attribute_list = self._traffic_util.create_transit_traffic_attribute_list(
                        scenario, demand_matrix_list, temp_attribute_list
                    )
                    # Create volume attributes
                    for tc in parameters["traffic_classes"]:
                        self._traffic_util.create_volume_attribute(scenario, tc["volume_attribute"])
                    # Calculate transit background traffic
                    self._traffic_util.calculate_transit_background_traffic(
                        scenario,
                        parameters,
                        self._tracker,
                    )
                    # Calculate applied toll factor
                    applied_toll_factor_list = self._traffic_util.calculate_applied_toll_factor(parameters)
                    # Calculate link costs
                    self._traffic_util.calculate_link_cost(
                        scenario,
                        parameters,
                        demand_matrix_list,
                        applied_toll_factor_list,
                        cost_attribute_list,
                        self._tracker,
                    )
                    # Calculate peak hour matrix
                    self._traffic_util.calculate_peak_hour_matrices(
                        scenario,
                        parameters,
                        demand_matrix_list,
                        peak_hour_matrix_list,
                        self._tracker,
                        self.number_of_processors,
                    )
                    self._tracker.complete_subtask()

                    # Assign traffic to road network
                    with _m.logbook_trace("Running Road Assignments."):
                        completed_path_analysis = False
                        if completed_path_analysis is False:
                            attributes = self._traffic_util.load_attribute_list(parameters, demand_matrix_list)
                            attribute_list = attributes[0]
                            volume_attribute_list = attributes[1]
                            mode_list = self._traffic_util.load_mode_list(parameters)

                            sola_spec = self._traffic_util.get_primary_SOLA_spec(
                                demand_matrix_list,
                                peak_hour_matrix_list,
                                applied_toll_factor_list,
                                mode_list,
                                volume_attribute_list,
                                cost_attribute_list,
                                time_matrix_list,
                                attribute_list,
                                None,
                                None,
                                None,
                                None,
                                None,
                                None,
                                None,
                                parameters,
                                multiprocessing,
                            )
                            report = self._tracker.run_tool(traffic_assignment_tool, sola_spec, scenario=scenario)
                        checked = self._load_stopping_criteria(report)
                        number = checked[0]
                        stopping_criterion = checked[1]
                        value = checked[2]

                        print("Primary assignment complete at %s iterations." % number)
                        print("Stopping criterion was %s with a value of %s." % (stopping_criterion, value))

    def _load_stopping_criteria(self, report):
        stopping_criterion = report["stopping_criterion"]
        iterations = report["iterations"]
        if len(iterations) > 0:
            final_iteration = iterations[-1]
        else:
            final_iteration = {"number": 0}
            stopping_criterion == "MAX_ITERATIONS"
        number = final_iteration["number"]
        if stopping_criterion == "MAX_ITERATIONS":
            value = final_iteration["number"]
        elif stopping_criterion == "RELATIVE_GAP":
            value = final_iteration["gaps"]["relative"]
        elif stopping_criterion == "NORMALIZED_GAP":
            value = final_iteration["gaps"]["normalized"]
        elif stopping_criterion == "BEST_RELATIVE_GAP":
            value = final_iteration["gaps"]["best_relative"]
        else:
            value = "undefined"
        return number, stopping_criterion, value

    @_m.method(return_type=_m.TupleType)
    def percent_completed(self):
        return self._tracker.get_progress()

    @_m.method(return_type=str)
    def tool_run_msg_status(self):
        return self.tool_run_msg
