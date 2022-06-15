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


from click import ParamType
import inro.modeller as _m
import csv

_m.TupleType = object
_m.ListType = list
_m.InstanceType = object
_MODELLER = _m.Modeller()
_bank = _MODELLER.emmebank
_util = _MODELLER.module("tmg2.utilities.general_utilities")


class ConvertBetweenNCSScenarios(_m.Tool()):
    version = "1.0.0"
    number_of_tasks = 1
    tool_run_msg = ""

    def __init__(self):
        self._tracker = _util.progress_tracker(self.number_of_tasks)

    def __call__(self, parameters):
        scenario = _util.load_scenario(parameters["old_ncs_scenario"])
        try:
            self._execute(scenario, parameters)
        except Exception as e:
            raise Exception(_util.format_reverse_stack())

    def run_xtmf(self, parameters):
        old_ncs_scenario = _util.load_scenario(parameters["old_ncs_scenario"])
        try:
            self._execute(old_ncs_scenario, parameters)
        except Exception as e:
            raise Exception(_util.format_reverse_stack())

    def _execute(self, old_ncs_scenario, parameters):

        centroid_dict = self.create_mapped_centroid_dict(parameters)

        network = old_ncs_scenario.get_network()
        # Conversion Steps
        self.update_zone_centroid_numbers(network, centroid_dict)

        # Copy scenario and write a new updated network
        self.copy_ncs_scenario(parameters, network, title="GTAModel - NCS22")

    def update_zone_centroid_numbers(self, network, centroid_dict):
        nodes_list = []
        for item in network.nodes():
            nodes_list.append(int(item))
        max_node_number = max(nodes_list) + 1
        for old_centroid in centroid_dict:
            centroid_to_update = network.node(old_centroid)
            if centroid_to_update is not None:
                centroid_to_update.number = old_centroid + max_node_number
        for old_centroid_node in centroid_dict:
            centroid_to_update = network.node(old_centroid_node + max_node_number)
            if centroid_to_update is not None:
                centroid_to_update.number = centroid_dict[old_centroid_node]

    def copy_ncs_scenario(self, parameters, network, title="New_NCS_Scenario"):
        new_ncs_scenario = _bank.scenario(parameters["new_ncs_scenario"])
        if new_ncs_scenario != None:
            _bank.delete_scenario(new_ncs_scenario)
        new_ncs_scenario = _bank.copy_scenario(parameters["old_ncs_scenario"], parameters["new_ncs_scenario"])
        new_ncs_scenario.publish_network(network)
        new_ncs_scenario.title = str(title)
        return new_ncs_scenario

    def update_centroid_lists_with_zone_centroids(self, parameters, old_centroid_list, new_centroid_list):
        with open(parameters["zone_centroid_file"], mode="r") as zone_centroids:
            zone_centroid_file = csv.reader(zone_centroids)
            next(zone_centroid_file)
            for centroid_range in zone_centroid_file:
                old_centroid_starts = int(centroid_range[1])
                old_centroid_ends = int(centroid_range[2])
                new_centroid_starts = int(centroid_range[3])
                new_centroid_ends = int(centroid_range[4])
                old_centroid_range = range(old_centroid_starts, old_centroid_ends + 1)
                new_centroid_range = range(new_centroid_starts, new_centroid_ends + 1)
                for centroid in old_centroid_range:
                    old_centroid_list.append(centroid)
                for centroid in new_centroid_range:
                    new_centroid_list.append(centroid)

    def update_centroid_lists_with_station_centroids(self, parameters, old_centroid_list, new_centroid_list):
        with open(parameters["station_centroid_file"], mode="r") as station_centroids:
            station_centroid_file = csv.reader(station_centroids)
            next(station_centroid_file)
            for centroid in station_centroid_file:
                old_station_centroid = int(centroid[2])
                new_station_centroid = int(centroid[3])
                if old_station_centroid <= 0 or new_station_centroid <= 0:
                    continue
                old_centroid_list.append(old_station_centroid)
                new_centroid_list.append(new_station_centroid)

    def create_mapped_centroid_dict(self, parameters):
        centroid_dict = {}
        old_centroid_list = []
        new_centroid_list = []
        self.update_centroid_lists_with_zone_centroids(parameters, old_centroid_list, new_centroid_list)
        self.update_centroid_lists_with_station_centroids(parameters, old_centroid_list, new_centroid_list)
        for old_centroid in old_centroid_list:
            old_centroids = old_centroid_list.index(old_centroid)
            centroid_dict[old_centroid] = new_centroid_list[old_centroids]
        return centroid_dict
