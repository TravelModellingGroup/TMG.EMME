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
"""
Contains a bunch of Python utility functions commonly used in TMG tools
and products. Set up as a non-runnable (e.g. private) Emme module so that
it can be distributed in the TMG toolbox

"""
import inro.modeller as _m
import inro.emme.core.exception as _excep
from contextlib import contextmanager
import warnings as _warn
import sys as _sys
import traceback as _tb
import subprocess as _sp
import six
import random
import csv

if six.PY2:
    from itertools import izip
from json import loads as _parsedict
from os.path import dirname

_MODELLER = _m.Modeller()
_bank = _MODELLER.emmebank
_trace = _m.logbook_trace
_write = _m.logbook_write

network_calculation_tool = _MODELLER.tool("inro.emme.network_calculation.network_calculator")
matrix_calc_tool = _MODELLER.tool("inro.emme.matrix_calculation.matrix_calculator")
extra_parameter_tool = _MODELLER.tool("inro.emme.traffic_assignment.set_extra_function_parameters")


class Face(_m.Tool()):
    def page(self):
        pb = _m.ToolPageBuilder(
            self,
            runnable=False,
            title="Utilities",
            description="Collection of private utilities",
            branding_text="- TMG Toolbox",
        )

        pb.add_text_element("To import, call inro.modeller.Modeller().module('%s')" % str(self))

        return pb.render()


# -------------------------------------------------------------------------------------------


def format_reverse_stack():
    eType, eVal, eTb = _sys.exc_info()
    stackList = _tb.extract_tb(eTb)
    msg = "%s: %s\n\n\Stack trace below:" % (eVal.__class__.__name__, str(eVal))
    stackList.reverse()
    for file, line, func, text in stackList:
        msg += "\n  File '%s', line %s, in %s" % (file, line, func)
    return msg


# -------------------------------------------------------------------------------------------
def num_to_mtxid(matrix_number):
    return "mf" + str(matrix_number)


# -------------------------------------------------------------------------------------------
def iterpairs(iterable):
    """
    Iterates through two subsequent elements in any iterable.
    Example:
        x = [1,2,3,4,5]
        for (val1, val2) in iterpairs(x): print "1=%s 2=%s" %(val1, val2)
        >>> 1=1 2=2
        >>> 1=2 2=3
        >>> 1=3 2=4
        >>> 1=4 2=5
    """

    iterator = iterable.__iter__()

    try:
        prev = six.next(iterator)
    except StopIteration:
        return

    for val in iterator:
        yield prev, val
        prev = val


# -------------------------------------------------------------------------------------------


def itersync(list1, list2):
    """
    Iterates through tuples of corresponding values for
    lists of the same length.

    Example:
        list1 = [1,2,3,4,5]
        list2 = [6,7,8,9,10]

        for a, b in itersync(list1, list2):
            print a,b
        >>>1 6
        >>>2 7
        >>>3 8
        >>>4 9
        >>>5 10
    """
    # izip is no longer included in Python 3
    if six.PY3:
        return izip(list1, list2)
    else:
        return zip(list1, list2)


# -------------------------------------------------------------------------------------------


def equap(number1, number2, precision=0.00001):
    """
    Tests for shallow floating point approximate equality.

    Args:
        - number 1: The first float
        - number 2: The second float
        - precision (=0.00001): The maximum allowed error.
    """
    diff = abs(float(number1), float(number2))
    return diff < precision


# -------------------------------------------------------------------------------------------


def databank_has_different_zones(emmebank):
    """
    Checks that all scenarios have the same zone system.

    Args:
        - emmebank: The Emmebank object to test

    Returns:
        - True if all of the scenarios have the same zone system,
                False otherwise.
    """

    scenarioZones = [set(sc.zone_numbers) for sc in emmebank.scenarios()]
    differentZones = False
    for nZones1, nZones2 in iterpairs(scenarioZones):
        if nZones1 != nZones2:
            differentZones = True
            break
    return differentZones


# -------------------------------------------------------------------------------------------


def getScenarioModes(scenario, types=["AUTO", "AUX_AUTO", "TRANSIT", "AUX_TRANSIT"]):
    """
    Returns a list of mode tuples [(id, type, description)] for a given Scenario object,
    bypassing the need to load the Network first.
    """
    """
    IMPLEMENTATION NOTE: This currently uses an *undocumented* function for the
    Scenario object (scenario.modes()). I can confirm that this function exists
    in Emme 4.0.3 - 4.0.8, and is supported in the 4.1 Beta versions (4.1.0.7 and
    4.1.0.8). Since this is unsupported, however, there is a possibility that
    this will need to be changed going forward (possibly using a new function
    scenario.get_partial_network(...) which is included in 4.1.0.7 but also
    currently undocumented).
        - @pkucirek 11/03/2014
    """
    return [(mode.id, mode.type, mode.description) for mode in scenario.modes() if mode.type in types]


# -------------------------------------------------------------------------------------------

_mtxNames = {"FULL": "mf", "DESTINATION": "md", "ORIGIN": "mo", "SCALAR": "ms"}


