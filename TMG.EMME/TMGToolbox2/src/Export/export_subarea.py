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

from symbol import parameters
import inro.modeller as _m
import multiprocessing
import traceback as _traceback
from contextlib import contextmanager

_m.TupleType = object
_m.ListType = list
_m.InstanceType = object

_trace = _m.logbook_trace
_write = _m.logbook_write

_MODELLER = _m.Modeller()
_bank = _MODELLER.emmebank

_util = _MODELLER.module("tmg2.utilities.general_utilities")
subarea_analysis_tool = _MODELLER.tool("inro.emme.subarea.subarea")
_tmg_tpb = _MODELLER.module("tmg2.utilities.TMG_tool_page_builder")
network_calc_tool = _MODELLER.tool("inro.emme.network_calculation.network_calculator")
_geo_lib = _MODELLER.module("tmg2.utilities.geometry")
shapely_to_esri = _geo_lib.Shapely2ESRI

EMME_VERSION = _util.get_emme_version(tuple)

matrix_calc_tool = _MODELLER.tool("inro.emme.matrix_calculation.matrix_calculator")
network_calculation_tool = _MODELLER.tool("inro.emme.network_calculation.network_calculator")
traffic_assignment_tool = _MODELLER.tool("inro.emme.traffic_assignment.sola_traffic_assignment")
extra_parameter_tool = _MODELLER.tool("inro.emme.traffic_assignment.set_extra_function_parameters")


class ExportSubarea(_m.Tool()):
    version = "1.0.0"
    tool_run_msg = ""
    number_of_tasks = 1

    def __init__(self):
        self._tracker = _util.progress_tracker(self.number_of_tasks)
        self.number_of_processors = multiprocessing.cpu_count()
        self._traffic_util = _util.assign_traffic_util()

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
                    self._traffic_util.calculate_transit_background_traffic(scenario, parameters, self._tracker)
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
                    with _m.logbook_trace("Running Sub Area Road Assignments."):
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
                            print(sola_spec)
                            self._create_subarea_extra_attribute(scenario, "LINK", parameters["subarea_gate_attribute"])
                            self._create_subarea_extra_attribute(scenario, "NODE", parameters["subarea_node_attribute"])
                            self._tag_subarea_centroids(scenario, parameters)
                            network = scenario.get_network()
                            subarea_nodes = self._load_shape_file(network, parameters["shape_file_location"])
                            if parameters["create_nflag_from_shapefile"]:
                                node_attribute = parameters["subarea_node_attribute"]
                                for node in subarea_nodes:
                                    node[node_attribute] = 1
                                scenario.publish_network(network)

                            print(parameters["subarea_output_folder"])

                            self._tracker.run_tool(
                                subarea_analysis_tool,
                                subarea_nodes=parameters["subarea_node_attribute"],
                                subarea_folder=parameters["subarea_output_folder"],
                                traffic_assignment_spec=sola_spec,
                                extract_transit=True,
                                overwrite=True,
                                gate_labels=parameters["subarea_gate_attribute"],
                                scenario=scenario,
                            )

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
