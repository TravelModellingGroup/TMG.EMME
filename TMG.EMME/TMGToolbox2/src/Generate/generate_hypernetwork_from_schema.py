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
import traceback as _traceback
import time as _time
import multiprocessing

from numpy import percentile
import inro.modeller as _m
from inro.emme.core.exception import ModuleError
from contextlib import contextmanager

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
Shapely2ESRI = _geometry.Shapely2ESRI
GridIndex = _spatial_index.GridIndex
transit_line_proxy = _network_edit.TransitLineProxy
null_pointer_exception = _util.null_pointer_exception
EMME_VERSION = _util.get_emme_version(tuple)


class GenerateHypernetworkFromSchema(_m.Tool()):
    version = "2.0.0"
    tool_run_msg = ""
    number_of_tasks = 5

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
        scenario = _util.load_scenario(parameters["scenario_number"])
        try:
            self._execute(scenario, parameters)
        except Exception as e:
            raise Exception(_util.format_reverse_stack())

    def run_xtmf(self, parameters):
        scenario = _util.load_scenario(parameters["scenario_number"])
        try:
            self._execute(scenario, parameters)
        except Exception as e:
            raise Exception(_util.format_reverse_stack())

    def _execute(self):
        ...
