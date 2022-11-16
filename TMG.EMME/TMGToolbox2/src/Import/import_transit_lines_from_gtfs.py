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
Generate Transit Lines from GTFS

    Authors: Peter Kucirek

    Previous revision by: lunaxi

    refactored for TMGToolbox 2 by WilliamsDiogu
    
    
    Generates transit line ITINERARIES ONLY from GTFS data. Assumes that most GTFS
    stop are matched to a group ID (GID) and each GID is matched to a network node.
    Both tables are inputs for this tool.
    
    Additionally, the 'routes' file of the GTFS feed must define two additional
    columns: 'emme_id' (defining up to the first 5 characters of the Emme transit
    line id), and 'emme_vehicle' (defining the Emme vehicle number used by the line).
    For convenience, if both 'routes.txt' and 'routes.csv' are defined, the CSV 
    file will be used (since this is likely to be edited using Excel).
    
    During the map-matching process, this tool will attempt to find the shortest
    path between two nodes in an itinerary, up to a maximum of 10 links. Any line
    requiring a path of more than 5 links will be flagged for review. Lines requiring
    longer paths will not be added at all (but will be reported in the logbook).
"""
# ---VERSION HISTORY
"""
    0.0.1 Created
    
    0.0.2 Added feature to take line names from routes file. Also added the feature to flag lines
        with short itineraries for checking. Also fixed a minor bug where the scenario title wasn't
        being applied
    
    0.0.3 Added feature to select a link attribute for prioritized links. Prioritized links are assumed
        to have triple the speed.
    
    0.0.4 Modified the tool to calculate shortest-paths including turn penalties (& restrictions). This runs a bit
        slower.
    
    0.0.5 Fixed a bug where the optional 'direction_id' in the trips file causes the tool to crash if omitted.
    
    0.0.6 Upgraded to using a better, turn-restricted shortest-path algorithm. 
