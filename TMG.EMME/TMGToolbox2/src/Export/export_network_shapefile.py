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
_tmg_tpb = _MODELLER.module("tmg2.utilities.TMG_tool_page_builder")
_export_shape_file = _MODELLER.tool("inro.emme.data.network.export_network_as_shapefile")
_util = _MODELLER.module("tmg2.utilities.general_utilities")


class ExportNetworkAsShapefile(_m.Tool()):
    version = "2.0.0"
    tool_run_msg = ""
    number_of_tasks = 1

    def __init__(self):
        self._tracker = _util.progress_tracker(self.number_of_tasks)
        self.export_metadata = ""

    def page(self):
        pb = _tmg_tpb.TmgToolPageBuilder(
            self,
            title="Export Network as Shapefile v%s" % self.version,
            description="Not Callable from Modeller. Please use XTMF. EXPERIMENTAL",
            branding_text="- XTMF",
        )
        return pb.render()

    def __call__(self, parameters):
        scenario = _util.load_scenario(parameters["scenario_number"])
        self._check_inputs(parameters["export_path"])
        try:
            self._execute(scenario, parameters)
        except Exception as e:
            msg = str(e) + "\n" + _traceback.format_exc()
            raise Exception(msg)

    def run_xtmf(self, parameters):
        scenario = _m.Modeller().emmebank.scenario(parameters["scenario_number"])
        self._check_inputs(parameters["export_path"])
        try:
            self._execute(scenario, parameters)
        except Exception as e:
            msg = str(e) + "\n" + _traceback.format_exc()
            raise Exception(msg)

    def _execute(self, scenario, parameters):
        print("Exporting scenario " + str(scenario.id) + "as a shapefile to " + parameters["export_path"])
        transit_shapes = parameters["transit_shapes"]
        if transit_shapes == "" or transit_shapes is None or transit_shapes == " ":
            transit_shapes = "SEGMENTS"

        _export_shape_file(
            export_path=parameters["export_path"],
            transit_shapes=transit_shapes,
            scenario=scenario,
        )
        self._tracker.complete_task()

    def _check_inputs(self, export_path):
        if export_path is None or export_path == "":
            raise IOError("Export file not specified")