def initialize_matrix(
    id=None,
    default=0,
    name="",
    description="",
    matrix_type="FULL",
    preserve_description=False,
    preserve_data=False,
):
    """
    Utility function for creation and initialization of matrices. Only works
    for the current Emmebank.

    Args:
        - id (=None): Optional. Accepted value is a string or integer ID  (must
            also specify a matrix_type to be able to use integer ID). If specified,
            this function will initialize the matrix with the given ID to a new
            default value; changing its name and description if they are given.
            If unspecified, this function will create an available matrix - however
            the 'matrix_type' argument MUST also be specified.
        - default (=0): Optional The numerical value to initialize the matrix to
            (i.e., its default value).
        - name (=""): Optional. If specified, the newly-initialized matrix will
            have this as its 6-character name.
        - description (=""): Optional. If specified, the newly-initialized matrix will
            have this as its 40-character description.
        - matrix_type (='FULL'): One of 'SCALAR', 'ORIGIN', 'DESTINATION',
            or 'FULL'. If an ID is specified, the matrix type will be
            inferred from the ID's prefix. This argument is NOT optional
            if passing in an integer ID, or if requesting a new matrix.
        - preserve_description (=False): Set to True to preserve the description of an
            existing matrix. This is useful if you don't know whether the matrix being
            initialized exists or is new, and you want to specify a 'default'
            description.

    Returns: The Emme Matrix object created or initialized.
    """

    if id is None:
        # Get an available matrix
        id = _bank.available_matrix_identifier(matrix_type)
    elif isinstance(id, int):
        # If the matrix id is given as an integer
        try:
            id = "%s%s" % (_mtxNames[matrix_type], id)
        except KeyError:
            raise TypeError("Matrix type '%s' is not a valid matrix type." % matrix_type)
    elif "type" in dir(id):
        # If the matrix id is given as a matrix object
        t = id.type
        if not t in _mtxNames:
            raise TypeError("Assumed id was a matrix, but its type value was not recognized %s" % type(id))
        id = id.id  # Set the 'id' variable to the matrix's 'id' property.
    elif not isinstance(id, six.string_types):
        raise TypeError("Id is not a supported type: %s" % type(id))

    mtx = _bank.matrix(id)

    if mtx is None:
        # Matrix does not exist, so create it.
        mtx = _bank.create_matrix(id, default_value=default)
        if name:
            mtx.name = name[:40]
        if description:
            mtx.description = description[:80]
        _m.logbook_write("Created new matrix %s: '%s' (%s)." % (id, mtx.name, mtx.description))
    else:
        if mtx.read_only:
            raise _excep.ProtectionError("Cannot modify matrix '%s' as it is protected against modifications." % id)

        if not preserve_data:
            mtx.initialize(value=default)
        if name:
            mtx.name = name[:6]
        if description and not preserve_description:
            mtx.description = description[:80]
        _m.logbook_write("Initialized existing matrix %s: '%s' (%s)." % (id, mtx.name, mtx.description))

    return mtx


# -------------------------------------------------------------------------------------------


def getAvailableScenarioNumber():
    """
    Returns: The number of an available scenario. Raises an exception
    if the _bank is full.
    """
    for i in range(0, _m.Modeller().emmebank.dimensions["scenarios"]):
        if _m.Modeller().emmebank.scenario(i + 1) is None:
            return i + 1

    raise inro.emme.core.exception.CapacityError("No new scenarios are available: databank is full!")


# -------------------------------------------------------------------------------------------

TEMP_ATT_PREFIXES = {
    "NODE": "ti",
    "LINK": "tl",
    "TURN": "tp",
    "TRANSIT_LINE": "tt",
    "TRANSIT_SEGMENT": "ts",
}


@contextmanager
def temp_extra_attribute_manager(scenario, domain, default=0.0, description=None, returnId=False):
    """
    Creates a temporary extra attribute in a given scenario, yield-returning the
    attribute object. Designed to be used as a context manager, for cleanup
    after a run.

    Extra attributes are labeled thusly:
        - Node: @ti123
        - Link: @tl123
        - Turn: @tp123
        - Transit Line: @tt123
        - Transit Segment: @ts123
        (where 123 is replaced by a number)

    Args: (scenario, domain, default= 0.0, description= None)
        - scenario= The Emme scenario object in which to create the extra attribute
        - domain= One of 'NODE', 'LINK', 'TURN', 'TRANSIT_LINE', 'TRANSIT_SEGMENT'
        - default= The default value of the extra attribute
        - description= An optional description for the attribute
        - returnId (=False): Flag to return either the Extra Attribute object, or its ID

    Yields: The Extra Attribute object created (or its ID as indicated by the returnId arg).
    """

    domain = str(domain).upper()
    if not domain in TEMP_ATT_PREFIXES:
        raise TypeError("Domain '%s' is not a recognized extra attribute domain." % domain)
    prefix = TEMP_ATT_PREFIXES[domain]

    existingAttributeSet = set([att.name for att in scenario.extra_attributes() if att.type == domain])

    index = 1
    id = "@%s%s" % (prefix, index)
    while id in existingAttributeSet:
        index += 1
        id = "@%s%s" % (prefix, index)
        if index > 999:
            raise Exception("Scenario %s already has 999 temporary extra attributes" % scenario)
    tempAttribute = scenario.create_extra_attribute(domain, id, default)
    msg = "Created temporary extra attribute %s in scenario %s" % (id, scenario)
    if description:
        tempAttribute.description = description
        msg += ": %s" % description
    _m.logbook_write(msg)

    if returnId:
        retval = tempAttribute.id
    else:
        retval = tempAttribute

    try:
        yield retval
    finally:
        scenario.delete_extra_attribute(id)
        _m.logbook_write("Deleted extra attribute %s" % id)


# -------------------------------------------------------------------------------------------


@contextmanager
def temp_matrix_manager(description="[No description]", matrix_type="FULL", default=0.0):
    """
    Creates a temporary matrix in a context manager.

    Args:
        - description (="[No description]"): The description of the temporary matrix.
        - matrix_type (='FULL'): The type of temporary matrix to create. One of
            'SCALAR', 'ORIGIN', 'DESTINATION', or 'FULL'.
        - default (=0.0): The matrix's default value.
    """

    mtx = initialize_matrix(
        default=default,
        description="Temporary %s" % description,
        matrix_type=matrix_type,
    )

    if mtx is None:
        raise Exception("Could not create temporary matrix: %s" % description)

    try:
        yield mtx
    finally:
        _bank.delete_matrix(mtx.id)

        s = "Deleted matrix %s." % mtx.id
        _m.logbook_write(s)


