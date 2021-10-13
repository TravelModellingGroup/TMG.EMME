# ---LICENSE----------------------
"""
    Copyright 2021 Travel Modelling Group, Department of Civil Engineering, University of Toronto

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
Assign V4 Boarding Penalties

    Authors: pkucirek

    Latest revision by: James Vaughan
    
    
    Assigns line-specific boarding penalties (stored in UT3) based on specified
    groupings, for transit assignment estimation.
        
"""
# ---VERSION HISTORY
"""
    0.0.1 Created on 2014-02-14 by TrajceNikolov
    
    1.0.0 Cleaned and published. Now accepts a list of scenarios, for easy use (Modeller only).
            Also changed the order of parameters to better match the order of groups used in
            GTAModel V4.
            
    1.0.1 Added short description

    1.1.0 Line groups are no longer hard-coded. Instead, user-inputted selector expressions are used
            and the number of line groups is open-ended.

    1.2.0 Added ability to set IVTT perception factor.

    1.2.1 Added ability to set Transfer boarding penalties.

    2.0.0 Refacted to work with XTMF2/TMGToolbox2 on 2021-10-12 by williamsDiogu

    2.0.1 Updated to process scenario numbers as an array instead of parcing strings

"""

import inro.modeller as _m
import traceback as _traceback
from re import split as _regex_split

_MODELLER = _m.Modeller()  # Instantiate Modeller once.
_util = _MODELLER.module("tmg2.utilities.general_utilities")
_tmgTPB = _MODELLER.module("tmg2.utilities.TMG_tool_page_builder")
NullPointerException = _util.NullPointerException

_m.TupleType = object
_m.ListType = list
_m.InstanceType = object

##################################################################################


