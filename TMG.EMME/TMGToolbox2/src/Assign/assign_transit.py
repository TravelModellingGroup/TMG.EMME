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
import enum
import math
import traceback as _traceback
import time as _time
import multiprocessing

from numpy import percentile
import inro.modeller as _m
import csv
from contextlib import contextmanager

_m.TupleType = object
_m.ListType = list
_m.InstanceType = object
_trace = _m.logbook_trace
_write = _m.logbook_write
_MODELLER = _m.Modeller()
_bank = _MODELLER.emmebank
_util = _MODELLER.module("tmg2.utilities.general_utilities")
_db_utils = _MODELLER.module("inro.emme.utility.database_utilities")
_tmg_tpb = _MODELLER.module("tmg2.utilities.TMG_tool_page_builder")
network_calc_tool = _MODELLER.tool("inro.emme.network_calculation.network_calculator")
extended_assignment_tool = _MODELLER.tool("inro.emme.transit_assignment.extended_transit_assignment")
matrix_calc_tool = _MODELLER.tool("inro.emme.matrix_calculation.matrix_calculator")
null_pointer_exception = _util.null_pointer_exception
EMME_VERSION = _util.get_emme_version(tuple)


class AssignTransit(_m.Tool()):
    version = "2.0.0"
    tool_run_msg = ""
    number_of_tasks = 15

    def __init__(self):
        self._tracker = _util.progress_tracker(self.number_of_tasks)
        self.number_of_processors = multiprocessing.cpu_count()
        self.connector_logit_truncation = 0.05
        self.consider_total_impedance = True
        self.use_logit_connector_choice = True

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

    def __call__(self, parameters):
        scenario = _util.load_scenario(parameters["scenario_number"])
        try:
            self._execute(scenario, parameters)
        except Exception as e:
            raise Exception(_util.format_reverse_stack())

    def run_xtmf(self, parameters):
        scenario = _util.load_scenario(parameters["scenario_number"])
        # self._check_attributes_exist(scenario, parameters)
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
            with _util.temporary_matrix_manager() as temp_matrix_list:
                # Initialize matrices with matrix ID = "mf0" not loaded in load_input_matrix_list
                demand_matrix_list = self._init_input_matrices(load_input_matrix_list, temp_matrix_list)
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
                impedance_matrix_list = self._get_impedance_matrices(parameters, temp_matrix_list)
                self._change_walk_speed(scenario, parameters["walk_speed"])
                with _util.temporary_attribute_manager(scenario) as temp_attribute_list:
                    effective_headway_attribute_list = self._create_headway_attribute_list(
                        scenario,
                        "TRANSIT_LINE",
                        temp_attribute_list,
                        default_value=0.0,
                        hdw_att_name=parameters["effective_headway_attribute"],
                    )
                    headway_fraction_attribute_list = self._create_headway_attribute_list(
                        scenario,
                        "NODE",
                        temp_attribute_list,
                        default_value=0.5,
                        hdw_att_name=parameters["headway_fraction_attribute"],
                    )
                    walk_time_perception_attribute_list = self._create_walk_time_perception_attribute_list(
                        scenario, parameters, temp_attribute_list
                    )
                    self._tracker.start_process(5)
                    self._assign_effective_headway(
                        scenario,
                        parameters,
                        effective_headway_attribute_list[0].id,
                    )
                    self._tracker.complete_subtask()
                    self._assign_walk_perception(scenario, parameters)
                    if parameters["node_logit_scale"] == True:
                        network = self._publish_efficient_connector_network(scenario)
                    else:
                        network = scenario.get_network()
                    with _util.temp_extra_attribute_manager(scenario, "TRANSIT_LINE") as stsu_att:
                        with self._temp_stsu_ttfs(scenario, parameters) as temp_stsu_ttf:
                            stsu_ttf_map = temp_stsu_ttf[0]
                            ttfs_changed = temp_stsu_ttf[1]
                            if parameters["surface_transit_speed"] == True:
                                self._set_base_speed(scenario, parameters, stsu_att, stsu_ttf_map, ttfs_changed)
                            self._run_transit_assignment(
                                scenario,
                                parameters,
                                network,
                                stsu_att,
                                demand_matrix_list,
                                effective_headway_attribute_list,
                                headway_fraction_attribute_list,
                                impedance_matrix_list,
                                walk_time_perception_attribute_list,
                            )

    # ---LOAD - SUB FUNCTIONS -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    def _load_atts(self, scenario, parameters):
        atts = {
            "Scenario": "%s - %s" % (scenario, scenario.title),
            "Version": self.version,
            "Wait Perception": [t_class["wait_time_perception"] for t_class in parameters["transit_classes"]],
            "Fare Perception": [t_class["fare_perception"] for t_class in parameters["transit_classes"]],
            "Boarding Perception": [t_class["board_penalty_perception"] for t_class in parameters["transit_classes"]],
            "Congestion": parameters["congested_assignment"],
            "self": self.__MODELLER_NAMESPACE__,
        }
        return atts

    def _check_attributes_exist(self, scenario, parameters):
        walk_att = "walk_time_perception_attribute"
        seg_att = "segment_fare_attribute"
        ehwy_att = "effective_headway_attribute"
        hwy_att = "headway_fraction_attribute"
        link_att = "link_fare_attribute_id"
        for transit_class in parameters["transit_classes"]:
            if scenario.extra_attribute(transit_class[walk_att]) is None:
                raise Exception("Walk perception attribute %s does not exist" % walk_att)
            if scenario.extra_attribute(transit_class[seg_att]) is None:
                raise Exception("Segment fare attribute %s does not exist" % seg_att)
            if scenario.extra_attribute(transit_class[link_att]) is None:
                raise Exception("Link fare attribute %s does not exist" % link_att)
        if scenario.extra_attribute(parameters[ehwy_att]) is None:
            raise Exception("Effective headway attribute %s does not exist" % ehwy_att)
        if scenario.extra_attribute(parameters[hwy_att]) is None:
            raise Exception("Effective headway attribute %s does not exist" % hwy_att)

    # ---INITIALIZE - SUB-FUNCTIONS  -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    def _load_output_matrices(self, parameters, matrix_name=[]):
        """
        This loads all (into a dictionary) output matrices by matrix_name list provided but
        assigns None to all zero matrices for later initialization
        """
        mtx_dict = {}
        transit_classes = parameters["transit_classes"]
        for i in range(0, len(matrix_name)):
            mtx_dict[matrix_name[i]] = [transit_class[matrix_name[i]] for transit_class in transit_classes]
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
        mtx_list = [
            _bank.matrix(transit_class[matrix_name])
            if transit_class[matrix_name] == "mf0" or _bank.matrix(transit_class[matrix_name]) is not None
            else exception(transit_class[matrix_name])
            for transit_class in transit_classes
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

    def _get_impedance_matrices(self, parameters, temp_matrix_list):
        """
        Creates temporary matrix for matrices with id = "mf0"
        """
        impedance_matrix_list = []
        transit_classes = parameters["transit_classes"]
        for transit_class in transit_classes:
            matrix_id = transit_class["impedance_matrix"]
            if matrix_id != "mf0":
                _util.initialize_matrix(
                    id=matrix_id,
                    description="Transit Perceived Travel times for %s" % transit_class["name"],
                )
                impedance_matrix_list.append(matrix)
            else:
                _write("Creating temporary Impedance Matrix for class %s" % transit_class["name"])
                matrix = _util.initialize_matrix(
                    default=0.0,
                    description="Temporary Impedance for class %s" % transit_class["name"],
                    matrix_type="FULL",
                )
                impedance_matrix_list.append(matrix)
                temp_matrix_list.append(matrix)
        return impedance_matrix_list

    def _init_output_matrices(
        self,
        load_output_matrix_dict,
        temp_matrix_list,
        matrix_name="",
        description="",
    ):
        """
        Initializes all output matrices provided.
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
            raise Exception('Output matrix name "%s" provided does not exist', matrix_name)
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
                    print("Detected function %s with existing congestion term." % function)
                    print("Original expression= '%s'" % cleaned_expression)
                    print("Healed expression= '%s'" % new_expression)
                    print("")
                    _write("Detected function %s with existing congestion term." % function)
                    _write("Original expression= '%s'" % cleaned_expression)
                    _write("Healed expression= '%s'" % new_expression)
                    changes += 1
                else:
                    raise Exception(
                        "Function %s already uses US3, which is reserved for transit" % function
                        + " segment congestion values. Please modify the expression "
                        + "to use different attributes."
                    )
        return changes

    def _change_walk_speed(self, scenario, walk_speed):
        with _trace("Setting walk speeds to %s" % walk_speed):
            partial_network = scenario.get_partial_network(["MODE"], True)
            for mode in partial_network.modes():
                if mode.type != "AUX_TRANSIT":
                    continue
                mode.speed = walk_speed
                _write("Changed mode %s" % mode.id)
            baton = partial_network.get_attribute_values("MODE", ["speed"])
            scenario.set_attribute_values("MODE", ["speed"], baton)

    def _create_walk_time_perception_attribute_list(self, scenario, parameters, temp_matrix_list):
        walk_time_perception_attribute_list = []
        for transit_class in parameters["transit_classes"]:
            walk_time_perception_attribute = _util.create_temp_attribute(
                scenario,
                str(transit_class["walk_time_perception_attribute"]),
                "LINK",
                default_value=1.0,
                assignment_type="transit",
            )
            walk_time_perception_attribute_list.append(walk_time_perception_attribute)
            temp_matrix_list.append(walk_time_perception_attribute)
        return walk_time_perception_attribute_list

    def _create_headway_attribute_list(
        self,
        scenario,
        attribute_type,
        temp_matrix_list,
        default_value=0.0,
        hdw_att_name="",
    ):
        headway_attribute_list = []
        headway_attribute = _util.create_temp_attribute(
            scenario,
            str(hdw_att_name),
            str(attribute_type),
            default_value=default_value,
            assignment_type="transit",
        )
        headway_attribute_list.append(headway_attribute)
        temp_matrix_list.append(headway_attribute)
        return headway_attribute_list

    def _assign_effective_headway(self, scenario, parameters, effective_headway_attribute_id):
        small_headway_spec = {
            "result": effective_headway_attribute_id,
            "expression": "hdw",
            "aggregation": None,
            "selections": {"transit_line": "hdw=0,15"},
            "type": "NETWORK_CALCULATION",
        }
        large_headway_spec = {
            "result": effective_headway_attribute_id,
            "expression": "15+2*" + str(parameters["effective_headway_slope"]) + "*(hdw-15)",
            "aggregation": None,
            "selections": {"transit_line": "hdw=15,999"},
            "type": "NETWORK_CALCULATION",
        }
        network_calc_tool(small_headway_spec, scenario)
        network_calc_tool(large_headway_spec, scenario)

    def _assign_walk_perception(self, scenario, parameters):
        transit_classes = parameters["transit_classes"]
        for transit_class in transit_classes:
            walk_time_perception_attribute = transit_class["walk_time_perception_attribute"]
            ex_att = scenario.extra_attribute(walk_time_perception_attribute)
            ex_att.initialize(1.0)

        def apply_selection(val, selection):
            spec = {
                "result": walk_time_perception_attribute,
                "expression": str(val),
                "aggregation": None,
                "selections": {"link": selection},
                "type": "NETWORK_CALCULATION",
            }
            network_calc_tool(spec, scenario)

        with _trace("Assigning perception factors"):
            for transit_class in transit_classes:
                for wp in transit_class["walk_perceptions"]:
                    selection = str(wp["filter"])
                    value = str(wp["walk_perception_value"])
                    apply_selection(value, selection)

    def _publish_efficient_connector_network(self, scenario):
        """
        Creates a network that completely replaces the scenario network in memory/disk, with
        one that allows for the use of a logit distribution at specified choice points.

        Run:
            - set "node_logit_scale" parameter = TRUE, to run Logit Discrete Choice Model
            - set "node_logit_scale" parameter = FALSE, to run Optimal Strategy Transit Assignment

            ** This method only runs when node logit scale is not FALSE

        Args:
            - scenario: The Emme Scenario object to load network from and to

        Implementation Notes:
            - Regular nodes that are centroids are used as choice points:

                ** Node attributes are set to -1 to apply logit distribution to efficient connectors
                   (connectors that bring travellers closer to destination) only. Setting node attributes
                   to 1 apply same to all connectors.

                    *** Outgoing link connector attributes must be set to -1 to override flow connectors with fixed proportions.
        """
        network = scenario.get_network()
        for node in network.regular_nodes():
            node.data1 = 0
        for node in network.regular_nodes():
            agency_counter = 0
            if node.number > 99999:
                continue
            for link in node.incoming_links():
                if link.i_node.is_centroid is True:
                    node.data1 = -1
                if link.i_node.number > 99999:
                    agency_counter += 1
            for link in node.outgoing_links():
                if link.j_node.is_centroid is True:
                    node.data1 = -1
            if agency_counter > 1:
                node.data1 = -1
                for link in node.incoming_links():
                    if link.i_node.number > 99999:
                        link.i_node.data1 = -1
                for link in node.outgoing_links():
                    if link.j_node.number > 99999:
                        link.j_node.data1 = -1
        scenario.publish_network(network)
        return network

    def _set_base_speed(self, scenario, parameters, stsu_att, stsu_ttf_map, ttfs_changed):
        erow_defined = self._check_attributes_and_get_erow(scenario)
        self._set_up_line_attributes(scenario, parameters, stsu_att)
        ttfs_xrow = self.process_ttfs_xrow(parameters)
        network = scenario.get_network()
        for line in network.transit_lines():
            for stsu in parameters["surface_transit_speeds"]:
                if line[stsu_att.id] <= 0.0:
                    continue
                default_duration = stsu["default_duration"]
                correlation = stsu["transit_auto_correlation"]
                erow_speed_global = stsu["global_erow_speed"]
                segments = line.segments()
                number_of_segments = segments.__length_hint__()
                for segment in segments:
                    if segment.allow_alightings == True and segment.allow_boardings == True:
                        segment.dwell_time = 0.01
                    else:
                        segment.dwell_time = 0.0
                    if segment.j_node is None:
                        continue
                    segment_number = segment.number
                    segment.transit_time_func = stsu_ttf_map[segment.transit_time_func]
                    time = segment.link["auto_time"]
                    if time > 0.0:
                        if segment.transit_time_func in ttfs_xrow:
                            if erow_defined == True and segment["@erow_speed"] > 0.0:
                                segment.data1 = segment["@erow_speed"]
                            else:
                                segment.data1 = erow_speed_global
                        else:
                            segment.data1 = (segment.link.length * 60.0) / (time * correlation)
                    if time <= 0.0:
                        if erow_defined == True and segment["@erow_speed"] > 0.0:
                            segment.data1 = segment["@erow_speed"]
                        else:
                            if segment_number <= 1 or segment_number >= (number_of_segments - 1):
                                segment.data1 = 20
                            else:
                                segment.data1 = erow_speed_global
                    if segment_number == 0:
                        continue
                    segment.dwell_time = (segment["@tstop"] * default_duration) / 60
        data = network.get_attribute_values("TRANSIT_SEGMENT", ["dwell_time", "transit_time_func", "data1"])
        scenario.set_attribute_values("TRANSIT_SEGMENT", ["dwell_time", "transit_time_func", "data1"], data)
        ttfs_changed.append(True)

    def process_ttfs_xrow(self, parameters):
        ttfs_xrow = set()
        parameter_xrow_range = parameters["xrow_ttf_range"].split()
        for ttf_range in parameter_xrow_range:
            if "-" in ttf_range:
                ttf_range = ttf_range.split("-")
                for i in range(int(ttf_range[0]), int(ttf_range[1]) + 1):
                    ttfs_xrow.add(i)
            else:
                ttfs_xrow.add(int(ttf_range))
        return ttfs_xrow

    def _check_attributes_and_get_erow(self, scenario):
        if scenario.extra_attribute("@doors") is None:
            print(
                "No Transit Vehicle door information is present in the network. Default assumption will be 2 doors per surface vehicle."
            )
        if scenario.extra_attribute("@boardings") is None:
            scenario.create_extra_attribute("TRANSIT_SEGMENT", "@boardings")
        if scenario.extra_attribute("@alightings") is None:
            scenario.create_extra_attribute("TRANSIT_SEGMENT", "@alightings")
        if scenario.extra_attribute("@erow_speed") is None:
            erow_defined = False
            print(
                "No segment specific exclusive ROW speed attribute is defined in the network. Global erow speed will be used."
            )
        else:
            erow_defined = True
        return erow_defined

    def _set_up_line_attributes(self, scenario, parameters, stsu_att):
        stsu = []
        for i, sts in enumerate(parameters["surface_transit_speeds"]):
            spec = {
                "type": "NETWORK_CALCULATION",
                "result": str(stsu_att.id),
                "expression": str(i + 1),
                "selections": {"transit_line": "mode = " + sts["mode_filter_expression"]},
            }
            if sts["line_filter_expression"] == "" and sts["mode_filter_expression"] != "":
                spec["selections"]["transit_line"] = "mode = " + sts["mode_filter_expression"]
            elif sts["line_filter_expression"] != "" and sts["mode_filter_expression"] != "":
                spec["selections"]["transit_line"] = (
                    sts["line_filter_expression"] + " and mode = " + sts["mode_filter_expression"]
                )
            elif sts["line_filter_expression"] != "" and sts["mode_filter_expression"] == "":
                spec["selections"]["transit_line"] = sts["mode_filter_expression"]
            elif sts["line_filter_expression"] == "" and sts["mode_filter_expression"] == "":
                spec["selections"]["transit_line"] = "all"
            else:
                raise Exception(
                    "Please enter a correct mode filter and/or line filter in Surface Transit Speed parameters %d"
                    % (i + 1)
                )
            report = network_calc_tool(spec, scenario=scenario)
        return stsu

    def _run_transit_assignment(
        self,
        scenario,
        parameters,
        network,
        stsu_att,
        demand_matrix_list,
        effective_headway_attribute_list,
        headway_fraction_attribute_list,
        impedance_matrix_list,
        walk_time_perception_attribute_list,
    ):
        if parameters["congested_assignment"] == True:
            used_functions = self._add_cong_term_to_func(scenario)
            with _trace(
                name="TMG Congested Transit Assignment",
                attributes=self._get_atts_congested(
                    scenario,
                    parameters,
                    demand_matrix_list,
                    self.connector_logit_truncation,
                    headway_fraction_attribute_list,
                    effective_headway_attribute_list,
                    walk_time_perception_attribute_list,
                    impedance_matrix_list,
                ),
            ) as trace:
                with _db_utils.congested_transit_temp_funcs(scenario, used_functions, False, "us3"):
                    with _db_utils.backup_and_restore(scenario, {"TRANSIT_SEGMENT": ["data3"]}):
                        congested_assignment = self._run_congested_assignment(
                            scenario,
                            parameters,
                            network,
                            demand_matrix_list,
                            impedance_matrix_list,
                            stsu_att,
                            headway_fraction_attribute_list,
                            effective_headway_attribute_list,
                            walk_time_perception_attribute_list,
                        )
                        alphas = congested_assignment[1]
                        strategies = congested_assignment[0]

                self._save_results(scenario, parameters, network, alphas, strategies)
                trace.write(
                    name="TMG Congested Transit Assignment",
                    attributes={"assign_end_time": scenario.transit_assignment_timestamp},
                )
        else:
            self._run_uncongested_assignment(
                scenario,
                parameters,
                stsu_att,
                demand_matrix_list,
                effective_headway_attribute_list,
                headway_fraction_attribute_list,
                impedance_matrix_list,
                walk_time_perception_attribute_list,
            )

    def _run_uncongested_assignment(
        self,
        scenario,
        parameters,
        stsu_att,
        demand_matrix_list,
        effective_headway_attribute_list,
        headway_fraction_attribute_list,
        impedance_matrix_list,
        walk_time_perception_attribute_list,
    ):
        if parameters["surface_transit_speed"] == False:
            self._run_spec_uncongested(
                scenario,
                parameters,
                stsu_att,
                demand_matrix_list,
                effective_headway_attribute_list,
                headway_fraction_attribute_list,
                impedance_matrix_list,
                walk_time_perception_attribute_list,
            )
        else:
            for itr in range(0, parameters["iterations"]):
                self._run_spec_uncongested(
                    scenario,
                    parameters,
                    stsu_att,
                    demand_matrix_list,
                    effective_headway_attribute_list,
                    headway_fraction_attribute_list,
                    impedance_matrix_list,
                    walk_time_perception_attribute_list,
                )
                network = scenario.get_network()
                network = self._surface_transit_speed_update(scenario, parameters, network, 1)

    def _run_congested_assignment(
        self,
        scenario,
        parameters,
        network,
        demand_matrix_list,
        impedance_matrix_list,
        stsu_att,
        headway_fraction_attribute_list,
        effective_headway_attribute_list,
        walk_time_perception_attribute_list,
    ):
        for iteration in range(0, parameters["iterations"] + 1):
            with _trace("Iteration %d" % iteration):
                print("Starting iteration %d" % iteration)

                if iteration == 0:
                    strategies = self._prep_strategy_files(scenario, parameters, demand_matrix_list)
                    zeroes = [0.0] * _bank.dimensions["transit_segments"]
                    setattr(scenario._net.segment, "data3", zeroes)
                    self._run_extended_transit_assignment(
                        scenario,
                        parameters,
                        iteration,
                        strategies,
                        demand_matrix_list,
                        headway_fraction_attribute_list,
                        effective_headway_attribute_list,
                        walk_time_perception_attribute_list,
                        impedance_matrix_list,
                    )
                    alphas = [1.0]
                    assigned_class_demand = self._compute_assigned_class_demand(
                        scenario, demand_matrix_list, self.number_of_processors
                    )
                    assigned_total_demand = sum(assigned_class_demand)
                    network = self._prepare_network(scenario, parameters, stsu_att)
                    if parameters["surface_transit_speed"] == True:
                        network = self._surface_transit_speed_update(scenario, parameters, network, 1)
                    average_min_trip_impedance = self._compute_min_trip_impedance(
                        scenario, demand_matrix_list, assigned_class_demand, impedance_matrix_list
                    )
                    congestion_costs = self._get_congestion_costs(parameters, network, assigned_total_demand)
                    average_impedance = average_min_trip_impedance + congestion_costs
                    if parameters["csvfile"].lower() is not "":
                        self._write_csv_files(iteration, network, "", "", "")
                else:
                    excess_km = self._compute_segment_costs(scenario, parameters, network)
                    self._run_extended_transit_assignment(
                        scenario,
                        parameters,
                        iteration,
                        strategies,
                        demand_matrix_list,
                        headway_fraction_attribute_list,
                        effective_headway_attribute_list,
                        walk_time_perception_attribute_list,
                        impedance_matrix_list,
                    )
                    network = self._update_network(scenario, network)
                    average_min_trip_impedance = self._compute_min_trip_impedance(
                        scenario, demand_matrix_list, assigned_class_demand, impedance_matrix_list
                    )
                    find_step_size = self._find_step_size(
                        parameters,
                        network,
                        average_min_trip_impedance,
                        average_impedance,
                        assigned_total_demand,
                        alphas,
                    )
                    lambdaK = find_step_size[0]
                    alphas = find_step_size[1]
                    if parameters["surface_transit_speed"] == True:
                        network = self._surface_transit_speed_update(scenario, parameters, network, 1)
                    self._update_volumes(network, lambdaK)
                    (average_impedance, cngap, crgap, norm_gap_difference, net_cost,) = self._compute_gaps(
                        assigned_total_demand,
                        lambdaK,
                        average_min_trip_impedance,
                        average_impedance,
                        network,
                    )
                    if parameters["csvfile"].lower() is not "":
                        self._write_csv_files(
                            iteration,
                            network,
                            cngap,
                            crgap,
                            norm_gap_difference,
                        )
                    if crgap < parameters["rel_gap"] or norm_gap_difference >= 0:
                        break
        return (strategies, alphas)

    def _run_spec_uncongested(
        self,
        scenario,
        parameters,
        stsu_att,
        demand_matrix_list,
        effective_headway_attribute_list,
        headway_fraction_attribute_list,
        impedance_matrix_list,
        walk_time_perception_attribute_list,
    ):
        for i, transit_class in enumerate(parameters["transit_classes"]):
            spec_uncongested = self._get_base_assignment_spec_uncongested(
                scenario,
                transit_class["board_penalty_perception"],
                self.connector_logit_truncation,
                self.consider_total_impedance,
                demand_matrix_list[i],
                effective_headway_attribute_list[i],
                transit_class["fare_perception"],
                headway_fraction_attribute_list[i],
                impedance_matrix_list[i],
                transit_class["link_fare_attribute_id"],
                [transit_class["mode"]],
                parameters["node_logit_scale"],
                self.number_of_processors,
                parameters["origin_distribution_logit_scale"],
                transit_class["segment_fare_attribute"],
                self.use_logit_connector_choice,
                transit_class["wait_time_perception"],
                parameters["walk_all_way_flag"],
                walk_time_perception_attribute_list[i],
            )
            self._tracker.run_tool(
                extended_assignment_tool,
                specification=spec_uncongested,
                class_name=transit_class["name"],
                scenario=scenario,
                add_volumes=(i != 0),
            )

    def _get_base_assignment_spec_uncongested(
        self,
        scenario,
        board_perception,
        connector_logit_truncation,
        consider_total_impedance,
        demand_matrix,
        effective_headway,
        fare_perception,
        headway_fraction,
        impedance_matrix,
        link_fare_attribute,
        modes,
        node_logit_scale,
        number_of_processors,
        origin_distribution_logit_scale,
        segment_fare,
        use_logit_connector_choice,
        wait_perception,
        walk_all_way_flag,
        walk_attribute,
    ):
        if fare_perception != 0.0:
            fare_perception = 60.0 / fare_perception
        base_spec = {
            "modes": modes,
            "demand": demand_matrix.id,
            "waiting_time": {
                "headway_fraction": headway_fraction.id,
                "effective_headways": effective_headway.id,
                "spread_factor": 1,
                "perception_factor": wait_perception,
            },
            "boarding_time": {
                "at_nodes": None,
                "on_lines": {
                    "penalty": "ut3",
                    "perception_factor": board_perception,
                },
            },
            "boarding_cost": {
                "at_nodes": {"penalty": 0, "perception_factor": 1},
                "on_lines": None,
            },
            "in_vehicle_time": {"perception_factor": "us2"},
            "in_vehicle_cost": {
                "penalty": segment_fare,
                "perception_factor": fare_perception,
            },
            "aux_transit_time": {"perception_factor": walk_attribute.id},
            "aux_transit_cost": {
                "penalty": link_fare_attribute,
                "perception_factor": fare_perception,
            },
            "connector_to_connector_path_prohibition": None,
            "od_results": {"total_impedance": impedance_matrix.id},
            "flow_distribution_between_lines": {"consider_total_impedance": consider_total_impedance},
            "save_strategies": True,
            "type": "EXTENDED_TRANSIT_ASSIGNMENT",
        }
        if use_logit_connector_choice:
            base_spec["flow_distribution_at_origins"] = {
                "choices_at_origins": {
                    "choice_points": "ALL_ORIGINS",
                    "choice_set": "ALL_CONNECTORS",
                    "logit_parameters": {
                        "scale": origin_distribution_logit_scale,
                        "truncation": connector_logit_truncation,
                    },
                },
                "fixed_proportions_on_connectors": None,
            }
        base_spec["performance_settings"] = {"number_of_processors": number_of_processors}
        if node_logit_scale is not False:
            base_spec["flow_distribution_at_regular_nodes_with_aux_transit_choices"] = {
                "choices_at_regular_nodes": {
                    "choice_points": "ui1",
                    "aux_transit_choice_set": "ALL_POSSIBLE_LINKS",
                    "logit_parameters": {
                        "scale": node_logit_scale,
                        "truncation": connector_logit_truncation,
                    },
                }
            }
        else:
            base_spec["flow_distribution_at_regular_nodes_with_aux_transit_choices"] = {
                "choices_at_regular_nodes": "OPTIMAL_STRATEGY"
            }

        mode_list = []
        partial_network = scenario.get_partial_network(["MODE"], True)
        mode_list = partial_network.modes() if modes == "*" else modes
        base_spec["journey_levels"] = [
            {
                "description": "Walking",
                "destinations_reachable": walk_all_way_flag,
                "transition_rules": self._create_journey_level_modes(mode_list, 0),
                "boarding_time": None,
                "boarding_cost": None,
                "waiting_time": None,
            },
            {
                "description": "Transit",
                "destinations_reachable": True,
                "transition_rules": self._create_journey_level_modes(mode_list, 1),
                "boarding_time": None,
                "boarding_cost": None,
                "waiting_time": None,
            },
        ]
        return base_spec

    def _surface_transit_speed_update(self, scenario, parameters, network, lambdaK):
        if "transit_alightings" not in network.attributes("TRANSIT_SEGMENT"):
            network.create_attribute("TRANSIT_SEGMENT", "transit_alightings", 0.0)
        for line in network.transit_lines():
            prev_volume = 0.0
            headway = line.headway
            number_of_trips = parameters["assignment_period"] * 60.0 / headway
            for stsu in parameters["surface_transit_speeds"]:
                boarding_duration = stsu["boarding_duration"]
                alighting_duration = stsu["alighting_duration"]
                default_duration = stsu["default_duration"]
                try:
                    doors = segment.line["@doors"]
                    if doors == 0.0:
                        number_of_door_pairs = 1.0
                    else:
                        number_of_door_pairs = doors / 2.0
                except:
                    number_of_door_pairs = 1.0

                for segment in line.segments(include_hidden=True):
                    segment_number = segment.number
                    if segment_number > 0 and segment.j_node is not None:
                        segment.transit_alightings = max(
                            prev_volume + segment.transit_boardings - segment.transit_volume,
                            0.0,
                        )
                    else:
                        continue
                    # prevVolume is used above for the previous segments volume, the first segment is always ignored.
                    prev_volume = segment.transit_volume

                    boarding = segment.transit_boardings / number_of_trips / number_of_door_pairs
                    alighting = segment.transit_alightings / number_of_trips / number_of_door_pairs

                    old_dwell = segment.dwell_time
                    # in seconds
                    segment_dwell_time = (
                        (boarding_duration * boarding)
                        + (alighting_duration * alighting)
                        + (segment["@tstop"] * default_duration)
                    )
                    # in minutes
                    segment_dwell_time /= 60
                    if segment_dwell_time >= 99.99:
                        segment_dwell_time = 99.98
                    alpha = 1 - lambdaK
                    segment.dwell_time = old_dwell * alpha + segment_dwell_time * lambdaK
        data = network.get_attribute_values("TRANSIT_SEGMENT", ["dwell_time", "transit_time_func"])
        scenario.set_attribute_values("TRANSIT_SEGMENT", ["dwell_time", "transit_time_func"], data)
        return network

    def _add_cong_term_to_func(self, scenario):
        used_functions = set()
        any_non_zero = False
        for segment in scenario.get_network().transit_segments():
            if segment.transit_time_func != 0:
                used_functions.add("ft" + str(segment.transit_time_func))
                any_non_zero = True
        if not any_non_zero:
            raise Exception("All segments have a TTF of 0!")
        return list(used_functions)

    def _get_atts_congested(
        self,
        scenario,
        parameters,
        demand_matrix_list,
        connector_logit_truncation,
        headway_fraction_attribute_list,
        effective_headway_attribute_list,
        walk_time_perception_attribute_list,
        impedance_matrix_list,
    ):
        attributes = {
            "Scenario": "%s - %s" % (scenario, scenario.title),
            "Assignment Period": parameters["assignment_period"],
            "Iterations": parameters["iterations"],
            "Normalized Gap": parameters["norm_gap"],
            "Relative Gap": parameters["rel_gap"],
            "congestion function": self._get_func_spec(parameters),
            "spec": self._get_base_assignment_spec(
                scenario,
                parameters,
                demand_matrix_list,
                connector_logit_truncation,
                headway_fraction_attribute_list,
                effective_headway_attribute_list,
                walk_time_perception_attribute_list,
                impedance_matrix_list,
                consider_total_impedance=True,
            ),
        }
        return attributes

    def _get_func_spec(self, parameters):
        partial_spec = (
            "import math \ndef calc_segment_cost(transit_volume, capacity, segment):\n    cap_period = "
            + str(parameters["assignment_period"])
        )
        i = 0
        for ttf_def in parameters["ttf_definitions"]:
            ttf = ttf_def["ttf"]
            alpha = ttf_def["congestion_exponent"]
            beta = (2 * alpha - 1) / (2 * alpha - 2)
            alpha_square = alpha ** 2
            beta_square = beta ** 2
            perception = ttf_def["congestion_perception"]
            if i == 0:
                partial_spec += (
                    "\n    if segment.transit_time_func == "
                    + f"{ttf}"
                    + ": \n        return max(0,("
                    + f"{perception}"
                    + " * (1 + math.sqrt("
                    + str(alpha_square)
                    + " * \n            (1 - transit_volume / capacity) ** 2 + "
                    + str(beta_square)
                    + ") - "
                    + str(alpha)
                    + " \n            * (1 - transit_volume / capacity) - "
                    + str(beta)
                    + ")))"
                )
            else:
                partial_spec += (
                    "\n    elif segment.transit_time_func == "
                    + f"{ttf}"
                    + ": \n        return max(0,("
                    + f"{perception}"
                    + " * (1 + math.sqrt("
                    + str(alpha_square)
                    + " *  \n            (1 - transit_volume / capacity) ** 2 + "
                    + str(beta_square)
                    + ") - "
                    + str(alpha)
                    + " \n            * (1 - transit_volume / capacity) - "
                    + str(beta)
                    + ")))"
                )
            i += 1
        partial_spec += '\n    else: \n        raise Exception("ttf=%s congestion values not defined in input" %s segment.transit_time_func)'
        func_spec = {
            "type": "CUSTOM",
            "assignment_period": parameters["assignment_period"],
            "orig_func": False,
            "congestion_attribute": "us3",
            "python_function": partial_spec,
        }
        return func_spec

    def _get_base_assignment_spec(
        self,
        scenario,
        parameters,
        demand_matrix_list,
        connector_logit_truncation,
        headway_fraction_attribute_list,
        effective_headway_attribute_list,
        walk_time_perception_attribute_list,
        impedance_matrix_list,
        consider_total_impedance=False,
    ):
        base_spec = []
        modes = []
        for i, transit_class in enumerate(parameters["transit_classes"]):
            fare_perception = transit_class["fare_perception"]
            modes.append(transit_class["mode"])
            if fare_perception != 0.0:
                fare_perception = 60.0 / fare_perception
            base_spec.append(
                {
                    "modes": [transit_class["mode"]],
                    "demand": demand_matrix_list[i].id,
                    "waiting_time": {
                        "headway_fraction": headway_fraction_attribute_list[i].id,
                        "effective_headways": effective_headway_attribute_list[i].id,
                        "spread_factor": 1,
                        "perception_factor": transit_class["wait_time_perception"],
                    },
                    "boarding_time": {
                        "at_nodes": None,
                        "on_lines": {"penalty": "ut3", "perception_factor": transit_class["board_penalty_perception"]},
                    },
                    "boarding_cost": {"at_nodes": {"penalty": 0, "perception_factor": 1}, "on_lines": None},
                    "in_vehicle_time": {"perception_factor": "us2"},
                    "in_vehicle_cost": {
                        "penalty": transit_class["segment_fare_attribute"],
                        "perception_factor": transit_class["segment_fare_attribute"],
                    },
                    "aux_transit_time": {"perception_factor": walk_time_perception_attribute_list[i].id},
                    "aux_transit_cost": {
                        "penalty": transit_class["link_fare_attribute_id"],
                        "perception_factor": fare_perception,
                    },
                    "connector_to_connector_path_prohibition": None,
                    "od_results": {"total_impedance": impedance_matrix_list[i].id},
                    "flow_distribution_between_lines": {"consider_total_impedance": consider_total_impedance},
                    "save_strategies": True,
                    "type": "EXTENDED_TRANSIT_ASSIGNMENT",
                }
            )
        for i in range(0, len(base_spec)):
            if parameters["node_logit_scale"]:
                base_spec[i]["flow_distribution_at_origins"] = {
                    "choices_at_origins": {
                        "choice_points": "ALL_ORIGINS",
                        "choice_set": "ALL_CONNECTORS",
                        "logit_parameters": {
                            "scale": parameters["origin_distribution_logit_scale"],
                            "truncation": connector_logit_truncation,
                        },
                    },
                    "fixed_proportions_on_connectors": None,
                }
            base_spec[i]["performance_settings"] = {"number_of_processors": self.number_of_processors}
            if scenario.extra_attribute("@node_logit") != None:
                base_spec[i]["flow_distribution_at_regular_nodes_with_aux_transit_choices"] = {
                    "choices_at_regular_nodes": {
                        "choice_points": "@node_logit",
                        "aux_transit_choice_set": "ALL_POSSIBLE_LINKS",
                        "logit_parameters": {"scale": 0.2, "truncation": 0.05},
                    }
                }
            else:
                base_spec[i]["flow_distribution_at_regular_nodes_with_aux_transit_choices"] = {
                    "choices_at_regular_nodes": "OPTIMAL_STRATEGY"
                }
            mode_list = []
            partial_network = scenario.get_partial_network(["MODE"], True)
            mode_list = partial_network.modes() if modes[i] == "*" else modes[i]
            base_spec[i]["journey_levels"] = [
                {
                    "description": "Walking",
                    "destinations_reachable": parameters["walk_all_way_flag"],
                    "transition_rules": self._create_journey_level_modes(mode_list, 0),
                    "boarding_time": None,
                    "boarding_cost": None,
                    "waiting_time": None,
                },
                {
                    "description": "Transit",
                    "destinations_reachable": True,
                    "transition_rules": self._create_journey_level_modes(mode_list, 1),
                    "boarding_time": None,
                    "boarding_cost": None,
                    "waiting_time": None,
                },
            ]
        return base_spec

    def _run_extended_transit_assignment(
        self,
        scenario,
        parameters,
        iteration,
        strategies,
        demand_matrix_list,
        headway_fraction_attribute_list,
        effective_headway_attribute_list,
        walk_time_perception_attribute_list,
        impedance_matrix_list,
    ):
        if iteration == 0:
            msg = "Prepare Initial Assignment"
        else:
            msg = "Prepare Transit Assignment"
        assignment_tool = extended_assignment_tool
        assignment_tool.iterative_transit_assignment = True
        with _trace(msg):
            for index, transit_class in enumerate(parameters["transit_classes"]):
                spec = self._get_transit_assignment_spec(
                    scenario,
                    index,
                    transit_class["fare_perception"],
                    transit_class["mode"],
                    demand_matrix_list,
                    headway_fraction_attribute_list,
                    effective_headway_attribute_list,
                    walk_time_perception_attribute_list,
                    impedance_matrix_list,
                    transit_class["wait_time_perception"],
                    self.consider_total_impedance,
                    self.use_logit_connector_choice,
                    parameters["origin_distribution_logit_scale"],
                    self.connector_logit_truncation,
                    self.number_of_processors,
                    parameters["node_logit_scale"],
                    parameters["walk_all_way_flag"],
                    transit_class["board_penalty_perception"],
                    transit_class["segment_fare_attribute"],
                    transit_class["link_fare_attribute_id"],
                )
                if index == 0:
                    self._tracker.run_tool(
                        assignment_tool,
                        specification=spec,
                        scenario=scenario,
                        add_volumes=False,
                    )
                else:
                    self._tracker.run_tool(
                        assignment_tool,
                        specification=spec,
                        scenario=scenario,
                        add_volumes=True,
                    )
                strategies_name = "Iteration %s %s" % (iteration, transit_class["name"])
                strategies_file = strategies.add_strat_file(strategies_name)
                classData = _db_utils.get_multi_class_strat(strategies, transit_class["name"])
                classData["strat_files"].append(strategies_name)
                values = scenario.get_attribute_values("TRANSIT_SEGMENT", ["transit_time"])
                strategies_file.add_attr_values("TRANSIT_SEGMENT", "transit_time", values[1])

    def _prep_strategy_files(self, scenario, parameters, demand_matrix_list):
        strategies = scenario.transit_strategies
        strategies.clear()
        _time.sleep(0.05)
        data = {
            "type": "CONGESTED_TRANSIT_ASSIGNMENT",
            "namespace": str(self),
            "custom_status": True,
            "per_strat_attributes": {"TRANSIT_SEGMENT": ["transit_time"]},
        }
        # mode_int_ids = scenario.get_attribute_values("MODE", [])[0]

        def format_modes(modes):
            if "*" in modes:
                modes = [m for m in scenario.modes() if m.type in ("TRANSIT", "AUX_TRANSIT")]
            modes = [str(m) for m in modes]
            return "".join(modes)

        class_data = []
        for i, transit_class in enumerate(parameters["transit_classes"]):
            name = transit_class["name"]
            demand = _MODELLER.matrix_snapshot(_bank.matrix(demand_matrix_list[i]))
            modes = transit_class["mode"]
            class_data.append(
                {
                    "name": name,
                    "modes": format_modes(modes),
                    "demand": demand,
                    "strat_files": [],
                }
            )
        data["classes"] = class_data
        data["multi_class"] = True
        strategies.data = data
        return strategies

    def _compute_assigned_class_demand(self, scenario, demand_matrix_list, number_of_processors):
        assigned_demand = []
        for i in range(0, len(demand_matrix_list)):
            matrix_calc_spec = {
                "type": "MATRIX_CALCULATION",
                "expression": str(demand_matrix_list[i]) + " * (p.ne.q)",
                # "expression": "mf10",
                "aggregation": {"origins": "+", "destinations": "+"},
            }
            report = matrix_calc_tool(
                specification=matrix_calc_spec,
                scenario=scenario,
                num_processors=number_of_processors,
            )
            trips = report["result"]
            if trips <= 0:
                raise Exception("Invalid number of trips assigned")
            assigned_demand.append(trips)
        return assigned_demand

    def _compute_min_trip_impedance(self, scenario, demand_matrix_list, assigned_class_demand, impedance_matrix_list):
        average_min_trip_impedance = 0.0
        class_imped = []
        for i in range(0, len(assigned_class_demand)):
            matrix_calc_spec = {
                "type": "MATRIX_CALCULATION",
                "expression": str(impedance_matrix_list[i].id)
                + "*"
                + str(demand_matrix_list[i])
                + "/"
                + str(assigned_class_demand[i]),
                "aggregation": {"origins": "+", "destinations": "+"},
            }
            report = matrix_calc_tool(
                specification=matrix_calc_spec,
                scenario=scenario,
                num_processors=self.number_of_processors,
            )
            class_imped.append(float(report["result"]))
        for i in range(0, len(assigned_class_demand)):
            average_min_trip_impedance += class_imped[i] * assigned_class_demand[i]
        average_min_trip_impedance = average_min_trip_impedance / sum(assigned_class_demand)
        return average_min_trip_impedance

    def _get_congestion_costs(self, parameters, network, assigned_total_demand):
        congestion_cost = 0.0
        for line in network.transit_lines():
            capacity = float(line.total_capacity)
            for segment in line.segments():
                flow_X_time = float(segment.voltr) * (float(segment.timtr) - float(segment.dwell_time))
                congestion = self._calculate_segment_cost(parameters, float(segment.voltr), capacity, segment)
                congestion_cost += flow_X_time * congestion
        return congestion_cost / assigned_total_demand

    def _prepare_network(self, scenario, parameters, stsu_att):
        network = scenario.get_partial_network(
            ["LINK", "TRANSIT_SEGMENT", "TRANSIT_LINE", "TRANSIT_VEHICLE"],
            include_attributes=False,
        )
        attributes_to_copy = {
            "TRANSIT_VEHICLE": ["total_capacity"],
            "NODE": ["initial_boardings", "final_alightings"],
            "LINK": ["length", "aux_transit_volume", "auto_time"],
            "TRANSIT_LINE": ["headway", str(stsu_att.id), "data2", "@doors"],
            "TRANSIT_SEGMENT": [
                "dwell_time",
                "transit_volume",
                "transit_time",
                "transit_boardings",
                "transit_time_func",
                "@tstop",
            ],
        }
        if scenario.extra_attribute("@tstop") is None:
            if parameters["surface_transit_speed"] == False:
                attributes_to_copy["TRANSIT_SEGMENT"].remove("@tstop")
            else:
                raise Exception(
                    "@tstop attribute needs to be defined. @tstop is an integer that shows how many transit stops are on each transit segment."
                )
        if "auto_time" not in scenario.attributes("LINK"):
            if parameters["surface_transit_speed"] == False:
                attributes_to_copy["LINK"].remove("auto_time")
            else:
                raise Exception("An auto assignment needs to be present on the scenario")
        if scenario.extra_attribute("@doors") is None:
            attributes_to_copy["TRANSIT_LINE"].remove("@doors")

        for type, atts in attributes_to_copy.items():
            atts = list(atts)
            data = scenario.get_attribute_values(type, atts)
            network.set_attribute_values(type, atts, data)
        for type, mapping in self._attribute_mapping().items():
            for source, dest in mapping.items():
                network.copy_attribute(type, source, dest)
        network.create_attribute("TRANSIT_SEGMENT", "current_voltr")
        network.create_attribute("TRANSIT_SEGMENT", "cost")
        network.create_attribute("TRANSIT_LINE", "total_capacity")
        network.copy_attribute("TRANSIT_SEGMENT", "transit_time", "uncongested_time")
        network.copy_attribute("TRANSIT_SEGMENT", "dwell_time", "base_dwell_time")
        for line in network.transit_lines():
            line.total_capacity = 60.0 * parameters["assignment_period"] * line.vehicle.total_capacity / line.headway
        return network

    def _get_transit_assignment_spec(
        self,
        scenario,
        index,
        fare_perception,
        modes,
        demand_matrix_list,
        headway_fraction_attribute_list,
        effective_headway_attribute_list,
        walk_time_perception_attribute_list,
        impedance_matrix_list,
        wait_time_perception,
        consider_total_impedance,
        use_logit_connector_choice,
        origin_distribution_logit_scale,
        connector_logit_truncation,
        number_of_processors,
        node_logit_scale,
        walk_all_way_flag,
        board_penalty_perception,
        segment_fare_attribute,
        link_fare_attribute_id,
    ):

        if fare_perception == 0.0:
            fare_perception = 0.0
        else:
            fare_perception = 60.0 / fare_perception

        base_spec = {
            "modes": [modes],
            "demand": demand_matrix_list[index].id,
            "waiting_time": {
                "headway_fraction": headway_fraction_attribute_list[index].id,
                "effective_headways": effective_headway_attribute_list[index].id,
                "spread_factor": 1,
                "perception_factor": wait_time_perception,
            },
            "boarding_time": {
                "at_nodes": None,
                "on_lines": None,
                "global": {"penalty": 0, "perception_factor": 1},
            },
            "boarding_cost": {
                "at_nodes": None,
                "on_lines": None,
                "global": {"penalty": 0, "perception_factor": 1},
            },
            "in_vehicle_time": {"perception_factor": "us2"},
            "in_vehicle_cost": {
                "penalty": segment_fare_attribute,
                "perception_factor": fare_perception,
            },
            "aux_transit_time": {"perception_factor": walk_time_perception_attribute_list[index].id},
            "aux_transit_cost": {
                "penalty": link_fare_attribute_id,
                "perception_factor": fare_perception,
            },
            "connector_to_connector_path_prohibition": None,
            "od_results": {"total_impedance": impedance_matrix_list[index].id},
            "flow_distribution_between_lines": {"consider_total_impedance": consider_total_impedance},
            "save_strategies": True,
            "type": "EXTENDED_TRANSIT_ASSIGNMENT",
        }
        if use_logit_connector_choice:
            base_spec["flow_distribution_at_origins"] = {
                "choices_at_origins": {
                    "choice_points": "ALL_ORIGINS",
                    "choice_set": "ALL_CONNECTORS",
                    "logit_parameters": {
                        "scale": origin_distribution_logit_scale,
                        "truncation": connector_logit_truncation,
                    },
                },
                "fixed_proportions_on_connectors": None,
            }
        base_spec["performance_settings"] = {"number_of_processors": number_of_processors}
        if node_logit_scale is not False:
            base_spec["flow_distribution_at_regular_nodes_with_aux_transit_choices"] = {
                "choices_at_regular_nodes": {
                    "choice_points": "ui1",
                    "aux_transit_choice_set": "ALL_POSSIBLE_LINKS",
                    "logit_parameters": {
                        "scale": node_logit_scale,
                        "truncation": connector_logit_truncation,
                    },
                }
            }
        else:
            base_spec["flow_distribution_at_regular_nodes_with_aux_transit_choices"] = {
                "choices_at_regular_nodes": "OPTIMAL_STRATEGY"
            }
        mode_list = []
        partial_network = scenario.get_partial_network(["MODE"], True)
        mode_list = partial_network.modes() if modes == "*" else modes
        # if all modes are selected for class, get all transit modes for journey levels
        base_spec["journey_levels"] = [
            {
                "description": "Walking",
                "destinations_reachable": walk_all_way_flag,
                "transition_rules": self._create_journey_level_modes(mode_list, 0),
                "boarding_time": {
                    "at_nodes": None,
                    "on_lines": {"penalty": "ut3", "perception_factor": board_penalty_perception},
                    "global": None,
                    "on_segments": None,
                },
                "boarding_cost": None,
                "waiting_time": None,
            },
            {
                "description": "Transit",
                "destinations_reachable": True,
                "transition_rules": self._create_journey_level_modes(mode_list, 1),
                "boarding_time": {
                    "at_nodes": None,
                    "on_lines": {"penalty": "ut2", "perception_factor": board_penalty_perception},
                    "global": None,
                    "on_segments": None,
                },
                "boarding_cost": None,
                "waiting_time": None,
            },
        ]
        return base_spec

    def _attribute_mapping(self):
        atts = {
            "NODE": {"initial_boardings": "inboa", "final_alightings": "fiali"},
            "LINK": {"aux_transit_volume": "volax"},
            "TRANSIT_SEGMENT": {
                "transit_time": "timtr",
                "transit_volume": "voltr",
                "transit_boardings": "board",
            },
        }
        return atts

    def _calculate_segment_cost(self, parameters, transit_volume, capacity, segment):
        cost = 0
        for ttf_def in parameters["ttf_definitions"]:
            ttf = segment.transit_time_func
            if ttf == ttf_def["ttf"]:
                alpha = ttf_def["congestion_exponent"]
                beta = (2 * alpha - 1) / (2 * alpha - 2)
                alpha_square = alpha ** 2
                beta_square = beta ** 2
                cost = ttf_def["congestion_perception"] * (
                    1
                    + math.sqrt(alpha_square * (1 - transit_volume / capacity) ** 2 + beta_square)
                    - alpha * (1 - transit_volume / capacity)
                    - beta
                )
                return max(0, cost)
        return 0

    def _compute_segment_costs(self, scenario, parameters, network):
        excess_km = 0.0
        for line in network.transit_lines():
            capacity = line.total_capacity
            for segment in line.segments():
                volume = segment.current_voltr = segment.voltr
                length = segment.link.length
                if volume >= capacity:
                    excess = volume - capacity
                    excess_km += excess * length
                segment.cost = self._calculate_segment_cost(parameters, segment.voltr, capacity, segment)
        values = network.get_attribute_values("TRANSIT_SEGMENT", ["cost"])
        scenario.set_attribute_values("TRANSIT_SEGMENT", ["data3"], values)
        return excess_km

    def _update_network(self, scenario, network):
        attribute_mapping = self._attribute_mapping()
        attribute_mapping["TRANSIT_SEGMENT"]["dwell_time"] = "dwell_time"
        for type, mapping in attribute_mapping.items():
            attributes = mapping.keys()
            data = scenario.get_attribute_values(type, attributes)
            network.set_attribute_values(type, attributes, data)
        return network

    def _find_step_size(
        self, parameters, network, average_min_trip_impedance, average_impedance, assigned_total_demand, alphas
    ):
        approx1 = 0.0
        approx2 = 0.5
        approx3 = 1.0
        grad1 = average_min_trip_impedance - average_impedance
        grad2 = self._compute_gradient(parameters, assigned_total_demand, approx2, network)
        grad2 += average_min_trip_impedance - average_impedance
        grad3 = self._compute_gradient(parameters, assigned_total_demand, approx3, network)
        grad3 += average_min_trip_impedance - average_impedance
        for m_steps in range(0, 21):
            h1 = approx2 - approx1
            h2 = approx3 - approx2
            delta1 = (grad2 - grad1) / h1
            delta2 = (grad3 - grad2) / h2
            d = (delta2 - delta1) / (h1 + h2)
            b = h2 * d + delta2
            t1 = grad3 * d * 4
            t2 = b ** 2
            if t2 > t1:
                temp = math.sqrt(t2 - t1)
            else:
                temp = 0.0
            if abs(b - temp) < abs(b + temp):
                temp = b + temp
            else:
                temp = b - temp
            if temp == 0.0:
                raise Exception(
                    "Congested transit assignment cannot be applied to this transit network, please use Capacitated transit assignment instead."
                )
            temp = -2 * grad3 / temp
            lambdaK = approx3 + temp
            temp = abs(temp) * 100000.0
            if temp < 100:
                break
            grad = self._compute_gradient(parameters, assigned_total_demand, lambdaK, network)
            grad += average_min_trip_impedance - average_impedance
            approx1 = approx2
            approx2 = approx3
            approx3 = lambdaK
            grad1 = grad2
            grad2 = grad3
            grad3 = grad
        lambdaK = max(0.0, min(1.0, lambdaK))
        alphas = [a * (1 - lambdaK) for a in alphas]
        alphas.append(lambdaK)
        return lambdaK, alphas

    def _compute_gradient(self, parameters, assigned_total_demand, lambdaK, network):
        value = 0.0
        for line in network.transit_lines():
            capacity = float(line.total_capacity)
            for segment in line.segments():
                assigned_volume = float(segment.current_voltr)
                cumulative_volume = float(segment.transit_volume)
                t0 = (segment.transit_time - segment.dwell_time) / (1 + segment.cost)
                volume_difference = cumulative_volume - assigned_volume
                if lambdaK == 1:
                    adjusted_volume = cumulative_volume
                else:
                    adjusted_volume = assigned_volume + lambdaK * (cumulative_volume - assigned_volume)
                cost_difference = self._calculate_segment_cost(
                    parameters, adjusted_volume, capacity, segment
                ) - self._calculate_segment_cost(parameters, assigned_volume, capacity, segment)
                value += t0 * cost_difference * volume_difference
        return value / assigned_total_demand

    def _create_journey_level_modes(self, mode_list, level):
        ret = []
        for mode in mode_list:
            if mode.type == "TRANSIT":
                ret.append({"mode": mode.id, "next_journey_level": 1})
            elif mode.type == "AUX_TRANSIT":
                next_level = 1 if level >= 1 else 0
                ret.append({"mode": mode.id, "next_journey_level": next_level})
        return ret

    def _update_volumes(self, network, lambdaK):
        alpha = 1 - lambdaK
        for node in network.regular_nodes():
            node.inboa = node.inboa * alpha + node.initial_boardings * lambdaK
            node.fiali = node.fiali * alpha + node.final_alightings * lambdaK
        for link in network.links():
            link.volax = link.volax * alpha + link.aux_transit_volume * lambdaK
        for line in network.transit_lines():
            # capacity = float(line.total_capacity)
            # congested = False
            for segment in line.segments():
                segment.voltr = segment.voltr * alpha + segment.transit_volume * lambdaK
                segment.board = segment.board * alpha + segment.transit_boardings * lambdaK
        return

    def _compute_gaps(
        self,
        assigned_total_demand,
        lambdaK,
        average_min_trip_impedance,
        previous_average_min_trip_impedance,
        network,
    ):
        cngap = previous_average_min_trip_impedance - average_min_trip_impedance
        net_costs = self._compute_network_costs(assigned_total_demand, lambdaK, network)
        average_impedance = (
            lambdaK * average_min_trip_impedance + (1 - lambdaK) * previous_average_min_trip_impedance + net_costs
        )
        crgap = cngap / average_impedance
        norm_gap_difference = (self.NormGap - cngap) * 100000.0
        return (average_impedance, cngap, crgap, norm_gap_difference, net_costs)

    @contextmanager
    def _temp_stsu_ttfs(self, scenario, parameters):
        orig_ttf_values = scenario.get_attribute_values("TRANSIT_SEGMENT", ["transit_time_func"])
        ttfs_changed = []
        stsu_ttf_map = {}
        created = {}
        for ttf in parameters["ttf_definitions"]:
            for i in range(1, 100):
                func = "ft" + str(i)
                if scenario.emmebank.function(func) is None:
                    scenario.emmebank.create_function(func, "(length*60/us1)")
                    stsu_ttf_map[int(ttf["ttf"])] = int(func[2:])
                    if str(ttf["ttf"]) in parameters["xrow_ttf_range"]:
                        parameters["xrow_ttf_range"].add(int(func[2:]))
                    created[func] = True
                    break
        try:
            yield stsu_ttf_map, ttfs_changed
        finally:
            for func in created:
                if created[func] == True:
                    scenario.emmebank.delete_function(func)
            if True in ttfs_changed:
                scenario.set_attribute_values("TRANSIT_SEGMENT", ["transit_time_func"], orig_ttf_values)

    @_m.method(return_type=_m.TupleType)
    def percent_completed(self):
        return self._tracker.get_progress()

    @_m.method(return_type=str)
    def tool_run_msg_status(self):
        return self.tool_run_msg
