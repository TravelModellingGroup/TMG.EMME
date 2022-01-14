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

    V 2.0.2 Updated to receive JSON file parameters from Python API call

"""

from inspect import Parameter
from os import error
from pydoc import describe
import inro.modeller as _m
import traceback as _traceback
from contextlib import contextmanager
import multiprocessing
import random
import json

_m.InstanceType = object
_m.ListType = list
_m.TupleType = object

_trace = _m.logbook_trace
_write = _m.logbook_write
_MODELLER = _m.Modeller()  # Instantiate Modeller once.
_bank = _MODELLER.emmebank
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
    version = "2.0.2"
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
        with self._temp_matrix_manager() as temp_matrix_list:
            # Initialize input matrices
            demand_matrix_list = self._init_demand_matrices(
                parameters, temp_matrix_list
            )
            with _trace(
                name="%s (%s v%s)"
                % (parameters["run_title"], self.__class__.__name__, self.version),
                attributes=self._load_atts(scenario, parameters),
            ):
                self._tracker.reset()
                # Load initialized output matrices
                output_matrices = self._load_output_matrices(
                    parameters, temp_matrix_list
                )
                cost_matrix_list = output_matrices[0]
                time_matrix_list = output_matrices[1]
                toll_matrix_list = output_matrices[2]
                peak_hour_matrix_list = output_matrices[3]
                self._tracker.complete_subtask()

    # ---LOAD - SUB FUNCTIONS -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    def _load_scenario(self, scenario_number):
        scenario = _m.Modeller().emmebank.scenario(scenario_number)
        if scenario is None:
            raise Exception("Scenario %s was not found!" % scenario_number)
        return scenario

    def _load_atts(self, scenario, parameters):
        time_matrix_ids = [mtx["time_matrix"] for mtx in parameters["traffic_classes"]]
        peak_hr_factors = [
            str(phf["peak_hour_factor"]) for phf in parameters["traffic_classes"]
        ]
        link_costs = [str(lc["link_cost"]) for lc in parameters["traffic_classes"]]
        atts = {
            "Run Title": parameters["run_title"],
            "Scenario": str(scenario.id),
            "Times Matrix": str(", ".join(time_matrix_ids)),
            "Peak Hour Factor": str(", ".join(peak_hr_factors)),
            "Link Cost": str(", ".join(link_costs)),
            "Iterations": str(parameters["iterations"]),
            "self": self.__MODELLER_NAMESPACE__,
        }
        return atts

    def _load_attribute_list(self, parameters, demand_matrix_list):
        attribute_list = []
        volume_attribute_list = [
            self.load_attribute_name(volume_attribute["volume_attribute"])
            for volume_attribute in parameters["traffic_classes"]
        ]
        for i in range(len(demand_matrix_list)):
            attribute_list.append(None)
        return attribute_list, volume_attribute_list

    def _load_mode_list(self, parameters):
        mode_list = [mode["mode"] for mode in parameters["traffic_classes"]]
        return mode_list

    def load_attribute_name(self, at):
        if at.startswith("@"):
            return at
        else:
            return "@" + at

    def _load_stopping_criteria(self, report):
        stopping_criteron = report["stopping_criterion"]
        iterations = report["iterations"]
        if len(iterations) > 0:
            final_iteration = iterations[-1]
        else:
            final_iteration = {"number": 0}
            stopping_criteron == "MAX_ITERATIONS"
        number = final_iteration["number"]

        if stopping_criteron == "MAX_ITERATIONS":
            value = final_iteration["number"]
        elif stopping_criteron == "RELATIVE_GAP":
            value = final_iteration["gaps"]["relative"]
        elif stopping_criteron == "NORMALIZED_GAP":
            value = final_iteration["gaps"]["normalized"]
        elif stopping_criteron == "BEST_RELATIVE_GAP":
            value = final_iteration["gaps"]["best_relative"]
        else:
            value = "undefined"

        return number, stopping_criteron, value

    # ---INITIALIZE - SUB-FUNCTIONS  -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

    def _init_demand_matrices(self, parameters, temp_matrix_list):
        checked_list = []
        demand_matrix_list = []
        # temp_matrix_list = []

        # Check all non-mf0 matrix
        for traffic_class in parameters["traffic_classes"]:
            demand_matrix_id = str(traffic_class["demand_matrix"]).lower()
            if demand_matrix_id == "mf0":
                checked_list.append(demand_matrix_id)
            elif _bank.matrix(demand_matrix_id) is None:
                raise Exception("Matrix %s was not found!" % demand_matrix_id)
            elif str(_bank.matrix(demand_matrix_id).id) == demand_matrix_id:
                checked_list.append(demand_matrix_id)
            else:
                raise Exception("Matrix %s was not found!" % demand_matrix_id)

        # Initializing all non-specified matrices and returning all
        for demand_matrix_id in checked_list:
            if demand_matrix_id == "mf0":
                demand_matrix = _util.initialize_matrix(matrix_type="FULL")
                demand_matrix_list.append(_bank.matrix(demand_matrix.id))
                temp_matrix_list.append(demand_matrix)
            else:
                demand_matrix_list.append(_bank.matrix(demand_matrix_id))

        return demand_matrix_list

    def _init_output_matrices(
        self, parameters, matrix_name, temp_matrix_list, description=""
    ):
        output_matrix_list = []
        traffic_classes = parameters["traffic_classes"]
        for traffic_class in traffic_classes:
            matrix_id = traffic_class[str(matrix_name)]
            desc = "AUTO %s FOR CLASS: %s" % (
                str(matrix_name).upper(),
                str(traffic_class["name"]).upper(),
            )
            if matrix_id == "mf0":
                matrix = _util.initialize_matrix(
                    name=str(matrix_name),
                    description=description if description != "" else desc,
                )
                temp_matrix_list.append(matrix)
                output_matrix_list.append(matrix)
            elif _bank.matrix(matrix_id) is None:
                matrix = _util.initialize_matrix(
                    id=matrix_id,
                    name=str(matrix_name),
                    description=description if description != "" else desc,
                )
                temp_matrix_list.append(matrix)
                output_matrix_list.append(matrix)
            else:
                matrix = _bank.matrix(matrix_id)
                output_matrix_list.append(matrix)

        return output_matrix_list

    def _init_temp_peak_hour_matrix(self, parameters, temp_matrix_list):
        peak_hour_matrix_list = []
        for traffic_class in parameters["traffic_classes"]:

            peak_hour_matrix = _util.initialize_matrix(
                default=traffic_class["peak_hour_factor"],
                description="Peak hour matrix",
            )
            peak_hour_matrix_list.append(peak_hour_matrix)
            temp_matrix_list.append(peak_hour_matrix)
        return peak_hour_matrix_list

    # ---CREATE - SUB FUNCTIONS-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

    def _create_time_attribute_list(
        self, scenario, demand_matrix_list, time_attribute_list
    ):
        for i in range(len(demand_matrix_list)):
            time_attribute = self._create_temp_attribute(
                scenario, "ltime", "LINK", default_value=0.0
            )
            time_attribute_list.append(time_attribute)
        return time_attribute_list

    def _create_cost_attribute_list(
        self, scenario, demand_matrix_list, cost_attribute_list
    ):
        for i in range(len(demand_matrix_list)):
            cost_attribute = self._create_temp_attribute(
                scenario, "lkcst", "LINK", default_value=0.0
            )
            cost_attribute_list.append(cost_attribute)
        return cost_attribute_list

    def create_transit_traffic_attribute_list(
        self, scenario, demand_matrix_list, transit_traffic_attribute_list
    ):
        for i in range(len(demand_matrix_list)):
            t_traffic_attribute = self._create_temp_attribute(
                scenario, "tvph", "LINK", default_value=0.0
            )
            transit_traffic_attribute_list.append(t_traffic_attribute)
        return transit_traffic_attribute_list

    def _create_volume_attribute(self, scenario, volume_attribute):

        volume_attribute_at = scenario.extra_attribute(volume_attribute)

        if volume_attribute_at is None:
            scenario.create_extra_attribute("LINK", volume_attribute, default_value=0)
        elif volume_attribute_at.type != "LINK":
            raise Exception(
                "Volume Attribute '%s' is not a link type attribute" % volume_attribute
            )
        elif volume_attribute is not None:
            _m.logbook_write("Deleting Previous Extra Attributes.")
            scenario.delete_extra_attribute(volume_attribute_at)
            scenario.create_extra_attribute("LINK", volume_attribute, default_value=0)
        else:
            scenario.create_extra_attribute("LINK", volume_attribute, default_value=0)

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

    # ---CALCULATE - SUB FUNCTIONS-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    def _calculate_link_cost(
        self,
        scenario,
        parameters,
        demand_matrix_list,
        applied_toll_factor_list,
        cost_attribute_list,
    ):
        with _m.logbook_trace("Calculating link costs"):
            for i in range(len(demand_matrix_list)):
                network_calculation_tool(
                    self._get_link_cost_calc_spec(
                        cost_attribute_list[i].id,
                        parameters["traffic_classes"][i]["link_cost"],
                        parameters["traffic_classes"][i]["link_toll_attribute_id"],
                        applied_toll_factor_list[i],
                    ),
                    scenario=scenario,
                )
            self._tracker.complete_subtask()

    def _calculate_peak_hour_matrix(
        self, scenario, parameters, demand_matrix_list, peak_hour_matrix_list
    ):
        with _m.logbook_trace("Calculting peak hour matrix"):
            for i in range(len(demand_matrix_list)):
                matrix_calc_tool(
                    self._get_peak_hour_spec(
                        peak_hour_matrix_list[i].id,
                        demand_matrix_list[i].id,
                        parameters["traffic_classes"][i]["peak_hour_factor"],
                    ),
                    scenario=scenario,
                    num_processors=self.number_of_processors,
                )
            self._tracker.complete_subtask()

    def _calculate_transit_background_traffic(self, scenario, parameters):
        if parameters["background_transit"].lower() == "true":
            if int(scenario.element_totals["transit_lines"]) > 0:
                with _m.logbook_trace("Calculating transit background traffic"):
                    network_calculation_tool(
                        self._get_transit_bg_spec(),
                        scenario=scenario,
                    )
                    self._tracker.complete_subtask()

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

    # ---SPECIFICATION - SUB FUNCTIONS-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
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

    def _load_output_matrices(self, parameters, temp_matrix_list):
        cost_matrix_list = self._init_output_matrices(
            parameters, "cost_matrix", temp_matrix_list, description="Cost matrix"
        )
        time_matrix_list = self._init_output_matrices(
            parameters, "time_matrix", temp_matrix_list, description=""
        )
        toll_matrix_list = self._init_output_matrices(
            parameters, "toll_matrix", temp_matrix_list, description="Time matrix"
        )
        peak_hour_matrix_list = self._init_temp_peak_hour_matrix(
            parameters, temp_matrix_list
        )
        return (
            cost_matrix_list,
            time_matrix_list,
            toll_matrix_list,
            peak_hour_matrix_list,
        )

    # ---CONTEXT MANAGERS---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

    @contextmanager
    def _load_temp_attributes(self, scenario, demand_matrix_list):
        with self._temp_attribute_manager(scenario) as time_attribute_list:
            self._create_time_attribute_list(
                scenario, demand_matrix_list, time_attribute_list
            )

            with self._temp_attribute_manager(scenario) as cost_attribute_list:
                self._create_cost_attribute_list(
                    scenario, demand_matrix_list, cost_attribute_list
                )

                with self._temp_attribute_manager(scenario) as transit_attribute_list:
                    self.create_transit_traffic_attribute_list(
                        scenario, demand_matrix_list, transit_attribute_list
                    )
                    yield time_attribute_list, cost_attribute_list, transit_attribute_list

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
                    _bank.delete_matrix(matrix.id)

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
        return self._tracker.get_progress()

    @_m.method(return_type=str)
    def tool_run_msg_status(self):
        return self.tool_run_msg
