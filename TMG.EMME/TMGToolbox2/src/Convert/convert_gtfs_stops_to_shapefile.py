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
from os import path as _path

_m.InstanceType = object
_m.TupleType = object
_m.ListType = list

_MODELLER = _m.Modeller()
_util = _MODELLER.module("tmg2.utilities.general_utilities")
_tmg_tpb = _MODELLER.module("tmg2.utilities.TMG_tool_page_builder")
_geo = _MODELLER.module("tmg2.utilities.geometry")

##########################################################################################################


class ConvertGTFSStopsToShapefile(_m.Tool()):

    version = "2.0.0"
    tool_run_msg = ""
    number_of_tasks = 1

    def __init__(self):
        self._tracker = _util.progress_tracker(self.number_of_tasks)

    def page(self):
        pb = _tmg_tpb.TmgToolPageBuilder(
            self,
            title="Export GTFS Stops As Shapefile v%s" % self.version,
            description="Converts the <b>stops.txt</b> file to a shapefile, flagging which \
                             modes it serves as well.",
            runnable=False,
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
        with _m.logbook_trace(
            name="{classname} v{version}".format(classname=(self.__class__.__name__), version=self.version),
            attributes=self._get_atts(),
        ):

            route_modes = self._load_routes(parameters["gtfs_folder"])
            print("Routes Loaded.")
            trip_modes = self._load_trips(route_modes, parameters["gtfs_folder"])
            print("Trips loaded.")
            stops = self._load_stops(parameters["gtfs_folder"])
            print("Stops loaded.")
            self._load_stop_times(stops, trip_modes, parameters["gtfs_folder"])
            print("Stop times loaded.")
            self._write_stops_to_shapefile(stops, parameters["shape_file_name"])
            self._write_projection_file(parameters["shape_file_name"])
            print("Shapefile written.")

    def _get_atts(self):
        atts = {"Version": self.version, "self": self.__MODELLER_NAMESPACE__}

        return atts

    def _load_routes(self, GTFS_folder_name):
        output = {}
        with open(GTFS_folder_name + "/routes.txt") as reader:
            header = reader.readline().strip().split(",")
            route_id_col = header.index("route_id")
            mode_col = header.index("route_type")

            for line in reader.readlines():
                cells = line.strip().split(",")
                output[cells[route_id_col]] = int(cells[mode_col])
        return output

    def _load_trips(self, route_modes, GTFS_folder_name):
        output = {}
        with open(GTFS_folder_name + "/trips.txt") as reader:
            header = reader.readline().strip().split(",")
            route_id_col = header.index("route_id")
            trip_id_col = header.index("trip_id")

            for line in reader.readlines():
                cells = line.strip().split(",")
                output[cells[trip_id_col]] = route_modes[cells[route_id_col]]
        return output

    def _load_stops(self, GTFS_folder_name):
        stops = {}
        with open(GTFS_folder_name + "/stops.txt") as reader:
            # stop_lat,zone_id,stop_lon,stop_id,stop_desc,stop_name,location_type
            header = reader.readline().strip().split(",")
            lat_col = header.index("stop_lat")
            lon_col = header.index("stop_lon")
            id_col = header.index("stop_id")
            name_col = header.index("stop_name")
            if "stop_desc" in header:
                desc_col = header.index("stop_desc")
            else:
                desc_col = header.index("stop_name")

            for line in reader.readlines():
                cells = line.strip().split(",")
                id = cells[id_col]
                stop = GTFS_stop(id, cells[lon_col], cells[lat_col], cells[name_col], cells[desc_col])
                stops[id] = stop
        return stops

    def _load_stop_times(self, stops, trip_modes, GTFS_folder_name):

        mode_character_map = {
            0: "s",
            1: "m",
            2: "r",
            3: "b",
            4: "f",
            5: "c",
            6: "g",
            7: "x",
        }

        with open(GTFS_folder_name + "/stop_times.txt") as reader:
            # trip_id,arrival_time,departure_time,stop_id,stop_sequence,stop_headsign,pickup_type,drop_off_type,shape_dist_traveled
            header = reader.readline().strip().split(",")
            trip_id_col = header.index("trip_id")
            stop_id_col = header.index("stop_id")

            for line in reader.readlines():
                cells = line.strip().split(",")
                if not cells[stop_id_col] in stops:
                    print("Could not find stop '%s'" % cells[stop_id_col])
                    continue
                stop = stops[cells[stop_id_col]]

                if not cells[trip_id_col] in trip_modes:
                    print("Could not find trip '%s'" % cells[trip_id_col])
                    continue
                mode = trip_modes[cells[trip_id_col]]

                stop.modes.add(mode_character_map[mode])

    def _write_stops_to_shapefile(self, stops, shape_file_name):
        with _geo.Shapely2ESRI(shape_file_name, "w", "POINT") as writer:
            max_description = 10
            max_name = 10
            for stop in stops.values():
                nameLen = len(stop.name)
                desLen = len(stop.description)

                if nameLen > max_name:
                    max_name = nameLen
                if desLen > max_description:
                    max_description = desLen
            print(max_description)
            print(max_name)
            writer.addField("StopID")
            writer.addField("Name", length=max_name)
            writer.addField("Description", length=max_description)
            writer.addField("Modes", length=8)

            def mode_set_to_string(mode_set):
                s = ""
                for c in mode_set:
                    s += c
                return s

            for stop in stops.values():
                point = _geo.Point(stop.lon, stop.lat)
                point["StopID"] = stop.id
                point["Name"] = stop.name
                point["Description"] = stop.description
                point["Modes"] = mode_set_to_string(stop.modes)
                writer.writeNext(point)

    def _write_projection_file(self, shape_file_name):
        wkt = 'GEOGCS["GCS_WGS_1984",DATUM["D_WGS_1984",SPHEROID["WGS_1984",6378137,298.257223563]],PRIMEM["Greenwich",0],UNIT["Degree",0.017453292519943295]]'
        with open(
            _path.splitext(shape_file_name)[0] + "/" + _path.splitext(_path.basename(shape_file_name))[0] + ".prj",
            "w",
        ) as writer:
            writer.write(wkt)

    @_m.method(return_type=_m.TupleType)
    def percent_completed(self):
        return self._tracker.get_progress()

    @_m.method(return_type=str)
    def tool_run_msg_status(self):
        return self.tool_run_msg


class GTFS_stop:
    def __init__(self, id, lon, lat, name, description):
        self.id = id
        self.lat = float(lat)
        self.lon = float(lon)
        self.name = name
        self.description = description
        self.modes = set()
