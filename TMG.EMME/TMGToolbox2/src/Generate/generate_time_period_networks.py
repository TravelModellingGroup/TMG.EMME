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
TMG Generate Full Network Set Tool
    
    This tool is only compatible with Emme 4.2 and later versions

    Authors: Eric Miller

    Latest revision by: WilliamsDiogu
    
    V 1.0.0 

    V 2.0.0 Refactored to work with XTMF2/TMGToolbox2 on 2022-07-20 by williamsDiogu   
"""
import traceback as _traceback
import inro.modeller as _m
import multiprocessing

_MODELLER = _m.Modeller()
_util = _MODELLER.module("tmg2.utilities.general_utilities")
_tmg_tpb = _MODELLER.module("tmg2.utilities.TMG_tool_page_builder")
_bank = _MODELLER.emmebank


class GenerateTimePeriodNetworks(_m.Tool()):
    version = "2.0.0"
    tool_run_msg = ""
    number_of_task = 1
    COLON = ":"
    COMMA = ","

    def __init__(self):
        # self._tracker = _util.progress_tracker(self.number_of_task)
        self.number_of_processors = multiprocessing.cpu_count()

    def page(self):
        pb = _tmg_tpb.TmgToolPageBuilder(
            self,
            title="Generate FullNetwork Setv%s" % self.version,
            description="Generates a full network set for GTAModel V4.2.\
                        <br><br><b>Cannot be called from Modeller.</b>\
                        <br><br>Hard-coded assumptions:\
                        <font color='red'>This tool is only compatible with Emme 4.1.5 and later versions</font>",
            runnable=False,
            branding_text="- TMG Toolbox",
        )
        return pb.render()

    def __call__(self, parameters):
        scenario = _util.load_scenario(parameters["base_scenario_number"])
        try:
            self._execute(scenario, parameters)
        except Exception as e:
            raise Exception(_util.format_reverse_stack())

    def run_xtmf(self, parameters):
        base_scenario = _util.load_scenario(parameters["base_scenario_number"])
        try:
            self._execute(base_scenario, parameters)
        except Exception as e:
            raise Exception(_util.format_reverse_stack())

    def _execute(self, base_scenario, parameters):
        with _m.logbook_trace(
            name="{classname} v{version}".format(classname=(self.__class__.__name__), version=self.version),
            attributes=self._get_atts(),
        ):
            self._check_filter_attributes(parameters["node_filter_attribute"], base_scenario, description="Node")
            self._check_filter_attributes(parameters["stop_filter_attribute"], base_scenario, description="Stop")
            self._check_filter_attributes(
                parameters["connector_filter_attribute"], base_scenario, description="Connector"
            )

            for periods in parameters["time_periods"]:
                self._delete_old_scenario(periods["uncleaned_scenario_number"])
                self._delete_old_scenario(periods["cleaned_scenario_number"])

    def _delete_old_scenario(self, scenario_number):
        if _bank.scenario(scenario_number) is not None:
            _bank.delete_scenario(scenario_number)

    def _get_atts(self):
        atts = {}
        return atts

    def _check_filter_attributes(self, base_scenario, filer_attribute_id, description=""):
        if filer_attribute_id.lower() == "none":
            filer_attribute_id = None
        else:
            if base_scenario.extra_attribute(filer_attribute_id) is None:
                raise Exception("%s filter attribute %s does not exist" % (filer_attribute_id, description))
        return filer_attribute_id
