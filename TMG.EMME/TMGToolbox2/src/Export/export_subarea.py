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

import inro.modeller as _m

_m.TupleType = object
_m.ListType = list
_m.InstanceType = object

_trace = _m.logbook_trace
_write = _m.logbook_write

_MODELLER = _m.Modeller()
_bank = _MODELLER.emmebank

_util = _MODELLER.module("tmg2.utilities.general_utilities")
_tmg_tpb = _MODELLER.module("tmg2.utilities.TMG_tool_page_builder")
network_calc_tool = _MODELLER.tool("inro.emme.network_calculation.network_calculator")
_geo_lib = _MODELLER.module("tmg2.utilities.geometry")
shapely_to_esri = _geo_lib.Shapely2ESRI


class ExportSubarea(_m.Tool()):
    version = "1.0.0"
    tool_run_msg = ""
    number_of_tasks = 1

    def __init__(self):
        self._tracker = _util.progress_tracker(self.number_of_tasks)

    def page(self):
        pb = _tmg_tpb.TmgToolPageBuilder(
            self,
            title="Export Subarea v%s" % self.version,
            description="",
            runnable=False,
            branding_text="- TMG Toolbox 2",
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
        self._create_subarea_extra_attribute(scenario, "LINK", parameters["subarea_gate_attribute"])
        self._create_subarea_extra_attribute(scenario, "NODE", parameters["subarea_node_attribute"])
        self._tag_subarea_centroids(scenario, parameters)
        network = scenario.get_network()
        subarea_nodes = self._load_shape_file(network, parameters["shape_file_location"])
        if parameters["create_nflag_from_shapefile"]:
            for node in subarea_nodes:
                node[parameters["subarea_node_attribute"]] = 1
            scenario.publish_network(network)

    def _create_subarea_extra_attribute(self, scenario, attrib_type, attrib_id):
        if scenario.extra_attribute(attrib_id) is None:
            scenario.create_extra_attribute(
                attrib_type,
                attrib_id,
            )

    def _tag_subarea_centroids(self, scenario, parameters):
        i_spec = {
            "type": "NETWORK_CALCULATION",
            "result": "@gate",
            "expression": "i",
            "selections": {"link": parameters["i_subarea_link_selection"]},
        }
        j_spec = {
            "type": "NETWORK_CALCULATION",
            "result": "@gate",
            "expression": "-j",
            "selections": {"link": parameters["j_subarea_link_selection"]},
        }
        network_calc_tool([i_spec, j_spec], scenario=scenario)

    def _load_shape_file(self, network, shape_file_location):
        with shapely_to_esri(shape_file_location, mode="read") as reader:
            if int(reader._size) != 1:
                raise Exception(
                    "Shapefile has invalid number of features. There should only be one 1 polygon in the shapefile"
                )
            subarea_nodes = []
            for node in network.nodes():
                for border in reader.readThrough():
                    if node not in subarea_nodes:
                        point = _geo_lib.nodeToShape(node)
                        if border.contains(point) == True:
                            subarea_nodes.append(node)
        return subarea_nodes
