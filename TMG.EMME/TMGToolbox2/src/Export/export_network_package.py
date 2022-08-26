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

from inspect import Parameter
from sqlite3 import paramstyle
import inro.modeller as _m
import traceback as _traceback
from contextlib import contextmanager
from os import path as _path
from datetime import datetime as _datetime
import shutil as _shutil
import zipfile as _zipfile
import tempfile as _tempfile

_m.InstanceType = object
_m.TupleType = object
_m.ListType = list

_MODELLER = _m.Modeller()
_util = _MODELLER.module("tmg2.utilities.general_utilities")
_export_modes = _MODELLER.tool("inro.emme.data.network.mode.export_modes")
_export_vehicles = _MODELLER.tool("inro.emme.data.network.transit.export_vehicles")
_export_base_network = _MODELLER.tool("inro.emme.data.network.base.export_base_network")
_export_transit_lines = _MODELLER.tool("inro.emme.data.network.transit.export_transit_lines")
_export_link_shapes = _MODELLER.tool("inro.emme.data.network.base.export_link_shape")
_export_turns = _MODELLER.tool("inro.emme.data.network.turn.export_turns")
_export_attributes = _MODELLER.tool("inro.emme.data.extra_attribute.export_extra_attributes")
_export_functions = _MODELLER.tool("inro.emme.data.function.export_functions")
_pdu = _MODELLER.module("tmg2.utilities.pandas_utils")
_tmgTPB = _MODELLER.module("tmg2.utilities.TMG_tool_page_builder")


