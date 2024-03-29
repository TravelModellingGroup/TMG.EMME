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
TMG Generate Full Network Set Tool
    
    This tool is only compatible with Emme 4.2 and later versions

    Authors: Eric Miller

    Latest revision by: WilliamsDiogu
    
    V 1.0.0 

    V 2.0.0 Refactored to work with XTMF2/TMGToolbox2 on 2022-07-20 by williamsDiogu   
"""
from re import split as _regex_split
import inro.modeller as _m
import traceback as _traceback
import multiprocessing
from contextlib import contextmanager

_MODELLER = _m.Modeller()
_util = _MODELLER.module("tmg2.utilities.general_utilities")
_tmg_tpb = _MODELLER.module("tmg2.utilities.TMG_tool_page_builder")
_edit = _MODELLER.module("tmg2.utilities.network_editing")
network_calc_tool = _MODELLER.tool("inro.emme.network_calculation.network_calculator")
_bank = _MODELLER.emmebank
_write = _m.logbook_write
_trace = _m.logbook_trace
force_error = _edit.ForceError
invalid_network_operation_error = _edit.InvalidNetworkOperationError
_m.TupleType = object
_m.ListType = list
_m.InstanceType = object


def naive_aggregation(departures, start, end):
    deltaTime = end - start
    numDep = len(departures)
    return deltaTime / numDep


def average_aggregation(departures, start, end):
    sum = 0
    counter = 0
    if len(departures) == 1:
        return end - start
    iter = departures.__iter__()
    prev_dep = next(iter)
    for dep in iter:
        headway = dep - prev_dep
        counter += 1
        sum += headway
        prev_dep = dep

    return sum / counter


class GenerateTimePeriodNetworks(_m.Tool()):
    version = "2.0.0"
    tool_run_msg = ""
    number_of_task = 10

    NAMED_AGGREGATORS = _edit.NAMED_AGGREGATORS

    @staticmethod
    def AVERAGE_BY_LENGTH_LINKS(att, link1, link2):
        a1 = link1[att]
        a2 = link2[att]
        l1 = link1.length
        l2 = link2.length

        return (a1 * l1 + a2 * l2) / (l1 + l2)

    @staticmethod
    def AVERAGE_BY_LENGTH_SEGMENTS(att, segment1, segment2):
        a1 = segment1[att]
        a2 = segment2[att]
        l1 = segment1.link.length
        l2 = segment2.link.length

        return (a1 * l1 + a2 * l2) / (l1 + l2)

    def __init__(self):
        self._tracker = _util.progress_tracker(self.number_of_task)
        self.number_of_processors = multiprocessing.cpu_count()
        self.naive_aggregation = 0

    def page(self):
        pb = _tmg_tpb.TmgToolPageBuilder(
            self,
            title="Generate FullNetwork Setv%s" % self.version,
            description="Generates a full network set for GTAModel V4.2.\
                        <br><br><b>Cannot be called from Modeller.</b>\
                        <br><br>Hard-coded assumptions:\
                        <font color='red'>This tool is only compatible with Emme 4.1.5 and later versions</font>",
            runnable=False,
            branding_text="- TMG Toolbox",
        )
        return pb.render()

    def __call__(self, parameters):
        scenario = _util.load_scenario(parameters["base_scenario_number"])
        try:
            self._execute(scenario, parameters)
        except Exception as e:
            raise Exception(_util.format_reverse_stack())

    def run_xtmf(self, parameters):
        base_scenario = _util.load_scenario(parameters["base_scenario_number"])
        try:
            self._execute(base_scenario, parameters)
        except Exception as e:
            raise Exception(_util.format_reverse_stack())

    def _execute(self, base_scenario, parameters):
        with _m.logbook_trace(
            name="{classname} v{version}".format(classname=(self.__class__.__name__), version=self.version),
            attributes=self._get_atts(base_scenario),
        ):
            network = base_scenario.get_network()
            self._check_transfer_mode_in_network(network, parameters["transfer_mode_string"])
            self._tracker.complete_task()
            print("Loaded network")
            node_filter_attribute = self._check_filter_attributes(
                base_scenario, parameters["node_filter_attribute"], description="Node"
            )
            stop_filter_attribute = self._check_filter_attributes(
                base_scenario, parameters["stop_filter_attribute"], description="Stop"
            )
            connector_filter_attribute = self._check_filter_attributes(
                base_scenario, parameters["connector_filter_attribute"], description="Connector"
            )
            for periods in parameters["time_periods"]:
                self._delete_old_scenario(periods["uncleaned_scenario_number"])
                self._delete_old_scenario(periods["cleaned_scenario_number"])
            self._tracker.complete_task()
            print("Deleted old scenarios")
            for periods in parameters["time_periods"]:
                network = base_scenario.get_network()
                network.create_attribute("TRANSIT_LINE", "trips", None)
                network.create_attribute("TRANSIT_LINE", "aggtype", None)
                bad_id_set = self._load_service_table(
                    network, periods["start_time"], periods["end_time"], parameters["transit_service_table_file"]
                ).union(
                    self._load_agg_type_select(
                        network,
                        parameters["transit_aggregation_selection_table_file"],
                        parameters["default_aggregation"],
                    )
                )
                self._tracker.complete_task()
                print("Loaded service table")
                if len(bad_id_set) > 0:
                    print("%s transit line IDs were not found in the network and were skipped." % len(bad_id_set))
                    _write("The following line IDs were not found in the network:")
                    for id in bad_id_set:
                        _write("%s" % id)
                self._tracker.complete_task()
                for index, alt_file in enumerate(parameters["additional_transit_alternative_table"]):
                    if index == 0 and alt_file["alternative_table_file"] is "":
                        self._process_transit_lines(network, periods["start_time"], periods["end_time"], None)
                    else:
                        if parameters["transit_alternative_table_file"] != "":
                            alt_data = self._load_alt_file(parameters["transit_alternative_table_file"])
                            self._process_transit_lines(network, periods["start_time"], periods["end_time"], alt_data)
                        else:
                            alt_data = None
                            self._process_transit_lines(network, periods["start_time"], periods["end_time"], alt_data)
                        if alt_data:
                            self._process_alt_lines(network, alt_data)
                print(
                    "Done processing transit lines for time period %s to %s"
                    % (periods["start_time"], periods["end_time"])
                )
                uncleaned_scenario = _bank.copy_scenario(base_scenario.id, periods["uncleaned_scenario_number"])
                uncleaned_scenario.title = periods["uncleaned_description"]
                print("Publishing network")
                network.delete_attribute("TRANSIT_LINE", "trips")
                network.delete_attribute("TRANSIT_LINE", "aggtype")
                uncleaned_scenario.publish_network(network)
            print("Created uncleaned time period networks and applied network updates")
            for periods in parameters["time_periods"]:
                uncleaned_scenario = _bank.scenario(periods["uncleaned_scenario_number"])
                # Apply Batch File to uncleaned scenario numbers
                if parameters["batch_edit_file"] != "":
                    self._apply_batch_edit_file(uncleaned_scenario, parameters["batch_edit_file"])
                    self._tracker.complete_task()
                    print("Edited transit line data in uncleaned scenario %s" % periods["uncleaned_scenario_number"])
                # Prorate transit speeds in uncleaned scenario numbers
                if parameters["line_filter_expression"] != "":
                    self._prorate_transit_speeds(
                        uncleaned_scenario, parameters["line_filter_expression"], parameters["unposted_speed_limit"]
                    )
                    print("Prorated transit speeds in uncleaned scenario %s" % periods["uncleaned_scenario_number"])
            base_network = base_scenario.get_network()
            self._tracker.complete_task()
            self._remove_extra_links(base_network, parameters["transfer_mode_string"])
            for periods in parameters["time_periods"]:
                clean_scenario = _bank.copy_scenario(
                    base_scenario.id, periods["cleaned_scenario_number"], copy_strat_files=False, copy_path_files=False
                )
                clean_scenario.title = periods["cleaned_description"]
                clean_scenario.publish_network(base_network, True)
            self._tracker.complete_subtask()
            _MODELLER.desktop.refresh_needed(True)

            self._parse_segment_aggregators(clean_scenario, parameters["attribute_aggregator"])
            self._tracker.complete_task()
            cleaned_network = clean_scenario.get_network()
            self._remove_extra_nodes(
                cleaned_network, node_filter_attribute, stop_filter_attribute, connector_filter_attribute
            )
            print("Cleaned networks")

    def _delete_old_scenario(self, scenario_number):
        if _bank.scenario(scenario_number) is not None:
            _bank.delete_scenario(scenario_number)

    def _get_atts(self, scenario):
        atts = {"Scenario": str(scenario.id), "Version": self.version, "self": self.__MODELLER_NAMESPACE__}
        return atts

    def _check_filter_attributes(self, base_scenario, filer_attribute_id, description=""):
        if filer_attribute_id.lower() == "none":
            filer_attribute_id = None
        else:
            if base_scenario.extra_attribute(filer_attribute_id) is None:
                raise Exception("%s filter attribute %s does not exist" % (filer_attribute_id, description))
        return filer_attribute_id

    def _load_service_table(self, network, start_time, end_time, transit_service_table_file):
        bounds = _util.float_range(start_time, end_time)
        bad_ids = set()
        if transit_service_table_file != "" or transit_service_table_file != "none":
            with _util.open_csv_reader(transit_service_table_file) as service_file:
                for line_number, service_file_list in enumerate(service_file):
                    emme_id_col = service_file_list[0]
                    departure_col = service_file_list[1]
                    arrival_col = service_file_list[2]
                    transit_line = network.transit_line(emme_id_col)
                    if transit_line is None:
                        bad_ids.add(emme_id_col)
                        continue
                    try:
                        departure = self._parse_string_time(departure_col)
                        arrival = self._parse_string_time(arrival_col)
                    except Exception as e:
                        print("Line " + str(line_number + 1) + " skipped in CSV file: " + str(e))
                        continue
                    if not departure in bounds:
                        continue
                    trip = (departure, arrival)
                    if transit_line.trips is None:
                        transit_line.trips = [trip]
                    else:
                        transit_line.trips.append(trip)
        return bad_ids

    def _load_agg_type_select(self, network, transit_aggregation_selection_table_file, default_aggregation):
        bad_ids = set()
        if transit_aggregation_selection_table_file != "" or transit_aggregation_selection_table_file != "none":
            with _util.open_csv_reader(transit_aggregation_selection_table_file) as aggregate_file:
                for line_number, aggregate_file_list in enumerate(aggregate_file):
                    emme_id_col = aggregate_file_list[0]
                    agg_col = aggregate_file_list[1]
                    transit_line = network.transit_line(emme_id_col)
                    if transit_line is None:
                        bad_ids.add(emme_id_col)
                        continue
                    if default_aggregation == self.naive_aggregation:
                        aggregation = "n"
                        if agg_col[0] == "a" or agg_col[0] == "A":
                            aggregation = "a"
                        elif agg_col[0] == "":
                            continue
                    else:
                        aggregation = "a"
                        if agg_col[0] == "n" or agg_col[0] == "N":
                            aggregation = "n"
                        elif agg_col[0] == "":
                            continue
                    if transit_line.aggtype is None:
                        transit_line.aggtype = aggregation
        return bad_ids

    def _parse_string_time(self, time_string):
        try:
            hms = time_string.split(":")
            if len(hms) != 3:
                raise IOError()
            hours = int(hms[0])
            minutes = int(hms[1])
            seconds = int(hms[2])
            return hours * 3600 + minutes * 60 + float(seconds)
        except Exception as e:
            raise IOError("Error passing time %s: %s" % (time_string, e))

    def _load_batch_file(self, scenario, batch_edit_file):
        if batch_edit_file != "" or batch_edit_file != "none":
            with open(batch_edit_file) as reader:
                header = reader.readline()
                cells = header.strip().split(",")
                filter_col = cells.index("filter")
                headway_title = scenario.id + "_hdwchange"
                speed_title = scenario.id + "_spdchange"
                try:
                    headway_col = cells.index(headway_title)
                except Exception as e:
                    msg = "Error. No headway match for specified scenario: '%s'." % scenario.id
                    _m._write(msg)
                    print(msg)
                    return
                try:
                    speed_col = cells.index(speed_title)
                except Exception as e:
                    msg = "Error. No speed match for specified scenario: '%s'." % scenario.id
                    _m._write(msg)
                    print(msg)
                    return
                instruction_data = {}
                for num, line in enumerate(reader):
                    cells = line.strip().split(",")
                    filter = cells[filter_col]
                    if cells[headway_col]:
                        hdw = cells[headway_col]
                    else:
                        # if the headway column is left blank, carry forward a factor of 1
                        hdw = 1
                    if cells[speed_col]:
                        spd = cells[speed_col]
                    else:
                        spd = 1
                    instruction_data[filter] = (float(hdw), float(spd))

        return instruction_data

    def _apply_line_changes(self, scenario, input_data):
        for filter, factors in input_data.items():
            if factors[0] != 1:
                spec = {
                    "type": "NETWORK_CALCULATION",
                    "expression": str(factors[0]) + "*hdw",
                    "result": "hdw",
                    "selections": {"transit_line": filter},
                }
                network_calc_tool(spec, scenario)
            if factors[1] != 1:
                spec = {
                    "type": "NETWORK_CALCULATION",
                    "expression": str(factors[1]) + "*speed",
                    "result": "speed",
                    "selections": {"transit_line": filter},
                }
                network_calc_tool(spec, scenario)

    def _process_transit_lines(self, network, start, end, alt_data):
        bounds = _util.float_range(0.01, 1000.0)
        to_delete = set()
        if alt_data is not None:
            # check if any headways or speeds are zero. Allow those lines to be deletable
            for k, v in alt_data.items():
                if v[0] == 0 or v[1] == 0:
                    del alt_data[k]
            do_not_delete = alt_data.keys()
        else:
            do_not_delete = []
        self._tracker.start_process(network.element_totals["transit_lines"])
        for line in network.transit_lines():
            # Pick aggregation type for given line
            if line.aggtype == "n":
                aggregator = naive_aggregation
            elif line.aggtype == "a":
                aggregator = average_aggregation
            elif self.DefaultAgg == "n":
                aggregator = naive_aggregation
                _write("Default aggregation was used for line %s" % (line.id))
            else:
                aggregator = average_aggregation
                _write("Default aggregation was used for line %s" % (line.id))
            # Line trips list is empty or None
            if not line.trips:
                if do_not_delete:
                    # don't delete lines whose headways we wish to manually set
                    if line.id not in do_not_delete:
                        to_delete.add(line.id)
                elif line.id not in to_delete:
                    to_delete.add(line.id)
                self._tracker.complete_subtask()
                continue
            # Calc line headway
            departures = [dep for dep, arr in line.trips]
            departures.sort()
            # Convert from seconds to minutes
            headway = aggregator(departures, start, end) / 60.0
            if not headway in bounds:
                print("%s: %s" % (line.id, headway))
            line.headway = headway
            # Calc line speed
            sumTimes = 0
            for dep, arr in line.trips:
                sumTimes += arr - dep
            # Convert from seconds to hours
            avgTime = sumTimes / len(line.trips) / 3600.0
            # Given in km
            length = sum([seg.link.length for seg in line.segments()])
            # km/hr
            speed = length / avgTime
            if not speed in bounds:
                print("%s: %s" % (line.id, speed))
            line.speed = speed
            self._tracker.complete_subtask()
        for id in to_delete:
            network.delete_transit_line(id)
        self._tracker.complete_task()

    def _load_alt_file(self, alternative_table_file, start_time):
        alt_data = {}
        with open(alternative_table_file) as reader:
            header = reader.readline()
            cells = header.strip().split(",")

            emme_id_col = cells.index("emme_id")
            headway_title = "{:0>4.0f}".format(start_time) + "_hdw"
            speed_title = "{:0>4.0f}".format(start_time) + "_spd"
            try:
                headway_col = cells.index(headway_title)
            except Exception as e:
                msg = "Error. No headway match for specified time period start: '%s'." % start_time
                _write(msg)
                print(msg)
            try:
                speed_col = cells.index(speed_title)
            except Exception as e:
                msg = "Error. No speed match for specified time period start: '%s'." % start_time
                _write(msg)
                print(msg)

            local_alt_data = {}

            for num, line in enumerate(reader):
                cells = line.strip().split(",")

                id = cells[emme_id_col]
                hdw = cells[headway_col]
                spd = cells[speed_col]
                if id not in local_alt_data:
                    local_alt_data[id] = (float(hdw), float(spd))
                else:
                    raise ValueError("Line %s has multiple entries. Please revise your alt file." % id)
            # now that the file has been loaded in move it into the combined altFile dictionary
        for id, data in local_alt_data.items():
            alt_data[id] = data
        return alt_data

    def _process_alt_lines(self, network, alt_data):
        bounds = _util.float_range(0.01, 1000.0)
        for key, data in alt_data.items():
            line = network.transit_line(key)
            if line:
                # a headway of 9999 indicates an unused line
                if data[0] == 9999:
                    network.delete_transit_line(line.id)
                    continue
                # a headway of 0 allows for a line to be in the alt data file without changing existing headway
                elif data[0] == 0:
                    print("%s: %s" % (line.id, data[0]))
                    _write("Headway = 0 in alt file. Headway remains as in base.  %s" % line.id)
                elif not data[0] in bounds:
                    print("%s: %s" % (line.id, data[0]))
                    _write("Headway out of bounds line %s: %s minutes. Line removed from network." % (line.id, data[0]))
                    network.delete_transit_line(line.id)
                    continue
                line.headway = data[0]
                if not data[1] in bounds:
                    print("%s: %s" % (line.id, data[1]))
                    _write("Speed out of bounds line %s: %s km/h. Speed remains as in base." % (line.id, data[1]))
                    continue
                line.speed = data[1]

    def _process_line(self, line, unposted_speed_limit):
        if line.speed <= 0:
            return
        free_flow_time = 0
        for segment in line.segments():
            speed = segment.link.data2
            if speed == 0:
                speed = unposted_speed_limit
            free_flow_time += segment.link.length / speed
        # In km
        line_length = sum([seg.link.length for seg in line.segments()])
        scheduled_cycle_time = line_length / line.speed
        factor = free_flow_time / scheduled_cycle_time

        for segment in line.segments():
            speed = segment.link.data2
            if speed == 0:
                speed = unposted_speed_limit
            segment.data1 = speed * factor

    def _get_net_calc_spec(self, flag_attribute_id, line_filter_expression):
        return {
            "result": flag_attribute_id,
            "expression": "1",
            "aggregation": None,
            "selections": {"transit_line": line_filter_expression},
            "type": "NETWORK_CALCULATION",
        }

    def _apply_batch_edit_file(self, scenario, batch_edit_file):
        changes_to_apply = self._load_batch_file(scenario, batch_edit_file)
        print("Instruction file loaded")
        if changes_to_apply:
            self._apply_line_changes(scenario, changes_to_apply)
            print("Headway and speed changes applied")
        else:
            print("No changes available in this scenario")

    def _prorate_transit_speeds(self, scenario, line_filter_expression, unposted_speed_limit):
        if int(scenario.element_totals["transit_lines"]) == 0:
            return 0
        with self._line_attribute_manager(scenario) as flag_attribute_id:
            with _trace("flagging selected lines"):
                self._tracker.run_tool(
                    network_calc_tool,
                    self._get_net_calc_spec(flag_attribute_id, line_filter_expression),
                    scenario,
                )
            network = scenario.get_network()
            flagged_lines = [line for line in network.transit_lines() if line[flag_attribute_id] == 1]
            print(flagged_lines)
            if len(flagged_lines) == 0:
                return 0
            self._tracker.start_process(len(flagged_lines))
            for line in flagged_lines:
                self._process_line(line, unposted_speed_limit)
                self._tracker.complete_subtask()
            self._tracker.complete_task()
            scenario.publish_network(network)
        return len(flagged_lines)

    def _remove_extra_links(self, base_network, transfer_mode_string):
        self._remove_transit_only_links_with_no_lines(base_network)
        self._remove_dead_end_links(base_network)
        self._create_transfer_mode_id_string(base_network, transfer_mode_string)
        self._tracker.complete_task()
        self._remove_stranded_nodes(base_network)
        self._tracker.start_process(2)

    def _remove_transit_only_links_with_no_lines(self, network):
        self._tracker.complete_task()
        for link in network.links():
            has_transit = False
            for segment in link.segments():
                has_transit = True
            transit_only = True
            if has_transit == False:
                for mode in link.modes:
                    if mode.type != "TRANSIT":
                        transit_only = False
                if transit_only == True:
                    network.delete_link(link.i_node, link.j_node)

    def _remove_dead_end_links(self, network):
        for link in network.links():
            has_transit = False
            for segment in link.segments():
                has_transit = True
            dead_start = True
            dead_end = True
            if has_transit == False:
                start_node = link.i_node
                end_node = link.j_node
                if start_node.is_centroid:
                    dead_start = False
                else:
                    for in_link in start_node.incoming_links():
                        if in_link.i_node != link.j_node:
                            dead_start = False
                if end_node.is_centroid:
                    dead_end = False
                else:
                    for out_link in end_node.outgoing_links():
                        if out_link.j_node != link.i_node:
                            dead_end = False
                if dead_start or dead_end:
                    network.delete_link(start_node, end_node)

    def _create_transfer_mode_id_string(self, network, transfer_mode_string):
        transfer_modes = set()
        for m in transfer_mode_string:
            transfer_modes.add(network.mode(m))
        for link in network.links():
            link_modes = link.modes
            # check if link has at least one transfer mode
            if len(link_modes.intersection(transfer_modes)) > 0:
                start_node = link.i_node
                end_node = link.j_node
                start_stop = False
                end_stop = False
                start_road = False
                end_road = False
                for in_link in start_node.incoming_links():
                    # only check if non-reverse links are on the road network
                    if in_link.i_node != link.j_node:
                        for mode in in_link.modes:
                            if mode.type != "TRANSIT" and mode not in transfer_modes:
                                start_road = True
                    # check if start node is end of line stop
                    for segment in in_link.segments():
                        if segment.line.segment(str(start_node.number) + "-0") != False:
                            start_stop = True
                for out_link in start_node.outgoing_links():
                    # check if start node has transit stops
                    for segment in out_link.segments():
                        if segment.allow_boardings or segment.allow_alightings:
                            start_stop = True
                for out_link in end_node.outgoing_links():
                    # only check if non-reverse links are on the road network
                    if out_link.j_node != link.i_node:
                        for mode in out_link.modes:
                            if mode.type != "TRANSIT" and mode not in transfer_modes:
                                end_road = True
                    # check to see if end node has transit stops
                    for segment in out_link.segments():
                        if segment.allow_boardings or segment.allow_alightings:
                            end_stop = True
                # check to see if node is end-of-line stop
                for segment in link.segments():
                    if segment.line.segment(str(end_node.number) + "-0") != False:
                        end_stop = True
                keep = False
                if start_stop == True and end_stop == True:
                    keep = True
                elif start_stop == True and end_road == True:
                    keep = True
                elif end_stop == True and start_road == True:
                    keep = True
                if keep == False:
                    # check if link has non-transfer modes, in which case these modes are removed from link, otherwise link is deleted
                    if link.modes.issubset(transfer_modes):
                        network.delete_link(start_node, end_node)
                    else:
                        link.modes = link.modes.difference(transfer_modes)

    def _check_transfer_mode_in_network(self, network, transfer_mode_string):
        for mode in transfer_mode_string:
            if network.mode(mode) == None:
                raise Exception("Transfer mode %s was not found in the network!" % mode)

    def _remove_stranded_nodes(self, network):
        # removes nodes not connected to any links
        for node in network.nodes():
            is_stranded = True
            for link in node.outgoing_links():
                is_stranded = False
            for link in node.incoming_links():
                is_stranded = False
            if is_stranded == True:
                network.delete_node(node.id)

    def _remove_extra_nodes(
        self, cleaned_network, node_filter_attribute, stop_filter_attribute, connector_filter_attribute
    ):

        nodes_to_delete = self._get_candidate_nodes(
            cleaned_network, node_filter_attribute, stop_filter_attribute, connector_filter_attribute
        )
        if len(nodes_to_delete) == 0:
            raise Exception("Found zero nodes to delete.")
        if connector_filter_attribute != "none" or connector_filter_attribute != "":
            self._remove_candidate_centroid_connectors(nodes_to_delete, connector_filter_attribute)
        log = self._remove_nodes(cleaned_network, nodes_to_delete)
        self._tracker.complete_task()
        self._write_report(log)

    def _get_candidate_nodes(self, network, node_filter_attribute, stop_filter_attribute, connector_filter_attribute):
        network.create_attribute("NODE", "is_stop", False)
        for segment in network.transit_segments():
            if segment.allow_boardings or segment.allow_alightings:
                segment.i_node.is_stop = True
        # Setup filter functions. True to delete node, False to preserve
        if node_filter_attribute != None:
            check_node_1 = lambda n: bool(n[node_filter_attribute])
        else:
            check_node_1 = lambda n: True

        if stop_filter_attribute != None:
            # True if node is not a stop or node is flagged
            check_node_2 = lambda n: not n.is_stop or n[stop_filter_attribute]
        else:
            check_node_2 = lambda n: not n.is_stop

        if connector_filter_attribute != None:
            check_connector = lambda l: bool(l[connector_filter_attribute])
        else:
            check_connector = lambda l: False

        retval = []
        self._tracker.start_process(network.element_totals["regular_nodes"])
        for node in network.regular_nodes():
            if self.check_node(node, check_node_1, check_node_2, check_connector):
                retval.append(node)
            self._tracker.complete_subtask()
        self._tracker.complete_task()
        _write("%s nodes were selected for deletion." % len(retval))
        return retval

    def _remove_candidate_centroid_connectors(self, nodes_to_delete, connector_filter_attribute):
        network = nodes_to_delete[0].network
        link_ids_to_delete = []
        for node in nodes_to_delete:
            for link in node.incoming_links():
                if link.i_node.is_centroid and link[connector_filter_attribute]:
                    link_ids_to_delete.append((link.i_node.number, node.number))
            for link in node.outgoing_links():
                if link.j_node.is_centroid and link[connector_filter_attribute]:
                    link_ids_to_delete.append((node.number, link.j_node.number))
        for i, j in link_ids_to_delete:
            network.delete_link(i, j, True)

    def _remove_nodes(self, network, nodes_to_delete):
        log = []
        deep_errors = []
        delete_nodes = 0
        self._tracker.start_process(len(nodes_to_delete))
        for node in nodes_to_delete:
            nid = node.number
            try:
                _edit.merge_links(
                    node,
                    delete_stop=True,
                    vertex=True,
                    link_aggregators=self._link_aggregators,
                    segment_aggregators=self._segment_aggregators,
                )
                delete_nodes += 1
            except force_error as fe:
                # User specified to keep these nodes
                log.append("Node %s not deleted. User-specified aggregator for '%s' detected changes." % (nid, fe))
            except invalid_network_operation_error as inee:
                log.append(str(inee))
            except Exception as e:
                log.append("Deep error processing node %s: %s" % (nid, e))
                deep_errors.append(_traceback.format_exc())
            self._tracker.complete_subtask()
        self._tracker.complete_task()
        _write("Removed %s nodes from the network." % delete_nodes)
        return log

    def _write_report(self, log):
        pb = _m.PageBuilder(title="Error log")
        doc = "<br>".join(log)
        pb.wrap_html(body=doc)
        _write("Error report", value=pb.render())

    def check_node(self, node, check_node_1, check_node_2, check_connector):
        if check_node_1(node) and check_node_2(node):
            neighbours = set()
            n_links = 0
            for link in node.outgoing_links():
                # is Connector
                if link.j_node.is_centroid:
                    # Make this link 'invisible'
                    if check_connector(link):
                        continue
                    # Connector not flagged for deletion, therefore cannot delete
                    # this node
                    return False
                neighbours.add(link.j_node.number)
                n_links += 1
            for link in node.incoming_links():
                if link.i_node.is_centroid:
                    if check_connector:
                        continue
                    return False
                neighbours.add(link.i_node.number)
                n_links += 1
            # Needs to have a degree of 2
            if len(neighbours) != 2:
                return False
                # Needs to be connected to either 2 or 4 links
            if n_links != 2 and n_links != 4:
                return False
            # Ok, so now we know this node is a candidate for deletion
            # For it to be selected for deletion, it must pass the two conditions
            return check_node_1(node) and check_node_2(node)

    def _parse_segment_aggregators(self, scenario, attribute_aggregator):
        # Setup the translation dictionary to get from Emme Desktop attribute names
        # to Modeller Python attribute names. Extra attributes are named the same.
        translator = self._get_translator_dict()
        multiple_domain_attributes = ["data1", "data2", "data3"]
        valid_func_names = ["sum", "avg", "or", "and", "min", "max", "first", "last", "zero", "avg_by_length", "force"]
        # Setup default aggregator function names
        link_extra_attributes = []
        segment_extra_attributes = []
        node_extra_attributes = []

        for exatt in scenario.extra_attributes():
            id = exatt.name
            t = exatt.type
            if t == "NODE":
                node_extra_attributes.append(id)
            elif t == "TRANSIT_SEGMENT":
                segment_extra_attributes.append(id)
            elif t == "LINK":
                link_extra_attributes.append(id)

        link_aggregators = {"length": "sum", "data1_l": "zero", "data2_l": "avg_by_length", "data3_l": "avg"}
        for att in link_extra_attributes:
            link_aggregators[att] = "avg"
            translator[att] = att

        segment_aggregators = {
            "dwell_time": "sum",
            "factor_dwell_time_by_length": "and",
            "transit_time_func": "force",
            "data1_s": "avg_by_length",
            "data2_s": "zero",
            "data3_s": "zero",
        }
        for att in segment_extra_attributes:
            segment_aggregators[att] = "avg"
            # Save extra attribute names into the translator for recognition
            translator[att] = att

        node_aggregators = {}
        for att in node_extra_attributes:
            node_aggregators[att] = "avg"
            translator[att] = att
        # Parse the argument string
        trimmed_string = attribute_aggregator.replace(" ", "")
        # Supports newline and/or commas
        components = _regex_split("\n|,", trimmed_string)

        for component in components:
            if component.isspace():
                # Skip if totally empty
                continue
            parts = component.split(":")
            if len(parts) != 2:
                msg = "Error parsing attribute aggregators: Separate attribute name from function with exactly one colon ':'"
                msg += ". [%s]" % component
                raise SyntaxError(msg)

            att_name, func_name = parts
            if att_name not in translator:
                raise IOError("Error parsing attribute aggregators: attribute '%s' not recognized." % att_name)
            att_name = translator[att_name]

            if not func_name in valid_func_names:
                raise IOError(
                    "Error parsing attribute aggregators: function '%s' not recognized for attribute '%s'"
                    % (func_name, att_name)
                )

            if att_name in link_aggregators:
                link_aggregators[att_name] = func_name
            elif att_name in segment_aggregators:
                segment_aggregators[att_name] = func_name
            elif att_name in node_aggregators:
                node_aggregators[att_name] = func_name
            elif att_name in multiple_domain_attributes:
                link_aggregators[att_name] = func_name
                segment_aggregators[att_name] = func_name
                node_aggregators[att_name] = func_name

        for key in link_aggregators.keys():
            if key.endswith("_l"):
                new_key = key.replace("_l", "")
                val = link_aggregators.pop(key)
                link_aggregators[new_key] = val

        for key in segment_aggregators:
            if key.endswith("_s"):
                new_key = key.replace("_s", "")
                val = segment_aggregators.pop(key)
                segment_aggregators[new_key] = val

        for key in node_aggregators:
            if key.endswith("_n"):
                new_key = key.replace("_n", "")
                val = node_aggregators.pop(key)
                node_aggregators[new_key] = val

        for att, func_name in link_aggregators.items():
            if func_name == "avg_by_length":
                link_aggregators[att] = self.AVERAGE_BY_LENGTH_LINKS
            else:
                link_aggregators[att] = _edit.NAMED_AGGREGATORS[func_name]
        for att, func_name in segment_aggregators.items():
            if func_name == "avg_by_length":
                segment_aggregators[att] = self.AVERAGE_BY_LENGTH_SEGMENTS
            else:
                segment_aggregators[att] = _edit.NAMED_AGGREGATORS[func_name]
        for att, func_name in node_aggregators.items():
            node_aggregators[att] = _edit.NAMED_AGGREGATORS[func_name]

    def _get_translator_dict(self):
        translator_dict = {
            "length": "length",
            "type": "type",
            "lanes": "num_lanes",
            "vdf": "volume_delay_func",
            "ul1": "data1_l",
            "ul2": "data2_l",
            "ul3": "data3_l",
            "dwt": "dwell_time",
            "dwfac": "factor_dwell_time_by_length",
            "ttf": "transit_time_func",
            "us1": "data1_s",
            "us2": "data2_s",
            "us3": "data3_s",
            "data1_l": "data1_l",
            "data2_l": "data2_l",
            "data3_l": "data3_l",
            "ui1": "data1_n",
            "ui2": "data2_n",
            "ui3": "data3_n",
            "dwell_time": "dwell_time",
            "factor_dwell_time_by_length": "factor_dwell_time_by_length",
            "transit_time_func": "transit_time_func",
            "data1_s": "data1_s",
            "data2_s": "data2_s",
            "data3_s": "data3_s",
            "data1": "data1",
            "data2": "data2",
            "data3": "data3",
            "noali": "allow_alightings",
            "noboa": "allow_boardings",
        }
        return translator_dict

    @contextmanager
    def _line_attribute_manager(self, scenario):
        """
        Context managers for temporary database modifications.
        """
        scenario.create_extra_attribute("TRANSIT_LINE", "@tlf1")
        _write("Created temporary attribute @tlf1")

        try:
            yield "@tlf1"
        finally:
            scenario.delete_extra_attribute("@tlf1")
            _write("Deleted temporary attribute @tlf1")

    @_m.method(return_type=_m.TupleType)
    def percent_completed(self):
        return self._tracker.get_progress()

    @_m.method(return_type=str)
    def tool_run_msg_status(self):
        return self.tool_run_msg
