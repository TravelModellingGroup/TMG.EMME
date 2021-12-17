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


@contextmanager
def blankManager(obj):
    try:
        yield obj
    finally:
        pass


class AssignTraffic(_m.Tool()):
    version = "2.0.2"
    tool_run_msg = ""

    def __init__(self):
        self._tracker = _util.progress_tracker(self.number_of_tasks)
        self.scenario = _MODELLER.scenario
        self.number_of_processors = multiprocessing.cpu_count()

    def __call__(self, parameters):
        parameters = self._load_json_file(parameters)
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
        ...

    # ---LOAD - SUB FUNCTIONS -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    def _load_json_file(self, json_file_name):
        print("Reading parameters from json file '%s'." % json_file_name)
        with open(json_file_name, "r") as json_file:
            return json.load(json_file)

    def _load_scenario(self, scenario_number):
        scenario = _m.Modeller().emmebank.scenario(scenario_number)
        if scenario is None:
            raise Exception("Scenario %s was not found!" % scenario_number)
        return scenario