# -------------------------------------------------------------------------------------------
def create_temp_attribute(
    scenario,
    attribute_id,
    attribute_type,
    description=None,
    default_value=0.0,
    assignment_type=None,
):
    """
    Creates a temporary extra attribute in a given scenario
    """
    ATTRIBUTE_TYPES = ["NODE", "LINK", "TURN", "TRANSIT_LINE", "TRANSIT_SEGMENT"]
    attribute_type = str(attribute_type).upper()
    # check if the type provided is correct
    if attribute_type not in ATTRIBUTE_TYPES:
        raise TypeError("Attribute type '%s' provided is not recognized." % attribute_type)
    if len(attribute_id) > 18:
        raise ValueError("Attribute id '%s' can only be 19 characters long with no spaces plus no '@'." % attribute_id)
    prefix = str(attribute_id)
    attrib_id = ""
    if assignment_type == "transit":
        temp_extra_attribute = process_transit_attribute(scenario, prefix, attribute_type, default_value)
    elif assignment_type == "traffic":
        temp_extra_attribute = process_traffic_attribute(scenario, prefix, attribute_type, default_value)
    else:
        raise Exception("Attribute type is 'None' or 'invalid'." "Type can only be either 'transit' or 'traffic'.")
    attrib_id = temp_extra_attribute[1]
    msg = "Created temporary extra attribute %s in scenario %s" % (
        attrib_id,
        scenario.id,
    )
    if description:
        temp_extra_attribute[0].description = description
        msg += ": %s" % description
    _m.logbook_write(msg)
    return temp_extra_attribute[0]


def process_transit_attribute(scenario, transit_attrib_id, attribute_type, default_value):
    if not transit_attrib_id.startswith("@"):
        transit_attrib_id = "@" + transit_attrib_id
    checked_extra_attribute = scenario.extra_attribute(transit_attrib_id)
    if checked_extra_attribute == None:
        temp_transit_attrib = scenario.create_extra_attribute(attribute_type, transit_attrib_id, default_value)
    elif checked_extra_attribute != None and checked_extra_attribute.type != attribute_type:
        raise Exception("Attribute %s already exist or has some issues!" % transit_attrib_id)
    else:
        temp_transit_attrib = scenario.extra_attribute(transit_attrib_id)
        temp_transit_attrib.initialize(default_value)
    return temp_transit_attrib, transit_attrib_id


def process_traffic_attribute(scenario, prefix, attribute_type, default_value):
    if prefix != "@tvph" and prefix != "tvph":
        while True:
            suffix = random.randint(1, 999999)
            if prefix.startswith("@"):
                traffic_attrib_id = "%s%s" % (prefix, suffix)
            else:
                traffic_attrib_id = "@%s%s" % (prefix, suffix)

            if scenario.extra_attribute(traffic_attrib_id) is None:
                temp_traffic_attrib = scenario.create_extra_attribute(attribute_type, traffic_attrib_id, default_value)
                break
    else:
        traffic_attrib_id = prefix
        if prefix.startswith("@"):
            traffic_attrib_id = "%s" % (prefix)
        else:
            traffic_attrib_id = "@%s" % (prefix)

        if scenario.extra_attribute(traffic_attrib_id) is None:
            temp_traffic_attrib = scenario.create_extra_attribute(attribute_type, traffic_attrib_id, default_value)
            _m.logbook_write("Created extra attribute '@tvph'")
        else:
            temp_traffic_attrib = scenario.extra_attribute(traffic_attrib_id)
            temp_traffic_attrib.initialize(0)
    return temp_traffic_attrib, traffic_attrib_id


# -------------------------------------------------------------------------------------------


@contextmanager
def temporary_matrix_manager():
    """
    Matrix objects created & added to this matrix list are deleted when this manager exits.
    """
    temp_matrix_list = []
    try:
        yield temp_matrix_list
    finally:
        for matrix in temp_matrix_list:
            if matrix is not None:
                _m.logbook_write("Deleting temporary matrix '%s': " % matrix.id)
                _MODELLER.emmebank.delete_matrix(matrix.id)


@contextmanager
def temporary_attribute_manager(scenario):
    temp_attribute_list = []
    try:
        yield temp_attribute_list
    finally:
        for temp_attribute in temp_attribute_list:
            if temp_attribute is not None:
                scenario.delete_extra_attribute(temp_attribute.id)
                _m.logbook_write("Deleted temporary '%s' link attribute" % temp_attribute.id)


# -------------------------------------------------------------------------------------------

# @deprecated: In Emme 4.1.2 the indices have been changed
def fastLoadTransitSegmentAttributes(scenario, list_of_attribtues):
    """
    BROEKN SINCE EMME 4.1.2. Use fastLoadSummedSegmentAttributes instead

    Performs a fast partial read of transit segment attributes,
    using scenario.get_attribute_values.

    Args:
        - scenario: The Emme Scenario object to load from
        - list_of_attributes: A list of TRANSIT SEGMENT attribute names to load.

    Returns: A dictionary, where the keys are transit line IDs.
        Each key is mapped to a list of attribute dictionaries.

        Example:
            {'TS01a': [{'number': 0, 'transit_volume': 200.0},
                        {'number': 1, 'transit_volume': 210.0} ...] ...}
    """
    """
    Implementation note: The scenario method 'get_attribute_vlues' IS documented,
    however the return value is NOT. I've managed to decipher its structure
    but since it is not documented by INRO it could be changed.
        - pkucirek April 2014
        
    IMPORTANT: This function is currently broken for version 4.1.2! An error
    will be raised if tried. - pkucirek June 2014
    """
    major, minor, release = get_emme_version(tuple)
    if (major, minor, release) >= (4, 1, 2):
        raise Exception("fastLoadTransitSegmentAttributes is deprecated in Emme 4.1.2 or newer versions!")

    retval = {}
    root_data = scenario.get_attribute_values("TRANSIT_SEGMENT", list_of_attribtues)
    indices = root_data[0]
    values = root_data[1:]

    for lineId, segmentIndices in indices.items():
        segments = []

        for number, dataIndex in enumerate(segmentIndices[1]):
            segment = {"number": number}
            for attIndex, attName in enumerate(list_of_attribtues):
                segment[attName] = values[attIndex][dataIndex]
            segments.append(segment)
        retval[lineId] = segments

    return retval


