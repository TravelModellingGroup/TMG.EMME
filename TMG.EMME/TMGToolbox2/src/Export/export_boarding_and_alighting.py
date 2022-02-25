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
import csv

_MODELLER = _m.Modeller()  # Instantiate Modeller once.
_util = _MODELLER.module("tmg2.utilities.general_utilities")


class ExportBoardingAndAlighting(_m.Tool()):
    version = "1.0.0"
    tool_run_msg = ""
    # For progress reporting, enter the integer number of tasks here
    number_of_tasks = 4
    parameters = _m.Attribute(str)

    def __init__(self):
        self.scenario = _MODELLER.scenario

    def page(self):
        pb = _m.ToolPageBuilder(
            self,
            title="Extract Boarding and Alighting",
            description="This tool get the total boarding and alighting for each transit stop of intrest.",
            runnable=True,
            branding_text="XTMF",
        )
        return pb.render()

    def __call__(self, parameters):
        scenario = _util.load_scenario(parameters["scenario_number"])
        try:
            self._execute(scenario, parameters)
        except Exception as e:
            raise Exception(_util.format_reverse_stack())

    def run(self, parameters):
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
        # Get network from scenario
        network = scenario.get_network()
        # Load transit segments and regular nodes
        regular_nodes = network.regular_nodes()
        # Check if scenario has transit results
        if scenario.has_transit_results:
            # check which input file to use
            checked = parameters["use_input_file"]
            if checked == False:
                self.get_node_id_and_label(parameters, network)
        else:
            raise Exception(
                "Network in Scenario %s do not have transit results!"
                % parameters["scenario_number"]
            )
        # Open file and read containing desired node ids, descriptions(station names)
        with open(parameters["input_file"], "r") as input_file:
            csv_input_file = csv.reader(input_file)
            node_frm_file_dict = self._load_node_from_file(csv_input_file)
            scenario_board_alight_dict = self._get_boarding_alighting(regular_nodes)
            # Write output file with fields ["node_id", "boardings", "alightings", "x", "y", "station"]
            with open(parameters["export_file"], "w", newline="") as output_file:
                fields = ["node_id", "boardings", "alightings", "x", "y", "station"]
                csv_file_writer = csv.writer(output_file)
                csv_file_writer.writerow(fields)
                ba_dict = self._find_boarding_alighting(
                    scenario_board_alight_dict, node_frm_file_dict
                )
                self._write_boarding_and_alighting_to_file(ba_dict, csv_file_writer)

    def _load_node_from_file(self, csv_file_to_read_from):
        # Reads the list of nodes and description (e.g. station names) provided in input file
        node_dict = {}
        for lines in csv_file_to_read_from:
            node_id = lines[0]
            if node_id == "id":
                continue
            description = lines[1]
            node_dict[node_id] = [description]
        return node_dict

    def _get_boarding_alighting(self, regular_nodes):
        # Sums up all boardings and alightngs for each outgoing segments at a node
        board_alight_dict = {}
        for node in regular_nodes:
            if node["@stop"] >= 1:
                out_segments = node.outgoing_segments(include_hidden=True)
                boardings = 0
                alightings = 0
                for segment in out_segments:
                    trans_boarding = segment.transit_boardings
                    boardings += trans_boarding
                    alightings += segment["@alightings"]
                column = [boardings, alightings, node.x, node.y]
                board_alight_dict[node.id] = column
        return board_alight_dict

    def _find_boarding_alighting(self, scenario_board_alight_dict, node_frm_file_dict):
        # Returns only stops specified by the user
        boarding_alighting_dict = dict(
            [
                (k, scenario_board_alight_dict[k] + node_frm_file_dict[k])
                for k in set(node_frm_file_dict) & set(scenario_board_alight_dict)
            ]
        )
        return boarding_alighting_dict

    def _write_boarding_and_alighting_to_file(self, ba_dict, csv_file_writer):
        # Writes summed up boardings, alightings, coordinates and id of each stop of interest to file
        for key in ba_dict:
            row = [
                key,
                ba_dict[key][0],
                ba_dict[key][1],
                str(ba_dict[key][2]),
                ba_dict[key][3],
                ba_dict[key][4],
            ]
            csv_file_writer.writerow(row)

    def get_node_id_and_label(self, parameters, network):
        regular_nodes = network.regular_nodes()
        with open(parameters["input_file"], "w") as file:
            file.write("id, stations \n")
            for node in regular_nodes:
                if node["@stop"] >= 1:
                    file.write("%s, %s \n" % (node.id, ""))
