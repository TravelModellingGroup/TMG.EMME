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
import csv
import inro.modeller as _m
import traceback as _traceback
import multiprocessing
from contextlib import contextmanager

_MODELLER = _m.Modeller()
_util = _MODELLER.module("tmg2.utilities.general_utilities")
_tmg_tpb = _MODELLER.module("tmg2.utilities.TMG_tool_page_builder")
network_calc_tool = _MODELLER.tool("inro.emme.network_calculation.network_calculator")
_bank = _MODELLER.emmebank
_write = _m.logbook_write
_trace = _m.logbook_trace

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
    number_of_task = 2

    def __init__(self):
        self._tracker = _util.progress_tracker(self.number_of_task)
        self.number_of_processors = multiprocessing.cpu_count()

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
            self._tracker.complete_task()
            print("Loaded network")
            self._check_filter_attributes(base_scenario, parameters["node_filter_attribute"], description="Node")
            self._check_filter_attributes(base_scenario, parameters["stop_filter_attribute"], description="Stop")
            self._check_filter_attributes(
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
                ).union(self._load_agg_type_select(network, parameters["transit_aggregation_selection_table_file"]))
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
                    self._prorate_transit_speeds(uncleaned_scenario, parameters["line_filter_expression"])
                    print("Prorated transit speeds in uncleaned scenario %s" % periods["uncleaned_scenario_number"])

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
            with self.open_csv_reader(transit_service_table_file) as service_file:
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

    def _load_agg_type_select(self, network, transit_aggregation_selection_table_file):
        bad_ids = set()
        if transit_aggregation_selection_table_file != "" or transit_aggregation_selection_table_file != "none":
            with self.open_csv_reader(transit_aggregation_selection_table_file) as aggregate_file:
                for line_number, aggregate_file_list in enumerate(aggregate_file):
                    emme_id_col = aggregate_file_list[0]
                    agg_col = aggregate_file_list[1]
                    transit_line = network.transit_line(emme_id_col)
                    if transit_line is None:
                        bad_ids.add(emme_id_col)
                        continue
                    try:
                        aggregation = self._parse_agg_type(agg_col)
                    except Exception as e:
                        print("Line " + line_number + " skipped: " + str(e))
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

    def _parse_agg_type(self, a):
        choice_set = ("n", "a")
        try:
            agg = a[0].lower()
            if agg not in choice_set:
                raise IOError()
            else:
                return agg
        except Exception as e:
            raise IOError("You must select either naive or average as an aggregation type %s: %s" % (a, e))

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

    def _process_line(self, line):
        # In km
        line_length = sum([seg.link.length for seg in line.segments()])
        # In minutes
        scheduled_cycle_time = line_length / line.speed * 60.0
        # All speeds are assumed to be in km/hr
        free_flow_time = 0
        for segment in line.segments():
            speed = segment.link.data2
            if speed == 0:
                # Assume nominal speed of 50 km/hr if it's otherwise undefined
                speed = 50
            free_flow_time += segment.link.length / speed * 60.0
        factor = free_flow_time / scheduled_cycle_time
        for segment in line.segments():
            speed = segment.link.data2
            if speed == 0:
                # Assume nominal speed of 50 km/hr if it's otherwise undefined
                speed = 50.0
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

    def _prorate_transit_speeds(self, scenario, line_filter_expression):
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
            if len(flagged_lines) == 0:
                return 0
            self._tracker.start_process(len(flagged_lines))
            for line in flagged_lines:
                self._process_line(line)
                self._tracker.complete_subtask()
            self._tracker.complete_task()
            scenario.publish_network(network)
        return len(flagged_lines)

    @contextmanager
    def open_csv_reader(self, file_path):
        """
        Open, reads and manages a CSV file
        NOTE: Does not return the first line of the CSV file
            Assumption is that the first row is the title of each field
        """
        csv_file = open(file_path, mode="r")
        file = csv.reader(csv_file)
        next(file)
        try:
            yield file
        finally:
            csv_file.close()

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
