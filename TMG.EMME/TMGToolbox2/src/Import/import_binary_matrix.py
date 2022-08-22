# ---LICENSE----------------------unicode
"""
    Copyright 2014 Travel Modelling Group, Department of Civil Engineering, University of Toronto

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
Import Binary Matrix

    Authors: pkucirek

    Latest revision by: lunaxi
    
    
    [Description]
        
"""
# ---VERSION HISTORY
"""
    0.0.1 Created on 2014-06-30 by pkucirek

    0.0.2 Modified on 2020-03-09 by lunaxi, allow the GUI to create a matrix first if not existed
    
"""


from inspect import Parameter
from sqlite3 import paramstyle
import inro.modeller as _m
import traceback as _traceback
from inro.emme.matrix import MatrixData as _matrix_data
import shutil
import os
import gzip

_m.InstanceType = object
_m.TupleType = object
_m.ListType = list

_MODELLER = _m.Modeller()  # Instantiate Modeller once.
_util = _MODELLER.module("tmg2.utilities.general_utilities")
_tmgTPB = _MODELLER.module("tmg2.utilities.TMG_tool_page_builder")
_bank = _MODELLER.emmebank

##########################################################################################################


class ImportBinaryMatrix(_m.Tool()):

    version = "0.0.2"
    tool_run_msg = ""
    number_of_tasks = 1  # For progress reporting, enter the integer number of tasks here

    MATRIX_TYPES = {1: "ms", 2: "mo", 3: "md", 4: "mf"}

    # ---PARAMETERS
    import_file = _m.Attribute(str)
    scenario = _m.Attribute(_m.InstanceType)
    matrix_id = _m.Attribute(str)
    matrix_description = _m.Attribute(str)
    matrix_type = _m.Attribute(str)

    new_matrix_id = _m.Attribute(int)
    new_matrix_name = _m.Attribute(str)
    new_matrix_description = _m.Attribute(str)
    new_matrix_type = _m.Attribute(str)

    def __init__(self):
        # ---Init internal variables
        self._tracker = _util.progress_tracker(self.number_of_tasks)  # init the progress_tracker

        # ---Set the defaults of parameters used by Modeller
        self.scenario = _MODELLER.scenario
        self.new_matrix_name = ""
        self.new_matrix_description = ""

    def page(self):
        pb = _tmgTPB.TmgToolPageBuilder(
            self,
            title="Import Binary Matrix v%s" % self.version,
            description="Imports a binary matrix from file.",
            branding_text="- TMG Toolbox 2",
        )

        if self.tool_run_msg != "":  # to display messages in the page
            pb.tool_run_status(self.tool_run_msg_status)

        pb.add_select_scenario(
            tool_attribute_name="scenario",
            title="Scenario:",
            allow_none=False,
            note="Only required if scenarios have different zone systems.",
        )

        pb.add_select_file(
            tool_attribute_name="import_file",
            window_type="file",
            file_filter="Emme matrix files | *.mdf ; *.emxd ; *.mtx ; *.mtx.gz\nAll files (*.*)",
            title="Import File",
        )

        pb.add_select_matrix(
            tool_attribute_name="matrix_id",
            id=True,
            title="Matrix",
            allow_none=True,
            note="Select an existing matrix to save data, or leave as None and create a new matrix below.",
        )

        pb.add_header("Create a NEW matrix to save data: (Ignore if using existing matrix)")

        with pb.add_table(visible_border=False) as t:
            mt_type = [
                ("FULL", "mf"),
                ("ORIGIN", "mo"),
                ("DESTINATION", "md"),
                ("SCALAR", "ms"),
            ]

            with t.table_cell():
                pb.add_select(
                    tool_attribute_name="new_matrix_type",
                    keyvalues=mt_type,
                    title="Matrix Type",
                )

            with t.table_cell():
                pb.add_text_box(
                    tool_attribute_name="new_matrix_id",
                    title="Matrix ID",
                    multi_line=False,
                )

            with t.table_cell():
                pb.add_text_box(
                    tool_attribute_name="new_matrix_name",
                    title="Matrix Name",
                    multi_line=False,
                )
            with t.table_cell():
                pb.add_text_box(
                    tool_attribute_name="new_matrix_description",
                    title="Description",
                    multi_line=False,
                )

        # ---JAVASCRIPT
        pb.add_html(
            """
<script type="text/javascript">
    $(document).ready( function ()
    {        
        var tool = new inro.modeller.util.Proxy(%s) ;

        if (tool.scenario_required())
        {
            $("#scenario").prop("disabled", false);;
        } else {
            $("#scenario").prop("disabled", true);;
        }
    });
</script>"""
            % pb.tool_proxy_tag
        )

        return pb.render()

    def run(self):
        self.tool_run_msg = ""
        self._tracker.reset()
        parameters = self._build_parameters_page_builder()
        try:
            self._execute(self.scenario, parameters, self.matrix_id)
        except Exception as e:
            self.tool_run_msg = _m.PageBuilder.format_exception(e, _traceback.format_exc(e))
            raise
        self.tool_run_msg = _m.PageBuilder.format_info("Done. Matrix is imported.")

    def __call__(self, parameters):
        scenario = _util.load_scenario(parameters["scenario_number"])
        matrix_id = self._check_matrix(parameters["matrix_type"], parameters["matrix_number"])
        try:
            self._execute(scenario, parameters, matrix_id)
        except Exception as e:
            msg = str(e) + "\n" + _traceback.format_exc()
            raise Exception(msg)

    def run_xtmf(self, parameters):
        scenario = _util.load_scenario(parameters["scenario_number"])
        matrix_id = self._check_matrix(parameters["matrix_type"], parameters["matrix_number"])
        try:
            self._execute(scenario, parameters, matrix_id)
        except Exception as e:
            msg = str(e) + "\n" + _traceback.format_exc()
            raise Exception(msg)

    def _execute(self, scenario, parameters, matrix_id):
        self._check_import_file(parameters["binary_matrix_file"])
        with _m.logbook_trace(
            name="%s v%s" % (self.__class__.__name__, self.version),
            attributes=self._get_atts(scenario),
        ):
            if matrix_id is None:
                matrix = _util.initialize_matrix(
                    id=parameters["new_matrix_id"],
                    name=parameters["new_matrix_name"],
                    description=parameters["new_matrix_description"],
                    matrix_type=parameters["new_matrix_type"],
                )
            else:
                matrix = _util.initialize_matrix(matrix_id)
                if parameters["matrix_description"]:
                    matrix.description = parameters["matrix_description"]

            if str(parameters["binary_matrix_file"])[-2:] == "gz":
                new_file = "matrix.mtx"
                with gzip.open(parameters["binary_matrix_file"], "rb") as zip_file, open(
                    new_file, "wb"
                ) as non_zip_file:
                    shutil.copyfileobj(zip_file, non_zip_file)
                data = _matrix_data.load(new_file)
                os.remove(new_file)
            else:
                data = _matrix_data.load(parameters["binary_matrix_file"])

            parameters["new_matrix_type"] = matrix.type
            # 2D matrix
            if parameters["new_matrix_type"] == "mf":
                origins, destinations = data.indices
                origins = set(origins)
                destinations = set(destinations)
                if origins ^ destinations:
                    raise Exception("Asymmetrical matrix detected. Matrix must be square.")
            # 1D matrix
            else:
                origins = data.indices[0]
                origins = set(origins)

            if _util.databank_has_different_zones(_bank):
                zones = set(scenario.zone_numbers)
                if zones ^ origins:
                    with _m.logbook_trace("Zones in matrix file but not in scenario"):
                        for index in origins - zones:
                            _m.logbook_write(index)
                    with _m.logbook_trace("Zones in scenario but not in file"):
                        for index in zones - origins:
                            _m.logbook_write(index)

                    raise Exception(
                        "Matrix zones not compatible with scenario %s. Check logbook for details." % scenario
                    )

                matrix.set_data(data, scenario_id=scenario.id)
            else:
                sc = _bank.scenarios()[0]
                zones = set(sc.zone_numbers)
                if zones ^ origins:
                    with _m.logbook_trace("Zones in matrix file but not in scenario"):
                        for index in origins - zones:
                            _m.logbook_write(index)
                    with _m.logbook_trace("Zones in scenario but not in file"):
                        for index in zones - origins:
                            _m.logbook_write(index)

                    raise Exception("Matrix zones not compatible with emmebank zone system. Check Logbook for details.")
                matrix.set_data(data)
            self._tracker.complete_task()

    def _get_atts(self, scenario):
        atts = {
            "scenario": str(scenario.id),
            "Version": self.version,
            "self": self.__MODELLER_NAMESPACE__,
        }
        return atts

    def _check_import_file(self, import_file):
        if import_file is None:
            raise IOError("Import file not specified")

    def _build_parameters_page_builder(self):
        parameters = {
            "matrix_type": self.matrix_type,
            "matrix_number": self.matrix_id,
            "binary_matrix_file": self.import_file,
            "scenario_number": self.scenario,
            "matrix_description": self.matrix_description,
            "new_matrix_type": self.new_matrix_type,
            "new_matrix_number": self.new_matrix_id,
            "new_matrix_name": self.new_matrix_name,
            "new_matrix_description": self.new_matrix_description,
        }
        return parameters

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
        return retval