# -------------------------------------------------------------------------------------------
def load_scenario(scenario_number):
    scenario = _MODELLER.emmebank.scenario(scenario_number)
    if scenario is None:
        raise Exception("Scenario %s was not found!" % scenario_number)
    return scenario


# -------------------------------------------------------------------------------------------


def fastLoadSummedSegmentAttributes(scenario, list_of_attributes):
    """
    Performs a fast partial read of transit segment attributes, aggregated to each line,
    using scenario.get_attribute_values.

    Args:
        - scenario: The Emme Scenario object to load from
        - list_of_attributes: A list of TRANSIT SEGMENT attribute names to load.

    Returns: A dictionary whose keys are transit line IDs and whose values
        are dictionaries of attributes.
    """
    retval = {}
    root_data = scenario.get_attribute_values("TRANSIT_SEGMENT", list_of_attributes)
    indices = root_data[0]
    values = root_data[1:]

    major, minor, release, beta = get_emme_version(tuple)
    if (major, minor, release) >= (4, 1, 2):
        get_iter = lambda segmentIndices: segmentIndices.items()
    else:
        get_iter = lambda segmentIndices: itersync(*segmentIndices)

    for lineId, segmentIndices in indices.items():
        line = {"id": lineId}

        for iNode, dataRow in get_iter(segmentIndices):
            for attName, dataColumn in itersync(list_of_attributes, values):
                value = dataColumn[dataRow]

                if attName in line:
                    line[attName] += value
                else:
                    line[attName] = value

        retval[lineId] = line

    return retval


# -------------------------------------------------------------------------------------------


def fastLoadTransitLineAttributes(scenario, list_of_attributes):
    """
    Performs a fast partial read of transit line attributes,
    using scenario.get_attribute_values.

    Args:
        - scenario: The Emme Scenario object to load from
        - list_of_attributes: A list of TRANSIT LINE attribute names to load.

    Returns: A dictionary, where the keys are transit line IDs.
        Each key is mapped to a dictionary of attributes (one for
        each attribute in the list_of_attributes arg) plus 'id'.

        Example:
            {'TS01a': {'id': 'TS01a', 'headway': 2.34, 'speed': 52.22 } ...}
    """

    retval = {}
    root_data = scenario.get_attribute_values("TRANSIT_LINE", list_of_attributes)
    indices = root_data[0]
    values = root_data[1:]

    for lineId, dataIndex in indices.items():
        line = {"id": lineId}

        for attIndex, attName in enumerate(list_of_attributes):
            line[attName] = values[attIndex][dataIndex]
        retval[lineId] = line
    return retval


# -------------------------------------------------------------------------------------------


def fastLoadLinkAttributes(scenario, list_of_attributes):
    """
    Performs a fast partial read of link attributes, using
    scenario.get_attribute_values.

    Args:
        - scenario: The scenario to load from
        - list_of_attributes: A list of attributes to load.

    Returns:
        A dictionary, where the keys are (i_node, j_node) tuples
        (link IDs), and whose values are dictionaries of
        attribute : values.

        Example: {(10001, 10002): {'i_node': 10001, 'j_node': 10002, 'length': 1.002} ...}
    """

    package = scenario.get_attribute_values("LINK", list_of_attributes)
    indices = package[0]
    attribute_tables = package[1:]

    retval = {}
    for i_node, outgoing_links in indices.items():
        for j_node, index in outgoing_links.items():
            link = i_node, j_node
            attributes = {"i_node": i_node, "j_node": j_node}
            for att_name, table in itersync(list_of_attributes, attribute_tables):
                attributes[att_name] = table[index]
            retval[link] = attributes
    return retval


# -------------------------------------------------------------------------------------------


def get_emme_version(returnType=str):
    """
    Gets the version of Emme that is currently running, as a string. For example,
    'Emme 4.0.8', or 'Emme 4.1.0 32-bit'.

    Args & returns:
        - returnType (=str): The desired Python type to return. Accepted types are:
            str: Returns in the form "Emme 4.1.0 32-bit". This is the most verbose.
            tuple: Returns in the form (4, 1, 0) tuple of integers.
            float: Returns in the form 4.1
            int: Return in the form 4

        - asTuple (=False): Boolean flag to return the version number as a string, or
                as a tuple of ints (e.g., [4,1,0] for Emme 4.1.0)
    """

    app = _MODELLER.desktop
    if hasattr(app, "version"):
        return _getVersionNew(app, returnType)
    else:
        return _getVersionOld(returnType)


def _getVersionNew(app, returnType):
    """
    Available in versions 4.1.3 and newer
    """

    if returnType == str:
        return str(app.version)

    version_tuple = app.version_info

    if returnType == tuple:
        # Test for a beta-version of EMME
        if version_tuple[0] <= 2:
            return (9, 9, 9, 0)
        return version_tuple

    if returnType == float:
        # Test for a beta-version of EMME
        if version_tuple[0] <= 2:
            return 9.0
        return version_tuple[0] + version_tuple[1] * 0.1

    if returnType == int:
        # Test for a beta-version of EMME
        if version_tuple[0] <= 2:
            return 9
        return version_tuple[0]

    raise TypeError("Type %s not accepted for getting Emme version" % returnType)


def _getVersionOld(returnType):
    """
    Implementation note: For the string-to-int-tuple conversion, I've assumed the
    string version is of the form ['Emme', '4.x.x', ...] (i.e., the version string
    is the second item in the space-separated list). -pkucirek April 2014
    """
    # The following is code directly from INRO
    emmeProcess = _sp.Popen(["Emme", "-V"], stdout=_sp.PIPE, stderr=_sp.PIPE)
    output = emmeProcess.communicate()[0]
    retval = output.split(",")[0]
    if returnType == str:
        return retval

    # The following is my own code
    components = retval.split(" ")
    version = components[1].split(".")
    versionTuple = [int(n) for n in version]
    if returnType == tuple:
        return versionTuple

    if returnType == float:
        return versionTuple[0] + versionTuple[1] * 0.1

    if returnType == int:
        return versionTuple[0]

    raise TypeError("Type %s not accepted for getting Emme version" % returnType)


