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
_bank = _MODELLER.emmebank
_write = _m.logbook_write


class GenerateTimePeriodNetworks(_m.Tool()):
    version = "2.0.0"
    tool_run_msg = ""
    number_of_task = 1
    COLON = ":"
    COMMA = ","

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
            attributes=self._get_atts(),
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

            network.create_attribute("TRANSIT_LINE", "trips", None)
            network.create_attribute("TRANSIT_LINE", "aggtype", None)

            for periods in parameters["time_periods"]:
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

    def _delete_old_scenario(self, scenario_number):
        if _bank.scenario(scenario_number) is not None:
            _bank.delete_scenario(scenario_number)

    def _get_atts(self):
        atts = {}
        return atts

    def _check_filter_attributes(self, base_scenario, filer_attribute_id, description=""):
        if filer_attribute_id.lower() == "none":
            filer_attribute_id = None
        else:
            if base_scenario.extra_attribute(filer_attribute_id) is None:
                raise Exception("%s filter attribute %s does not exist" % (filer_attribute_id, description))
        return filer_attribute_id

    def _load_service_table(self, network, start_time, end_time, transit_service_table_file):
        # network.create_attribute("TRANSIT_LINE", "trips", None)

        bounds = _util.float_range(start_time, end_time)
        bad_ids = set()

        if transit_service_table_file != "" or transit_service_table_file != "none":
            with open(transit_service_table_file) as service_file:

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
            with open(transit_aggregation_selection_table_file) as aggregate_file:
                for line_number, service_file_list in enumerate(aggregate_file):
                    emme_id_col = service_file_list[0]
                    agg_col = service_file_list[1]
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
            hms = time_string.split(self.COLON)
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
