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
Generate Hypernetwork From Schema Tool
    
    This tool is only compatible with Emme 4.6 and later versions

    Authors: pkucirek

    Initial revision by: mattaustin222

    Latest version by: WilliamsDiogu
    
    #---VERSION HISTORY
    
    0.0.1 Created on 2014-03-09 by pkucirek
    
    1.0.0 Debugged and deployed by 2014-05-23
    
    1.1.0 Added feature to save base I-node IDs for transit segments
        as they are being moved over to the hyper network. This enables
        transit speed updating.
    
    1.1.1 Fixed a bug in PrepareNetwork which only considers segments that permit alightings as 
        'stops.' We want to catch both boardings AND alightings
    
    1.1.2 Slightly tweaked the page() function's Javascript to allow the NONE option when segment
        attributes are pre-loaded from scenario.
        
    1.1.3 Slightly tweaked to over-write the FBTN scenario if it already exists.
    
    1.1.4 Fixed a bug in the scenario overwrite: If the target (new) scenario already exists,
        it gets deleted, then the base scenario is copied in its place first. This ensures that
        the new scenario is a verbatim copy of the base scenario prior to publishing the network.
        Before, it was possible to end up with different extra attributes between the two 
        scenarios.
        
    1.1.5 Modified to use the new spatial index. Also changed the copy scenario call to NOT
        copy over strategy or path files as this considerably increases runtime.
    
    1.2.0 Added new feature to accept relative paths for shapefiles. Absolute paths are still
        supported.
    
    1.3.0 Added new feature to associate a set of station zones with line group. Initial boarding rules
        will then be applied to all centroid connectors going from station zones to a stop of that
        operator.
        
    1.3.1 Minor change to accept two station groups being associated with a shared line group

    1.4.0 Added option to allow station-to-centroid hypernetwork connections by default. This 
        enables the proper connection of a centroid to a multi-operator station. The station group
        method allows for finer control of centroids, but cannot handle multiple operators at 
        a station. 
    2.0.0 Refactored and improved by WilliamsDiogu for XTMF2, compatible  with Emme 4.6 and base on
        Python 3 . 
