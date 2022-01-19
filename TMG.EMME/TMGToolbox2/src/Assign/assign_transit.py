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
TMG Transit Assignment Tool
    Executes a multi-class congested transit assignment procedure for GTAModel V4.0+. 

    Hard-coded assumptions: 
    -  Boarding penalties are assumed stored in UT3
    -  The congestion term is stored in US3
    -  In-vehicle time perception is 1.0
    -  Unless specified, all available transit modes will be used.
    
    This tool is only compatible with Emme 4.2 and later versions

    Authors: Eric Miller

    Latest revision by: WilliamsDiogu
    
    Executes a transit assignment which allows for surface transit speed updating.
    
    V 1.0.0 

    V 2.0.0 Refactored to work with XTMF2/TMGToolbox2 on 2021-12-15 by williamsDiogu      

    V 2.0.1 Updated to receive JSON object parameters from XTMX2

    V 2.0.2 Updated to receive JSON file parameters from Python API call
"""

import traceback as _traceback
import time as _time
import multiprocessing
from typing import DefaultDict
import inro.modeller as _m
from contextlib import contextmanager
import random
import json
import csv


_m.TupleType = object
_m.ListType = list
_m.InstanceType = object

_trace = _m.logbook_trace
_write = _m.logbook_write
_MODELLER = _m.Modeller()
_bank = _MODELLER.emmebank
_util = _MODELLER.module("tmg2.utilities.general_utilities")
_tmg_tpb = _MODELLER.module("tmg2.utilities.TMG_tool_page_builder")
_net_edit = _MODELLER.module("tmg2.utilities.network_editing")
# congestedAssignmentTool = _MODELLER.tool('inro.emme.transit_assignment.congested_transit_assignment')
_db_utils = _MODELLER.module("inro.emme.utility.database_utilities")
extended_assignment_tool = _MODELLER.tool(
    "inro.emme.transit_assignment.extended_transit_assignment"
)
network_calc_tool = _MODELLER.tool("inro.emme.network_calculation.network_calculator")
network_results_tool = _MODELLER.tool(
    "inro.emme.transit_assignment.extended.network_results"
)
matrix_results_tool = _MODELLER.tool(
    "inro.emme.transit_assignment.extended.matrix_results"
)
strategy_analysis_tool = _MODELLER.tool(
    "inro.emme.transit_assignment.extended.strategy_based_analysis"
)
matrix_calc_tool = _MODELLER.tool("inro.emme.matrix_calculation.matrix_calculator")
null_pointer_exception = _util.null_pointer_exception

EMME_VERSION = _util.get_emme_version(tuple)


class AssignTransit(_m.Tool()):
    version = "2.0.0"
    tool_run_msg = ""
    number_of_tasks = 15

    def __init__(self):
        self._tracker = _util.progress_tracker(self.number_of_tasks)
        self.scenario = _MODELLER.scenario
        self.number_of_processors = multiprocessing.cpu_count()

    def page(self):
        if EMME_VERSION < (4, 1, 5):
            raise ValueError("Tool not compatible. Please upgrade to version 4.1.5+")
        pb = _tmg_tpb.TmgToolPageBuilder(
            self,
            title="Multi-Class Transit Assignment v%s" % self.version,
            description="Executes a congested transit assignment procedure\
                        for GTAModel V4.0.\
                        <br><br><b>Cannot be called from Modeller.</b>\
                        <br><br>Hard-coded assumptions:\
                        <ul><li> Boarding penalties are assumed stored in <b>UT3</b></li>\
                        <li> The congestion term is stored in <b>US3</b></li>\
                        <li> In-vehicle time perception is 1.0</li>\
                        <li> All available transit modes will be used.</li>\
                        </ul>\
                        <font color='red'>This tool is only compatible with Emme 4.1.5 and later versions</font>",
            runnable=False,
            branding_text="- TMG Toolbox",
        )
        return pb.render()

    def run(self):
        ...

    def __call__(self, parameters):
        scenario = self._load_scenario(parameters["scenario_number"])
        try:
            self._execute(scenario, parameters)
        except Exception as e:
            raise Exception(_util.format_reverse_stack())

    def run_xtmf(self, parameters):
        scenario = self._load_scenario(parameters["scenario_number"])
        try:
            self._execute(scenario, parameters)
        except Exception as e:
            raise Exception(_util.format_reverse_stack())

    def _execute(self, scenario, parameters):
        load_input_matrix_list = self._load_input_matrices(parameters, "demand_matrix")
        load_output_matrix_dict = self._load_output_matrices(
            parameters,
            matrix_name=[
                "in_vehicle_time_matrix",
                "congestion_matrix",
                "walk_time_matrix",
                "wait_time_matrix",
                "fare_matrix",
                "board_penalty_matrix",
                "impedance_matrix",
            ],
        )

        with _trace(
            name="(%s v%s)" % (self.__class__.__name__, self.version),
            attributes=self._load_atts(scenario, parameters),
        ):
            self._tracker.reset()
            with _trace("Checking travel time functions..."):
                changes = self._heal_travel_time_functions()
                if changes == 0:
                    _write("No problems were found")
            with self._temp_matrix_manager() as temp_matrix_list:
                # Initialize matrices with matrix ID = "mf0" not loaded in load_input_matrix_list
                demand_matrix_list = self._init_input_matrices(
                    load_input_matrix_list, temp_matrix_list
                )
                in_vehicle_time_matrix_list = self._init_output_matrices(
                    load_output_matrix_dict,
                    temp_matrix_list,
                    matrix_name="in_vehicle_time_matrix",
                    description="Transit in-vehicle travel times.",
                )
                congestion_matrix_list = self._init_output_matrices(
                    load_output_matrix_dict,
                    temp_matrix_list,
                    matrix_name="congestion_matrix",
                    description="Transit in-vehicle congestion.",
                )
                walk_time_matrix_list = self._init_output_matrices(
                    load_output_matrix_dict,
                    temp_matrix_list,
                    matrix_name="walk_time_matrix",
                    description="Transit total walk times.",
                )
                wait_time_matrix_list = self._init_output_matrices(
                    load_output_matrix_dict,
                    temp_matrix_list,
                    matrix_name="wait_time_matrix",
                    description="Transit total wait times.",
                )
                fare_matrix_list = self._init_output_matrices(
                    load_output_matrix_dict,
                    temp_matrix_list,
                    matrix_name="fare_matrix",
                    description="Transit total fares",
                )
                board_penalty_matrix_list = self._init_output_matrices(
                    load_output_matrix_dict,
                    temp_matrix_list,
                    matrix_name="board_penalty_matrix",
                    description="Transit total boarding penalties",
                )
                impedance_matrix_list = self._init_output_matrices(
                    load_output_matrix_dict,
                    temp_matrix_list,
                    matrix_name="impedance_matrix",
                    description="Transit Perceived Travel times",
                )
            self._change_walk_speed(scenario, parameters["walk_speed"])

    # ---LOAD - SUB FUNCTIONS -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    def _load_scenario(self, scenario_number):
        scenario = _m.Modeller().emmebank.scenario(scenario_number)
        if scenario is None:
            raise Exception("Scenario %s was not found!" % scenario_number)
        return scenario

    def _load_atts(self, scenario, parameters):
        # TODO: Load atts
        atts = {}
        return atts

    # ---INITIALIZE - SUB-FUNCTIONS  -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    def _load_traffic_class_names(self, parameters):
        transit_classes = parameters["transit_classes"]
        class_list = [class_name["name"] for class_name in transit_classes]
        return class_list

    def _load_output_matrices(self, parameters, matrix_name=list):
        """
        This loads all (into a dictionary) output matrices by matrix_name list provided but
        assigns None to all zero matrices for later initialization
        """
        mtx_dict = {}
        transit_classes = parameters["transit_classes"]
        for i in range(0, len(matrix_name)):
            mtx_dict[matrix_name[i]] = [tc[matrix_name[i]] for tc in transit_classes]
        for mtx_name, mtx_ids in mtx_dict.items():
            mtx = [None if id == "mf0" else _bank.matrix(id) for id in mtx_ids]
            mtx_dict[mtx_name] = mtx
        return mtx_dict

    def _load_input_matrices(self, parameters, matrix_name):
        """
        Load input matrices creates and loads all (input) matrix into a list based on
        matrix_name supplied. E.g of matrix_name: "demand_matrix" and matrix_id: "mf2"
        """

        def exception(mtx_id):
            raise Exception("Matrix %s was not found!" % mtx_id)

        transit_classes = parameters["transit_classes"]
        mtx_name = matrix_name
        mtx_list = [
            _bank.matrix(tc[mtx_name])
            if tc[mtx_name] == "mf0" or _bank.matrix(tc[mtx_name]).id == tc[mtx_name]
            else exception(tc[mtx_name])
            for tc in transit_classes
        ]
        return mtx_list

    def _init_input_matrices(self, load_input_matrix_list, temp_matrix_list):
        input_matrix_list = []
        for mtx in load_input_matrix_list:
            if mtx == None:
                mtx = _util.initialize_matrix(matrix_type="FULL")
                input_matrix_list.append(_bank.matrix(mtx.id))
                temp_matrix_list.append(mtx)
            else:
                input_matrix_list.append(mtx)
        return input_matrix_list

    def _init_output_matrices(
        self,
        load_output_matrix_dict,
        temp_matrix_list,
        matrix_name="",
        description="",
    ):
        """
        Initiializes all output matrices provided. However, only creates temporary matrix for
        impedance matrices when matrix id is mf0 or none
        """
        output_matrix_list = []
        desc = "TRANSIT %s FOR CLASS" % (matrix_name.upper())
        if matrix_name in load_output_matrix_dict.keys():
            for mtx in load_output_matrix_dict[matrix_name]:
                if mtx != None:
                    matrix = _util.initialize_matrix(
                        name=matrix_name,
                        description=description if description != "" else desc,
                    )
                    output_matrix_list.append(matrix)
                else:
                    if matrix_name == "impedance_matrix":
                        _write('Creating Temporary Impedance Matrix "%s"', matrix_name)
                        matrix = _util.initialize_matrix(
                            default=0.0,
                            description=description if description != "" else desc,
                            matrix_type="FULL",
                        )
                        output_matrix_list.append(matrix)
                        temp_matrix_list.append(matrix)
                    else:
                        output_matrix_list.append(mtx)
        else:
            raise Exception(
                'Output matrix name "%s" provided does not exist', matrix_name
            )
        return output_matrix_list

    def _heal_travel_time_functions(self):
        changes = 0
        for function in _bank.functions():
            if function.type != "TRANSIT_TIME":
                continue
            cleaned_expression = function.expression.replace(" ", "")
            if "us3" in cleaned_expression:
                if cleaned_expression.endswith("*(1+us3)"):
                    index = cleaned_expression.find("*(1+us3)")
                    new_expression = cleaned_expression[:index]
                    function.expression = new_expression
                    print(
                        "Detected function %s with existing congestion term." % function
                    )
                    print("Original expression= '%s'" % cleaned_expression)
                    print("Healed expression= '%s'" % new_expression)
                    print("")
                    _write(
                        "Detected function %s with existing congestion term." % function
                    )
                    _write("Original expression= '%s'" % cleaned_expression)
                    _write("Healed expression= '%s'" % new_expression)
                    changes += 1
                else:
                    raise Exception(
                        "Function %s already uses US3, which is reserved for transit"
                        % function
                        + " segment congestion values. Please modify the expression "
                        + "to use different attributes."
                    )
        return changes

    def _change_walk_speed(self, scenario, walk_speed):
        with _trace("Setting walk speeds to %s" % walk_speed):
            if EMME_VERSION >= (4, 1):
                self._change_walk_speed_4p1(scenario, walk_speed)
            else:
                self._change_walk_speed_4p0(scenario, walk_speed)

    def _change_walk_speed_4p0(self, scenario, walk_speed):
        change_mode_tool = _MODELLER.tool("inro.emme.data.network.mode.change_mode")
        for mode in scenario.modes():
            if mode.type != "AUX_TRANSIT":
                continue
            change_mode_tool(mode, mode_speed=walk_speed, scenario=scenario)

    def _change_walk_speed_4p1(self, scenario, walk_speed):
        partial_network = scenario.get_partial_network(["MODE"], True)
        for mode in partial_network.modes():
            if mode.type != "AUX_TRANSIT":
                continue
            mode.speed = walk_speed
            _write("Changed mode %s" % mode.id)
        baton = partial_network.get_attribute_values("MODE", ["speed"])
        scenario.set_attribute_values("MODE", ["speed"], baton)

    # ---CALCULATE - SUB FUNCTIONS-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    @contextmanager
    def _temp_matrix_manager(self):
        """
        Matrix objects created & added to this matrix list are deleted when this manager exits.
        """
        temp_matrix_list = []
        try:
            yield temp_matrix_list
        finally:
            for matrix in temp_matrix_list:
                if matrix is not None:
                    _write("Deleting temporary matrix '%s': " % matrix.id)
                    _bank.delete_matrix(matrix.id)

    @contextmanager
    def _temp_attribute_manager(self, scenario):
        temp_attribute_list = []
        try:
            yield temp_attribute_list
        finally:
            for temp_attribute in temp_attribute_list:
                if temp_attribute is not None:
                    scenario.delete_extra_attribute(temp_attribute.id)
                    _write("Deleted temporary '%s' link attribute" % temp_attribute.id)

    @_m.method(return_type=str)
    def get_scenario_node_attributes(self, scenario):
        options = ["<option value='-1'>None</option>"]
        for exatt in scenario.extra_attributes():
            if exatt.type == "NODE":
                options.append(
                    '<option value="%s">%s - %s</option>'
                    % (exatt.id, exatt.id, exatt.description)
                )
        return "\n".join(options)

    @_m.method(return_type=str)
    def get_scenario_link_attributes(self, scenario, include_none=True):
        options = []
        if include_none:
            options.append("<option value='-1'>None</option>")
        for exatt in scenario.extra_attributes():
            if exatt.type == "LINK":
                options.append(
                    '<option value="%s">%s - %s</option>'
                    % (exatt.id, exatt.id, exatt.description)
                )
        return "\n".join(options)

    @_m.method(return_type=str)
    def get_scenario_segment_attribtues(self, scenario):
        options = []
        for exatt in scenario.extra_attributes():
            if exatt.type == "TRANSIT_SEGMENT":
                options.append(
                    '<option value="%s">%s - %s</option>'
                    % (exatt.id, exatt.id, exatt.description)
                )
        return "\n".join(options)

    @_m.method(return_type=_m.TupleType)
    def percent_completed(self):
        return self._tracker.get_progress()

    @_m.method(return_type=str)
    def tool_run_msg_status(self):
        return self.tool_run_msg