"""

import inro.modeller as _m
import traceback as _traceback
import csv
from os import path as _path

_m.InstanceType = object
_m.TupleType = object
_m.ListType = list

_MODELLER = _m.Modeller()
_bank = _MODELLER.emmebank
_editing = _MODELLER.module("tmg2.utilities.network_editing")
_util = _MODELLER.module("tmg2.utilities.general_utilities")
_tmg_tpb = _MODELLER.module("tmg2.utilities.TMG_tool_page_builder")

##########################################################################################################

gtfs_mode_map = {"s": "0", "l": "0", "m": "1", "r": "2", "b": "3", "q": "3", "g": "3"}


def last(list):
    if len(list) == 0:
        return None
    return list[len(list) - 1]


class ImportTransitLinesFromGTFS(_m.Tool()):

    version = "2.0.0"
    tool_run_msg = ""
    number_of_tasks = 8
    # Tool Input Parameters
    #    Only those parameters neccessary for Modeller and/or XTMF to dock with
    #    need to be placed here. Internal parameters (such as lists and dicts)
    #    get intitialized during construction (__init__)
    scenario = _m.Attribute(_m.InstanceType)
    new_scenario_id = _m.Attribute(str)
    new_scenario_title = _m.Attribute(str)
    max_non_stop_nodes = _m.Attribute(int)
    link_priority_attribute_id = _m.Attribute(str)
    gtfs_folder = _m.Attribute(str)
    stop_to_node_file = _m.Attribute(str)

    line_service_table_file = _m.Attribute(str)
    publish_flag = _m.Attribute(bool)
    mapping_file_name = _m.Attribute(str)

    def __init__(self):
        # ---Init internal variables
        self._tracker = _util.progress_tracker(self.number_of_tasks)
        # ---Set the defaults of parameters used by Modeller
        self.scenario = _MODELLER.scenario
        self.max_non_stop_nodes = 15
        self.publish_flag = True
        self.new_scenario_title = self.scenario.title

    def page(self):
        pb = _tmg_tpb.TmgToolPageBuilder(
            self,
            title="Generate Transit Line Itineraries from GTFS v%s" % self.version,
            description="<p class='tmg_left'>Generates transit line ITINERARIES ONLY from GTFS data. \
                        Assumes that most GTFS are matched to a network node. Unmatched stops are 'invisible'.\
                        <br><br>Additionally, the 'routes' file of the GTFS feed must define two additional\
                        columns: 'emme_id' (defining up to the first 5 characters of the Emme transit\
                        line id), and 'emme_vehicle' (defining the Emme vehicle number used by the line).\
                        For convenience, if both 'routes.txt' and 'routes.csv' are defined, the CSV \
                        file will be used (since this is likely to be edited using Excel) \
                        An optional column 'emme_descr' can also be provided to define lines' descriptions.\
                        <br><br>During the map-matching process, this tool will attempt to find the shortest\
                        path between two nodes in an itinerary, up to a specified maximum. Any line\
                        with a path having more than 5 links between any two stops will be flagged for review. \
                        Lines requiring paths longer than the maximum will not be added at all (but will be \
                        reported in the logbook). \
                        Lines which result in a repeated node (looped lines) will also be flagged for review.\
                        <br><br><b>Tip: </b>Press CTRL+K to bring up the Python Console to view tool progress.</p>",
            branding_text="- TMG Toolbox 2",
        )

        if self.tool_run_msg != "":
            pb.tool_run_status(self.tool_run_msg_status)

        pb.add_select_scenario(tool_attribute_name="scenario", title="Base Scenario", allow_none=False)

        pb.add_text_box(tool_attribute_name="max_non_stop_nodes", size=3, title="Maximum Inter-stop Links")

        key_vals = dict([(att.id, "{id} - LINK - {desc}".format(id=att.id, desc=att.description)) for att in self.scenario.extra_attributes() if att.type == "LINK"])
        pb.add_select(
            tool_attribute_name="link_priority_attribute_id",
            keyvalues=key_vals,
            title="Link Priority Attribute",
            note="A factor applied to link speeds.\
                      <br><font color='red'><b>Warning: </b></font>\
                      It is recommended to use an attribute with \
                      a default value of 1.0.",
        )

        pb.add_header("GTFS INPUTS")

        pb.add_select_file(tool_attribute_name="gtfs_folder", window_type="directory", title="GTFS Folder")

        pb.add_select_file(
            tool_attribute_name="stop_to_node_file",
            window_type="file",
            file_filter="*.csv",
            title="Stop-to-Node File",
            note="<b>First Column</b>: Stop ID\
                           <br><b>Second Column</b>: Node ID",
        )

        pb.add_header("TOOL OUTPUTS")

        with pb.add_table(visible_border=False) as t:
            with t.table_cell():
                pb.add_new_scenario_select(tool_attribute_name="new_scenario_id", title="New Scenario", note="The id of the copied scenario")
            with t.table_cell():
                pb.add_text_box(tool_attribute_name="new_scenario_title", size=60, multi_line=True, title="New Scenario Title")

        pb.add_select_file(tool_attribute_name="line_service_table_file", window_type="save_file", file_filter="*.csv", title="Transit Service Table")

        pb.add_select_file(tool_attribute_name="mapping_file_name", window_type="save_file", file_filter="*.csv", title="Mapping file to map between EMME ID and GTFS Trip ID")

        pb.add_checkbox(tool_attribute_name="publish_flag", label="Publish network? Leave unchecked for debugging.")

        pb.add_html(
            """
