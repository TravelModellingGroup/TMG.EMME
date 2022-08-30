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
[TITLE]

    Authors: pkucirek

    Latest revision by: pkucirek
    
    
    [Description]
        
"""
# ---VERSION HISTORY
"""
    0.0.1 Created on 2014-08-28 by pkucirek
    
    1.0.0 Published on 2014-08-28

    2.0.0 Refactored & updated for XTMF2/TMGToolbox2 on 2021-10-20 by Williams Diogu
    
"""
import traceback as _traceback
import inro.modeller as _m

_m.InstanceType = object
_m.TupleType = object

_MODELLER = _m.Modeller()
_util = _MODELLER.module("tmg2.utilities.general_utilities")
_tmgTPB = _MODELLER.module("tmg2.utilities.TMG_tool_page_builder")

##########################################################################################################


class ReverseTransitLines(_m.Tool()):
    version = "2.0.0"
    tool_run_msg = ""
    number_of_tasks = 1

    def __init__(self):
        self._tracker = _util.progress_tracker(self.number_of_tasks)

    def page(self):
        pb = _tmgTPB.TmgToolPageBuilder(
            self,
            title="Reverse Transit Lines v%s" % self.version,
            description="Reverses the itineraries of a subset of transit lines. It will \
                         try to preserve the line ID of the original line by appending or \
                         modifying the final character. Reports to the Logbook which new lines \
                         are reversed copies of which other lines.",
            runnable=False,
            branding_text="- TMG Toolbox",
        )
        return pb.render()

    def __call__(self, parameters):
        scenario = _util.load_scenario(parameters["scenario_number"])
        try:
            self._execute(scenario, parameters)
        except Exception as e:
            self.tool_run_msg = _m.PageBuilder.format_exception(e, _traceback.format_exc())
            raise

    def run_xtmf(self, parameters):
        scenario = _util.load_scenario(parameters["scenario_number"])
        try:
            self._execute(scenario, parameters)
        except Exception as e:
            self.tool_run_msg = _m.PageBuilder.format_exception(e, _traceback.format_exc())
            raise

    def _execute(self, scenario, parameters):
        with _m.logbook_trace(
            name="{classname} v{version}".format(classname=(self.__class__.__name__), version=self.version),
            attributes=self._get_atts(scenario, parameters["line_selector_expression"]),
        ):

            with _util.temp_extra_attribute_manager(scenario, "TRANSIT_LINE") as line_flag_attribute:
                self._flag_lines(scenario, line_flag_attribute.id, parameters["line_selector_expression"])

                network = scenario.get_network()
                print("Loaded network")

                lines_to_reverse = [line for line in network.transit_lines() if line[line_flag_attribute.id]]
                if len(lines_to_reverse) == 0:
                    _m.logbook_write("Found no lines to reverse")
                    return
                print("Found %s lines to reverse" % len(lines_to_reverse))

                self._reverse_lines(lines_to_reverse)

                scenario.publish_network(network)

    def _get_atts(self, scenario, line_selector_expression):
        atts = {
            "Scenario": str(scenario.id),
            "Line Selector Expression": line_selector_expression,
            "Version": self.version,
            "self": self.__MODELLER_NAMESPACE__,
        }
        return atts

    def _flag_lines(self, scenario, flag_attribute_id, line_selector_expression):
        spec = {
            "result": flag_attribute_id,
            "expression": "1",
            "aggregation": None,
            "selections": {"transit_line": line_selector_expression},
            "type": "NETWORK_CALCULATION",
        }
        tool = _MODELLER.tool("inro.emme.network_calculation.network_calculator")
        tool(spec, scenario=scenario)

    def _reverse_lines(self, lines_to_reverse):
        network = lines_to_reverse[0].network
        att_names = network.attributes("TRANSIT_SEGMENT")
        error_lines = []
        reversed_lines = []
        self._tracker.start_process(len(lines_to_reverse))
        for line in lines_to_reverse:
            try:
                new_id = self._reverse_line(line, network, att_names)
                reversed_lines.append((line.id, new_id))
            except Exception as e:
                t = line.id, e.__class__.__name__, str(e)
                error_lines.append(t)
            self._tracker.complete_subtask()
        self._tracker.complete_task()

        self._write_main_report(reversed_lines)
        if error_lines:
            self._WriteErrorReport(error_lines)

    def _reverse_line(self, line, network, att_names):
        new_id = self._get_new_id(line.id, network)
        segment_attributes = []
        for segment in line.segments(False):
            d = {}
            for att_name in att_names:
                d[att_name] = segment[att_name]
            segment_attributes.append(d)
        new_itinerary = [node.number for node in line.itinerary()]
        new_itinerary.reverse()
        copy = network.create_transit_line(new_id, line.vehicle.id, new_itinerary)
        for segment in copy.segments(False):
            d = segment_attributes.pop()
            for att_name, value in d.items():
                segment[att_name] = value
        return new_id

    def _get_new_id(self, original_id, network):
        if len(original_id) < 6:
            for i in range(ord("a"), ord("z") + 1):
                new_id = original_id + chr(i)
                if network.transit_line(new_id) is None:
                    return new_id
            raise Exception("Could not create a valid ID for the reversed line")
        last_digit = original_id[5]
        for i in range(ord(last_digit), ord("z") + 1):
            new_id = original_id[:-1] + chr(i)
            if network.transit_line(new_id) is None:
                return new_id
        raise Exception("Could not create a valid ID for the reverse line")

    def _write_main_report(self, reversed_lines):
        acc = ""
        for original_id, new_id in reversed_lines:
            acc += "<tr><td>" + self.escape(original_id) + "</td><td>" + self.escape(new_id) + "</td></tr>"
        body = (
            """
        <table>
            <tr>
                <th>Original ID</th>
                <th>Reversed ID</th>
            </tr>
        """
            + acc
            + """
        </table>
        """
        )
        pb = _m.PageBuilder(title="Reversed Lines Report")
        pb.wrap_html(body=str(body))
        _m.logbook_write("Reversed lines report", value=pb.render())

    def _WriteErrorReport(self, error_lines):
        acc = ""
        for line_id, error_type, error_msg in error_lines:
            acc += (
                "<tr><td>"
                + self.escape(line_id)
                + "</td><td>"
                + self.escape(error_type)
                + "</td><td>"
                + self.escape(error_msg)
                + "</td></tr>"
            )

        body = (
            """
        <table>
            <tr>
                <th>Line ID</th>
                <th>Error Type</th
                <th>Error Message</th>
            </tr>
            """
            + bcc
            + """
        </table>
        """
        )
        pb = _m.PageBuilder(title="Error Report")
        pb.wrap_html(body=str(body))
        _m.logbook_write("Error report", value=pb.render())

    def escape(self, html_string):
        escapes = {'"': "&quot;", "'": "&#39;", "<": "&lt;", ">": "&gt;"}
        html_string = html_string.replace("&", "&amp;")
        for seq, esc in escapes.items():
            html_string = html_string.replace(seq, esc)
        return html_string

    @_m.method(return_type=_m.TupleType)
    def percent_completed(self):
        return self._tracker.get_progress()

    @_m.method(return_type=str)
    def tool_run_msg_status(self):
        return self.tool_run_msg
