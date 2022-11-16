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

# from posix import EX_TEMPFAIL
import inro.modeller as _m
import csv
import traceback as _traceback
from contextlib import contextmanager

# from contextlib import nested
from os import path as _path
from pyproj import Proj

_m.InstanceType = object
_m.TupleType = object
_m.ListType = list

_MODELLER = _m.Modeller()  # Instantiate Modeller once.
_util = _MODELLER.module("tmg2.utilities.general_utilities")
_tmgTPB = _MODELLER.module("tmg2.utilities.TMG_tool_page_builder")
_geo = _MODELLER.module("tmg2.utilities.geometry")
_spindex = _MODELLER.module("tmg2.utilities.spatial_index")
EMME_VERSION = _util.get_emme_version(tuple)


class GTFStoEmmeMap(_m.Tool()):
    version = "2.0.0"
    tool_run_msg = ""
    number_of_tasks = 1

    # Tool Parameters
    file_name = _m.Attribute(str)
    mapping_output_file = _m.Attribute(str)

    def __init__(self):
        # ---Init internal variables
        self._tracker = _util.progress_tracker(self.number_of_tasks)  # init the progress_tracker

    def page(self):

        pb = _tmgTPB.TmgToolPageBuilder(
            self,
            title="GTFS Stops to Emme Node File v%s" % self.version,
            description="Takes the <b>stops.txt</b> file or a <b>shapefile</b> to create a mapping file that shows \
                             the node in the EMME network which it corresponds to.",
            branding_text="- TMG Toolbox",
        )

        if self.tool_run_msg != "":  # to display messages in the page
            pb.tool_run_status(self.tool_run_msg_status)

        pb.add_select_file(
            tool_attribute_name="file_name",
            window_type="file",
            file_filter="*.txt *.shp",
            title="stops.txt file from the GTFS folder or stops file in *.shp format",
        )

        pb.add_select_file(
            tool_attribute_name="mapping_output_file",
            window_type="save_file",
            file_filter="*.csv",
            title="Map file to export",
        )

        return pb.render()

    def __call__(self, parameters):

        try:
            self._execute(parameters)
        except Exception as e:
            self.tool_run_msg = _m.PageBuilder.format_exception(e, _traceback.format_exc())
            raise

        self.tool_run_msg = _m.PageBuilder.format_info("Done.")

    def run(self):
        self.tool_run_msg = ""
        self._tracker.reset()
        parameters = self._build_page_builder_parameters()
        try:
            self._execute(parameters)
        except Exception as e:
            self.tool_run_msg = _m.PageBuilder.format_exception(e, _traceback.format_exc())
            raise

        self.tool_run_msg = _m.PageBuilder.format_info("Done")

    def run_xtmf(self, parameters):
        try:
            self._execute(parameters)
        except Exception as e:
            raise Exception(_traceback.format_exc())

    def _execute(self, parameters):
        with _m.logbook_trace(name="{classname} v{version}".format(classname=(self.__class__.__name__), version=self.version), attributes=self._get_atts()):
            # def file type
            if parameters["input_stop_file"][-3:].lower() == "txt":
                stops = self._load_stops_txt(parameters["input_stop_file"])
            elif parameters["input_stop_file"][-3:].lower() == "shp":
                stops = self._load_stops_shp(parameters["input_stop_file"])
            else:
                raise Exception("Not a correct format")
            # need to convert stops from lat lon to UTM
            converted_stops = self._convert_stops(stops)
            # load nodes from network
            all_nodes = _MODELLER.scenario.get_network().regular_nodes()
            # create node dictionary like converted stops?
            nodes = {}
            for n in all_nodes:
                nodes[int(n.id)] = (float(n.x), float(n.y))
            # find extents
            extents = self._find_extents(converted_stops, nodes)
            # load and find nearest point
            mapping = self._find_nearest(extents, converted_stops, nodes)
            self._store_nearest(mapping, parameters["output_mapping_file"])

    def _get_atts(self):
        atts = {"Version": self.version, "self": self.__MODELLER_NAMESPACE__}

        return atts

    def _load_stops_txt(self, file_name):
        stops = {}
        with open(file_name) as reader:
            # stop_lat,zone_id,stop_lon,stop_id,stop_desc,stop_name,location_type
            header = reader.readline().strip().split(",")
            lat_col = header.index("stop_lat")
            lon_col = header.index("stop_lon")
            id_col = header.index("stop_id")
            name_col = header.index("stop_name")
            desc_col = header.index("stop_desc")

            for line in reader.readlines():
                cells = line.strip().split(",")
                id = cells[id_col]
                stop = gtfs_stop(id, cells[lon_col], cells[lat_col], cells[name_col], cells[desc_col])
                stops[id] = [float(cells[lon_col]), float(cells[lat_col])]
        return stops

    def _load_stops_shp(self, file_name):
        stops = {}
        with _geo.Shapely2ESRI(file_name, "r") as reader:
            for point in reader.readThrough():
                id = str(point.properties["stop_id"])
                lat = float(point.properties["stop_lat"])
                lon = float(point.properties["stop_lon"])
                stops[id] = [lon, lat]
        return stops

    def _convert_stops(self, stops):
        converted_stops = {}
        # find what zone system the file is using
        full_zone_string = _m.Modeller().desktop.project.spatial_reference_file
        if EMME_VERSION >= (4, 3, 0):
            with open(full_zone_string, "r") as zone_file:
                zone_string = zone_file.read()
                hemisphere = zone_string[28:29]
                project_zone = int(zone_string[26:28])
        else:
            hemisphere = full_zone_string[-5:-4]
            project_zone = int(full_zone_string[-7:-5])
        # put try and exception statements here?
        if hemisphere.lower() == "s":
            p = Proj("+proj=utm +ellps=WGS84 +zone=%d +south" % project_zone)
        else:
            p = Proj("+proj=utm +ellps=WGS84 +zone=%d" % project_zone)
        for stop in stops.keys():
            temp_lons = (float(stops[stop][0]),)
            temp_lats = (float(stops[stop][1]),)
            x, y = p(temp_lons, temp_lats)
            converted_stops[stop] = x + y
            converted_stops[stop] = (
                float(converted_stops[stop][0]),
                float(converted_stops[stop][1]),
            )
        return converted_stops

    def _find_extents(self, converted_stops, nodes):
        # find extents
        max_extent_x = float("-inf")
        min_extent_x = float("inf")
        max_extent_y = float("-inf")
        min_extent_y = float("inf")
        for key in converted_stops:
            if converted_stops[key][0] < min_extent_x:
                min_extent_x = float(converted_stops[key][0])
            if converted_stops[key][0] > max_extent_x:
                max_extent_x = float(converted_stops[key][0])
            if converted_stops[key][1] < min_extent_y:
                min_extent_y = float(converted_stops[key][1])
            if converted_stops[key][1] > max_extent_y:
                max_extent_y = float(converted_stops[key][1])
        for node in nodes:
            if nodes[node][0] < min_extent_x:
                min_extent_x = float(nodes[node][0])
            if nodes[node][0] > max_extent_x:
                max_extent_x = float(nodes[node][0])
            if nodes[node][1] < min_extent_y:
                min_extent_y = float(nodes[node][1])
            if nodes[node][1] > max_extent_y:
                max_extent_y = float(nodes[node][1])
        extents = (min_extent_x - 1, min_extent_y - 1, max_extent_x + 1, max_extent_y + 1)
        return extents

    def _find_nearest(self, extents, converted_stops, nodes):
        map = []
        spatial_index = _spindex.GridIndex(extents, 1000, 1000)
        network = _MODELLER.scenario.get_network()
        for node in network.regular_nodes():
            spatial_index.insertPoint(node)
        for stop in converted_stops:
            nearest_node = spatial_index.nearestToPoint(converted_stops[stop][0], converted_stops[stop][1])
            if nearest_node[0] == "Nothing Found":
                map.append(
                    [
                        stop,
                        nearest_node[0],
                        converted_stops[stop][0],
                        converted_stops[stop][1],
                        -1,
                        -1,
                    ]
                )
            elif nearest_node[0] is None:
                map.append(
                    [
                        stop,
                        nearest_node[0],
                        converted_stops[stop][0],
                        converted_stops[stop][1],
                        0,
                        0,
                    ]
                )
            else:
                cleaned_number = int(nearest_node[0])
                map.append(
                    [
                        stop,
                        cleaned_number,
                        converted_stops[stop][0],
                        converted_stops[stop][1],
                        nodes[cleaned_number][0],
                        nodes[cleaned_number][1],
                    ]
                )
        return map

    def _store_nearest(self, map, mapping_output_file):
        with open(mapping_output_file, "w", newline="") as csv_file:
            map_file = csv.writer(csv_file, delimiter=",")
            header = ["stopID", "emmeID", "stop x", "stop y", "node x", "node y"]
            map_file.writerow(header)
            for row in map:
                map_file.writerow([row[0], row[1], row[2], row[3], row[4], row[5]])

    def _build_page_builder_parameters(self):
        parameters = {
            "file_name": self.file_name,
            "mapping_output_file": self.mapping_output_file,
        }
        return parameters

    @_m.method(return_type=_m.TupleType)
    def percent_completed(self):
        return self._tracker.get_progress()

    @_m.method(return_type=str)
    def tool_run_msg_status(self):
        return self.tool_run_msg


class gtfs_stop:
    def __init__(self, id, lon, lat, name, description):
        self.id = id
        self.lat = float(lat)
        self.lon = float(lon)
        self.name = name
        self.description = description
        self.modes = set()
