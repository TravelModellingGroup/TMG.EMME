from platform import node
import inro.modeller as _m
import csv

_MODELLER = _m.Modeller()  # Instantiate Modeller once.
_bank = _MODELLER.emmebank


class ExtractBoardingAndAlighting(_m.Tool()):
    version = "1.0.0"
    tool_run_msg = ""
    # For progress reporting, enter the integer number of tasks here
    number_of_tasks = 4
    parameters = _m.Attribute(str)

    def __init__(self):
        self._tracker = _util.progress_tracker(self.number_of_tasks)
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
        scenario = self._load_scenario(parameters["scenario_number"])
        try:
            self._execute(scenario, parameters)
        except Exception as e:
            raise Exception(_util.format_reverse_stack())

    def run_xtmf(self, parameters):
        scenario = self._load_scenario(parameters["scenario_number"])

        try:
            self._execute(scenario, parameters)
        except Exception as e:
            raise Exception(_util.format_reverse_stack())

    def _execute(self, scenario, parameters):
        # Get network from scenario
        network = scenario.get_network()

        # Load transit segments and regular nodes
        transit_segments = network.transit_segments()
        regular_nodes = network.regular_nodes()

        # Open file and read containing desired node ids, descriptions(station names)
        with open(parameters["input_file"], "r") as input_file:
            csv_input_file = csv.reader(input_file)
            node_frm_file_dict = self._load_node_from_file(csv_input_file)
            scenario_board_alight_dict = self._get_boarding_alighting(regular_nodes)
            with open("outputs.csv", "w", newline="") as output_file:
                fields = ["node_id", "boardings", "alightings", "x", "y", "station"]
                csv_file_writer = csv.writer(output_file)
                csv_file_writer.writerow(fields)

                ba_dict = self._find_boarding_alighting(
                    scenario_board_alight_dict, node_frm_file_dict
                )
                self._write_boarding_and_alighting_to_file(ba_dict, csv_file_writer)

    def _load_scenario(self, scenario_number):
        scenario = _bank.scenario(scenario_number)
        if scenario is None:
            raise Exception("Scenario %s was not found!" % scenario_number)
        return scenario

    def _load_node_from_file(self, csv_file_to_read_from):
        node_dict = {}
        for lines in csv_file_to_read_from:
            node_id = lines[0]
            if node_id == "id":
                continue
            description = lines[1]
            node_dict[node_id] = [description]
        return node_dict

    def _get_boarding_alighting(self, regular_nodes):
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
                rows = [boardings, alightings, node.x, node.y]
                board_alight_dict[node.id] = rows
        return board_alight_dict

    def _find_boarding_alighting(self, scenario_board_alight_dict, node_frm_file_dict):
        boarding_alighting_dict = dict(
            [
                (k, scenario_board_alight_dict[k] + node_frm_file_dict[k])
                for k in set(node_frm_file_dict) & set(scenario_board_alight_dict)
            ]
        )
        return boarding_alighting_dict

    def _write_boarding_and_alighting_to_file(ba_dict, csv_file_writer):
        for key in ba_dict:
            rows = [
                key,
                ba_dict[key][0],
                ba_dict[key][1],
                str(ba_dict[key][2]),
                ba_dict[key][3],
                ba_dict[key][4],
            ]
            csv_file_writer.writerow(rows)
