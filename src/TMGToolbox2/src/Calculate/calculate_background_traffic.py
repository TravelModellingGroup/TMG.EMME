# ---LICENSE----------------------
"""
    Copyright 2023 Travel Modelling Group, Department of Civil Engineering, University of Toronto

    This file is part of TMG.EMME for XTMF2.

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
    V1.0.0 version by: WilliamsDiogu
"""
import inro.modeller as _m
import multiprocessing

_m.InstanceType = object
_m.ListType = list
_m.TupleType = object

_trace = _m.logbook_trace
_MODELLER = _m.Modeller()
_bank = _MODELLER.emmebank
_write = _m.logbook_write
_util = _MODELLER.module("tmg2.utilities.general_utilities")
EMME_VERSION = _util.get_emme_version(tuple)
network_calculation_tool = _MODELLER.tool("inro.emme.network_calculation.network_calculator")


class CalculateBackgroundTraffic(_m.Tool()):
    version = "1.0.0"
    tool_run_msg = ""
    number_of_tasks = 5
    parameters = _m.Attribute(str)
    number_of_processors = _m.Attribute(int)

    def __init__(self):
        self._tracker = _util.progress_tracker(self.number_of_tasks)
        self.scenario = _MODELLER.scenario
        self.number_of_processors = multiprocessing.cpu_count()
        
    def page(self):
        pb = _m.ToolPageBuilder(
            self,
            title="Calculate Background Traffic",
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
        time_dependent_component_attribute_list = self._create_time_dependent_attribute_list(parameters["link_component_attribute"], parameters["interval_length_list"], parameters["start_index"])
        
        link_component_attribute_list = self._create_transit_traffic_attribute_list(scenario, time_dependent_component_attribute_list)
        print(link_component_attribute_list)
        self._calculate_transit_background_traffic(scenario, parameters, link_component_attribute_list, self._tracker)        

    def _calculate_transit_background_traffic(self, scenario, parameters, link_component_attribute_list, tracker):
        if int(scenario.element_totals["transit_lines"]) > 0:
            bg_spec_list = []
            with _trace("Calculating transit background traffic"):
                for link_component_attribute in link_component_attribute_list:
                    spec = self.get_transit_bg_spec(parameters, link_component_attribute.id)
                    bg_spec_list.append(spec)
                network_calculation_tool(bg_spec_list, scenario=scenario)
                tracker.complete_subtask()
         
    def get_transit_bg_spec(self, parameters, link_component_attribute):
        ttf_terms = str.join(
            " + ",
            [
                "((ttf >=" + str(x["start"]) + ") * (ttf <= " + str(x["stop"]) + "))"
                for x in parameters["mixed_use_ttf_ranges"]
            ],
        )        
        return {
            "result": link_component_attribute,
            "expression": "(60 / hdw) * (vauteq) " + ("* (" + ttf_terms + ")" if ttf_terms else ""),
            "aggregation": "+",
            "selections": {"link": "all", "transit_line": "all"},
            "type": "NETWORK_CALCULATION",
        }
    
    def _create_time_dependent_attribute_list(self, attribute_name, interval_length_list, attribute_start_index):
        def check_att_name(at):
            if at.startswith("@"):
                return at
            else:
                return "@" + at

        time_dependent_attribute_list = [check_att_name(attribute_name) + str(attribute_start_index + i) for i, j in enumerate(interval_length_list)]
        return time_dependent_attribute_list

    def _create_transit_traffic_attribute_list(self, scenario, link_component_attribute_list):
        transit_traffic_attribute_list = []
        for transit_traffic_att in link_component_attribute_list:
            attribute_at = scenario.extra_attribute(transit_traffic_att)
            if attribute_at is not None:
                if attribute_at.type != "LINK":
                    raise Exception("Attribute '%s' is not a link type attribute" % transit_traffic_att)
                scenario.delete_extra_attribute(attribute_at)
            t_traffic_attribute = scenario.create_extra_attribute("LINK", transit_traffic_att, default_value=0.0)
            transit_traffic_attribute_list.append(t_traffic_attribute)
        return transit_traffic_attribute_list