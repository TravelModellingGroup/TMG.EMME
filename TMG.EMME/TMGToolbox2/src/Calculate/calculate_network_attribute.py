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

# ---METADATA------------------
"""
Extract Transit Origin and Destination Vectors

    Authors: Trajce Nikolov

    Latest revision by: Trajce Nikolov
    
    
    Runs the network calculator tool and returns the sum from the report.
        
"""
# ---VERSION HISTORY

"""
    0.0.1 Created on 2015-10-06 by Trajce Nikolov

    2.0.0 Refactored & updated for XTMF2/TMGToolbox2 on 2021-10-14 by Williams Diogu
   
"""

import inro.modeller as _m


_MODELLER = _m.Modeller()
_network_calculation = _m.Modeller().tool("inro.emme.network_calculation.network_calculator")
_util = _MODELLER.module("tmg2.utilities.general_utilities")


class CalculateNetworkAttribute(_m.Tool()):
    def __init__(self):
        self.scenario = _MODELLER.scenario
        self.link = 0
        self.node = 1
        self.transit_line = 2
        self.transit_segment = 3

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
        self._process_domains(parameters)
        spec = self.network_calculator_spec(parameters)
        report = _network_calculation(spec, scenario)
        if "sum" in report:
            return report["sum"]
        return ""

    def network_calculator_spec(self, parameters):

        spec = {
            "result": parameters["result"],
            "expression": parameters["expression"],
            "aggregation": None,
            "type": "NETWORK_CALCULATION",
        }
        selections = {}
        if parameters["node_selection"] is not None:
            selections["node"] = parameters["node_selection"]
        if parameters["link_selection"] is not None:
            selections["link"] = parameters["link_selection"]
        if parameters["transit_line_selection"] is not None:
            selections["transit_line"] = parameters["transit_line_selection"]
        if len(selections) == 0:
            selections["node"] = "all"
        spec["selections"] = selections
        return spec

    def _process_domains(self, parameters):
        if parameters["result"] is None or parameters["result"] == "None":
            parameters["result"] = None
        if parameters["domain"] == self.link:
            parameters["node_selection"] = None
            parameters["transit_line_selection"] = None
        elif parameters["domain"] == self.node:
            parameters["link_selection"] = None
            parameters["transit_line_selection"] = None
        elif parameters["domain"] == self.transit_line:
            parameters["node_selection"] = None
            parameters["link_selection"] = None
        elif parameters["domain"] == self.transit_segment:
            parameters["node_selection"] = None