class ExportNetworkPackage(_m.Tool()):
    version = "2.0.0"
    tool_run_msg = ""
    number_of_tasks = 11

    scenario = _m.Attribute(_m.InstanceType)
    export_file = _m.Attribute(str)
    export_all_flag = _m.Attribute(bool)
    attribute_ids_to_export = _m.Attribute(_m.ListType)
    export_meta_data = _m.Attribute(str)
    export_to_emme_old_version = _m.Attribute(bool)
    extra_attributes = _m.Attribute(str)
    scenario_number = _m.Attribute(int)

    def __init__(self):
        self._tracker = _util.progress_tracker(self.number_of_tasks)

        self.scenario = _MODELLER.scenario
        self.export_meta_data = ""
        self.export_to_emme_old_version = False

    def __call__(self, parameters):
        scenario = _util.load_scenario(parameters["scenario_number"])
        try:
            self._execute(scenario, parameters)
        except Exception as e:
            msg = str(e) + "\n" + _traceback.format_exc()
            raise Exception(msg)

    def run_xtmf(self, parameters):
        scenario = _util.load_scenario(parameters["scenario_number"])
        try:
            self._execute(scenario, parameters)
        except Exception as e:
            msg = str(e) + "\n" + _traceback.format_exc()
            raise Exception(msg)

    def _execute(self, scenario, parameters):
        logbook_attributes = {
            "Scenario": str(scenario.id),
            "Export File": _path.splitext(parameters["export_file"])[0],
            "Version": self.version,
            "self": self.__MODELLER_NAMESPACE__,
        }
        with _m.logbook_trace(
            name="%s v%s" % (self.__class__.__name__, self.version),
            attributes=logbook_attributes,
        ):
            attribute_ids_to_export = self._check_attributes(scenario, parameters)
            with _zipfile.ZipFile(
                parameters["export_file"], "w", _zipfile.ZIP_DEFLATED
            ) as zf, self._temp_file() as temp_folder:
                version_file = _path.join(temp_folder, "version.txt")
                with open(version_file, "w") as writer:
                    writer.write("%s\n%s" % (str(5.0), _util.get_emme_version(returnType=str)))
                zf.write(version_file, arcname="version.txt")
                info_path = _path.join(temp_folder, "info.txt")
                self._write_info_file(scenario, info_path, parameters["export_meta_data"])
                zf.write(info_path, arcname="info.txt")
                self._batchout_modes(temp_folder, zf, scenario)
                self._batchout_vehicles(temp_folder, zf, scenario)
                self._batchout_base(temp_folder, zf, scenario)
                self._batchout_shapes(temp_folder, zf, scenario)
                self._batchout_lines(temp_folder, zf, scenario)
                self._batchout_turns(temp_folder, zf, scenario)
                self._batchout_functions(temp_folder, zf)
                if len(attribute_ids_to_export) > 0:
                    self._batchout_extra_attributes(temp_folder, zf, attribute_ids_to_export, scenario)
                else:
                    self._tracker.complete_task()
                if scenario.has_traffic_results:
                    self._batchout_traffic_results(temp_folder, zf, scenario)
                self._tracker.complete_task()
                if scenario.has_transit_results:
                    self._batchout_transit_results(temp_folder, zf)
                self._tracker.complete_task()

    def _check_attributes(self, scenario, parameters):
        """
        Due to the dynamic nature of the selection process, it could happen that attributes are
        selected which don't exist in the current scenario. The method checks early to catch
        any problems
        """
        if parameters["extra_attributes"].lower() == "all":
            parameters["export_all_flag"] = True
        else:
            cells = parameters["extra_attributes"].split(",")
            attribute_ids_to_export = [str(c.strip()) for c in cells if c.strip()]
        defined_attributes = [att.name for att in scenario.extra_attributes()]
        if parameters["export_all_flag"]:
            attribute_ids_to_export = defined_attributes
        else:
            missing_attributes = set(attribute_ids_to_export).difference(defined_attributes)
            if missing_attributes:
                raise IOError(
                    "Attributes [%s] not defined in scenario %s" % (", ".join(missing_attributes), scenario.number)
                )
        return attribute_ids_to_export

    @_m.logbook_trace("Exporting modes")
    def _batchout_modes(self, temp_folder, zf, scenario):
        export_file = _path.join(temp_folder, "modes.201")
        self._tracker.run_tool(_export_modes, export_file=export_file, scenario=scenario)
        zf.write(export_file, arcname="modes.201")

    @_m.logbook_trace("Exporting vehicles")
    def _batchout_vehicles(self, temp_folder, zf, scenario):
        export_file = _path.join(temp_folder, "vehicles.202")
        if scenario.element_totals["transit_vehicles"] == 0:
            self._export_blank_batch_file(export_file, "vehicles")
            self._tracker.complete_task()
        else:
            self._tracker.run_tool(_export_vehicles, export_file=export_file, scenario=scenario)
        zf.write(export_file, arcname="vehicles.202")

    @_m.logbook_trace("Exporting base network")
    def _batchout_base(self, temp_folder, zf, scenario):
        export_file = _path.join(temp_folder, "base.211")
        self._tracker.run_tool(
            _export_base_network,
            export_file=export_file,
            scenario=scenario,
            export_format="ENG_DATA_FORMAT",
        )
        zf.write(export_file, arcname="base.211")

    @_m.logbook_trace("Exporting link shapes")
    def _batchout_shapes(self, temp_folder, zf, scenario):
        export_file = _path.join(temp_folder, "shapes.251")
        self._tracker.run_tool(_export_link_shapes, export_file=export_file, scenario=scenario)
        zf.write(export_file, arcname="shapes.251")

    @_m.logbook_trace("Exporting transit lines")
    def _batchout_lines(self, temp_folder, zf, scenario):
        export_file = _path.join(temp_folder, "transit.221")
        if scenario.element_totals["transit_lines"] == 0:
            self._export_blank_batch_file(export_file, "lines")
            self._tracker.complete_task()
        else:
            # check if the description is empty or has single quote
            network = scenario.get_network()
            for line in network.transit_lines():
                if len(line.description) == 0:
                    line.description = "No Description"
                else:
                    line.description = line.description.replace("'", "`").replace('"', " ")
                    if len(line.description) > 20 and self.export_to_emme_old_version:
                        line.description = line.description[0:19]
            scenario.publish_network(network)

            self._tracker.run_tool(
                _export_transit_lines,
                export_file=export_file,
                scenario=scenario,
                export_format="ENG_DATA_FORMAT",
            )
        zf.write(export_file, arcname="transit.221")

    @_m.logbook_trace("Exporting turns")
    def _batchout_turns(self, temp_folder, zf, scenario):
        export_file = _path.join(temp_folder, "turns.231")
        if scenario.element_totals["turns"] == 0:
            self._tracker.complete_task()
        else:
            self._tracker.run_tool(
                _export_turns,
                export_file=export_file,
                scenario=scenario,
                export_format="ENG_DATA_FORMAT",
            )
            zf.write(export_file, arcname="turns.231")

    @_m.logbook_trace("Exporting Functions")
    def _batchout_functions(self, temp_folder, zf):
        export_file = _path.join(temp_folder, "functions.411")
        self._tracker.run_tool(_export_functions, export_file=export_file)
        zf.write(export_file, arcname="functions.411")

    @_m.logbook_trace("Exporting extra attributes")
    def _batchout_extra_attributes(self, temp_folder, zf, attribute_ids_to_export, scenario):
        _m.logbook_write("List of attributes: %s" % attribute_ids_to_export)

        extra_attributes = [scenario.extra_attribute(id_) for id_ in attribute_ids_to_export]
        types = set([att.type.lower() for att in extra_attributes])

        self._tracker.run_tool(
            _export_attributes,
            extra_attributes,
            temp_folder,
            field_separator=",",
            scenario=scenario,
            export_format="SCI_DATA_FORMAT",
        )
        for t in types:
            if t == "transit_segment":
                t = "segment"
            filename = _path.join(temp_folder, "extra_%ss_%s.csv" % (t, scenario.number))
            zf.write(filename, arcname="exatt_%ss.241" % t)
        summary_file = _path.join(temp_folder, "exatts.241")
        self._export_attribute_definition_file(summary_file, extra_attributes)
        zf.write(summary_file, arcname="exatts.241")

    def _batchout_traffic_results(self, temp_folder, zf, scenario):
        link_filepath = _path.join(temp_folder, "link_results.csv")
        turn_filepath = _path.join(temp_folder, "turn_results.csv")
        traffic_result_attributes = ["auto_volume", "additional_volume", "auto_time"]

        links = _pdu.load_link_dataframe(scenario)[traffic_result_attributes]
        links.to_csv(link_filepath, index=True)
        zf.write(link_filepath, arcname=_path.basename(link_filepath))

        turns = _pdu.load_turn_dataframe(scenario)
        if not (turns is None):
            turns = turns[traffic_result_attributes]
            turns.to_csv(turn_filepath)
            zf.write(turn_filepath, arcname=_path.basename(turn_filepath))

    def _batchout_transit_results(self, temp_folder, zf, scenario):
        segment_filepath = _path.join(temp_folder, "segment_results.csv")
        result_attributes = ["transit_boardings", "transit_time", "transit_volume"]
        segments = _pdu.load_transit_segment_dataframe(scenario)[result_attributes]
        segments.to_csv(segment_filepath)
        zf.write(segment_filepath, arcname=_path.basename(segment_filepath))

        aux_transit_filepath = _path.join(temp_folder, "aux_transit_results.csv")
        aux_result_attributes = ["aux_transit_volume"]
        aux_transit = _pdu.load_link_dataframe(scenario)[aux_result_attributes]
        aux_transit.to_csv(aux_transit_filepath)
        zf.write(aux_transit_filepath, arcname=_path.basename(aux_transit_filepath))

    @contextmanager
    def _temp_file(self):
        foldername = _tempfile.mkdtemp()
        _m.logbook_write("Created temporary directory at `%s`" % foldername)
        try:
            yield foldername
        finally:
            _shutil.rmtree(foldername, True)
            _m.logbook_write("Deleted temporary directory at `%s`" % foldername)

    @staticmethod
    def _export_blank_batch_file(filename, t_record):
        with open(filename, "w") as file_:
            file_.write("t %s init" % t_record)

    @staticmethod
    def _export_attribute_definition_file(filename, attribute_list):
        with open(filename, "w") as writer:
            writer.write("name,type, default")
            for att in attribute_list:
                writer.write(
                    "\n{name},{type},{default},'{desc}'".format(
                        name=att.name,
                        type=att.type,
                        default=att.default_value,
                        desc=att.description,
                    )
                )

    def _write_info_file(self, scenario, fp, export_meta_data):
        with open(fp, "w") as writer:
            bank = _MODELLER.emmebank
            lines = [
                str(bank.title),
                str(bank.path),
                "%s - %s" % (scenario, scenario.title),
                _datetime.now().strftime("%Y-%m-%d %H:%M"),
                export_meta_data,
            ]
            writer.write("\n".join(lines))

    def _get_select_attribute_options_json(self):
        keyval = {}
        for att in self.scenario.extra_attributes():
            label = "{id} ({domain}) - {name}".format(id=att.name, domain=att.type, name=att.description)
            keyval[att.name] = label
        return keyval

    @_m.method(return_type=str)
    def _get_select_attribute_options_html(self):
        list_ = []
        for att in self.scenario.extra_attributes():
            label = "{id} ({domain}) - {name}".format(id=att.name, domain=att.type, name=att.description)
            html = str('<option value="{id}">{text}</option>'.format(id=att.name, text=label))
            list_.append(html)
        return "\n".join(list_)

    @_m.method(return_type=_m.TupleType)
    def percent_completed(self):
        return self._tracker.get_progress()

    @_m.method(return_type=str)
    def tool_run_msg_status(self):
        return self.tool_run_msg
