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
ExportBinaryMatrix

    Authors: pkucirek

    Latest revision by: pkucirek

    Exports matrix data in the new binary format.
        
"""
# ---VERSION HISTORY
"""
    0.0.1 Created on 2014-06-06 by pkucirek
    
    1.0.0 Published on 2014-06-09
    
    1.0.1 Tool now checks that the matrix exists.

    2.0.0 improved for XTMF2/TMGToolbox2 by WilliamsDiogu
    
"""

import inro.modeller as _m

_MODELLER = _m.Modeller()
_util = _MODELLER.module("tmg2.utilities.general_utilities")
_bank = _MODELLER.emmebank
_tmg_tpb = _MODELLER.module("tmg2.utilities.TMG_tool_page_builder")

##########################################################################################################


class ExportBinaryMatrix(_m.Tool()):

    version = "2.0.0"
    tool_run_msg = ""
    number_of_tasks = 1

    MATRIX_TYPES = {1: "ms", 2: "mo", 3: "md", 4: "mf"}

    def __init__(self):
        self._tracker = _util.progress_tracker(self.number_of_tasks)

    def page(self):
        pb = _tmg_tpb.TmgToolPageBuilder(
            self,
            title="Export Binary Matrix v%s" % self.version,
            description="Exports a matrix in the special binary format, which is \
                         considerably smaller and quicker to load.",
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

    def _execute(self, scenario, parameters):
        matrix_id = self._check_matrix(parameters["matrix_type"], parameters["matrix_number"])
        with _m.logbook_trace(
            name="{classname} v{version}".format(classname=(self.__class__.__name__), version=self.version),
            attributes=self._get_atts(matrix_id, parameters["file_location"], scenario),
        ):
            matrix = _bank.matrix(matrix_id)
            if _util.databank_has_different_zones(_bank):
                data = matrix.get_data(scenario)
            else:
                data = matrix.get_data()
            data.save(parameters["file_location"])
            self._tracker.complete_task()

    def _get_atts(self, matrix_id, file_location, scenario):
        atts = {
            "Matrix": matrix_id,
            "Export File": file_location,
            "Version": self.version,
            "self": self.__MODELLER_NAMESPACE__,
        }
        if _util.databank_has_different_zones(_bank):
            atts["Scenario"] = scenario
        return atts

    def _check_matrix(self, matrix_type, matrix_number):
        if not matrix_type in self.MATRIX_TYPES:
            raise IOError(
                "Matrix type '%s' is not recognized. Valid types are " % matrix_type
                + "1 for scalar, 2 for origin, 3 for destination, and "
                + "4 for full matrices."
            )
        matrix_id = self.MATRIX_TYPES[matrix_type] + str(matrix_number)
        if _bank.matrix(matrix_id) == None:
            raise IOError("Matrix %s does not exist." % matrix_id)
        return matrix_id

    @_m.method(return_type=_m.TupleType)
    def percent_completed(self):
        return self._tracker.get_progress()

    @_m.method(return_type=str)
    def tool_run_msg_status(self):
        return self.tool_run_msg

    @_m.method(return_type=bool)
    def scenario_required(self):
        retval = _util.databank_has_different_zones(_bank)
        print(retval)
        return retval
