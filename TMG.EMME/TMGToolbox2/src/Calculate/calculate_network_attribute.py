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
import traceback as _traceback
import numpy as _np
from multiprocessing import cpu_count


_MODELLER = _m.Modeller()  # Instatiate Modeller once.
_network_calculation = _m.Modeller().tool("inro.emme.network_calculation.network_calculator")


class CalculateNetworkAttribute(_m.Tool()):
    # ---Parameters---
    scenario_number = _m.Attribute(int)
    domain = _m.Attribute(int)
    expression = _m.Attribute(str)
    node_selection = _m.Attribute(str)
    link_selection = _m.Attribute(str)
    transit_line_selection = _m.Attribute(str)
    result = _m.Attribute(str)

    def __init__(self):
        self.scenario = _MODELLER.scenario

    def __call__(
        self,
        scenario_number,
        domain,
        expression,
        node_selection,
        link_selection,
        transit_line_selection,
        result,
    ):

        # self.scenario = _MODELLER.emmebank.scenario(scenario_number)
        self.domain = domain
        self.expression = expression
        self._load_scenario(self.scenario_number)

        self._process_parameters(result, link_selection, node_selection, transit_line_selection)

        # self._report()
        spec = self.network_calculator_spec()

        report = _network_calculation(spec, self.scenario)

        if "sum" in report:
            return report["sum"]

        return ""

    def run_xtmf(self, parameters):
        self.scenario_number = parameters["scenario_number"]
        self.domain = parameters["domain"]
        self.expression = parameters["expression"]
        self.node_selection = parameters["node_selection"]
        self.link_selection = parameters["link_selection"]
        self.transit_line_selection = parameters["transit_line_selection"]
        self.result = parameters["result"]

        # self.scenario = _MODELLER.emmebank.scenario(self.scenario_number)

        self._load_scenario(self.scenario_number)

        self._process_parameters(
            self.result,
            self.link_selection,
            self.node_selection,
            self.transit_line_selection,
        )
        spec = self.network_calculator_spec()

        report = _network_calculation(spec, self.scenario)

        if "sum" in report:
            return report["sum"]

        return ""

    def network_calculator_spec(self):
        spec = {
            "result": self.result,
            "expression": self.expression,
            "aggregation": None,
            "type": "NETWORK_CALCULATION",
        }

        selections = {}
        if self.node_selection is not None:
            selections["node"] = self.node_selection
        if self.link_selection is not None:
            selections["link"] = self.link_selection
        if self.transit_line_selection is not None:
            selections["transit_line"] = self.transit_line_selection
        if len(selections) == 0:
            selections["node"] = "all"
        spec["selections"] = selections

        return spec

    def _load_scenario(self, scenario_number):
        scenario = _MODELLER.emmebank.scenario(scenario_number)
        if scenario is None:
            raise Exception("Scenario %s was not found!" % scenario_number)

        return scenario

    def _process_parameters(self, result, link_selection, node_selection, transit_line_selection):
        if self.result is not None and self.result != "None":
            self.result = result
        else:
            self.result = None

        if self.domain == 0:  # Link
            self.node_selection = None
            self.link_selection = link_selection
            self.transit_line_selection = None
        elif self.domain == 1:  # Node
            self.node_selection = node_selection
            self.link_selection = None
            self.transit_line_selection = None
        elif self.domain == 2:  # transit line
            self.node_selection = None
            self.link_selection = None
            self.transit_line_selection = transit_line_selection
        elif self.domain == 3:  # transit segment
            self.node_selection = None
            self.link_selection = link_selection
            self.transit_line_selection = transit_line_selection
