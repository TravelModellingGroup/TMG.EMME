# ---LICENSE----------------------
"""
    Copyright 2021 Travel Modelling Group, Department of Civil Engineering, University of Toronto

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

"""

import inro.modeller as _m
import traceback as _traceback
from contextlib import contextmanager
import multiprocessing

_m.InstanceType = object
_m.ListType = list
_m.TupleType = object

_MODELLER = _m.Modeller()  # Instantiate Modeller once.
_util = _MODELLER.module("tmg2.utilities.general_utilities")
EMME_VERSION = _util.get_emme_version(tuple)

matrix_calc_tool = _MODELLER.tool("inro.emme.matrix_calculation.matrix_calculator")
network_calculation_tool = _MODELLER.tool(
    "inro.emme.network_calculation.network_calculator"
)
traffic_assignment_tool = _MODELLER.tool(
    "inro.emme.traffic_assignment.sola_traffic_assignment"
)

delete_matrix = _MODELLER.tool("inro.emme.data.matrix.delete_matrix")


@contextmanager
def blankManager(obj):
    try:
        yield obj
    finally:
        pass


class AssignTraffic(_m.Tool()):
    version = "1.1.1"
    tool_run_msg = ""
    # For progress reporting, enter the integer number of tasks here
    number_of_tasks = 4

    # Tool Input Parameters
    #    Only those parameters neccessary for Modeller and/or XTMF to dock with
    #    need to be placed here. Internal parameters (such as lists and dicts)
    #    get intitialized during construction (__init__)
    # ---Variable definitions
    # scenario = _m.Attribute(_m.InstanceType)
    # # Parameters for AssignTraffic (Multi-Class Road Assignment in TMGToolbox1)
    # scenario_number = _m.Attribute(int)
    # run_title = _m.Attribute(str)
    # iterations = _m.Attribute(int)
    # r_gap = _m.Attribute(float)
    # br_gap = _m.Attribute(float)
    # norm_gap = _m.Attribute(float)
    # performance_flag = _m.Attribute(bool)
    # peak_hour_factor = _m.Attribute(float)
    # sola_flag = _m.Attribute(bool)
    # background_transit = _m.Attribute(str)

    # # Parameters for Traffic Class
    # name = _m.Attribute(str)
    # mode = _m.Attribute(str)
    # demand_matrix = _m.Attribute(str)
    # times_matrix = _m.Attribute(int)
    # cost_matrix = _m.Attribute(int)
    # tolls_matrix = _m.Attribute(int)
    # link_toll_attribute_id = _m.Attribute(str)
    # link_cost = _m.Attribute(float)
    # toll_weight = _m.Attribute(float)
    # volume_attribute = _m.Attribute(str)

    # # Parameters for Path Analysis
    # result_attributes = _m.Attribute(str)
    # analysis_attributes = _m.Attribute(str)
    # analysis_attributes_matrix = _m.Attribute(str)
    # aggregation_operator = _m.Attribute(str)
    # aggregation_matrix = _m.Attribute(int)
    # lower_bound = _m.Attribute(str)
    # upper_bound = _m.Attribute(str)
    # path_selection = _m.Attribute(str)
    # multiply_path_prop_by_demand = _m.Attribute(str)
    # multiply_path_prop_by_value = _m.Attribute(str)

    number_of_processors = _m.Attribute(int)

    def __init__(self):
        self._tracker = _util.progress_tracker(self.number_of_tasks)
        self.scenario = _MODELLER.scenario
        self.number_of_processors = multiprocessing.cpu_count()

    def page(self):
        pb = _m.ToolPageBuilder(
            self,
            title="Multi-Class Road Assignment",
            description="Cannot be called from Modeller.",
            runnable=False,
            branding_text="XTMF",
        )
        return pb.render()

    def __call__(self):
        # ---1 Set up Scenario
        # self._load_scenario(scenario_number)

        # TODO: Process parameters for __call__
        pass

    def run_xtmf(self, parameters):
        scenario = self._load_scenario(parameters["scenario_number"])

        try:
            self._execute(scenario, parameters)
        except Exception as e:
            raise Exception(_util.format_reverse_stack())

    def _execute(self, scenario, parameters):
        # Initialize non-temporary matrices (input matrices)
        demand_matrix_list = self._init_non_temp_matrices(parameters)
        # Initialize temporary matrices (output matrices)
        temp_matrix_list = self._init_temp_matrix(parameters)

        with self._temp_matrix_manager(temp_matrix_list) as temp_matrix:

            self._tracker.complete_subtask()

            time_attribute_list = self._temp_time_attribute(
                scenario, demand_matrix_list
            )
            with self._time_attribute_manager(time_attribute_list) as time_attribute:
                ...

    # ---SUB FUNCTIONS-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

    def _load_scenario(self, scenario_number):
        scenario = _m.Modeller().emmebank.scenario(scenario_number)
        if scenario is None:
            raise Exception("Scenario %s was not found!" % scenario_number)
        return scenario

    def _get_atts(self, parameters):
        ...

    def _init_non_temp_matrices(self, parameters):
        checked_matrix_list = []
        demand_matrix_list = []

        # Check all non-mf0 matrix
        for c in parameters["traffic_classes"]:
            demand_string = str(c["demand_matrix"]).lower()
            if demand_string == "mf0":
                checked_matrix_list.append(demand_string)
            elif (
                demand_string != "mf0"
                and _MODELLER.emmebank.matrix(demand_string) is None
            ):
                raise Exception("Matrix %s was not found!" % demand_string)
            elif str(_MODELLER.emmebank.matrix(demand_string)) == demand_string:
                checked_matrix_list.append(demand_string)
            else:
                raise Exception("Matrix %s was not found!" % demand_string)

        # Initializing all non-specified matrices and returning all
        for dm in checked_matrix_list:
            if dm == "mf0":
                demand_matrix = _util.initialize_matrix(matrix_type="FULL")
                demand_matrix_list.append(_MODELLER.emmebank.matrix(demand_matrix.id))
            else:
                demand_matrix_list.append(_MODELLER.emmebank.matrix(dm))

        return demand_matrix_list

    def _init_temp_matrix(self, parameters):
        temp_mtx_list = []
        for temp_mtx in parameters["traffic_classes"]:
            # Check Cost Matrix
            cost_str = str(temp_mtx["cost_matrix"])
            if cost_str == "mf0":
                temp_mtx_list.append(None)
            elif cost_str != "mf0" and _MODELLER.emmebank.matrix(cost_str) is None:
                cost_mtx = _util.initialize_matrix(
                    cost_str,
                    name="acost",
                    description="AUTO COST FOR CLASS: %s" % temp_mtx["name"],
                )
                temp_mtx_list.append(cost_mtx)
            elif str(_MODELLER.emmebank.matrix(cost_str)) == cost_str:
                cost_mtx = _MODELLER.emmebank.matrix(cost_str)
                temp_mtx_list.append(cost_mtx)
            else:
                raise Exception("Matrix %s was not found!" % cost_str)

            # Check Time Matrix
            time_str = str(temp_mtx["time_matrix"])
            if time_str == "mf0":
                temp_mtx_list.append(None)
            elif time_str != "mf0" and _MODELLER.emmebank.matrix(time_str) is None:
                time_mtx = _util.initialize_matrix(
                    time_str,
                    name="aivtt",
                    description="AUTO TIME FOR CLASS: %s" % temp_mtx["name"],
                )
                temp_mtx_list.append(time_mtx)
            elif str(_MODELLER.emmebank.matrix(time_str)) == time_str:
                time_mtx = _MODELLER.emmebank.matrix(time_str)
                temp_mtx_list.append(time_mtx)
            else:
                raise Exception("Matrix %s was not found!" % time_str)

            # Check Toll Matrix
            toll_str = str(temp_mtx["toll_matrix"])
            if toll_str == "mf0":
                temp_mtx_list.append(None)
            elif toll_str != "mf0" and _MODELLER.emmebank.matrix(toll_str) is None:
                toll_mtx = _util.initialize_matrix(
                    toll_str,
                    name="atoll",
                    description="AUTO TOLL FOR CLASS: %s" % temp_mtx["name"],
                )
                temp_mtx_list.append(toll_mtx)
            elif str(_MODELLER.emmebank.matrix(toll_str)) == toll_str:
                toll_mtx = _MODELLER.emmebank.matrix(toll_str)
                temp_mtx_list.append(toll_mtx)
            else:
                raise Exception("Matrix %s was not found!" % toll_str)

        return temp_mtx_list

    def _temp_time_attribute(self, scenario, demand_matrix_list):
        time_attribute_list = []
        for i in range(len(self.demand_matrix_list)):
            at = "@ltime" + str(i + 1)
            time_attribute = scenario.extra_attribute(at)
            if time_attribute is None:
                # @ltime hasn't been defined
                _m.logbook_write(
                    "Creating temporary link time attribute '@ltime" + str(i + 1) + "'."
                )
                time_attribute = scenario.create_extra_attribute(
                    "LINK", at, default_value=0
                )
                time_attribute_list.append(time_attribute)
            elif scenario.extra_attribute(at).type != "LINK":
                # '@ltime' exists, but is not a link attribute
                _m.logbook_write(
                    "Creating temporary link time attribute '@ltime" + str(i + 2) + "'."
                )
                time_attribute = scenario.create_extra_attribute(
                    "LINK", at, default_value=0
                )
                time_attribute_list.append(time_attribute)
            elif time_attribute is not None:
                time_attribute = scenario.create_extra_attribute("LINK", at).initialize
                time_attribute_list.append(time_attribute)
                _m.logbook_write("Initialized link time attribute to value of 0.")
            else:
                raise Exception(
                    "Extra link time attribute %s was not found!" % time_attribute
                )

        return time_attribute_list
        ...

    def _temp_cost_attribute(self, scenario, parameters):
        ...

    def _temp_transit_traffic_attribute(self, scenario, parameters):
        ...

    # ---CONTEXT MANAGERS---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

    @contextmanager
    def _temp_matrix_manager(self, temp_matrix_list=[]):
        """
        Matrix objects created & added to this matrix list are deleted when this manager exits.
        """
        try:
            yield temp_matrix_list
        finally:
            for matrix in temp_matrix_list:
                if matrix is not None:
                    _m.logbook_write("Deleting temporary matrix '%s': " % matrix.id)
                    _MODELLER.emmebank.delete_matrix(matrix.id)

    @contextmanager
    def _time_attribute_manager(self, scenario, time_attribute_list=[]):

        try:
            yield time_attribute_list
        finally:
            for time_attribute in time_attribute_list:
                if time_attribute is not None:
                    _m.logbook_write("Deleting temporary link time attribute.")
                    scenario.delete_extra_attribute(time_attribute.id)

    @contextmanager
    def _cost_attribute_manager(self, scenario, cost_attribute_list=[]):

        try:
            yield cost_attribute_list
        finally:
            for cost_attribute in cost_attribute_list:
                if cost_attribute is not None:
                    _m.logbook_write("Deleting temporary link cost attribute.")
                    scenario.delete_extra_attribute(cost_attribute.id)

    @contextmanager
    def _transit_traffic_attribute_manager(self, scenario, traffic_attribute_list=[]):

        try:
            yield traffic_attribute_list
        finally:
            for bg_traffic_attribute in traffic_attribute_list:
                if bg_traffic_attribute is not None:
                    _m.logbook_write(
                        "Deleting temporary link transit traffic attribute."
                    )
                    scenario.delete_extra_attribute(bg_traffic_attribute.id)