# -------------------------------------------------------------------------------------------

EMME_INFINITY = float("1E+20")


def isEmmeInfinity(number, precision=0.001):
    """
    Tests if a matrix value is equal to "Emme infinity" or 1E+20 using approximate equality.
    """
    return equap(number, EMME_INFINITY, precision)


# -------------------------------------------------------------------------------------------

# @deprecated:
def getExtents(network):
    """
    Creates an Extents object from the given Network.
    """
    minX = float("inf")
    maxX = -float("inf")
    minY = float("inf")
    maxY = -float("inf")
    for node in network.nodes():
        minX = min(minX, node.x)
        maxX = max(maxX, node.x)
        minY = min(minY, node.y)
        maxY = max(maxY, node.y)
    return Extents(minX - 1.0, minY - 1.0, maxX + 1.0, maxY + 1.0)


# -------------------------------------------------------------------------------------------
class assign_traffic_util:
    def load_atts(self, scenario, parameters, modeller_namespace):
        traffic_classes = parameters["traffic_classes"]
        time_matrix_ids = [mtx["time_matrix"] for mtx in traffic_classes]
        peak_hr_factors = [str(phf["peak_hour_factor"]) for phf in traffic_classes]
        link_costs = [str(lc["link_cost"]) for lc in traffic_classes]
        atts = {
            "Run Title": parameters["run_title"],
            "Scenario": str(scenario.id),
            "Times Matrix": str(", ".join(time_matrix_ids)),
            "Peak Hour Factor": str(", ".join(peak_hr_factors)),
            "Link Cost": str(", ".join(link_costs)),
            "Iterations": str(parameters["iterations"]),
            "self": modeller_namespace,
        }
        return atts

    def load_output_matrices(self, parameters, matrix_name=""):
        """
        Load input matrices creates and loads all (input) matrix into a list based on
        matrix_name supplied. E.g of matrix_name: "demand_matrix" and matrix_id: "mf2"
        """
        mtx_dict = {}
        traffic_classes = parameters["traffic_classes"]
        for i in range(0, len(matrix_name)):
            mtx_dict[matrix_name[i]] = [tc[matrix_name[i]] for tc in traffic_classes]
        for mtx_name, mtx_ids in mtx_dict.items():
            mtx = [None if id == "mf0" else _bank.matrix(id) for id in mtx_ids]
            mtx_dict[mtx_name] = mtx
        return mtx_dict

    def load_input_matrices(self, parameters, matrix_name):
        """
        Load input matrices creates and returns a list of (input) matrices based on matrix_name supplied.
        E.g of matrix_name: "demand_matrix", matrix_id: "mf2"
        """

        def exception(mtx_id):
            raise Exception("Matrix %s was not found!" % mtx_id)

        traffic_classes = parameters["traffic_classes"]
        mtx_name = matrix_name

        mtx_list = [
            _bank.matrix(tc[mtx_name])
            if tc[mtx_name] == "mf0" or _bank.matrix(tc[mtx_name]).id == tc[mtx_name]
            else exception(tc[mtx_name])
            for tc in traffic_classes
        ]
        return mtx_list

    def load_attribute_list(self, parameters, demand_matrix_list):
        def check_att_name(at):
            if at.startswith("@"):
                return at
            else:
                return "@" + at

        traffic_classes = parameters["traffic_classes"]
        attribute_list = []
        att = "volume_attribute"
        vol_attribute_list = [check_att_name(vol[att]) for vol in traffic_classes]
        for i in range(len(demand_matrix_list)):
            attribute_list.append(None)
        return attribute_list, vol_attribute_list

    def load_mode_list(self, parameters):
        mode_list = [mode["mode"] for mode in parameters["traffic_classes"]]
        return mode_list

    # ---INITIALIZE - SUB-FUNCTIONS  -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

    def init_input_matrices(self, load_input_matrix_list, temp_matrix_list):
        """
        - Checks the list of all load matrices in load_input_matrix_list,
            for None, create a temporary matrix and initialize
        - Returns a list of all input matrices provided
        """
        input_matrix_list = []
        for mtx in load_input_matrix_list:
            if mtx == None:
                mtx = initialize_matrix(matrix_type="FULL")
                input_matrix_list.append(_bank.matrix(mtx.id))
                temp_matrix_list.append(mtx)
            else:
                input_matrix_list.append(mtx)
        return input_matrix_list

    def init_output_matrices(
        self,
        load_output_matrix_dict,
        temp_matrix_list,
        matrix_name="",
        description="",
    ):
        """
        - Checks the dictionary of all load matrices in load_output_matrix_dict,
            for None, create a temporary matrix and initialize
        - Returns a list of all input matrices provided
        """
        output_matrix_list = []
        desc = "AUTO %s FOR CLASS" % (matrix_name.upper())
        if matrix_name in load_output_matrix_dict.keys():
            for mtx in load_output_matrix_dict[matrix_name]:
                if mtx == None:
                    matrix = initialize_matrix(
                        name=matrix_name,
                        description=description if description != "" else desc,
                    )
                    output_matrix_list.append(matrix)
                    temp_matrix_list.append(matrix)
                else:
                    output_matrix_list.append(mtx)
        else:
            raise Exception('Output matrix name "%s" provided does not exist', matrix_name)
        return output_matrix_list

    def init_temp_peak_hour_matrix(self, parameters, temp_matrix_list):
        peak_hour_matrix_list = []
        traffic_classes = parameters["traffic_classes"]
        for tc in traffic_classes:
            peak_hour_matrix = initialize_matrix(
                default=tc["peak_hour_factor"],
                description="Peak hour matrix",
            )
            peak_hour_matrix_list.append(peak_hour_matrix)
            temp_matrix_list.append(peak_hour_matrix)
        return peak_hour_matrix_list

    # ---CREATE - SUB FUNCTIONS-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

    def create_time_attribute_list(self, scenario, demand_matrix_list, temp_attribute_list):
        time_attribute_list = []
        time_attribute = create_temp_attribute(scenario, "ltime", "LINK", default_value=0.0, assignment_type="traffic")
        time_attribute_list = len(demand_matrix_list) * [time_attribute]
        for att in time_attribute_list:
            temp_attribute_list.append(att)
        return time_attribute_list

    def create_cost_attribute_list(self, scenario, demand_matrix_list, temp_attribute_list):
        cost_attribute_list = []
        count = 0
        while count < len(demand_matrix_list):
            cost_attribute = create_temp_attribute(
                scenario, "lkcst", "LINK", default_value=0.0, assignment_type="traffic"
            )
            cost_attribute_list.append(cost_attribute)
            temp_attribute_list.append(cost_attribute)
            count += 1
        return cost_attribute_list

    def create_transit_traffic_attribute_list(self, scenario, demand_matrix_list, temp_attribute_list):
        t_traffic_attribute = create_temp_attribute(
            scenario, "tvph", "LINK", default_value=0.0, assignment_type="traffic"
        )
        transit_traffic_attribute_list = len(demand_matrix_list) * [t_traffic_attribute]
        for att in transit_traffic_attribute_list:
            temp_attribute_list.append(att)
        return transit_traffic_attribute_list

    def create_volume_attribute(self, scenario, volume_attribute):
        volume_attribute_at = scenario.extra_attribute(volume_attribute)
        if volume_attribute_at is None:
            scenario.create_extra_attribute("LINK", volume_attribute, default_value=0)
        elif volume_attribute_at.type != "LINK":
            raise Exception("Volume Attribute '%s' is not a link type attribute" % volume_attribute)
        elif volume_attribute is not None:
            _write("Deleting Previous Extra Attributes.")
            scenario.delete_extra_attribute(volume_attribute_at)
            scenario.create_extra_attribute("LINK", volume_attribute, default_value=0)
        else:
            scenario.create_extra_attribute("LINK", volume_attribute, default_value=0)

    # ---CALCULATE - SUB FUNCTIONS-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    def calculate_link_cost(
        self,
        scenario,
        parameters,
        demand_matrix_list,
        applied_toll_factor_list,
        cost_attribute_list,
        tracker,
    ):
        with _trace("Calculating link costs"):
            for i in range(len(demand_matrix_list)):
                network_calculation_tool(
                    self.get_link_cost_calc_spec(
                        cost_attribute_list[i].id,
                        parameters["traffic_classes"][i]["link_cost"],
                        parameters["traffic_classes"][i]["link_toll_attribute"],
                        applied_toll_factor_list[i],
                    ),
                    scenario=scenario,
                )
            tracker.complete_subtask()

    def calculate_peak_hour_matrices(
        self,
        scenario,
        parameters,
        demand_matrix_list,
        peak_hour_matrix_list,
        tracker,
        number_of_processors,
    ):
        with _trace("Calculating peak hour matrix"):
            for i in range(len(demand_matrix_list)):
                matrix_calc_tool(
                    self.get_peak_hour_spec(
                        peak_hour_matrix_list[i].id,
                        demand_matrix_list[i].id,
                        parameters["traffic_classes"][i]["peak_hour_factor"],
                    ),
                    scenario=scenario,
                    num_processors=number_of_processors,
                )
            tracker.complete_subtask()

    def calculate_transit_background_traffic(self, scenario, parameters, tracker):
        if parameters["background_transit"] == True:
            if int(scenario.element_totals["transit_lines"]) > 0:
                with _trace("Calculating transit background traffic"):
                    network_calculation_tool(
                        self.get_transit_bg_spec(parameters),
                        scenario=scenario,
                    )
                    extra_parameter_tool(el1="@tvph")
                    tracker.complete_subtask()
        else:
            extra_parameter_tool(el1="0")
            tracker.complete_subtask()

    def calculate_applied_toll_factor(self, parameters):
        applied_toll_factor = []
        for tc in parameters["traffic_classes"]:
            if tc["toll_weight"] is not None:
                try:
                    toll_weight = 60 / tc["toll_weight"]
                    applied_toll_factor.append(toll_weight)
                except ZeroDivisionError:
                    toll_weight = 0
                    applied_toll_factor.append(toll_weight)
        return applied_toll_factor

    # ---SPECIFICATION - SUB FUNCTIONS-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    def get_primary_SOLA_spec(
        self,
        demand_matrix_list,
        peak_hour_matrix_list,
        applied_toll_factor_list,
        mode_list,
        volume_attribute_list,
        cost_attribute_list,
        time_matrix_list,
        attribute_list,
        matrix_list,
        operator_list,
        lower_bound_list,
        upper_bound_list,
        selector_list,
        multiply_path_demand,
        multiply_path_value,
        parameters,
        multiprocessing,
    ):
        if parameters["performance_flag"] == "true":
            number_of_processors = multiprocessing.cpu_count()
        else:
            number_of_processors = max(multiprocessing.cpu_count() - 1, 1)
        # Generic Spec for SOLA
        SOLA_spec = {
            "type": "SOLA_TRAFFIC_ASSIGNMENT",
            "classes": [],
            "path_analysis": None,
            "cutoff_analysis": None,
            "traversal_analysis": None,
            "performance_settings": {"number_of_processors": number_of_processors},
            "background_traffic": None,
            "stopping_criteria": {
                "max_iterations": parameters["iterations"],
                "relative_gap": parameters["r_gap"],
                "best_relative_gap": parameters["br_gap"],
                "normalized_gap": parameters["norm_gap"],
            },
        }
        SOLA_path_analysis = []
        for i in range(0, len(demand_matrix_list)):
            if attribute_list[i] is None:
                SOLA_path_analysis.append([])
            else:
                SOLA_path_analysis.append([])
                all_none = True
                for j in range(len(attribute_list[i])):
                    if attribute_list[i][j] is None:
                        continue
                    all_none = False
                    path = {
                        "link_component": attribute_list[i][j],
                        "turn_component": None,
                        "operator": operator_list[i][j],
                        "selection_threshold": {
                            "lower": lower_bound_list[i][j],
                            "upper": upper_bound_list[i][j],
                        },
                        "path_to_od_composition": {
                            "considered_paths": selector_list[i][j],
                            "multiply_path_proportions_by": {
                                "analyzed_demand": multiply_path_demand[i][j],
                                "path_value": multiply_path_value[i][j],
                            },
                        },
                        "results": {"od_values": matrix_list[i][j]},
                        "analyzed_demand": None,
                    }
                    SOLA_path_analysis[i].append(path)
                if all_none is True:
                    SOLA_path_analysis[i] = []
        SOLA_class_generator = [
            {
                "mode": mode_list[i],
                "demand": peak_hour_matrix_list[i].id,
                "generalized_cost": {
                    "link_costs": cost_attribute_list[i].id,
                    "perception_factor": 1,
                },
                "results": {
                    "link_volumes": volume_attribute_list[i],
                    "turn_volumes": None,
                    "od_travel_times": {"shortest_paths": time_matrix_list[i].id},
                },
                "path_analyses": SOLA_path_analysis[i],
            }
            for i in range(len(mode_list))
        ]
        SOLA_spec["classes"] = SOLA_class_generator

        return SOLA_spec

    def get_transit_bg_spec(self, parameters):
        ttf_terms = str.join(
            " + ",
            [
                "((ttf >=" + str(x["start"]) + ") * (ttf <= " + str(x["stop"]) + "))"
                for x in parameters["mixed_use_ttf_ranges"]
            ],
        )
        return {
            "result": "@tvph",
            "expression": "(60 / hdw) * (vauteq) " + ("* (" + ttf_terms + ")" if ttf_terms else ""),
            "aggregation": "+",
            "selections": {"link": "all", "transit_line": "all"},
            "type": "NETWORK_CALCULATION",
        }

    def get_link_cost_calc_spec(self, cost_attribute_id, link_cost, link_toll_attribute, perception):
        return {
            "result": cost_attribute_id,
            "expression": "(length * %f + %s)*%f" % (link_cost, link_toll_attribute, perception),
            "aggregation": None,
            "selections": {"link": "all"},
            "type": "NETWORK_CALCULATION",
        }

    def get_peak_hour_spec(self, peak_hour_matrix_id, demand_matrix_id, peak_hour_factor):
        return {
            "expression": demand_matrix_id + "*" + str(peak_hour_factor),
            "result": peak_hour_matrix_id,
            "constraint": {"by_value": None, "by_zone": None},
            "aggregation": {"origins": None, "destinations": None},
            "type": "MATRIX_CALCULATION",
        }