class AssignVBoardingPenalties(_m.Tool()):

    version = "1.2.0"
    tool_run_msg = ""
    number_of_tasks = (
        15  # For progress reporting, enter the integer number of tasks here
    )

    # Tool Input Parameters
    #    Only those parameters necessary for Modeller and/or XTMF to dock with
    #    need to be placed here. Internal parameters (such as lists and dicts)
    #    get initialized during construction (__init__)

    # xtmf_ScenarioNumbers = _m.Attribute(str)  # parameter used by XTMF only
    scenario_numbers = _m.Attribute(_m.ListType)  # parameter used by XTMF only
    Scenarios = _m.Attribute(_m.ListType)  # common variable or parameter
    penalty_filter_string = _m.Attribute(str)

    def __init__(self):
        # ---Init internal variables
        self.TRACKER = _util.ProgressTracker(
            self.number_of_tasks
        )  # init the ProgressTracker

        # ---Set the defaults of parameters used by Modeller
        """
        Example:
            penalty_filter_string = [{'filter': 'mode=r',
            'initial': 1,
            'ivttPerception': 1,
            'label': 'GO Train',
            'transfer': 1}]
        """
        self.penalty_filter_string = ""

    def page(self):

        pb = _tmgTPB.TmgToolPageBuilder(
            self,
            title="Assign V4 Boarding Penalties v%s" % self.version,
            description="Assigns line-specific boarding penalties (stored in UT3) \
                         based on specified line groupings.",
            branding_text="- TMG Toolbox",
        )

        if self.tool_run_msg != "":  # to display messages in the page
            pb.tool_run_status(self.tool_run_msg_status)

        pb.add_select_scenario(tool_attribute_name="Scenarios", title="Scenarios:")

        pb.add_text_box(
            tool_attribute_name="penalty_filter_string",
            size=500,
            multi_line=True,
            title="Line Group Boarding Penalties",
            note="List of filters and boarding penalties for line groups. \
                        <br><br><b>Syntax:</b> [<em>label (line group name)</em>] : [<em>network selector expression</em>] \
                        : [<em>initial boarding penalty</em>] : [<em>Transfer boarding penalty</em>] : [<em>IVTT Perception Factor</em>] ... \
                        <br><br>Separate (label-filter-penalty) groups with a comma or new line.\
                        <br><br>Note that order matters, since penalties are applied sequentially.",
        )

        # ---JAVASCRIPT
        pb.add_html(
            """
<script type="text/javascript">
    $(document).ready( function ()
    {
        var tool = new inro.modeller.util.Proxy(%s);
    
        //Modeller likes to make multi-line text boxes very
        //short, so this line changes the default height
        //to something a little more visible.
        $("#penalty_filter_string").css({height: '200px'});
        $("#penalty_filter_string").css({width: '400px'});
        
        
    });
</script>"""
            % pb.tool_proxy_tag
        )

        return pb.render()

    ##########################################################################################################

    def run(self):
        self.tool_run_msg = ""

        try:
            if len(self.Scenarios) == 0:
                raise Exception("No scenarios selected.")
            if self.penalty_filter_string is None:
                raise NullPointerException("Penalties not specified")

            self._Execute()
        except Exception as e:
            self.tool_run_msg = _m.PageBuilder.format_exception(
                e, _traceback.format_exc()
            )
            raise

        self.tool_run_msg = _m.PageBuilder.format_info("Done.")

    def __call__(self, scenario_number, penalty_filter_string):

        # ---1 Set up scenarios
        self.Scenarios = [_MODELLER.emmebank.scenario(x) for x in self.scenario_numbers]
        self.penalty_filter_string = penalty_filter_string
        try:
            self._Execute()
        except Exception as e:
            msg = str(e) + "\n" + _traceback.format_exc()
            raise Exception(msg)

    ##########################################################################################################
    def run_xtmf(self, parameters):
        self.scenario_numbers = parameters["scenario_numbers"]
        self.penalty_filter_string = parameters["penalty_filter_string"]
        self.Scenarios = [_MODELLER.emmebank.scenario(x) for x in self.scenario_numbers]

        try:
            self._Execute()
        except Exception as e:
            msg = str(e) + "\n" + _traceback.format_exc()
            raise Exception(msg)

    def _Execute(self):
        with _m.logbook_trace(
            name="{classname} v{version}".format(
                classname=(self.__class__.__name__), version=self.version
            ),
            attributes=self._GetAtts(),
        ):

            tool = _MODELLER.tool("inro.emme.network_calculation.network_calculator")

            self.TRACKER.reset(len(self.Scenarios))

            filterList = self.penalty_filter_string

            for scenario in self.Scenarios:
                with _m.logbook_trace("Processing scenario %s" % scenario):
                    self._ProcessScenario(scenario, filterList)
                self.TRACKER.completeTask()

            _MODELLER.desktop.refresh_needed(True)

    ##########################################################################################################

    # ----SUB FUNCTIONS---------------------------------------------------------------------------------

    def _GetAtts(self):
        atts = {
            "Scenarios": str(self.Scenarios),
            "Version": self.version,
            "self": self.__MODELLER_NAMESPACE__,
        }

        return atts

    def _ProcessScenario(self, scenario, penaltyFilterList):
        tool = _MODELLER.tool("inro.emme.network_calculation.network_calculator")

        self.TRACKER.startProcess(2 * len(penaltyFilterList) + 2)

        with _m.logbook_trace("Resetting UT2 and UT3 to 0"):
            tool(specification=self._GetClearLineSpec("ut2", "0"), scenario=scenario)
            tool(specification=self._GetClearLineSpec("ut3", "0"), scenario=scenario)
            self.TRACKER.completeSubtask()

        for group in penaltyFilterList:
            with _m.logbook_trace("Applying " + group["label"] + " BP"):
                tool(specification=self._GetGroupSpecInitial(group), scenario=scenario)
                tool(specification=self._GetGroupSpecTransfer(group), scenario=scenario)
                self.TRACKER.completeSubtask()

        with _m.logbook_trace("Resetting US2 to 1"):
            tool(specification=self._GetClearSegmentSpec("us2", "1"), scenario=scenario)
            self.TRACKER.completeSubtask()

        for group in penaltyFilterList:
            with _m.logbook_trace("Applying " + group["label"] + " IVTT Perception"):
                tool(specification=self._IVTTPerceptionSpec(group), scenario=scenario)
                self.TRACKER.completeSubtask()

    def _GetClearLineSpec(self, variable, expression):
        return {
            "result": variable,
            "expression": expression,
            "aggregation": None,
            "selections": {"transit_line": "all"},
            "type": "NETWORK_CALCULATION",
        }

    def _GetClearSegmentSpec(self, variable, expression):
        return {
            "result": variable,
            "expression": expression,
            "aggregation": None,
            "selections": {"transit_line": "all", "link": "all"},
            "type": "NETWORK_CALCULATION",
        }

    def _GetGroupSpecTransfer(self, group):
        return {
            "result": "ut2",
            "expression": str(group["transfer"]),
            "aggregation": None,
            "selections": {"transit_line": group["filter"]},
            "type": "NETWORK_CALCULATION",
        }

    def _GetGroupSpecInitial(self, group):
        return {
            "result": "ut3",
            "expression": str(group["initial"]),
            "aggregation": None,
            "selections": {"transit_line": group["filter"]},
            "type": "NETWORK_CALCULATION",
        }

    def _IVTTPerceptionSpec(self, group):
        return {
            "result": "us2",
            "expression": str(group["ivttPerception"]),
            "aggregation": None,
            "selections": {"transit_line": group["filter"], "link": "all"},
            "type": "NETWORK_CALCULATION",
        }

    @_m.method(return_type=_m.TupleType)
    def percent_completed(self):
        return self.TRACKER.getProgress()

    @_m.method(return_type=str)
    def tool_run_msg_status(self):
        return self.tool_run_msg

    def short_description(self):
        return "Assign boarding penalties to line groups."