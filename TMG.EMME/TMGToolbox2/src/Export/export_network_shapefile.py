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


import inro.modeller as _m
import traceback as _traceback
from os import path as _path
from datetime import datetime as _dt
import shutil as _shutil
import zipfile as _zipfile
import tempfile as _tf

_m.ListType = list
_m.InstanceType = object

_MODELLER = _m.Modeller()  # Instantiate Modeller once.
_tmgTPB = _MODELLER.module("tmg2.utilities.TMG_tool_page_builder")
_exportShapefile = _MODELLER.tool("inro.emme.data.network.export_network_as_shapefile")
_util = _MODELLER.module("tmg2.utilities.general_utilities")


class ExportNetworkAsShapefile(_m.Tool()):
    version = "2.0.0"
    tool_run_msg = ""
    number_of_tasks = 1

    scenario = _m.Attribute(_m.InstanceType)
    scenario_number = _m.Attribute(int)
    export_path = _m.Attribute(str)
    transit_shapes = _m.Attribute(str)

    def __init__(self):
        # Init internal variables
        self.TRACKER = _util.progress_tracker(self.number_of_tasks)  # init the progress_tracker

        # Set the defaults of parameters used by Modeller
        self.scenario = _MODELLER.scenario  # Default is primary scenario
        self.export_metadata = ""

    def page(self):
        pb = _tmgTPB.TmgToolPageBuilder(
            self,
            title="Export Network as Shapefile v%s" % self.version,
            description="Not Callable from Modeller. Please use XTMF. EXPERIMENTAL",
            branding_text="- XTMF",
        )
        return pb.render()

    def __call__(self, export_path, transit_shapes, scenario_number):
        self.export_path = export_path
        self.transit_shapes = transit_shapes
        self.scenario_number = scenario_number
        self.scenario = _m.Modeller().emmebank.scenario(self.scenario_number)
        self._check_inputs()

        try:
            self._execute()
        except Exception as e:
            raise Exception(_util.format_reverse_stack())

    def run_xtmf(self, parameters):
        self.scenario_number = parameters["scenario_number"]
        self.export_path = parameters["export_path"]
        self.transit_shapes = parameters["transit_shapes"]

        self.scenario = _m.Modeller().emmebank.scenario(self.scenario_number)
        self._check_inputs()
        try:
            self._execute()
        except Exception as e:
            raise Exception(_util.format_reverse_stack())

    def _execute(self):

        print("Exporting scenario " + str(self.scenario_number) + "as a shapefile to " + self.export_path)

        if self.transit_shapes == "" or self.transit_shapes is None or self.transit_shapes == " ":
            self.transit_shapes = "SEGMENTS"

        _exportShapefile(
            export_path=self.export_path,
            transit_shapes=self.transit_shapes,
            scenario=self.scenario,
        )
        self.TRACKER.complete_task()

    def _check_inputs(self):
        if self.scenario is None:
            raise Exception("Scenario '%s' is not a valid scenario" % self.scenario_number)

        if self.export_path is None or "":
            raise IOError("Export file not specified")