# --------------------------------------------------------------------------------------------


class IntRange:
    """
    A smaller object to represent a range of integer values.
    Does NOT simplify to a list!
    """

    def __init__(self, min, max):
        min = int(min)
        max = int(max)

        if min > max:
            self.__reversed = True
            self.min = max
            self.max = min
        else:
            self.__reversed = False
            self.min = min
            self.max = max

    def __contains__(self, val):
        return val >= self.min and val < self.max

    def __str__(self):
        return "%s - %s" % (self.min, self.max)

    def __iter__(self):
        i = self.min
        while i < self.max:
            yield i
            i += 1 - 2 * self.__reversed  # Count down if reversed

    def __len__(self):
        return abs(self.max - self.min)

    def contains(self, val):
        return val in self

    def length(self):
        return len(self)

    def overlaps(self, otherRange):
        return otherRange.min in self or otherRange.max in self or self.max in otherRange or self.min in otherRange


# -------------------------------------------------------------------------------------------


class float_range:
    """
    Represents a range of float values. Supports containment and
    overlapping boolean operations.
    """

    def __init__(self, min, max):
        self.min = (float)(min)
        self.max = (float)(max)

    def __contains__(self, val):
        return self.contains(val)

    def contains(self, val):
        return val >= self.min and val < self.max

    def length(self):
        return abs(self.max - self.min)

    def overlaps(self, otherRange):
        return otherRange.min in self or otherRange.max in self or self.max in otherRange or self.min in otherRange

    def __str__(self):
        return "%s - %s" % (self.min, self.max)