<script type="text/javascript">
    $(document).ready( function ()
    {
        $("#link_priority_attribute_id")
             .prepend(0,"<option value='-1' selected='selected'>None</option>")
             .prop("selectedIndex", 0)
             .trigger('change')
        //alert($("#link_priority_attribute_id").selectedIndex);
        
        var tool = new inro.modeller.util.Proxy(%s) ;
        $("#Scenario").bind('change', function()
        {
            $(this).commit();
            var options = tool.get_extra_attributes(scenario);
            
            $("#link_priority_attribute_id")
                .empty()
                .append("<option value='-1' selected='selected'>None</option>")
                .append(options)
                //.data("combobox")._refresh_width();
            inro.modeller.page.preload("#link_priority_attribute_id");
            $("#link_priority_attribute_id").trigger('change');
        });
        
        $("#publish_flag").bind('change', function()
        {
            $(this).commit();
            if ($(this).is(":checked")) {
                $("#new_scenario_id").prop("disabled", false);
                $("#new_scenario_title").prop("disabled", false);
            } else {
                $("#new_scenario_id").prop("disabled", true);
                $("#new_scenario_title").prop("disabled", true);
            }
        });
    });
</script>"""
            % pb.tool_proxy_tag
        )

        return pb.render()

    ##########################################################################################################

    def run(self):
        self.tool_run_msg = ""
        self._tracker.reset()
        parameters = self._build_page_builder_parameters()
        try:
            self._execute(parameters)
        except Exception as e:
            self.tool_run_msg = _m.PageBuilder.format_exception(e, _traceback.format_exc())
            raise
        self.tool_run_msg = _m.PageBuilder.format_info("Tool complete.")

    ##########################################################################################################

    def run_xtmf(self, parameters):
        try:
            self._execute(parameters)
        except Exception as e:
            raise Exception(_traceback.format_exc())

    def _execute(self, parameters):
        with _m.logbook_trace(
            name="{classname} v{version}".format(classname=(self.__class__.__name__), version=self.version),
            attributes=self._get_atts(parameters["scenario_id"], self.version),
        ):
            routes = self._load_check_gtfs_routes_file(parameters["gtfs_folder"])
            self._tracker.complete_task()
            sc = _bank.scenario(str(parameters["scenario_id"]))
            network = sc.get_network()
            print("Loaded network")
            self._tracker.complete_task()
            stops_to_nodes = self._load_stop_node_map_file(network, parameters["stop_to_node_file"])
            trips = self._load_trips(routes, parameters["gtfs_folder"])
            self._load_print_stop_times(trips, stops_to_nodes, parameters["gtfs_folder"])
            with open(parameters["service_table_file"], "w") as writer:
                self._generate_lines(routes, stops_to_nodes, network, writer, parameters["mapping_file"], parameters["max_non_stop_nodes"], parameters["link_priority_attribute"], parameters["publish_flag"])
            dest = _bank.scenario(str(parameters["new_scenario_id"]))
            if dest is not None:
                _bank.delete_scenario(dest.id)
            if parameters["publish_flag"]:
                copy = _bank.copy_scenario(sc.id, str(parameters["new_scenario_id"]))
                copy.title = parameters["new_scenario_title"]
                copy.publish_network(network, True)
            self._tracker.complete_task()

    # ----SUB FUNCTIONS---------------------------------------------------------------------------------

    def _get_atts(self, scenario, version):
        atts = {
            "Scenario": scenario,
            "Version": version,
            "self": self.__MODELLER_NAMESPACE__,
        }
        return atts

    def _load_check_gtfs_routes_file(self, gtfs_folder):
        routes_path = gtfs_folder + "/routes.csv"
        if not _path.exists(routes_path):
            routes_path = gtfs_folder + "/routes.txt"
            if not _path.exists(routes_path):
                raise IOError("Folder does not contain a routes file")
        with _util.CSVReader(routes_path) as reader:
            for label in ["emme_id", "emme_vehicle", "route_id", "route_long_name"]:
                if label not in reader.header:
                    raise IOError("Routes file does not define column '%s'" % label)
            use_line_names = False
            if "emme_descr" in reader.header:
                use_line_names = True

            emme_id_set = set()
            routes = {}
            for record in reader.readlines():
                emme_id = record["emme_id"][:5]
                print(emme_id)
                if emme_id in emme_id_set:
                    raise IOError("Route file contains duplicate id '%s'" % emme_id)

                emme_id_set.add(emme_id)
                if use_line_names:
                    descr = record["emme_descr"]
                    route = Route(record, description=descr[:17])
                else:
                    route = Route(record)
                routes[route.route_id] = route
        msg = "%s routes loaded from transit feed" % len(routes)
        print(msg)
        _m.logbook_write(msg)
        return routes

    def _load_stop_node_map_file(self, network, stop_to_node_file):
        stops_to_nodes = {}
        with open(stop_to_node_file) as reader:
            reader.readline()
            for line in reader.readlines():
                line = line.strip()
                cells = line.split(",")
                if cells[1] == "0":
                    self._tracker.complete_subtask()
                    continue
                if network.node(cells[1]) is None:
                    raise IOError("Mapping error: Node %s does not exist" % cells[1])
                stops_to_nodes[cells[0]] = cells[1]
            self._tracker.complete_task()
        msg = "%s stop-node pairs loaded." % len(stops_to_nodes)
        print(msg)
        _m.logbook_write(msg)
        return stops_to_nodes

    def _load_trips(self, routes, gtfs_folder):
        trips = {}
        with _util.CSVReader(gtfs_folder + "/trips.txt") as reader:
            self._tracker.start_process(len(reader))
            direction_given = "direction_id" in reader.header
            for record in reader.readlines():
                route = routes[record["route_id"]]
                if direction_given:
                    direction = record["direction_id"]
                else:
                    direction = None
                trip = Trip(record["trip_id"], route, direction)
                route.trips[trip.id] = trip
                trips[trip.id] = trip
                self._tracker.complete_subtask()
            self._tracker.complete_task()
        msg = "%s trips loaded." % len(trips)
        print(msg)
        _m.logbook_write(msg)
        return trips

    def _load_print_stop_times(self, trips, stops_to_nodes, gtfs_folder):
        count = 0
        with _util.CSVReader(gtfs_folder + "/stop_times.txt") as reader:
            with open(gtfs_folder + "/stop_times_emme_nodes.txt", "w") as writer:
                s = reader.header[0]
                for i in range(1, len(reader.header)):
                    s += "," + reader.header[i]
                writer.write(s)
                writer.write(",emme_node")
                self._tracker.start_process(len(reader))
                for record in reader.readlines():
                    try:
                        trip = trips[record["trip_id"]]
                    except KeyError:
                        continue
                    index = int(record["stop_sequence"])
                    stop_id = record["stop_id"]
                    stop_time = StopTime(stop_id, record["departure_time"], record["arrival_time"])
                    trip.stop_times.append((index, stop_time))
                    if stop_id in stops_to_nodes:
                        node = stops_to_nodes[stop_id]
                    else:
                        node = None
                    writer.write("\n%s,%s" % (record, node))
                    count += 1
                    self._tracker.complete_subtask()
                self._tracker.complete_task()
        msg = "%s stop times loaded" % count
        print(msg)
        _m.logbook_write(msg)
        print("Stop times file updated with emme node mapping.")
        pb = _m.PageBuilder(title="Link to updated stop times file")
        pb.add_link(gtfs_folder + "/stop_times_emme_nodes.txt")
        _m.logbook_write("Link to updated stop times file", value=pb.render())

    def _generate_lines(self, routes, stops_to_nodes, network, writer, mapping_file_name, max_non_stop_nodes, link_priority_attribute_id, publish_flag):
        # This is the main method
        with open(mapping_file_name, "w") as csv_file:
            csv_writer = csv.writer(csv_file)
            csv_writer.writerow(["tripId", "emme_id"])
            lines_to_check = []
            failed_sequences = []
            skipped_stop_ids = {}
            writer.write("emme_id,trip_depart,trip_arrive")
            # Setup the shortest-path algorithm
            if link_priority_attribute_id != "":

                def speed(link):
                    factor = link[link_priority_attribute_id]
                    if factor == 0:
                        return 0
                    if link.data2 == 0:
                        return 30.0 * factor
                    return link.data2 * factor

            else:
                factor = 1

                def speed(link):
                    if link.data2 == 0:
                        return 30.0 * factor
                    return link.data2 * factor

            algo = _editing.AStarLinks(network, link_speed_func=speed)
            algo.max_degrees = max_non_stop_nodes
            function_bank = self._get_mode_filter_map(network, link_priority_attribute_id)
            self._tracker.start_process(len(routes))
            line_count = 0
            print("Starting line itinerary generation")
            for route in routes.values():
                base_emme_id = route.emme_id
                vehicle = network.transit_vehicle(route.emme_vehicle)
                if vehicle is None:
                    raise Exception("Cannot find a vehicle with id=%s" % route.emme_vehicle)
                if gtfs_mode_map[vehicle.mode.id] != route.route_type:
                    print("Warning: Vehicle mode of route {0} ({1}) does not match suggested route type ({2})".format(route.route_id, vehicle.mode.id, route.route_type))
                filter = function_bank[vehicle.mode]
                algo.link_filter = filter
                # Collect all trips with the same stop sequence
                trip_set = self._get_organized_trips(route)
                # Create route profile
                branch_number = 0
                seq_count = 1
                for seq, trips in trip_set.items():
                    stop_itin = seq.split(";")
                    # Get node itinerary
                    node_itin = self._get_node_itinerary(stop_itin, stops_to_nodes, network, skipped_stop_ids)
                    # Must have at least two nodes to build a route
                    if len(node_itin) < 2:
                        # routeId, branchNum, error, seq
                        failed_sequences.append((base_emme_id, seq_count, "too few nodes", seq))
                        seq_count += 1
                        continue
                    # Generate full, mode-constrained path
                    iter = node_itin.__iter__()
                    previous_node = next(iter)
                    full_itin = [previous_node]
                    seg_stops = []
                    break_flag = False
                    long_route = False
                    for node in iter:
                        path = algo.calcPath(previous_node, node)
                        if not path:
                            # routeId, branchNum, error, seq
                            msg = "no path between %s and %s by mode %s" % (
                                previous_node,
                                node,
                                vehicle.mode,
                            )
                            failed_sequences.append((base_emme_id, seq_count, msg, seq))
                            break_flag = True
                            seq_count += 1
                            break
                        flag = True
                        if len(path) > 5:
                            long_route = True
                        for link in path:
                            full_itin.append(link.j_node)
                            seg_stops.append(flag)
                            flag = False
                        previous_node = node
                    seg_stops.append(True)  # Last segment should always be a stop.
                    if break_flag:
                        seq_count += 1
                        continue
                    # Try to create the line
                    id = base_emme_id + chr(branch_number + 65)
                    if trips[0].direction == "0":
                        id += "a"
                    elif trips[0].direction == "1":
                        id += "b"
                    d = ""
                    if route.description:
                        d = "%s %s" % (route.description, chr(branch_number + 65))
                        for trip in trips:
                            csv_writer.writerow([trip.id, id])
                    try:
                        line = network.create_transit_line(id, vehicle, full_itin)
                        line.description = d
                        # Ensure that nodes which aren't stops are flagged as such.
                        for i, stopFlag in enumerate(seg_stops):
                            seg = line.segment(i)
                            seg.allow_alightings = stopFlag
                            seg.allow_boardings = stopFlag
                            # No dwell time if there is no stop, 0.01 minutes if there is a stop
                            seg.dwell_time = 0.01 * float(stopFlag)
                        branch_number += 1
                        line_count += 1
                    except Exception as e:
                        print("Exception for line %s: %s" % (id, e))
                        # routeId, branchNum, error, seq
                        failed_sequences.append((base_emme_id, seq_count, str(e), seq))
                        seq_count += 1
                        continue
                    seq_count += 1
                    if long_route:
                        lines_to_check.append(
                            (
                                id,
                                "Possible express route: more than 5 links in-between one or more stops.",
                            )
                        )
                    # Check for looped routes
                    node_set = set(full_itin)
                    for node in node_set:
                        count = full_itin.count(node)
                        if count > 1:
                            lines_to_check.append((id, "Loop detected. Possible map matching error."))
                            break
                    if len(node_itin) < 5:
                        lines_to_check.append((id, "Short route: less than 4 total links in path"))
                    # Write to service table
                    for trip in trips:
                        writer.write(
                            "\n%s,%s,%s"
                            % (
                                id,
                                trip.stop_times[0][1].departure_time,
                                trip.last_stop_time()[1].arrival_time,
                            )
                        )
                        csv_writer.writerow([trip.id, id])
                print("Added route %s" % route.emme_id)
                self._tracker.complete_subtask()
        self._tracker.complete_task()
        msg = "Done. %s lines were successfully created." % line_count
        print(msg)
        _m.logbook_write(msg)
        _m.logbook_write("Skipped stops report", value=self._write_skipped_stops_report(skipped_stop_ids))
        print("%s stops skipped" % len(skipped_stop_ids))
        _m.logbook_write(
            "Failed sequences report",
            value=self._write_failed_sequences_report(failed_sequences),
        )
        print("%s sequences failed" % len(failed_sequences))
        if publish_flag:
            _m.logbook_write(
                "Lines to check report",
                value=self._write_lines_to_check_report(lines_to_check),
            )
            print("%s lines were logged for review." % len(lines_to_check))

    def _get_organized_trips(self, route):
        trip_set = {}
        for trip in route.trips.values():
            trip.stop_times.sort()
            seq = [st[1].stop_id for st in trip.stop_times]
            seqs = seq[0]
            for i in range(1, len(seq)):
                seqs += ";" + seq[i]
            if seqs in trip_set:
                trip_set[seqs].append(trip)
            else:
                trip_set[seqs] = [trip]
        return trip_set

    def _get_mode_filter_map(self, network, link_priority_attribute_id):
        map = {}
        modes = [mode for mode in network.modes() if mode.type == "TRANSIT"]
        for mode in modes:
            if link_priority_attribute_id == "":
                func = ModeOnlyFilter(mode)
                map[mode] = func
            else:
                func = ModeAndAttributeFilter(mode, link_priority_attribute_id)
                map[mode] = func
        return map

    def _get_node_itinerary(self, stop_itin, stops_to_nodes, network, skipped_stop_ids):
        node_itin = []
        for stop_id in stop_itin:
            if not stop_id in stops_to_nodes:
                if stop_id in skipped_stop_ids:
                    skipped_stop_ids[stop_id] += 1
                else:
                    skipped_stop_ids[stop_id] = 1
                continue
            node_id = stops_to_nodes[stop_id]
            node = network.node(node_id)
            if node is None:
                if stop_id in skipped_stop_ids:
                    skipped_stop_ids[stop_id] += 1
                else:
                    skipped_stop_ids[stop_id] = 1
                print("Could not find node %s" % node_id)
                continue
            if last(node_itin) == node:
                continue
            node_itin.append(node)
        return node_itin

    def _write_skipped_stops_report(self, skipped_stop_ids):
        pb = _m.PageBuilder()
        stop_data = []
        count_data = []
        for x, item in enumerate(skipped_stop_ids.items()):
            stop, count = item
            stop_data.append((x, stop))
            count_data.append((x, count))
        cds = [
            {"title": "Stop ID", "data": stop_data},
            {"title": "Count", "data": count_data},
        ]
        opt = {"table": True, "graph": False}
        pb.add_chart_widget(
            cds,
            options=opt,
            title="Skipped Stops Table",
            note="'Count' is the number of times skipped.",
        )
        return pb.render()

    def _write_failed_sequences_report(self, failed_sequences):
        pb = _m.PageBuilder()
        id_data = []
        branch_data = []
        error_data = []
        seq_data = []
        for x, item in enumerate(failed_sequences):  # Not a map
            routeId, branchNum, error, seq = item
            id_data.append((x, routeId))
            branch_data.append((x, branchNum))
            error_data.append((x, error))
            seq_data.append((x, seq))
        cds = [
            {"title": "Route ID", "data": id_data},
            {"title": "Branch #", "data": branch_data},
            {"title": "Error", "data": error_data},
            {"title": "Stop Sequence", "data": seq_data},
        ]
        opt = {"table": True, "graph": False}
        pb.add_chart_widget(
            cds,
            options=opt,
            title="Failed Sequences Table",
            note="Stop sequence refers to GTFS stop ids.",
        )
        return pb.render()

    def _write_lines_to_check_report(self, lines_to_check):
        pb = _m.PageBuilder()
        id_data = []
        check_data = []
        for x, item in enumerate(lines_to_check):
            id, reason = item
            id_data.append((x, id))
            check_data.append((x, reason))
        cds = [
            {"title": "Line ID", "data": id_data},
            {"title": "Check Reason", "data": check_data},
        ]
        opt = {"table": True, "graph": False}
        pb.add_chart_widget(cds, options=opt, title="Emme Lines to Check")
        return pb.render()

    def _build_page_builder_parameters(self):
        parameters = {
            "scenario": self.scenario,
            "new_scenario_id": self.new_scenario_id,
            "new_scenario_title": self.new_scenario_title,
            "max_non_stop_nodes": self.max_non_stop_nodes,
            "link_priority_attribute_id": self.link_priority_attribute_id,
            "gtfs_folder": self.gtfs_folder,
            "stop_to_node_file": self.stop_to_node_file,
            "line_service_table_file": self.line_service_table_file,
            "publish_flag": self.publish_flag,
            "mapping_file_name": self.mapping_file_name,
        }
        return parameters

    @_m.method(return_type=_m.TupleType)
    def percent_completed(self):
        return self._tracker.get_progress()

    @_m.method(return_type=str)
    def tool_run_msg_status(self):
        return self.tool_run_msg

    @_m.method(return_type=str)
    def get_extra_attributes(self, scenario):
        key_vals = {}
        sc = _bank.scenario(scenario)
        for att in sc.extra_attributes():
            if att.type != "LINK":
                continue
            descr = "{id} - LINK - {desc}".format(id=att.id, desc=att.description)
            key_vals[att.id] = descr
        options = []
        for tuple in key_vals.items():
            html = '<option value="%s">%s</option>' % tuple
            options.append(html)
        return "\n".join(options)


class Trip:
    def __init__(self, id, route, direction_id):
        self.id = id
        self.route = route
        self.direction = direction_id

        self.stop_times = []

    def last_stop_time(self):
        return self.stop_times[len(self.stop_times) - 1]


class Route:
    def __init__(self, record, description=""):
        self.route_id = record["route_id"]
        self.emme_id = record["emme_id"]
        self.emme_vehicle = record["emme_vehicle"]
        self.route_type = record["route_type"]
        self.trips = {}
        self.description = description


class StopTime:
    def __init__(self, stop, depart, arrive):
        self.stop_id = stop
        self.departure_time = depart
        self.arrival_time = arrive


class ModeOnlyFilter:
    def __init__(self, mode):
        self.__mode = mode

    def __call__(self, link):
        return self.__mode in link.modes


class ModeAndAttributeFilter:
    def __init__(self, mode, attribute):
        self.__mode = mode
        self.__att = attribute

    def __call__(self, link):
        return self.__mode in link.modes and link[self.__att] != 0
