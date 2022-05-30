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
from copy import copy
from sqlite3 import paramstyle
import traceback as _traceback
from xml.etree import ElementTree as _ET
import time as _time
import multiprocessing
from itertools import combinations as get_combinations
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


class grid:
    """
    Grid class to support tuple indexing (just for coding convenience).

    Upon construction, it copies the default value into each of its cells.
    """

    def __init__(self, x_size, y_size, default=None):
        x_size, y_size = int(x_size), int(y_size)
        self._data = []
        self.x = x_size
        self.y = y_size
        i = 0
        total = x_size * y_size
        while i < total:
            self._data.append(copy(default))
            i += 1

    def __getitem__(self, key):
        x, y = key
        x, y = int(x), int(y)
        index = x * self.y + y
        return self._data[index]

    def __setitem__(self, key, val):
        x, y = key
        x, y = int(x), int(y)
        index = x * self.y + y
        self._data[index] = val


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
    __BOOL_PARSER = {"TRUE": True, "T": True, "FALSE": False, "F": False}

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
                            zone_id_2_int, int_2_zone_id, node_proxies = self._load_zones(
                                parameters, base_scenario, zones_element, zone_att.id
                            )
                            print("Loaded zones.")
                    else:
                        zone_id_2_int, int_2_zone_id, node_proxies = {}, {}, {}
                    # Complete the group/zone loading task
                    self._tracker.complete_task()
                    # Load and prepare the network.
                    self._tracker.start_process(2)
                    network = base_scenario.get_network()
                    print("Network loaded.")
                    self._tracker.complete_subtask()
                    self._prepare_network(network, node_proxies, line_group_att.id)
                    self._tracker.complete_task()
                    print("Prepared base network.")
                    with _trace("Transforming hyper network"):
                        transfer_grid, zone_crossing_grid = self._transform_network(
                            parameters, network, n_groups, n_zones
                        )
                        print(transfer_grid)
                        if n_station_groups > 0:
                            self._index_station_connectors(network, transfer_grid, station_groups, group_ids_2_int)
                        print("Hyper network generated.")
                    # Apply fare rules to network.
                    with _trace("Applying fare rules"):
                        self._tracker.start_process(n_rules + 1)
                        for i, fare_class in enumerate(parameters["fare_classes"]):
                            fare_rules_element = root_fare[i].find("fare_rules")
                            self._apply_fare_rules(
                                network,
                                fare_rules_element,
                                transfer_grid,
                                zone_crossing_grid,
                                group_ids_2_int,
                                zone_id_2_int,
                                fare_class["segment_fare_attribute"],
                                fare_class["link_fare_attribute"],
                            )

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
        knowing the node coordinates to work.
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
                else:
                    raise Exception("Zone element type '%s' is not node_selection or from_shapefile!" % typ)
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

    def _index_node_geometries(self, base_scenario):
        """
        -> Uses get_attribute_values() (Scenario function) to create proxy objects for Emme nodes.
        -> This is done to allow node locations to be loaded IN THE ORDER SPECIFIED BY THE FILE,
        regardless of whether those nodes are specified by a selector or by geometry.
        """
        indices, xtable, ytable = base_scenario.get_attribute_values("NODE", ["x", "y"])
        extents = min(xtable), min(ytable), max(xtable), max(ytable)
        spatial_index = grid_index(extents, marginSize=1.0)
        proxies = {}
        for node_number, index in indices.items():
            x = xtable[index]
            y = ytable[index]
            # Using a proxy class defined in THIS file, because we don't yet
            # have the full network loaded.
            node_proxy = node_spatial_proxy(node_number, x, y)
            spatial_index.insertPoint(node_proxy)
            proxies[node_number] = node_proxy
        return spatial_index, proxies

    def _load_zone_from_selection(self, base_scenario, zone_element, zone_attribute_id, tool, number, nodes):
        id = zone_element.attrib["id"]
        for selection_element in zone_element.findall("node_selector"):
            spec = {
                "result": zone_attribute_id,
                "expression": str(number),
                "aggregation": None,
                "selections": {"node": selection_element.text},
                "type": "NETWORK_CALCULATION",
            }
            try:
                tool(spec, scenario=base_scenario)
            except ModuleError as me:
                raise IOError("Error loading zone '%s': %s" % (id, me))
        # Update the list of proxy nodes with the network's newly-loaded zones attribute
        indices, table = base_scenario.get_attribute_values("NODE", [zone_attribute_id])
        for number, index in indices.items():
            nodes[number].zone = table[index]

    def _load_zone_from_geometry(self, zone_element, spatial_index, shape_files, number):
        id = zone_element.attrib["id"]
        for from_shape_file_element in zone_element.findall("from_shapefile"):
            sid = from_shape_file_element.attrib["id"]
            fid = int(from_shape_file_element.attrib["FID"])
            reader = shape_files[sid]
            polygon = reader.readFrom(fid)
            nodes_to_check = spatial_index.queryPolygon(polygon)
            for proxy in nodes_to_check:
                point = proxy.geometry
                if polygon.intersects(point):
                    proxy.zone = number

    # ---HYPER NETWORK GENERATION--------------------------------------------------------------------------
    def _prepare_network(self, network, node_proxies, line_group_att_id):
        """
        Prepares network attributes for transformation
        """
        network.create_attribute("TRANSIT_LINE", "group", 0)
        # Set of groups passing through but not stopping at the node
        network.create_attribute("NODE", "passing_groups", None)
        # Set of groups stopping at the node
        network.create_attribute("NODE", "stopping_groups", None)
        # The number of the fare zone
        network.create_attribute("NODE", "fare_zone", 0)
        # Dictionary to get from the node to its hyper nodes
        network.create_attribute("NODE", "to_hyper_node", None)
        # Link topological role
        network.create_attribute("LINK", "role", 0)
        # Node topological role
        network.create_attribute("NODE", "role", 0)
        # Initialize node attributes (incl. copying node zone)
        # Also, copy the zones loaded into the proxies
        for node in network.regular_nodes():
            node.passing_groups = set()
            node.stopping_groups = set()
            node.to_hyper_node = {}
            if node.number in node_proxies:
                proxy = node_proxies[node.number]
                node.fare_zone = proxy.zone
        # Determine stops & assign operators to nodes
        for line in network.transit_lines():
            group = int(line[line_group_att_id])
            line.group = group
            for segment in line.segments(True):
                i_node = segment.i_node
                if segment.allow_boardings or segment.allow_alightings:
                    i_node.stopping_groups.add(group)
                    if group in i_node.passing_groups:
                        i_node.passing_groups.remove(group)
                else:
                    if not group in i_node.stopping_groups:
                        i_node.passing_groups.add(group)
        # Determine node role. This needs to be done AFTER stops have been identified
        for node in network.regular_nodes():
            self.apply_node_role(node)
        # Determine link role. Needs to happen after node role's have been identified
        for link in network.links():
            i, j = link.i_node, link.j_node
            if i.is_centroid or j.is_centroid:
                # Link is a centroid connector
                continue
            permits_walk = False
            for mode in link.modes:
                if mode.type == "AUX_TRANSIT":
                    permits_walk = True
                    break
            if i.role == 1 and j.role == 2 and permits_walk:
                link.role = 1  # Station connector (access)
            elif i.role == 2 and j.role == 1 and permits_walk:
                link.role = 1  # Station connector (egress)
            elif i.role == 2 and j.role == 2 and permits_walk:
                link.role = 2  # Station transfer

    def apply_node_role(self, node):
        if not node.stopping_groups and not node.passing_groups:
            if node.is_centroid == False:
                #  Surface node without transit
                node.role = 1
            # Skip nodes without an incident transit segment
            return
        for link in node.outgoing_links():
            if link.i_node.is_centroid or link.j_node.is_centroid:
                continue
            for mode in link.modes:
                if mode.type == "AUTO":
                    # Surface node
                    node.role = 1
                    return
        for link in node.incoming_links():
            if link.i_node.is_centroid or link.j_node.is_centroid:
                continue
            for mode in link.modes:
                if mode.type == "AUTO":
                    node.role = 1
                    # Surface node
                    return
        # Station node is a transit stop, but does NOT connect to any auto links
        node.role = 2

    def _transform_network(self, parameters, network, number_of_groups, number_of_zones):
        total_nodes_0 = network.element_totals["regular_nodes"]
        total_links_0 = network.element_totals["links"]
        base_surface_nodes = []
        base_station_nodes = []
        for node in network.regular_nodes():
            if node.role == 1:
                base_surface_nodes.append(node)
            elif node.role == 2:
                base_station_nodes.append(node)
        transfer_grid = grid(number_of_groups + 1, number_of_groups + 1, set())
        zone_crossing_grid = grid(number_of_zones + 1, number_of_zones + 1, set())
        transfer_mode = network.mode(parameters["transfer_mode"])
        line_ids = [line.id for line in network.transit_lines()]
        n_tasks = 2 * (len(base_surface_nodes) + len(base_station_nodes)) + len(line_ids)
        self._tracker.start_process(n_tasks)
        for i, node in enumerate(base_surface_nodes):
            self._transform_surface_node(parameters, node, transfer_grid, transfer_mode)
            self._tracker.complete_subtask()
        print("Processed surface nodes")
        total_nodes_1 = network.element_totals["regular_nodes"]
        total_links_1 = network.element_totals["links"]
        _write("Created %s virtual road nodes." % (total_nodes_1 - total_nodes_0))
        _write("Created %s access links to virtual road nodes" % (total_links_1 - total_links_0))
        for i, node in enumerate(base_station_nodes):
            self._transform_station_node(parameters, node, transfer_grid, transfer_mode)
            self._tracker.complete_subtask()
        print("Processed station nodes")
        total_nodes_2 = network.element_totals["regular_nodes"]
        total_links_2 = network.element_totals["links"]
        _write("Created %s virtual transit nodes." % (total_nodes_2 - total_nodes_1))
        _write("Created %s access links to virtual transit nodes" % (total_links_2 - total_links_1))
        for node in base_surface_nodes:
            self._connect_surface_or_station_node(node, transfer_grid)
            self._tracker.complete_subtask()
        for node in base_station_nodes:
            self._connect_surface_or_station_node(node, transfer_grid)
            self._tracker.complete_subtask()
        print("Connected surface and station nodes")
        total_links_3 = network.element_totals["links"]
        _write("Created %s road-to-transit connector links" % (total_links_3 - total_links_2))

        def save_function(segment, i_node_id):
            pass

        for line_id in line_ids:
            self._process_transit_line(line_id, network, zone_crossing_grid, save_function)
            self._tracker.complete_subtask()
        print("Processed transit lines")
        total_links_4 = network.element_totals["links"]
        _write("Created %s in-line virtual links" % (total_links_4 - total_links_3))
        self._tracker.complete_task()
        return transfer_grid, zone_crossing_grid

    def _transform_surface_node(self, parameters, base_node, transfer_grid, transfer_mode):
        network = base_node.network
        created_nodes = []
        links_created = 0
        # Create the virtual nodes for stops
        for group_number in base_node.stopping_groups:
            new_node = network.create_regular_node(self._get_new_node_number(parameters, network))
            # Copy the node attributes, including x, y coordinates
            for att in network.attributes("NODE"):
                new_node[att] = base_node[att]
            # newNode.label = "RS%s" %int(groupNumber)
            new_node.label = base_node.label
            # Attach the new node to the base node for later
            base_node.to_hyper_node[group_number] = new_node
            created_nodes.append((new_node, group_number))
            # Connect base node to operator node
            in_bound_link = network.create_link(base_node.number, new_node.number, [transfer_mode])
            out_bound_link = network.create_link(new_node.number, base_node.number, [transfer_mode])
            links_created += 2
            # Attach the transfer links to the grid for indexing
            transfer_grid[0, group_number].add(in_bound_link)
            transfer_grid[group_number, 0].add(out_bound_link)
        # Connect the virtual nodes to each other
        for tup_a, tup_b in get_combinations(created_nodes, 2):  # Iterate through unique pairs of nodes
            node_a, group_a = tup_a
            node_b, group_b = tup_b
            link_ab = network.create_link(node_a.number, node_b.number, [transfer_mode])
            link_ba = network.create_link(node_b.number, node_a.number, [transfer_mode])
            links_created += 2
            transfer_grid[group_a, group_b].add(link_ab)
            transfer_grid[group_b, group_a].add(link_ba)
        # Create any virtual non-stop nodes
        for group_number in base_node.passing_groups:
            new_node = network.create_regular_node(self._get_new_node_number(parameters, network))
            # Copy the node attributes, including x, y coordinates
            for att in network.attributes("NODE"):
                new_node[att] = base_node[att]
            # newNode.label = "RP%s" %int(groupNumber)
            new_node.label = base_node.label
            # Attach the new node to the base node for later
            base_node.to_hyper_node[group_number] = new_node
            # Don't need to connect the new node to anything right now

    def _transform_station_node(self, parameters, base_node, transfer_grid, transfer_mode):
        network = base_node.network
        virtual_nodes = []
        # Catalog and classify inbound and outbound links for copying
        outgoing_links = []
        incoming_links = []
        outgoing_connectors = []
        incoming_connectors = []
        for link in base_node.outgoing_links():
            if link.role == 1:
                outgoing_links.append(link)
            elif link.j_node.is_centroid:
                if parameters["station_connector_flag"]:
                    outgoing_links.append(link)
                else:
                    outgoing_connectors.append(link)
        for link in base_node.incoming_links():
            if link.role == 1:
                incoming_links.append(link)
            elif link.i_node.is_centroid:
                if parameters["station_connector_flag"]:
                    incoming_links.append(link)
                else:
                    incoming_connectors.append(link)
        first = True
        for group_number in base_node.stopping_groups:
            if first:
                # Assign the existing node to the first group
                base_node.to_hyper_node[group_number] = base_node
                virtual_nodes.append((base_node, group_number))
                # Index the incoming and outgoing links to the Grid
                for link in incoming_links:
                    transfer_grid[0, group_number].add(link)
                for link in outgoing_links:
                    transfer_grid[group_number, 0].add(link)
                first = False
            else:
                virtual_node = network.create_regular_node(self._get_new_node_number(parameters, network))
                # Copy the node attributes, including x, y coordinates
                for att in network.attributes("NODE"):
                    virtual_node[att] = base_node[att]
                # virtualNode.label = "TS%s" %int(groupNumber)
                virtual_node.label = base_node.label
                # Assign the new node to its group number
                base_node.to_hyper_node[group_number] = virtual_node
                virtual_nodes.append((virtual_node, group_number))
                # Copy the base node's existing centroid connectors to the new virtual node
                if not parameters["station_connector_flag"]:
                    for connector in outgoing_connectors:
                        new_link = network.create_link(virtual_node.number, connector.j_node.number, connector.modes)
                        for att in network.attributes("LINK"):
                            new_link[att] = connector[att]
                    for connector in incoming_connectors:
                        new_link = network.create_link(connector.i_node.number, virtual_node.number, connector.modes)
                        for att in network.attributes("LINK"):
                            new_link[att] = connector[att]
                # Copy the base node's existing station connectors to the new virtual node
                for connector in outgoing_links:
                    new_link = network.create_link(virtual_node.number, connector.j_node.number, connector.modes)
                    for att in network.attributes("LINK"):
                        new_link[att] = connector[att]
                    # Index the new connector to the Grid
                    transfer_grid[group_number, 0].add(new_link)
                for connector in incoming_links:
                    new_link = network.create_link(connector.i_node.number, virtual_node.number, connector.modes)
                    for att in network.attributes("LINK"):
                        new_link[att] = connector[att]
                    # Index the new connector to the Grid
                    transfer_grid[0, group_number].add(new_link)
        # Connect the virtual nodes to each other
        # Iterate through unique pairs of nodes
        for tup_a, tup_b in get_combinations(virtual_nodes, 2):
            node_a, group_a = tup_a
            node_b, group_b = tup_b
            link_ab = network.create_link(node_a.number, node_b.number, [transfer_mode])
            link_ba = network.create_link(node_b.number, node_a.number, [transfer_mode])
            transfer_grid[group_a, group_b].add(link_ab)
            transfer_grid[group_b, group_a].add(link_ba)
        for group in base_node.passing_groups:
            new_node = network.create_regular_node(self._get_new_node_number(parameters, network))
            for att in network.attributes("NODE"):
                new_node[att] = base_node[att]
            new_node.label = base_node.label
            base_node.to_hyper_node[group] = new_node

    def _connect_surface_or_station_node(self, base_node_1, transfer_grid):
        network = base_node_1.network
        # Theoretically, we should only need to look at outgoing links,
        # since one node's outgoing link is another node's incoming link.
        for link in base_node_1.outgoing_links():
            if link.role == 0:
                # Skip non-connector links
                continue
            base_node_2 = link.j_node
            for group_number_1 in base_node_1.stopping_groups:
                virtual_node_1 = base_node_1.to_hyper_node[group_number_1]
                for group_number_2 in base_node_2.stopping_groups:
                    virtual_node_2 = base_node_2.to_hyper_node[group_number_2]
                    if network.link(virtual_node_1.number, virtual_node_2.number) is not None:
                        # Link already exists. Index it just in case
                        if group_number_1 != group_number_2:
                            transfer_grid[group_number_1, group_number_2].add(
                                network.link(virtual_node_1.number, virtual_node_2.number)
                            )
                        continue
                    new_link = network.create_link(virtual_node_1.number, virtual_node_2.number, link.modes)
                    for att in network.attributes("LINK"):
                        new_link[att] = link[att]
                    # Only index if the group numbers are different. Otherwise, this is the only
                    # part of the code where intra-group transfers are identified, so DON'T do
                    # it to have the matrix be consistent.
                    if group_number_1 != group_number_2:
                        transfer_grid[group_number_1, group_number_2].add(new_link)

    def _process_transit_line(self, line_id, network, zone_transfer_grid, save_function):
        line = network.transit_line(line_id)
        group = line.group
        line_mode = set([line.mode])
        base_links = [segment.link for segment in line.segments(False)]
        new_itinerary = [base_links[0].i_node.to_hyper_node[group].number]
        for base_link in base_links:
            iv = base_link.i_node.to_hyper_node[group].number
            jv = base_link.j_node.to_hyper_node[group].number
            new_itinerary.append(jv)
            v_link = network.link(iv, jv)
            if v_link is None:
                v_link = network.create_link(iv, jv, line_mode)
                for att in network.attributes("LINK"):
                    v_link[att] = base_link[att]
            else:
                v_link.modes |= line_mode
        new_line = network.create_transit_line("temp", line.vehicle.id, new_itinerary)
        for att in network.attributes("TRANSIT_LINE"):
            new_line[att] = line[att]
        for segment in line.segments(True):
            new_segment = new_line.segment(segment.number)
            for att in network.attributes("TRANSIT_SEGMENT"):
                new_segment[att] = segment[att]
            save_function(new_segment, segment.i_node.number)
            link = segment.link
            if link is not None:
                fzi = link.i_node.fare_zone
                fzj = link.j_node.fare_zone
                if fzi != fzj and fzi != 0 and fzj != 0:
                    # Add the segment's identifier, since change_transit_line_id de-references
                    # the line copy.
                    zone_transfer_grid[fzi, fzj].add((line_id, segment.number))
        network.delete_transit_line(line_id)
        _network_edit.change_transit_line_id(new_line, line_id)

    def _get_new_node_number(self, parameters, network):
        test_node = network.node(parameters["virtual_node_domain"])
        while test_node is not None:
            parameters["virtual_node_domain"] += 1
            test_node = network.node(parameters["virtual_node_domain"])
        return parameters["virtual_node_domain"]

    def _index_station_connectors(self, network, transfer_grid, station_groups, group_ids_2_int):
        print("Indexing station connectors")
        for line_group_id, station_centroids in station_groups.items():
            idx = group_ids_2_int[line_group_id]
            for node_id in station_centroids:
                centroid = network.node(node_id)
                # Skip non-zones
                if not centroid.is_centroid:
                    continue
                for link in centroid.outgoing_links():
                    if idx in link.j_node.stopping_groups:
                        transfer_grid[0, idx].add(link)
                for link in centroid.incoming_links():
                    if idx in link.i_node.stopping_groups:
                        transfer_grid[idx, 0].add(link)
            print("Indexed connectors for group %s" % line_group_id)

    # ---LOAD FARE RULES-----------------------------------------------------------------------------------

    def _apply_fare_rules(
        self,
        network,
        fare_rules_element,
        group_transfer_grid,
        zone_crossing_grid,
        group_ids_2_int,
        zone_ids_2_int,
        segment_fare_attribute,
        link_fare_attribute,
    ):
        lines_id_exed_by_group = {}
        for line in network.transit_lines():
            group = line.group
            if group in lines_id_exed_by_group:
                lines_id_exed_by_group[group].append(line)
            else:
                lines_id_exed_by_group[group] = [line]
        for fare_element in fare_rules_element.findall("fare"):
            typ = fare_element.attrib["type"]
            if typ == "initial_boarding":
                self._apply_initial_boarding_fare(
                    fare_element, group_ids_2_int, zone_ids_2_int, group_transfer_grid, link_fare_attribute
                )
            elif typ == "transfer":
                self._apply_transfer_boarding_fare(
                    fare_element, group_ids_2_int, group_transfer_grid, link_fare_attribute
                )
            elif typ == "distance_in_vehicle":
                self._apply_fare_by_distance(
                    fare_element, group_ids_2_int, lines_id_exed_by_group, segment_fare_attribute
                )
            elif typ == "zone_crossing":
                self._apply_zone_crossing_fare(
                    fare_element, group_ids_2_int, zone_ids_2_int, zone_crossing_grid, network, segment_fare_attribute
                )
            self._tracker.complete_subtask()

    def _apply_initial_boarding_fare(
        self, fare_element, group_ids_2_int, zone_ids_2_int, transfer_grid, link_fare_attribute
    ):
        cost = float(fare_element.attrib["cost"])
        with _trace("Initial Boarding Fare of %s" % cost):
            group_id = fare_element.find("group").text
            _write("Group: %s" % group_id)
            group_number = group_ids_2_int[group_id]
            in_zone_element = fare_element.find("in_zone")
            if in_zone_element is not None:
                zone_id = in_zone_element.text
                zone_number = zone_ids_2_int[zone_id]
                _write("In zone: %s" % zone_id)
                check_link = lambda link: link.i_node.fare_zone == zone_number
            else:
                check_link = lambda link: True
            include_all_element = fare_element.find("include_all_groups")
            if include_all_element is not None:
                include_all = self.__BOOL_PARSER[include_all_element.text]
                _write("Include all groups: %s" % include_all)
            else:
                include_all = True
            count = 0
            if include_all:
                for x_index in range(transfer_grid.x):
                    for link in transfer_grid[x_index, group_number]:
                        if check_link(link):
                            link[link_fare_attribute] += cost
                            count += 1
            else:
                for link in transfer_grid[0, group_number]:
                    if check_link(link):
                        link[link_fare_attribute] += cost
                        count += 1
            _write("Applied to %s links." % count)

    def _apply_transfer_boarding_fare(self, fare_element, group_ids_2_int, transfer_grid, link_fare_attribute):
        cost = float(fare_element.attrib["cost"])

        with _trace("Transfer Boarding Fare of %s" % cost):
            from_group_id = fare_element.find("from_group").text
            from_number = group_ids_2_int[from_group_id]
            _write("From Group: %s" % from_group_id)
            to_group_id = fare_element.find("to_group").text
            to_number = group_ids_2_int[to_group_id]
            _write("To Group: %s" % to_group_id)
            bi_directional_element = fare_element.find("bidirectional")
            if bi_directional_element is not None:
                bi_directional = self.__BOOL_PARSER[bi_directional_element.text.upper()]
                _write("Bidirectional: %s" % bi_directional)
            else:
                bi_directional = False
            count = 0
            for link in transfer_grid[from_number, to_number]:
                link[link_fare_attribute] += cost
                count += 1
            if bi_directional:
                for link in transfer_grid[to_number, from_number]:
                    link[link_fare_attribute] += cost
                    count += 1
            _write("Applied to %s links." % count)

    def _apply_fare_by_distance(self, fare_element, group_ids_2_int, lines_id_exed_by_group, segment_fare_attribute):
        cost = float(fare_element.attrib["cost"])
        with _trace("Fare by Distance of %s" % cost):
            group_id = fare_element.find("group").text
            group_number = group_ids_2_int[group_id]
            _write("Group: %s" % group_id)
            count = 0
            for line in lines_id_exed_by_group[group_number]:
                for segment in line.segments(False):
                    segment[segment_fare_attribute] += segment.link.length * cost
                    count += 1
            _write("Applied to %s segments." % count)

    def _apply_zone_crossing_fare(
        self, fare_element, group_ids_2_int, zone_ids_2_int, crossing_grid, network, segment_fare_attribute
    ):
        cost = float(fare_element.attrib["cost"])
        with _trace("Zone Crossing Fare of %s" % cost):
            group_id = fare_element.find("group").text
            group_number = group_ids_2_int[group_id]
            _write("Group: %s" % group_id)
            from_zone_id = fare_element.find("from_zone").text
            from_number = zone_ids_2_int[from_zone_id]
            _write("From Zone: %s" % from_zone_id)
            to_zone_id = fare_element.find("to_zone").text
            to_number = zone_ids_2_int[to_zone_id]
            _write("To Zone: %s" % to_zone_id)
            bi_directional_element = fare_element.find("bidirectional")
            if bi_directional_element is not None:
                bi_directional = self.__BOOL_PARSER[bi_directional_element.text.upper()]
                _write("Bidirectional: %s" % bi_directional)
            else:
                bi_directional = False
            count = 0
            for line_id, segment_number in crossing_grid[from_number, to_number]:
                line = network.transit_line(line_id)
                if line.group != group_number:
                    continue
                line.segment(segment_number)[segment_fare_attribute] += cost
                count += 1
            if bi_directional:
                for line_id, segment_number in crossing_grid[to_number, from_number]:
                    line = network.transit_line(line_id)
                    if line.group != group_number:
                        continue
                    line.segment(segment_number)[segment_fare_attribute] += cost
                    count += 1
            _write("Applied to %s segments." % count)