# -------------------------------------------------------------------------------------------


class progress_tracker:

    """
    Convenience class for tracking and reporting progress. Also
    captures the progress from other Emme Tools (such as those
    provided by INRO), and combines with a total progress.

    Handles progress at two levels: Tasks and Subtasks. Running
    an Emme Tool counts as a Task. The total number of tasks
    must be known at initialization.

    Update April 2014: Can be 'reset' with a new number of tasks,
    for when two task-levels are needed but the number of full
    tasks are not known at initialization.
    """

    def __init__(self, number_of_tasks):
        self._taskIncr = 1000.0 / number_of_tasks  # floating point number
        self.reset()
        self._errorTools = set()

    def reset(self, number_of_tasks=None):
        self._subTasks = 0
        self._completedSubtasks = 0
        self._progress = 0.0  # floating point number
        self._toolIsRunning = False
        self._processIsRunning = False
        self._activeTool = None

        if number_of_tasks is not None:  # Can be reset with a new number of tasks
            self._taskIncr = 1000.0 / number_of_tasks

    def complete_task(self):
        """
        Call to indicate a Task is complete.

        This function is called automatically
        at the end of a Subtask and at the end
        of a Tool run.
        """
        if self._processIsRunning:
            self._processIsRunning = False
            self._subTasks = 0
            self._completedSubtasks = 0
        self._progress += self._taskIncr

    def run_tool(self, tool, *args, **kwargs):
        """
        Launches another Emme Tool, 'capturing' its progress
        to report a combined overall progress.

        Args:
            - tool: The Emme Tool to run
            - *args, **kwargs: The arguments & keyword arguments
                to be passed to the Emme Tool.
        """
        self._activeTool = tool
        self._toolIsRunning = True
        # actually run the tool. no knowledge of the arguments is required.
        ret = self._activeTool(*args, **kwargs)
        self._toolIsRunning = False
        self._activeTool = None
        self.complete_task()
        return ret

    def start_process(self, number_of_subtasks):
        """
        Tells the Tracker to start up a new Task
        with a given number of Subtasks.
        """
        if number_of_subtasks <= 0:
            raise Exception("A new process requires at least one task!")

        self._subTasks = number_of_subtasks
        self._completedSubtasks = 0
        self._processIsRunning = True

    def complete_subtask(self):
        """
        Call to indicate that a Subtask is complete.
        """

        if not self._processIsRunning:
            return

        if self._completedSubtasks >= self._subTasks:
            self._processIsRunning = False
            self._subTasks = 0
            self._completedSubtasks = 0
            self.complete_task()
        else:
            self._completedSubtasks += 1

    # @_m.method(return_type=_m.TupleType)
    def get_progress(self):
        """
        Call inside a Tool's percent_completed method
        in order to report that Tool's progress.
        """

        if self._toolIsRunning:
            tup = self._activeTool.percent_completed()
            if tup[2] is None:  # Tool is returning the 'marquee' display option
                # Just return the current progress. The task will be completed by the other thread.
                self._toolIsRunning = False
                return (0, 1000, self._progress)
            toolProg = (float(tup[2]) - tup[0]) / (tup[1] - tup[0])
            return (0, 1000, self._progress + toolProg * self._taskIncr)
        elif self._processIsRunning:
            return (
                0,
                1000,
                self._progress + self._taskIncr * float(self._completedSubtasks) / float(self._subTasks),
            )
        else:
            return (0, 1000, self._progress)


