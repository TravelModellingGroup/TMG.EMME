# ---LICENSE----------------------
"""
    Copyright 2026 Travel Modelling Group, Department of Civil Engineering, University of Toronto

    This file is part of the TMG Toolbox.

    The TMG Toolbox 2 is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    The TMG Toolbox 2 is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with the TMG Toolbox 2.  If not, see <http://www.gnu.org/licenses/>.
"""

# ---METADATA------------------
"""
Set Screen Line

Authors: James Vaughan
    
        
"""
# ---VERSION HISTORY

"""

2.0.0 Created on 2026-11-22 by James Vaughan
   
"""

import inro
import inro.modeller as _m
from typing import TypeAlias, TypedDict

_MODELLER = _m.Modeller()
_network_calculation = _m.Modeller().tool("inro.emme.network_calculation.network_calculator")
_util = _MODELLER.module("tmg2.utilities.general_utilities")

# alias for the Scenario type hints.
Scenario: TypeAlias = inro.emme.database.scenario.Scenario
Network: TypeAlias = inro.emme.network.Network
#Node: TypeAlias = inro.emme.network.node.Node

class ParametersParams(TypedDict):
    """
    Configuration parameters for the tool.
    """
    scenario_number: int
    output_attribute: str
    station_attributes: list[str]
    station_codes: list[int]

class SetScreenLine(_m.Tool()):
    def __init__(self):

        return

    def __call__(self, parameters: ParametersParams):
        return

    def run_xtmf(self, parameters: ParametersParams) -> None:
        try:
            self._execute(parameters)
        except Exception as e:
            raise Exception(_util.format_reverse_stack())

    def _execute(self, parameters: ParametersParams) -> None:
        scenario: Scenario = _util.load_scenario(parameters["scenario_number"])
        output_attribute = parameters["output_attribute"]
        station_attributes = parameters["station_attributes"]
        station_codes = parameters["station_codes"]
        
        # Validate that the station attributes exist in the network
        existing_attributes = scenario.attributes("LINK")

        for station_attribute in station_attributes:
            if station_attribute not in existing_attributes:
                raise Exception(f"Station attribute '{station_attribute}' does not exist in the network.")

        # If the output attribute does not exist, create it as a new attribute.
        if output_attribute not in existing_attributes:
            scenario.create_extra_attribute("LINK", output_attribute, 0.0)

        network = scenario.get_network();
        # Go through each link and set it if it has a station code.        
        for link in network.links():
            for station_attribute in station_attributes:
                if link[station_attribute] in station_codes:
                    link[output_attribute] = 1            
        
        scenario.publish_network(network, True)
        return
