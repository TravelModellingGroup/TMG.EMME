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
import traceback as _traceback
from contextlib import contextmanager
import os.path

_m.InstanceType = object
_m.TupleType = object
_m.ListType = list

_MODELLER = _m.Modeller()
_util = _MODELLER.module("tmg2.utilities.general_utilities")

##########################################################################################################


class FilterGTFSForServiceIdAndRoutes(_m.Tool()):
    version = "0.0.1"
    tool_run_msg = ""
    number_of_tasks = 4

    def __init__(self):
        self._tracker = _util.progress_tracker(self.number_of_tasks)
        self._warning = ""

    def page(self):
        pb = _m.ToolPageBuilder(
            self,
            title="Clean GTFS Folder v%s" % self.version,
            description="Cleans a set of GTFS files by service ID. Filters all \
                         GTFS files except for routes, calendar, and shapes.",
            branding_text="- TMG Toolbox 2",
        )
        return pb.render()

    def __call__(self, parameters):
        try:
            self._execute(parameters)
        except Exception as e:
            raise Exception(_traceback.format_exc())

    def run_xtmf(self, parameters):
        try:
            self._execute(parameters)
        except Exception as e:
            raise Exception(_traceback.format_exc())

    def _execute(self, parameters):
        cells = parameters["service_id"].split(",")
        service_id_set = set(cells)
        routes_file = ""
        if not parameters["routes_file"]:
            routes_file = parameters["gtfs_folder"] + "/routes.txt"
        else:
            routes_file = parameters["routes_file"]
        route_id_set = self._get_route_id_set(routes_file)
        self._tracker.complete_task()

        trip_id_set = self._filter_trips_file(route_id_set, service_id_set, parameters["gtfs_folder"])
        if len(trip_id_set) == 0:
            self._warning = "Warning: No trips were selected."
        self._tracker.complete_task()

        serviced_stops_set = self._filter_stop_times_file(trip_id_set, parameters["gtfs_folder"])
        self._tracker.complete_task()

        self._filter_stops_file(serviced_stops_set, parameters["gtfs_folder"])
        self._tracker.complete_task()

    def _get_route_id_set(self, routes_file):
        id_set = set()
        with open(routes_file) as reader:
            header = reader.readline().split(",")
            id_col = header.index("route_id")
            for line in reader.readlines():
                cells = line.split(",")
                id_set.add(cells[id_col])
        return id_set

    def _filter_trips_file(self, route_id_set, service_id_set, gtfs_folder_name):
        exists = os.path.isfile(gtfs_folder_name + "/shapes.txt")
        shape_id_set = set()
        trip_id_set = set()
        with open(gtfs_folder_name + "/trips.txt") as reader:
            with open(gtfs_folder_name + "/trips.updated.csv", "w") as writer:
                header = reader.readline().strip()
                cells = header.split(",")
                writer.write(header)
                route_id_col = cells.index("route_id")
                service_id_col = cells.index("service_id")
                trip_id_col = cells.index("trip_id")
                if exists == True:
                    shape_id_col = cells.index("shape_id")
                for line in reader.readlines():
                    line = line.strip()
                    cells = line.split(",")
                    if not cells[route_id_col] in route_id_set:
                        continue
                    if not cells[service_id_col] in service_id_set:
                        continue
                    trip_id_set.add(cells[trip_id_col])
                    if exists == True:
                        shape_id_set.add(cells[shape_id_col])
                    writer.write("\n %s" % line)
        if exists == True:
            cleaned_shapes = self._filter_shape_file(shape_id_set, gtfs_folder_name)
        return trip_id_set

    def _filter_shape_file(self, shape_id_set, gtfs_folder_name):
        with open(gtfs_folder_name + "/shapes.txt") as reader:
            with open(gtfs_folder_name + "/shapes.updated.csv", "w") as writer:
                header = reader.readline().strip()
                cells = header.split(",")
                writer.write(header)
                shape_id_col = cells.index("shape_id")
                for line in reader.readlines():
                    line = line.strip()
                    cells = line.split(",")
                    if not cells[shape_id_col] in shape_id_set:
                        continue
                    writer.write("\n %s" % line)

    def _filter_stop_times_file(self, trip_id_set, gtfs_folder_name):
        serviced_stops_set = set()
        with open(gtfs_folder_name + "/stop_times.txt") as reader:
            with open(gtfs_folder_name + "/stop_times.updated.csv", "w") as writer:
                header = reader.readline().strip()
                writer.write(header)
                cells = header.split(",")
                trip_id_col = cells.index("trip_id")
                stop_id_col = cells.index("stop_id")
                for line in reader.readlines():
                    line = line.strip()
                    cells = line.split(",")
                    if not cells[trip_id_col] in trip_id_set:
                        continue
                    serviced_stops_set.add(cells[stop_id_col])
                    writer.write("\n%s" % line)
        return serviced_stops_set

    def _filter_stops_file(self, serviced_stops_set, gtfs_folder_name):
        with open(gtfs_folder_name + "/stops.txt") as reader:
            with open(gtfs_folder_name + "/stops.updated.csv", "w") as writer:
                header = reader.readline().strip()
                writer.write(header)
                cells = header.split(",")
                stop_id_col = cells.index("stop_id")
                for line in reader.readlines():
                    line = line.strip()
                    cells = line.split(",")
                    if not cells[stop_id_col] in serviced_stops_set:
                        continue
                    writer.write("\n%s" % line)

    @_m.method(return_type=_m.TupleType)
    def percent_completed(self):
        return self._tracker.get_progress()

    @_m.method(return_type=str)
    def tool_run_msg_status(self):
        return self.tool_run_msg