"""
from sqlite3 import paramstyle
import traceback as _traceback
from xml.etree import ElementTree as _ET
import time as _time
import multiprocessing

from numpy import percentile
import inro.modeller as _m
from inro.emme.core.exception import ModuleError
from contextlib import contextmanager
from os import path

_m.TupleType = object
_m.ListType = list
_m.InstanceType = object

_trace = _m.logbook_trace
_write = _m.logbook_write
_MODELLER = _m.Modeller()
_bank = _MODELLER.emmebank
_util = _MODELLER.module("tmg2.utilities.general_utilities")
_tmg_tpb = _MODELLER.module("tmg2.utilities.TMG_tool_page_builder")
_geometry = _MODELLER.module("tmg2.utilities.geometry")
_network_edit = _MODELLER.module("tmg2.utilities.network_editing")
_spatial_index = _MODELLER.module("tmg2.utilities.spatial_index")
shapely_2_esri = _geometry.Shapely2ESRI
grid_index = _spatial_index.GridIndex
transit_line_proxy = _network_edit.TransitLineProxy
null_pointer_exception = _util.null_pointer_exception
EMME_VERSION = _util.get_emme_version(tuple)


class xml_validation_error(Exception):
    pass


class node_spatial_proxy:
    def __init__(self, id, x, y):
        self.id = id
        self.x = x
        self.y = y
        self.zone = 0
        self.geometry = _geometry.Point(x, y)

    def __str__(self):
        return str(self.id)


class GenerateHypernetworkFromSchema(_m.Tool()):
    version = "2.0.0"
    tool_run_msg = ""
    number_of_tasks = 5
    __ZONE_TYPES = ["node_selection", "from_shapefile"]

    def __init__(self):
        self._tracker = _util.progress_tracker(self.number_of_tasks)
        self.number_of_processors = multiprocessing.cpu_count()

    def page(self):
        if EMME_VERSION < (4, 6, 0):
            raise ValueError("Tool not compatible. Please upgrade to version 4.6.0+")
        pb = _tmg_tpb.TmgToolPageBuilder(
            self,
            title="Generate Hypernetwork From Schema v%s" % self.version,
            description="Generates a hyper-network to support fare-based transit \
                     assignment (FBTA), from an XML schema file. Links and segments with negative\
                     fare values will be reported to the Logbook for further inspection. \
                     For fare schema specification, \
                     please consult TMG documentation.\
                     <br><br><b>Temporary storage requirements:</b> one transit line extra \
                     attribute, one node extra attribute.\
                     <br><br><em>Not Callable from Modeller. Please use XTMF</em>",
            runnable=False,
            branding_text="- TMG Toolbox",
        )
        return pb.render()

    def __call__(self, parameters):
        base_scenario = _util.load_scenario(parameters["base_scenario"])
        try:
            self._execute(parameters, base_scenario)
        except Exception as e:
            msg = str(e) + "\n" + _traceback.format_exc()
            raise Exception(msg)

    def run_xtmf(self, parameters):
        base_scenario = _util.load_scenario(parameters["base_scenario"])
        try:
            self._execute(parameters, base_scenario)
        except Exception as e:
            msg = str(e) + "\n" + _traceback.format_exc()
            raise Exception(msg)

    def _execute(self, parameters, base_scenario):
        with _trace(
            name="{classname} v{version}".format(classname=(self.__class__.__name__), version=self.version),
            attributes=self._get_att(parameters),
        ):
            root_base = _ET.parse(parameters["base_schema_file"]).getroot()

            n_groups, n_zones, n_station_groups, valid_group_ids, valid_zone_ids = self._validate_base_schema_file(
                parameters, root_base
            )
            n_rules = []
            root_fare = []
            for i, fare_class in enumerate(parameters["fare_classes"]):
                root_fare.append(_ET.parse(fare_class["schema_file"]).getroot())
                n_rules.append(self._validate_fare_schema_file(root_fare[i], valid_group_ids, valid_zone_ids))
            n_rules = sum(n_rules)
            self._tracker.complete_task()

            # Load the line groups and zones
            version = root_base.find("version").attrib["number"]
            _write("Loading Base Schema File version %s" % version)
            print("Loading Base Schema File version %s" % version)

            self._tracker.start_process(n_groups + n_zones)
            with _util.temp_extra_attribute_manager(
                base_scenario, "TRANSIT_LINE", description="Line Group"
            ) as line_group_att:
                with _util.temp_extra_attribute_manager(base_scenario, "NODE", description="Fare Zone") as zone_att:
                    with _trace("Transit Line Groups"):
                        groups_element = root_base.find("groups")
                        group_ids_2_int, int_2_group_ids = self._load_groups(
                            base_scenario, groups_element, line_group_att.id
                        )
                        print("Loaded groups.", group_ids_2_int, int_2_group_ids)
                    station_groups_element = root_base.find("station_groups")
                    if station_groups_element is not None:
                        with _trace("Station Groups"):
                            station_groups = self._load_station_groups(base_scenario, station_groups_element)
                            print("Loaded station groups")
                    zones_element = root_base.find("zones")
                    if zones_element is not None:
                        with _trace("Fare Zones"):
                            self._load_zones(parameters, base_scenario, zones_element, zone_att.id)
                            # zone_id_2_int, int_2_zone_id, node_proxies = self._load_zones(
                            #     parameters, base_scenario, zones_element, zone_att.id
                            # )
                            print("Loaded zones.")
                    else:
                        zone_id_2_int, int_2_zone_id, node_proxies = {}, {}, {}
                    # Complete the group/zone loading task
                    self._tracker.complete_task()

    def _get_att(self, parameters):
        atts = {
            "Scenario": str(parameters["base_scenario"]),
            "Version": self.version,
            "self": self.__MODELLER_NAMESPACE__,
        }
        return atts

    def _validate_base_schema_file(self, parameters, root):
        # check the top-level of the file
        version_element = root.find("version")
        if version_element is None:
            raise xml_validation_error("Base Schema must specify a 'version' element.")
        groups_element = root.find("groups")
        if groups_element is None:
            raise xml_validation_error("Base schema must specify a 'group' element.")
        zones_element = root.find("zones")

        # Validate version
        try:
            version = version_element.attrib["number"]
        except KeyError:
            raise xml_validation_error("Version element must specify a 'number' attribute.")

        # Validate groups
        group_elements = groups_element.findall("group")
        valid_group_ids = set()
        if len(group_elements) == 0:
            raise xml_validation_error("Scehma must specify at least one group elements")
        for i, group_element in enumerate(group_elements):
            if not "id" in group_element.attrib:
                raise xml_validation_error("Group element #%s must specify an 'id' attribute" % i)
            id = group_element.attrib["id"]
            if id in valid_group_ids:
                raise xml_validation_error("Group id '%s' found more than once. Each id must be unique." % id)
            valid_group_ids.add(id)

            selection_elements = group_element.findall("selection")
            if len(selection_elements) == 0:
                raise xml_validation_error("Group element '%s' does not specify any 'selection' sub-elements" % id)

        # Validate zones, if required
        valid_zone_ids = set()
        if zones_element is not None:
            shape_file_elements = zones_element.findall("shapefile")
            zone_elements = zones_element.findall("zone")

            shape_file_ids = set()
            for i, shape_file_element in enumerate(shape_file_elements):
                if not "id" in shape_file_element.attrib:
                    raise xml_validation_error("Shapefile #%s element must specify an 'id' attribute" % i)

                id = shape_file_element.attrib["id"]
                if id in shape_file_ids:
                    raise xml_validation_error("Shapefile id '%' found more than once. Each id must be unique" % id)
                shape_file_ids.add(id)

                if not "path" in shape_file_element.attrib:
                    raise xml_validation_error("Shapefile '%s' must specify a 'path' attribute" % id)
                p = shape_file_element.attrib["path"]
                # Joins the path if it is relative.
                p = self._get_absolute_filepath(parameters, p)
                if not path.exists(p):
                    raise xml_validation_error("File not found for id '%s' at %s" % (id, p))
            for i, zone_element in enumerate(zone_elements):
                if not "id" in zone_element.attrib:
                    raise xml_validation_error("Zone element #%s must specify an 'id' attribute" % i)
                id = zone_element.attrib["id"]
                if id in valid_zone_ids:
                    raise xml_validation_error("Zone id '%s' found more than once. Each id must be unique" % id)
                valid_zone_ids.add(id)
                if not "type" in zone_element.attrib:
                    raise xml_validation_error("Zone '%s' must specify a 'type' attribute" % id)
                zone_type = zone_element.attrib["type"]
                if not zone_type in self.__ZONE_TYPES:
                    raise xml_validation_error("Zone type '%s' for zone '%s' is not recognized." % (zone_type, id))
                if zone_type == "node_selection":
                    if len(zone_element.findall("node_selector")) == 0:
                        raise xml_validation_error(
                            "Zone type 'node_selection' for zone '%s' must specify at least one 'node_selector' element."
                            % id
                        )
                elif zone_type == "from_shapefile":
                    child_element = zone_element.find("from_shapefile")
                    if child_element is None:
                        raise xml_validation_error(
                            "Zone type 'from_shapefile' for zone '%s' must specify exactly one 'from_shapefile' element."
                            % id
                        )
                    if not "id" in child_element.attrib:
                        raise xml_validation_error("from_shapefile element must specify an 'id' attribute.")
                    if not "FID" in child_element.attrib:
                        raise xml_validation_error("from_shapefile element must specify a 'FID' attribute.")
                    sid = child_element.attrib["id"]
                    if not sid in shape_file_ids:
                        raise xml_validation_error(
                            "Could not find a shapefile with the id '%s' for zone '%s'." % (sid, id)
                        )
                    try:
                        FID = int(child_element.attrib["FID"])
                        if FID < 0:
                            raise Exception()
                    except:
                        raise xml_validation_error("FID attribute must be a positive integer.")
        else:
            zone_elements = []

        n_station_groups = 0
        station_groups_element = root.find("station_groups")
        if station_groups_element is not None:
            station_group_elements = station_groups_element.findall("station_group")

            for element in station_group_elements:
                forGroup = element.attrib["for"]
                if not forGroup in valid_group_ids:
                    raise xml_validation_error(
                        "Could not find a group '%s' for to associate with a station group" % forGroup
                    )
                n_station_groups += 1
        return len(group_elements), len(zone_elements), n_station_groups, valid_group_ids, valid_zone_ids

    def _get_absolute_filepath(self, parameters, other_path):
        """
        For the shapefile path, this function checks if it is a relative path or not.
        If it is a relative path, it returns a valid absolute path based on the
        location of the XML Schema File.
        """
        if path.isabs(other_path):
            return other_path
        return path.join(path.dirname(parameters["base_schema_file"]), other_path)

    def _validate_fare_schema_file(self, root, valid_group_ids, valid_zone_ids):
        fare_rules_element = root.find("fare_rules")
        if fare_rules_element is None:
            raise xml_validation_error("Fare schema must specify a 'fare_rules' element.")
        fare_elements = fare_rules_element.findall("fare")

        def check_group_id(group, name):
            if not group in valid_group_ids:
                raise xml_validation_error("Could not find a group with id '%s' for element '%s'" % (group, name))

        def check_zone_id(zone, name):
            if not zone in valid_zone_ids:
                raise xml_validation_error("Could not find a zone with id '%s' for element '%s'" % (zone, name))

        def check_is_bool(val, name):
            if not val.upper() in ["TRUE", "T", "FALSE", "F"]:
                raise xml_validation_error("Value '%s' for element '%s' must be True or False." % (val, name))

        for i, fare_element in enumerate(fare_elements):
            if not "cost" in fare_element.attrib:
                raise xml_validation_error("Fare element #%s must specify a 'cost' attribute" % i)
            if not "type" in fare_element.attrib:
                raise xml_validation_error("Fare element #%s must specify a 'type' attribute" % i)
            try:
                cost = float(fare_element.attrib["cost"])
            except ValueError:
                raise xml_validation_error("Fare element #%s attribute 'cost' must be valid decimal number." % i)
            rule_type = fare_element.attrib["type"]
            if rule_type == "initial_boarding":
                required_children = {"group": check_group_id}
                optional_children = {"in_zone": check_zone_id, "include_all_groups": check_is_bool}
            elif rule_type == "transfer":
                required_children = {"from_group": check_group_id, "to_group": check_group_id}
                optional_children = {"bidirectional": check_is_bool}
            elif rule_type == "zone_crossing":
                required_children = {"group": check_group_id, "from_zone": check_zone_id, "to_zone": check_zone_id}
                optional_children = {"bidirectional": check_is_bool}
            elif rule_type == "distance_in_vehicle":
                required_children = {"group": check_group_id}
                optional_children = {}
            else:
                raise xml_validation_error("Fare rule type '%s' not recognized." % rule_type)
            # Check required children
            for name, check_func in required_children.items():
                child = fare_element.find(name)
                if child is None:
                    raise xml_validation_error(
                        "Fare element #%s of type '%s' must specify a '%s' element" % (i, rule_type, name)
                    )
                text = child.text
                check_func(text, name)
            # Check optional children
            for name, check_func in optional_children.items():
                child = fare_element.find(name)
                if child is None:
                    continue
                text = child.text
                check_func(text, name)
        return len(fare_elements)

    def _load_groups(self, base_scenario, groups_element, line_group_att_id):
        group_ids_2_int = {}
        int_2_group_ids = {}

        tool = _MODELLER.tool("inro.emme.network_calculation.network_calculator")

        def get_spec(number, selection):
            return {
                "result": line_group_att_id,
                "expression": str(number),
                "aggregation": None,
                "selections": {"transit_line": selection},
                "type": "NETWORK_CALCULATION",
            }

        for i, group_element in enumerate(groups_element.findall("group")):
            group_number = i + 1

            id = group_element.attrib["id"]
            group_ids_2_int[id] = group_number
            int_2_group_ids[group_number] = id

            for selection_element in group_element.findall("selection"):
                selector = selection_element.text
                spec = get_spec(group_number, selector)
                try:
                    tool(spec, scenario=base_scenario)
                except ModuleError:
                    msg = "Emme runtime error processing line group '%s'." % id
                    _write(msg)
                    print(msg)

            msg = "Loaded group %s: %s" % (group_number, id)
            print(msg)
            _write(msg)
            self._tracker.complete_subtask()
        return group_ids_2_int, int_2_group_ids

    def _load_station_groups(self, base_scenario, station_groups_element):
        tool = _MODELLER.tool("inro.emme.network_calculation.network_calculator")

        station_groups, ids = {}, []
        with _util.temp_extra_attribute_manager(base_scenario, "NODE", returnId=True) as attr:

            for i, station_group_element in enumerate(station_groups_element.findall("station_group")):
                for_group = station_group_element.attrib["for"]
                selector = station_group_element.attrib["selection"]

                spec = {
                    "result": attr,
                    "expression": str(i + 1),  # Plus one since the attribute is initialized to 0
                    "aggregation": None,
                    "selections": {"node": selector},
                    "type": "NETWORK_CALCULATION",
                }
                tool(spec, scenario=base_scenario)
                station_groups[for_group] = set()
                ids.append(for_group)

            indices, table = base_scenario.get_attribute_values("NODE", [attr])
            for node_number, index in indices.items():
                value = int(table[index])
                if value == 0:
                    continue
                station_groups[ids[value - 1]].add(node_number)

        return station_groups

    def _load_zones(self, parameters, base_scenario, zones_element, zone_attribute_id):
        """
        Loads node zone numbers. This is a convoluted process in order to allow
        users to apply zones by BOTH selectors AND geometry. The first method
        applies changes directly to the base scenario, which the second requires
        knowing the node coordindates to work.

        Much of this method (and associated sub-methods) is BLACK MAGIC
        """
        zone_id_2_int = {}
        int_2_zone_id = {}

        tool = _MODELLER.tool("inro.emme.network_calculation.network_calculator")

        shape_files = self._load_shape_files(parameters, zones_element)
        spatial_index, nodes = self._index_node_geometries(base_scenario)

        try:
            for number, zone_element in enumerate(zones_element.findall("zone")):
                id = zone_element.attrib["id"]
                typ = zone_element.attrib["type"]

                number += 1

                zone_id_2_int[id] = number
                int_2_zone_id[number] = id

                if typ == "node_selection":
                    self._load_zone_from_selection(base_scenario, zone_element, zone_attribute_id, tool, number, nodes)
                elif typ == "from_shapefile":
                    self._load_zone_from_geometry(zone_element, spatial_index, shape_files, number)

                msg = "Loaded zone %s: %s" % (number, id)
                _write(msg)
                print(msg)
                self._tracker.complete_subtask()
        finally:
            # Close the shapefile readers
            for reader in shape_files.values():
                reader.close()

        return zone_id_2_int, int_2_zone_id, nodes

    def _load_shape_files(self, parameters, zones_element):
        shape_files = {}
        try:
            for shape_file_element in zones_element.findall("shapefile"):
                id = shape_file_element.attrib["id"]
                pth = shape_file_element.attrib["path"]
                # Join the path if it is relative
                pth = self._get_absolute_filepath(parameters, pth)

                reader = shapely_2_esri(pth, "r")
                reader.open()
                if reader.getGeometryType() != "POLYGON":
                    raise IOError("Shapefile %s does not contain POLYGONS" % pth)

                shape_files[id] = reader
        except:
            for reader in shape_files.values():
                reader.close()
            raise

        return shape_files
