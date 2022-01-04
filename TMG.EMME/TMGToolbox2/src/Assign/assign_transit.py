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
import inro.modeller as _m
from contextlib import contextmanager
import random
import json
import csv


_m.TupleType = object
_m.ListType = list
_m.InstanceType = object

_trace = _m.logbook_trace
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


@contextmanager
def blankManager(obj):
    try:
        yield obj
    finally:
        pass


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
        # Initialize demand matrices (input matrices)
        demand_matrix_list = self._init_demand_matrices(parameters)

        with _m.logbook_trace(
            name="%s (%s v%s)"
            % (parameters["run_title"], self.__class__.__name__, self.version),
            attributes=self._load_atts(scenario, parameters),
        ):

            self._tracker.reset()

    # ---LOAD - SUB FUNCTIONS -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    def _load_scenario(self, scenario_number):
        scenario = _m.Modeller().emmebank.scenario(scenario_number)
        if scenario is None:
            raise Exception("Scenario %s was not found!" % scenario_number)
        return scenario

    # ---INITIALIZE - SUB-FUNCTIONS  -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    def _initialize_matrices(self, parameters):
        ...

    def _init_demand_matrices(self, parameters):
        checked_matrix_list = self._check_non_zero_matrix(parameters)
        demand_matrix_list = []
        # Initializing all non-specified matrices and returning all
        for dm in checked_matrix_list:
            if dm == "mf0":
                demand_matrix = _util.initialize_matrix(matrix_type="FULL")
                demand_matrix_list.append(_bank.matrix(demand_matrix.id))
            else:
                demand_matrix_list.append(_bank.matrix(dm))

        return demand_matrix_list

    def _check_non_zero_matrix(self, parameters):
        checked_matrix_list = []
        # Check all non-mf0 matrix
        for tc in parameters["transit_classes"]:
            matrix_string = str(tc["demand_matrix"]).lower()
            if matrix_string == "mf0":
                checked_matrix_list.append(matrix_string)
            elif _bank.matrix(matrix_string) is None:
                raise Exception("Matrix %s was not found!" % matrix_string)
            elif str(_bank.matrix(matrix_string).id) == matrix_string:
                checked_matrix_list.append(matrix_string)
            else:
                raise Exception("Matrix %s was not found!" % matrix_string)

        return checked_matrix_list

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