class CSVReader:
    def __init__(self, filepath, append_blanks=True):
        self.filepath = filepath
        self.header = None
        self.append_blanks = append_blanks

    def open(self):
        self.__peek()
        self.__reader = open(self.filepath, "r")
        self.header = self.__reader.readline().strip().split(",")

        # Clean up special characters
        for i in range(len(self.header)):
            self.header[i] = self.header[i].replace(" ", "_").replace("@", "").replace("+", "").replace("*", "")

        self.__lincount = 1

    def __peek(self):
        count = 0
        with open(self.filepath, "r") as reader:
            for l in reader:
                count += 1
        self.__count = count

    def __enter__(self):
        self.open()
        return self

    def close(self):
        self.__reader.close()
        del self.__reader
        self.header = None

    def __exit__(self, *args, **kwargs):
        self.close()

    def __len__(self):
        return self.__count

    def readline(self):
        try:
            cells = self.__reader.readline().strip().split(",")
            self.__lincount += 1
            if not self.append_blanks and len(cells) < len(self.header):
                raise IOError("Fewer records than header")

            while len(cells) < len(self.header) and self.append_blanks:
                cells.append("")

            atts = {}
            for i, column_label in enumerate(self.header):
                atts[column_label] = cells[i]
            return Record(atts)

        except Exception as e:
            raise IOError("Error reading line %s: %s" % (self.__lincount, e))

    def readlines(self):
        try:
            for line in self.__reader.readlines():
                self.__lincount += 1
                if not (line):
                    continue
                cells = line.strip().split(",")
                if not self.append_blanks and len(cells) < len(self.header):
                    raise IOError("Fewer records than header")

                while len(cells) < len(self.header) and self.append_blanks:
                    cells.append("")

                yield Record(self.header, cells)
        except Exception as e:
            raise IOError("Error reading line %s: %s" % (self.__lincount, e))


class Record:
    def __init__(self, header, cells):
        self.__dic = {}
        self.__hdr = header
        for i, head in enumerate(header):
            self.__dic[header[i]] = cells[i]

    def __getitem__(self, key):
        if type(key) == int:
            return self.__dic[self.__hdr[key]]
        elif type(key) == str:
            return self.__dic[key]
        else:
            raise Exception()

    def __setitem__(self, key, val):
        self.__hdr.append(key)
        self.__dic[key] = val

    def __len__(self):
        return len(self.__hdr)

    def __str__(self):
        s = self[0]
        for i in range(1, len(self)):
            s += "," + self[i]
        return s


class null_pointer_exception(Exception):
    pass


"""
Gets the demand matrix name (mfxx) that was used during the
previous transit assignment for the given scenario.

EMME_VERSION is a tuple, scenario is the scenario object.
"""


def DetermineAnalyzedTransitDemandId(EMME_VERSION, scenario):
    configPath = dirname(_MODELLER.desktop.project_file_name()) + "/Database/STRATS_s%s/config" % scenario
    with open(configPath) as reader:
        config = _parsedict(reader.read())

        data = config["data"]
        if "multi_class" in data:
            if data["multi_class"] == True:
                multiclass = "yes"
            else:
                multiclass = "no"
        else:
            multiclass = "no"
        strat = config["strat_files"]
        demandMatrices = {}
        if data["type"] == "MULTICLASS_TRANSIT_ASSIGNMENT":  # multiclass extended transit assignment
            for i in range(len(strat)):
                demandMatrices[strat[i]["name"]] = strat[i]["data"]["demand"]
            return demandMatrices
        elif multiclass == "yes":  # multiclass congested assignment
            for i in range(len(data["classes"])):
                demandMatrices[data["classes"][i]["name"]] = data["classes"][i]["demand"]
            return demandMatrices
        else:  # non multiclass congested
            strats = scenario.transit_strategies
            return strats.data["demand"]


@contextmanager
def open_csv_reader(file_path):
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
