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
Toll-Based Road Assignment

    Authors: David King, Eric Miller

    Latest revision by: dKingII
    
    Executes a multi-class road assignment which allows for the generalized penalty of road tolls.
    
    V 1.0.0

    V 1.1.0 Added link volume attributes for increased resolution of analysis.

    V 1.1.1 Updated to allow for multi-threaded matrix calcs in 4.2.1+

    V 2.0.0 Refactored to work with XTMF2/TMGToolbox2 on 2021-10-21 by williamsDiogu      

    V 2.0.1 Updated to receive JSON object parameters from XTMX2

"""

from os import error
import inro.modeller as _m
import traceback as _traceback
from contextlib import contextmanager
import multiprocessing
import random
import json

_m.InstanceType = object
_m.ListType = list
_m.TupleType = object

_MODELLER = _m.Modeller()  # Instantiate Modeller once.
_util = _MODELLER.module("tmg2.utilities.general_utilities")
EMME_VERSION = _util.get_emme_version(tuple)

matrix_calc_tool = _MODELLER.tool("inro.emme.matrix_calculation.matrix_calculator")
network_calculation_tool = _MODELLER.tool(
    "inro.emme.network_calculation.network_calculator"
)
traffic_assignment_tool = _MODELLER.tool(
    "inro.emme.traffic_assignment.sola_traffic_assignment"
)

delete_matrix = _MODELLER.tool("inro.emme.data.matrix.delete_matrix")


@contextmanager
def blankManager(obj):
    try:
        yield obj
    finally:
        pass


class AssignTraffic(_m.Tool()):
    version = "1.1.1"
    tool_run_msg = ""
    # For progress reporting, enter the integer number of tasks here
    number_of_tasks = 4

    # Tool Input Parameters
    #    Only those parameters neccessary for Modeller and/or XTMF to dock with
    #    need to be placed here. Internal parameters (such as lists and dicts)
    #    get intitialized during construction (__init__)
    # ---Variable definitions

    # Parameters takes in a json file name
    parameters = _m.Attribute(str)
    number_of_processors = _m.Attribute(int)

    def __init__(self):
        self._tracker = _util.progress_tracker(self.number_of_tasks)
        self.scenario = _MODELLER.scenario
        self.number_of_processors = multiprocessing.cpu_count()

    def page(self):
        pb = _m.ToolPageBuilder(
            self,
            title="Multi-Class Road Assignment",
            description="Cannot be called from Modeller.",
            runnable=False,
            branding_text="XTMF",
        )
        return pb.render()

    def __call__(self, parameters):
        parameters = self._read_json_file(parameters)
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
        # Initialize non-temporary matrices (input matrices)
        demand_matrix_list = self._init_non_temp_matrices(parameters)

        with self._temp_matrix_manager() as cost_matrix_list:
            # Initialize cost matrices (output matrices)
            self._init_temp_matrix("cost_matrix", parameters, cost_matrix_list)

            with self._temp_matrix_manager() as time_matrix_list:
                # Initialize time matrices (output matrices)
                self._init_temp_matrix("time_matrix", parameters, time_matrix_list)

                with self._temp_matrix_manager() as toll_matrix_list:
                    # Initialize toll matrices (output matrices)
                    self._init_temp_matrix("toll_matrix", parameters, toll_matrix_list)

                    self._tracker.complete_subtask()

                    with self._temp_attribute_manager(scenario) as time_attribute_list:
                        self._time_attribute(
                            scenario, demand_matrix_list, time_attribute_list
                        )

                        with self._temp_attribute_manager(
                            scenario
                        ) as cost_attribute_list:
                            self._cost_attribute(
                                scenario, demand_matrix_list, cost_attribute_list
                            )

                            with self._temp_attribute_manager(
                                scenario
                            ) as transit_attribute_list:
                                self._transit_traffic_attribute(
                                    scenario, demand_matrix_list, transit_attribute_list
                                )

                                for tc in parameters["traffic_classes"]:
                                    self._create_volume_attribute(
                                        scenario, tc["volume_attribute"]
                                    )

                                with self._temp_matrix_manager() as peak_hour_matrix_list:
                                    self._init_temp_phf_matrices(
                                        demand_matrix_list, peak_hour_matrix_list
                                    )
                                    if (
                                        parameters["background_transit"].lower()
                                        == "true"
                                        or True
                                    ):
                                        if (
                                            int(
                                                scenario.element_totals["transit_lines"]
                                            )
                                            > 0
                                        ):
                                            with _m.logbook_trace(
                                                "Calculating transit background traffic"
                                            ):
                                                network_calculation_tool(
                                                    self._get_transit_bg_spec(),
                                                    scenario=scenario,
                                                )
                                                self._tracker.complete_subtask()

                                    applied_toll_factor_list = (
                                        self._calculate_applied_toll_factor(parameters)
                                    )

                                    with _m.logbook_trace("Calculating link costs"):
                                        for i in range(len(demand_matrix_list)):
                                            # TODO: visit below
                                            network_calculation_tool(
                                                self._get_link_cost_calc_spec(
                                                    cost_attribute_list[i].id,
                                                    parameters["traffic_classes"][i][
                                                        "link_cost"
                                                    ],
                                                    parameters["traffic_classes"][i][
                                                        "link_toll_attribute_id"
                                                    ],
                                                    applied_toll_factor_list[i],
                                                ),
                                                scenario=scenario,
                                            )
                                        self._tracker.complete_subtask()

                                    with _m.logbook_trace(
                                        "Calculting peak hour matrix"
                                    ):
                                        for i in range(len(demand_matrix_list)):
                                            matrix_calc_tool(
                                                self._get_peak_hour_spec(
                                                    peak_hour_matrix_list[i].id,
                                                    demand_matrix_list[i].id,
                                                    parameters["traffic_classes"][i][
                                                        "peak_hour_factor"
                                                    ],
                                                ),
                                                scenario=scenario,
                                                num_processors=self.number_of_processors,
                                            )
                                        self._tracker.complete_subtask()

                                    self._tracker.complete_subtask()

                                    with _m.logbook_trace("Running Road Assignments."):

                                        # TODO: Ignore path analysis and return to it later
                                        # {PATH ANALYSIS GOES HERE}
                                        # TODO: Ignore path analysis and return to it later

                                        path_analysis_is_complete = False
                                        if path_analysis_is_complete is False:
                                            attribute_list = []
                                            mode_list = [
                                                mode["mode"]
                                                for mode in parameters[
                                                    "traffic_classes"
                                                ]
                                            ]
                                            volume_attribute_list = [
                                                self.get_attribute_name(
                                                    volume_attribute["volume_attribute"]
                                                )
                                                for volume_attribute in parameters[
                                                    "traffic_classes"
                                                ]
                                            ]
                                            for i in range(len(demand_matrix_list)):
                                                attribute_list.append(None)
                                            spec = self._get_primary_SOLA_spec(
                                                demand_matrix_list,
                                                peak_hour_matrix_list,
                                                applied_toll_factor_list,
                                                mode_list,
                                                volume_attribute_list,
                                                cost_attribute_list,
                                                time_matrix_list,
                                                attribute_list,
                                                None,
                                                None,
                                                None,
                                                None,
                                                None,
                                                None,
                                                None,
                                                parameters,
                                            )
                                            report = self._tracker.run_tool(
                                                traffic_assignment_tool,
                                                spec,
                                                scenario=scenario,
                                            )

                                        stopping_criteron = report["stopping_criterion"]
                                        iterations = report["iterations"]
                                        if len(iterations) > 0:
                                            final_iteration = iterations[-1]
                                        else:
                                            final_iteration = {"number": 0}
                                            stopping_criteron == "MAX_ITERATIONS"
                                        number = final_iteration["number"]

                                        if stopping_criteron == "MAX_ITERATIONS":
                                            val = final_iteration["number"]
                                        elif stopping_criteron == "RELATIVE_GAP":
                                            val = final_iteration["gaps"]["relative"]
                                        elif stopping_criteron == "NORMALIZED_GAP":
                                            val = final_iteration["gaps"]["normalized"]
                                        elif stopping_criteron == "BEST_RELATIVE_GAP":
                                            val = final_iteration["gaps"][
                                                "best_relative"
                                            ]
                                        else:
                                            val = "undefined"

                                        print(
                                            "Primary assignment complete at %s iterations."
                                            % number
                                        )
                                        print(
                                            "Stopping criterion was %s with a value of %s."
                                            % (stopping_criteron, val)
                                        )

    # ---SUB FUNCTIONS-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

    def _load_scenario(self, scenario_number):
        scenario = _m.Modeller().emmebank.scenario(scenario_number)
        if scenario is None:
            raise Exception("Scenario %s was not found!" % scenario_number)
        return scenario

    def _read_json_file(self, json_file_name):
        try:
            print("Reading parameters from json file '%s'." % json_file_name)
            with open(json_file_name, "r") as json_file:
                return json.load(json_file)
        except:
            raise Exception

    def _get_atts(self, parameters):
        ...

    def get_attribute_name(self, at):
        if at.startswith("@"):
            return at
        else:
            return "@" + at

    # ---MATRICES  -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

    def _init_non_temp_matrices(self, parameters):
        checked_matrix_list = []
        demand_matrix_list = []

        # Check all non-mf0 matrix
        for c in parameters["traffic_classes"]:
            demand_string = str(c["demand_matrix"]).lower()
            if demand_string == "mf0":
                checked_matrix_list.append(demand_string)
            elif _MODELLER.emmebank.matrix(demand_string) is None:
                raise Exception("Matrix %s was not found!" % demand_string)
            elif str(_MODELLER.emmebank.matrix(demand_string).id) == demand_string:
                checked_matrix_list.append(demand_string)
            else:
                raise Exception("Matrix %s was not found!" % demand_string)

        # Initializing all non-specified matrices and returning all
        for dm in checked_matrix_list:
            if dm == "mf0":
                demand_matrix = _util.initialize_matrix(matrix_type="FULL")
                demand_matrix_list.append(_MODELLER.emmebank.matrix(demand_matrix.id))
            else:
                demand_matrix_list.append(_MODELLER.emmebank.matrix(dm))

        return demand_matrix_list

    def _init_temp_matrix(self, matrix_name, parameters, temp_matrix_list):
        traffic_classes = parameters["traffic_classes"]
        for temp_matrix in traffic_classes:
            # TODO: process matrix id
            if matrix_name == "cost" or matrix_name == "cost_matrix":
                matrix_id = str(temp_matrix["cost_matrix"])
                desc = "COST"
            elif matrix_name == "time" or matrix_name == "time_matrix":
                matrix_id = str(temp_matrix["time_matrix"])
                desc = "TIME"
            elif matrix_name == "toll" or matrix_name == "toll_matrix":
                matrix_id = str(temp_matrix["toll_matrix"])
                desc = "TOLL"

            if matrix_id == "mf0":
                temp_matrix_list.append(None)
            elif matrix_id != "mf0" and _MODELLER.emmebank.matrix(matrix_id) is None:
                matrix = _util.initialize_matrix(
                    matrix_id,
                    name="acost",
                    description="AUTO %s FOR CLASS: %s" % (temp_matrix["name"], desc),
                )
                temp_matrix_list.append(matrix)
            elif str(_MODELLER.emmebank.matrix(matrix_id).id) == matrix_id:
                matrix = _MODELLER.emmebank.matrix(matrix_id)
                temp_matrix_list.append(matrix)
            else:
                raise Exception("Matrix %s was not found!" % matrix_id)

    def _init_temp_phf_matrices(self, demand_matrix_list, peak_hour_matrix_list):
        # peak_hour_matrix_list = []
        for i in range(len(demand_matrix_list)):
            peak_hour_matrix = _util.initialize_matrix(description="Peak hour matrix")
            peak_hour_matrix_list.append(peak_hour_matrix)
        return peak_hour_matrix_list

    def _create_volume_attribute(self, scenario, volume_attribute):

        volume_attribute_at = scenario.extra_attribute(volume_attribute)

        if volume_attribute_at is None:
            scenario.create_extra_attribute("LINK", volume_attribute, default_value=0)
        elif volume_attribute_at.type != "LINK":
            raise Exception(
                "Volume Attribute '%s' is not a link type attribute" % volume_attribute
            )
        elif volume_attribute is not None:
            # TODO: check if you can create_extra_attribute with the same name
            _m.logbook_write("Deleting Previous Extra Attributes.")
            scenario.delete_extra_attribute(volume_attribute_at)
            scenario.create_extra_attribute("LINK", volume_attribute, default_value=0)
        else:
            scenario.create_extra_attribute("LINK", volume_attribute, default_value=0)

    # ---EXTRA ATTRIBUTES  -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

    def _time_attribute(self, scenario, demand_matrix_list, time_attribute_list):
        # time_attribute_list = []
        for i in range(len(demand_matrix_list)):
            time_attribute = self._create_temp_attribute(
                scenario, "ltime", "LINK", default_value=0.0
            )
            time_attribute_list.append(time_attribute)
        return time_attribute_list

    def _cost_attribute(self, scenario, demand_matrix_list, cost_attribute_list):
        # cost_attribute_list = []
        for i in range(len(demand_matrix_list)):
            cost_attribute = self._create_temp_attribute(
                scenario, "lkcst", "LINK", default_value=0.0
            )
            cost_attribute_list.append(cost_attribute)
        return cost_attribute_list

    def _transit_traffic_attribute(
        self, scenario, demand_matrix_list, t_traffic_attribute_list
    ):
        # t_traffic_attribute_list = []
        for i in range(len(demand_matrix_list)):
            t_traffic_attribute = self._create_temp_attribute(
                scenario, "tvph", "LINK", default_value=0.0
            )
            t_traffic_attribute_list.append(t_traffic_attribute)
        return t_traffic_attribute_list

    def _create_temp_attribute(
        self,
        scenario,
        attribute_id,
        attribute_type,
        description=None,
        default_value=0.0,
    ):
        """
        Creates a temporary extra attribute in a given scenario
        """
        ATTRIBUTE_TYPES = ["NODE", "LINK", "TURN", "TRANSIT_LINE", "TRANSIT_SEGMENT"]

        attribute_type = str(attribute_type).upper()
        # check if the type provided is correct
        if attribute_type not in ATTRIBUTE_TYPES:
            raise TypeError(
                "Attribute type '%s' provided is recognized." % attribute_type
            )

        if len(attribute_id) > 18:
            raise ValueError(
                "Attribute id '%s' can only be 19 characters long with no spaces plus  no '@'."
                % attribute_id
            )
        prefix = str(attribute_id)
        attrib_id = ""
        if prefix != "@tvph" and prefix != "tvph":
            while True:
                suffix = random.randint(1, 999999)
                if prefix.startswith("@"):
                    attrib_id = "%s%s" % (prefix, suffix)
                else:
                    attrib_id = "@%s%s" % (prefix, suffix)

                if scenario.extra_attribute(attrib_id) is None:
                    temp_extra_attribute = scenario.create_extra_attribute(
                        attribute_type, attrib_id, default_value
                    )
                    break
        else:
            attrib_id = prefix
            if prefix.startswith("@"):
                attrib_id = "%s" % (prefix)
            else:
                attrib_id = "@%s" % (prefix)

            if scenario.extra_attribute(attrib_id) is None:
                temp_extra_attribute = scenario.create_extra_attribute(
                    attribute_type, attrib_id, default_value
                )
                _m.logbook_write("Created extra attribute '@tvph'")
            else:
                temp_extra_attribute = scenario.extra_attribute(attrib_id).initialize(0)

        msg = "Created temporary extra attribute %s in scenario %s" % (
            attrib_id,
            scenario.id,
        )
        if description:
            temp_extra_attribute.description = description
            msg += ": %s" % description
        _m.logbook_write(msg)

        return temp_extra_attribute

    # ---SPECIFICATIONS & CALCULATIONS  -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    def _calculate_applied_toll_factor(self, parameters):
        applied_toll_factor = []
        for toll_weight in parameters["traffic_classes"]:
            if toll_weight["toll_weight"] is not None:
                try:
                    toll_weight = 60 / toll_weight["toll_weight"]
                    applied_toll_factor.append(toll_weight)
                except ZeroDivisionError:
                    toll_weight = toll_weight["toll_weight"]
                    applied_toll_factor.append(toll_weight)

        return applied_toll_factor

    def _get_transit_bg_spec(self):
        return {
            "result": "@tvph",
            "expression": "(60 / hdw) * (vauteq) * (ttf >= 3)",
            "aggregation": "+",
            "selections": {"link": "all", "transit_line": "all"},
            "type": "NETWORK_CALCULATION",
        }

    def _get_link_cost_calc_spec(
        self, cost_attribute_id, link_cost, link_toll_attribute_id, perception
    ):
        return {
            "result": cost_attribute_id,
            "expression": "(length * %f + %s)*%f"
            % (link_cost, link_toll_attribute_id, perception),
            "aggregation": None,
            "selections": {"link": "all"},
            "type": "NETWORK_CALCULATION",
        }

    def _get_peak_hour_spec(
        self, peak_hour_matrix_id, demand_matrix_id, peak_hour_factor
    ):
        return {
            "expression": demand_matrix_id + "*" + str(peak_hour_factor),
            "result": peak_hour_matrix_id,
            "constraint": {"by_value": None, "by_zone": None},
            "aggregation": {"origins": None, "destinations": None},
            "type": "MATRIX_CALCULATION",
        }

    # ---ALL THINGS SOLA GOES HERE------------------------------------------------------------------------------------------------------------------------------------------------------------------------

    def _get_primary_SOLA_spec(
        self,
        demand_matrix_list,
        peak_hour_matrix_list,
        applied_toll_factor_list,
        mode_list,
        volume_attribute_list,
        cost_attribute_list,
        time_matrix_list,
        attribute_list,
        matrix_list,
        operator_list,
        lower_bound_list,
        upper_bound_list,
        selector_list,
        multiply_path_demand,
        multiply_path_value,
        parameters,
    ):
        if parameters["performance_flag"] == "true":
            number_of_processors = multiprocessing.cpu_count()
        else:
            number_of_processors = max(multiprocessing.cpu_count() - 1, 1)
        # Generic Spec for SOLA
        SOLA_spec = {
            "type": "SOLA_TRAFFIC_ASSIGNMENT",
            "classes": [],
            "path_analysis": None,
            "cutoff_analysis": None,
            "traversal_analysis": None,
            "performance_settings": {"number_of_processors": number_of_processors},
            "background_traffic": None,
            "stopping_criteria": {
                "max_iterations": parameters["iterations"],
                "relative_gap": parameters["r_gap"],
                "best_relative_gap": parameters["br_gap"],
                "normalized_gap": parameters["norm_gap"],
            },
        }
        SOLA_path_analysis = []
        for i in range(0, len(demand_matrix_list)):
            if attribute_list[i] is None:
                SOLA_path_analysis.append([])
            else:
                SOLA_path_analysis.append([])
                all_none = True
                for j in range(len(attribute_list[i])):
                    if attribute_list[i][j] is None:
                        continue
                    all_none = False
                    path = {
                        "link_component": attribute_list[i][j],
                        "turn_component": None,
                        "operator": operator_list[i][j],
                        "selection_threshold": {
                            "lower": lower_bound_list[i][j],
                            "upper": upper_bound_list[i][j],
                        },
                        "path_to_od_composition": {
                            "considered_paths": selector_list[i][j],
                            "multiply_path_proportions_by": {
                                "analyzed_demand": multiply_path_demand[i][j],
                                "path_value": multiply_path_value[i][j],
                            },
                        },
                        "results": {"od_values": matrix_list[i][j]},
                        "analyzed_demand": None,
                    }
                    SOLA_path_analysis[i].append(path)
                if all_none is True:
                    SOLA_path_analysis[i] = []
        SOLA_class_generator = [
            {
                "mode": mode_list[i],
                "demand": peak_hour_matrix_list[i].id,
                "generalized_cost": {
                    "link_costs": cost_attribute_list[i].id,
                    "perception_factor": 1,
                },
                "results": {
                    "link_volumes": volume_attribute_list[i],
                    "turn_volumes": None,
                    "od_travel_times": {"shortest_paths": time_matrix_list[i]},
                },
                "path_analyses": SOLA_path_analysis[i],
            }
            for i in range(len(mode_list))
        ]

        SOLA_spec["classes"] = SOLA_class_generator

        return SOLA_spec

    # ---CONTEXT MANAGERS---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

    @contextmanager
    def _temp_matrix_manager(self):
        """
        Matrix objects created & added to this matrix list are deleted when this manager exits.
        """
        temp_matrix_list = []
        try:
            yield temp_matrix_list
        finally:
            for matrix in temp_matrix_list:
                if matrix is not None:
                    _m.logbook_write("Deleting temporary matrix '%s': " % matrix.id)
                    _MODELLER.emmebank.delete_matrix(matrix.id)

    @contextmanager
    def _temp_attribute_manager(self, scenario):
        temp_attribute_list = []
        try:
            yield temp_attribute_list
        finally:
            for temp_attribute in temp_attribute_list:
                if temp_attribute is not None:
                    scenario.delete_extra_attribute(temp_attribute.id)
                    _m.logbook_write(
                        "Deleted temporary '%s' link attribute" % temp_attribute.id
                    )

    @_m.method(return_type=_m.TupleType)
    def percent_completed(self):
        return self._tracker.getProgress()

    @_m.method(return_type=str)
    def tool_run_msg_status(self):
        return self.tool_run_msg
