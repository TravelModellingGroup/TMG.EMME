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

    2.0.0 Refactored to work with XTMF2/TMGToolbox2 on 2021-10-21 by williamsDiogu        
"""

import inro.modeller as _m
import traceback as _traceback
import multiprocessing

_m.InstanceType = object
_m.ListType = list
_m.TupleType = object

_MODELLER = _m.Modeller()  # Instantiate Modeller once.
_util = _MODELLER.module("tmg2.utilities.general_utilities")
EMME_VERSION = _util.getEmmeVersion(tuple)


@contextmanager
def blankManager(obj):
    try:
        yield obj
    finally:
        pass


class AssignDemandToRoadAssignment(_m.Tool()):
    version = "1.1.1"
    tool_run_msg = ""
    number_of_tasks = (
        4  # For progress reporting, enter the integer number of tasks here
    )

    # Tool Input Parameters
    #    Only those parameters neccessary for Modeller and/or XTMF to dock with
    #    need to be placed here. Internal parameters (such as lists and dicts)
    #    get intitialized during construction (__init__)
    # ---Variable definitions
    scenario_number = _m.Attribute(int)
    scenario = _m.Attribute(_m.InstanceType)

    # DemandMatrix = _m.Attribute(_m.InstanceType) #remove?

    link_toll_attribute_id = _m.Attribute(str)

    times_matrix_id = _m.Attribute(int)
    cost_matrix_id = _m.Attribute(int)
    tolls_matrix_id = _m.Attribute(int)
    run_title = _m.Attribute(str)

    mode_list = _m.Attribute(
        str
    )  # Must be passed as a string, with modes comma separated (e.g. 'a,b,c') cov => ['a','b','c']
    demand_string = _m.Attribute(
        str
    )  # Must be passed as a string, with demand matricies comma separated (e.g. 'a,b,c') cov => ['a','b','c']
    demand_list = _m.Attribute(str)  # The Demand Matrix List

    peak_hour_factor = _m.Attribute(float)
    link_cost = _m.Attribute(int)
    toll_weight = _m.Attribute(int)
    iterations = _m.Attribute(int)
    r_gap = _m.Attribute(float)
    br_gap = _m.Attribute(float)
    norm_gap = _m.Attribute(float)

    performance_flag = _m.Attribute(bool)
    sola_flag = _m.Attribute(bool)
    name_string = _m.Attribute(str)
    result_attributes = _m.Attribute(str)
    analysis_attributes = _m.Attribute(str)
    analysis_attributes_matrix_id = _m.Attribute(int)
    aggregation_operator = _m.Attribute(str)
    lower_bound = _m.Attribute(str)
    upper_bound = _m.Attribute(str)
    path_selection = _m.Attribute(str)
    multiply_path_prop_by_demand = _m.Attribute(str)
    multiply_path_prop_by_value = _m.Attribute(str)
    background_transit = _m.Attribute(str)

    # class_analysis_attributes = _m.Attribute(str)
    # class_analysis_attributes_matrix = _m.Attribute(str)
    # class_analysis_operators = _m.Attribute(str)
    # class_analysis_lower_bounds = _m.Attribute(str)
    # class_analysis_upper_bounds = _m.Attribute(str)
    # class_analysis_selectors = _m.Attribute(str)
    number_of_processors = _m.Attribute(int)

    def __init__(self):
        self._tracker = _util.ProgressTracker(self.number_of_tasks)

        self.scenario = _MODELLER.scenario

        # Old Demand Matrix Definition
        # mf10 = _MODELLER.emmebank.matrix('mf10')
        # if mf10 is not None:
        # self.DemandMatrix = mf10

        self.peak_hour_factor = 0.43
        self.link_cost = 0
        self.toll_weight = 0
        self.iterations = 100
        self.r_gap = 0
        self.br_gap = 0.1
        self.norm_gap = 0.05
        self.performance_flag = False
        self.run_title = ""
        self.link_toll_attribute_id = "@toll"

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

    def __call__(
        self,
        scenario_number,
        mode_list,
        demand_string,
        times_matrix_id,
        cost_matrix_id,
        tolls_matrix_id,
        peak_hour_factor,
        link_cost,
        toll_weight,
        iterations,
        r_gap,
        br_gap,
        norm_gap,
        performance_flag,
        run_title,
        link_toll_attribute_id,
        name_string,
        result_attributes,
        analysis_attributes,
        analysis_attributes_matrix_id,
        aggregation_operator,
        lower_bound,
        upper_bound,
        path_selection,
        multiply_path_prop_by_demand,
        multiply_path_prop_by_value,
        background_transit,
    ):
        # ---1 Set up Scenario
        self._load_scenario(scenario_number)

        # ---2 All Process Parameters
        self._process_parameters(
            mode_list,
            demand_string,
            times_matrix_id,
            cost_matrix_id,
            tolls_matrix_id,
            peak_hour_factor,
            link_cost,
            toll_weight,
            iterations,
            r_gap,
            br_gap,
            norm_gap,
            performance_flag,
            run_title,
            link_toll_attribute_id,
            name_string,
            result_attributes,
            analysis_attributes,
            analysis_attributes_matrix_id,
            aggregation_operator,
            lower_bound,
            upper_bound,
            path_selection,
            multiply_path_prop_by_demand,
            multiply_path_prop_by_value,
            background_transit,
        )

        # ---3. Run
        try:
            print("Starting assignment.")
            self._execute()
            print("Assignment complete.")
        except Exception as e:
            raise Exception(_util.formatReverseStack())

    def run_xtmf(self, parameters):
        self.scenario_number = parameters["scenario_number"]
        self.mode_list = parameters["mode_list"]
        self.demand_string = parameters["demand_string"]
        self.times_matrix_id = parameters["times_matrix_id"]
        self.cost_matrix_id = parameters["cost_matrix_id"]
        self.tolls_matrix_id = parameters["tolls_matrix_id"]
        self.peak_hour_factor = parameters["peak_hour_factor"]
        self.link_cost = parameters["link_cost"]
        self.toll_weight = parameters["toll_weight"]
        self.iterations = parameters["iterations"]
        self.r_gap = parameters["r_gap"]
        self.br_gap = parameters["br_gap"]
        self.norm_gap = parameters["norm_gap"]
        self.performance_flag = parameters["performance_flag"]
        self.run_title = parameters["run_title"]
        self.link_toll_attribute_id = parameters["link_toll_attribute_id"]
        self.name_string = parameters["name_string"]
        self.result_attributes = parameters["result_attributes"]
        self.analysis_attributes = parameters["analysis_attributes"]
        self.analysis_attributes_matrix_id = parameters["analysis_attributes_matrix_id"]
        self.aggregation_operator = parameters["aggregation_operator"]
        self.lower_bound = parameters["lower_bound"]
        self.upper_bound = parameters["upper_bound"]
        self.path_selection = parameters["path_selection"]
        self.multiply_path_prop_by_demand = parameters["multiply_path_prop_by_demand"]
        self.multiply_path_prop_by_value = parameters["multiply_path_prop_by_value"]
        self.background_transit = parameters["background_transit"]

        # ---1: Set-up Scenario
        self._load_scenario(self.scenario_number)

        # ---2: Process Parameters
        self._process_parameters(
            self.mode_list,
            self.demand_string,
            self.times_matrix_id,
            self.cost_matrix_id,
            self.tolls_matrix_id,
            self.peak_hour_factor,
            self.link_cost,
            self.toll_weight,
            self.iterations,
            self.r_gap,
            self.br_gap,
            self.norm_gap,
            self.performance_flag,
            self.run_title,
            self.link_toll_attribute_id,
            self.name_string,
            self.result_attributes,
            self.analysis_attributes,
            self.analysis_attributes_matrix_id,
            self.aggregation_operator,
            self.lower_bound,
            self.upper_bound,
            self.path_selection,
            self.multiply_path_prop_by_demand,
            self.multiply_path_prop_by_value,
            self.background_transit,
        )
        # ---3. Run
        try:
            print("Starting assignment.")
            self._execute()
            print("Assignment complete.")
        except Exception as e:
            raise Exception(_util.formatReverseStack())

    def _execute(self):
        with _m.logbook_trace(
            name="%s (%s v%s)"
            % (self.run_title, self.__class__.__name__, self.version),
            attributes=self._getAtts(),
        ):

            self._tracker.reset()

            matrixCalcTool = _MODELLER.tool(
                "inro.emme.matrix_calculation.matrix_calculator"
            )
            networkCalculationTool = _MODELLER.tool(
                "inro.emme.network_calculation.network_calculator"
            )
            trafficAssignmentTool = _MODELLER.tool(
                "inro.emme.traffic_assignment.sola_traffic_assignment"
            )

            self._tracker.startProcess(5)

            with self._initOutputMatrices() as OutputMatrices:

                self._tracker.completeSubtask()

                with self._costAttributeMANAGER() as costAttribute, self._transitTrafficAttributeMANAGER() as bgTransitAttribute, self._timeAttributeMANAGER() as imeAttribute:
                    # bgTransitAttribute is None

                    # Adding @ for the process of generating link cost attributes and declaring list variables

                    def get_attribute_name(at):
                        if at.startswith("@"):
                            return at
                        else:
                            return "@" + at

                    class_volume_attributes = [
                        get_attribute_name(at)
                        for at in self.result_attributes.split(",")
                    ]

                    for name in class_volume_attributes:
                        if name == "@None" or name == "@none":
                            name = None
                            continue
                        if self.scenario.extra_attribute(name) is not None:
                            _m.logbook_write("Deleting Previous Extra Attributes.")
                            self.scenario.delete_extra_attribute(name)
                        _m.logbook_write("Creating link cost attribute '@(mode)'.")
                        self.scenario.create_extra_attribute(
                            "LINK", name, default_value=0
                        )

                    with (
                        _util.tempMatrixMANAGER(description="Peak hour matrix")
                        for Demand in self.demand_list
                    ) as peakHourMatrix:
                        if (
                            self.BackgroundTransit == True
                        ):  # only do if you want background transit
                            if (
                                int(self.scenario.element_totals["transit_lines"]) > 0
                            ):  # only do if there are actually transit lines present in the network
                                with _m.logbook_trace(
                                    "Calculating transit background traffic"
                                ):  # Do Once
                                    networkCalculationTool(
                                        self._getTransitBGSpec(), scenario=self.scenario
                                    )
                                    self._tracker.completeSubtask()

                        applied_toll_factor = self._calculateAppliedTollFactor()

                        with _m.logbook_trace(
                            "Calculating link costs"
                        ):  # Do for each class
                            for i in range(len(self.demand_list)):
                                networkCalculationTool(
                                    self._getLinkCostCalcSpec(
                                        costAttribute[i].id,
                                        self.link_cost[i],
                                        self.link_toll_attribute_id[i],
                                        applied_toll_factor[i],
                                    ),
                                    scenario=self.scenario,
                                )
                                self._tracker.completeSubtask()

                        with _m.logbook_trace(
                            "Calculating peak hour matrix"
                        ):  # For each class
                            for i in range(len(self.demand_list)):
                                if EMME_VERSION >= (4, 2, 1):
                                    matrixCalcTool(
                                        self._getPeakHourSpec(
                                            peakHourMatrix[i].id, self.demand_list[i]
                                        ),
                                        scenario=self.scenario,
                                        num_processors=self.number_of_processors,
                                    )
                                else:
                                    matrixCalcTool(
                                        self._getPeakHourSpec(
                                            peakHourMatrix[i].id, self.demand_list[i].id
                                        ),
                                        scenario=self.scenario,
                                    )
                            self._tracker.completeSubtask()

                        self._tracker.completeTask()

                        with _m.logbook_trace("Running Road Assignments."):
                            assignmentComplete = False  # init assignment flag. if assignment done, then trip flag
                            attributeDefined = False  # init attribute flag. if list has something defined, then trip flag
                            allAttributes = []
                            allMatrices = []
                            operators = []
                            lower_bounds = []
                            upper_bounds = []
                            pathSelectors = []
                            multiply_path_demand = []
                            multiplyPathValue = []
                            for i in range(
                                len(self.demand_list)
                            ):  # check to see if any cost matrices defined
                                allAttributes.append([])
                                allMatrices.append([])
                                operators.append([])
                                lower_bounds.append([])
                                upper_bounds.append([])
                                pathSelectors.append([])
                                multiply_path_demand.append([])
                                multiplyPathValue.append([])
                                if self.cost_matrix_id[i] is not None:
                                    _m.logbook_write(
                                        "Cost matrix defined for class %s"
                                        % self.class_names[i]
                                    )
                                    allAttributes[i].append(costAttribute[i].id)
                                    allMatrices[i].append(self.cost_matrix_id[i])
                                    operators[i].append("+")
                                    lower_bounds[i].append(None)
                                    upper_bounds[i].append(None)
                                    pathSelectors[i].append("ALL")
                                    multiply_path_demand[i].append(False)
                                    multiplyPathValue[i].append(True)
                                    attributeDefined = True
                                else:
                                    allAttributes[i].append(None)
                                if self.tolls_matrix_id[i] is not None:
                                    _m.logbook_write(
                                        "Toll matrix defined for class %s"
                                        % self.class_names[i]
                                    )
                                    allAttributes[i].append(
                                        self.link_toll_attribute_id[i]
                                    )
                                    allMatrices[i].append(self.tolls_matrix_id[i])
                                    operators[i].append("+")
                                    lower_bounds[i].append(None)
                                    upper_bounds[i].append(None)
                                    pathSelectors[i].append("ALL")
                                    multiply_path_demand[i].append(False)
                                    multiplyPathValue[i].append(True)
                                    attributeDefined = True
                                else:
                                    allAttributes[i].append(None)
                                for j in range(len(self.class_analysis_attributes[i])):
                                    if self.class_analysis_attributes[i][j] is not None:
                                        _m.logbook_write(
                                            "Additional matrix for attribute %s defined for class %s"
                                            % (
                                                self.class_analysis_attributes[i][j],
                                                self.class_names[i],
                                            )
                                        )
                                        allAttributes[i].append(
                                            self.class_analysis_attributes[i][j]
                                        )
                                        allMatrices[i].append(
                                            self.class_analysis_attributes_matrix[i][j]
                                        )
                                        operators[i].append(
                                            self.class_analysis_operators[i][j]
                                        )
                                        lower_bounds[i].append(
                                            self.class_analysis_lower_bounds[i][j]
                                        )
                                        upper_bounds[i].append(
                                            self.class_analysis_upper_bounds[i][j]
                                        )
                                        pathSelectors[i].append(
                                            self.class_analysis_selectors[i][j]
                                        )
                                        multiply_path_demand[i].append(
                                            self.class_analysis_multiply_path_demand[i][
                                                j
                                            ]
                                        )
                                        multiplyPathValue[i].append(
                                            self.class_analysis_multiply_path_value[i][
                                                j
                                            ]
                                        )
                                        attributeDefined = True
                                    else:
                                        allAttributes[i].append(None)
                            if attributeDefined is True:
                                spec = self._getPrimarySOLASpec(
                                    peakHourMatrix,
                                    applied_toll_factor,
                                    self.mode_list_split,
                                    class_volume_attributes,
                                    costAttribute,
                                    allAttributes,
                                    allMatrices,
                                    operators,
                                    lower_bounds,
                                    upper_bounds,
                                    pathSelectors,
                                    multiply_path_demand,
                                    multiplyPathValue,
                                )
                                report = self._tracker.runTool(
                                    trafficAssignmentTool, spec, scenario=self.scenario
                                )
                                assignmentComplete = True
                            for i in range(len(self.demand_list)):
                                if (
                                    self.times_matrix_id[i] is not None
                                ):  # check to see if any time matrices defined to fix the times matrix for that class
                                    matrixCalcTool(
                                        self._CorrectTimesMatrixSpec(
                                            self.times_matrix_id[i],
                                            self.cost_matrix_id[i],
                                        ),
                                        scenario=self.scenario,
                                        num_processors=self.number_of_processors,
                                    )
                                if (
                                    self.cost_matrix_id[i] is not None
                                ):  # check to see if any cost matrices defined to fix the cost matrix for that class
                                    matrixCalcTool(
                                        self._CorrectCostMatrixSpec(
                                            self.cost_matrix_id[i],
                                            applied_toll_factor[i],
                                        ),
                                        scenario=self.scenario,
                                        num_processors=self.number_of_processors,
                                    )

                            """
                                if attributeDefined is True: # if something, then do the assignment
                                    if assignmentComplete is False:
                                        # need to do blank assignment in order to get auto times saved in timeau
                                        attributes = []
                                        for i in range(len(self.demand_list)):
                                            attributes.append(None)
                                        spec = self._getPrimarySOLASpec(peakHourMatrix, applied_toll_factor, self.mode_list_split,\
                                                                class_volume_attributes, costAttribute, attributes, None, None, None, \
                                                                None, None, None, None)
                                        report = self._tracker.runTool(trafficAssignmentTool, spec, scenario=self.scenario)
                                    # get true times matrix
                                    with _m.logbook_trace("Calculating link time"): 
                                        for i in range(len(self.demand_list)):
                                            networkCalculationTool(self._getSaveAutoTimesSpec(timeAttribute[i].id), scenario=self.scenario)
                                            self._tracker.completeSubtask()
                                    attributes = []
                                    matrices = []
                                    operators = []
                                    lower_bounds = []
                                    upper_bounds = []
                                    pathSelectors = []
                                    multiply_path_demand = []
                                    multiplyPathValue = []
                                    for i in range(len(self.demand_list)):
                                        attributes.append([])
                                        matrices.append([])
                                        operators.append([])
                                        lower_bounds.append([])
                                        upper_bounds.append([])
                                        pathSelectors.append([])
                                        multiply_path_demand.append([])
                                        multiplyPathValue.append([])
                                        if self.times_matrix_id[i] is not None:
                                            attributes[i].append(timeAttribute[i].id)
                                            matrices[i].append(self.times_matrix_id[i])
                                            operators[i].append("+")
                                            lower_bounds[i].append(None)
                                            upper_bounds[i].append(None)
                                            pathSelectors[i].append("ALL")
                                            multiply_path_demand[i].append(False)
                                            multiplyPathValue[i].append(True)
                                        else:
                                            attributes[i].append(None)
                                            matrices[i].append(None)
                                            operators[i].append(None)
                                            lower_bounds[i].append(None)
                                            upper_bounds[i].append(None)
                                            pathSelectors[i].append(None)
                                            multiply_path_demand[i].append(None)
                                            multiplyPathValue[i].append(None)
                                    spec = self._getPrimarySOLASpec(peakHourMatrix, applied_toll_factor, self.mode_list_split,\
                                                                class_volume_attributes, costAttribute, attributes, matrices,  operators, lower_bounds, \
                                                                upper_bounds,pathSelectors, multiply_path_demand, multiplyPathValue)
                                    report = self._tracker.runTool(trafficAssignmentTool, spec, scenario=self.scenario)
                                    assignmentComplete = True
                                """
                            if (
                                assignmentComplete is False
                            ):  # if no assignment has been done, do an assignment
                                attributes = []
                                for i in range(len(self.demand_list)):
                                    attributes.append(None)
                                spec = self._getPrimarySOLASpec(
                                    peakHourMatrix,
                                    applied_toll_factor,
                                    self.mode_list_split,
                                    class_volume_attributes,
                                    costAttribute,
                                    attributes,
                                    None,
                                    None,
                                    None,
                                    None,
                                    None,
                                    None,
                                    None,
                                )
                                report = self._tracker.runTool(
                                    trafficAssignmentTool, spec, scenario=self.scenario
                                )

                            stoppingCriterion = report["stopping_criterion"]
                            iterations = report["iterations"]
                            if len(iterations) > 0:
                                finalIteration = iterations[-1]
                            else:
                                finalIteration = {"number": 0}
                                stoppingCriterion = "MAX_ITERATIONS"
                            number = finalIteration["number"]

                            if stoppingCriterion == "MAX_ITERATIONS":
                                val = finalIteration["number"]
                            elif stoppingCriterion == "RELATIVE_GAP":
                                val = finalIteration["gaps"]["relative"]
                            elif stoppingCriterion == "NORMALIZED_GAP":
                                val = finalIteration["gaps"]["normalized"]
                            elif stoppingCriterion == "BEST_RELATIVE_GAP":
                                val = finalIteration["gaps"]["best_relative"]
                            else:
                                val = "undefined"

                            print(
                                "Primary assignment complete at %s iterations." % number
                            )
                            print(
                                "Stopping criterion was %s with a value of %s."
                                % (stoppingCriterion, val)
                            )

    def _load_scenario(self, scenario_number):
        scenario = _m.Modeller().emmebank.scenario(scenario_number)

        if self.scenario is None:
            raise Exception("Scenario %s was not found!" % scenario_number)

        return scenario

    def _process_parameters(
        self,
        mode_list,
        demand_string,
        times_matrix_id,
        cost_matrix_id,
        tolls_matrix_id,
        peak_hour_factor,
        link_cost,
        toll_weight,
        iterations,
        r_gap,
        br_gap,
        norm_gap,
        performance_flag,
        run_title,
        link_toll_attribute_id,
        name_string,
        result_attributes,
        analysis_attributes,
        analysis_attributes_matrix_id,
        aggregation_operator,
        lower_bound,
        upper_bound,
        path_selection,
        multiply_path_prop_by_demand,
        multiply_path_prop_by_value,
        background_transit,
    ):
        #:List will be passed as follows: demand_string = "mf10,mf11,mf12", Will be parsed into a list

        self.demand_list = demand_string.split(",")

        # Splitting the Time, Cost and Toll string into Lists, and Modes for denoting results
        self.result_attributes = result_attributes
        self.times_matrix_id = times_matrix_id.split(",")
        self.cost_matrix_id = cost_matrix_id.split(",")
        self.tolls_matrix_id = tolls_matrix_id.split(",")
        self.mode_list_split = mode_list.split(",")
        self.class_names = [x for x in name_string.split(",")]
        self.toll_weight = [float(x) for x in toll_weight.split(",")]
        self.link_cost = [float(x) for x in link_cost.split(",")]
        self.link_toll_attribute_id = [x for x in link_toll_attribute_id.split(",")]
        analysis_attributes = [x for x in analysis_attributes.split("|")]
        analysis_attributes_matrix_id = [
            x for x in analysis_attributes_matrix_id.split("|")
        ]
        self.operators = [x for x in aggregation_operator.split("|")]
        self.lower_bounds = [x for x in lower_bound.split("|")]
        self.upper_bounds = [x for x in upper_bound.split("|")]
        self.selectors = [x for x in path_selection.split("|")]
        self.multiply_path_demand = [x for x in multiply_path_prop_by_demand.split("|")]
        self.multiply_path_value = [x for x in multiply_path_prop_by_value.split("|")]
        self.class_analysis_attributes = []
        self.class_analysis_attributes_matrix = []
        self.class_analysis_operators = []
        self.class_analysis_lower_bounds = []
        self.class_analysis_upper_bounds = []
        self.class_analysis_selectors = []
        self.class_analysis_multiply_path_demand = []
        self.class_analysis_multiply_path_value = []
        operator_list = ["+", "-", "*", "/", "%", ".max.", ".min."]
        for i in range(len(self.demand_list)):
            self.class_analysis_attributes.append(
                [x for x in analysis_attributes[i].split(",")]
            )
            self.class_analysis_attributes_matrix.append(
                [x for x in analysis_attributes_matrix_id[i].split(",")]
            )
            self.class_analysis_operators.append(
                [x for x in self.operators[i].split(",")]
            )
            self.class_analysis_lower_bounds.append(
                [x for x in self.lower_bounds[i].split(",")]
            )
            self.class_analysis_upper_bounds.append(
                [x for x in self.upper_bounds[i].split(",")]
            )
            self.class_analysis_selectors.append(
                [x for x in self.selectors[i].split(",")]
            )
            self.class_analysis_multiply_path_demand.append(
                [x for x in self.multiply_path_demand[i].split(",")]
            )
            self.class_analysis_multiply_path_value.append(
                [x for x in self.multiply_path_value[i].split(",")]
            )
            for j in range(len(self.class_analysis_attributes[i])):
                if self.class_analysis_attributes[i][j] == "":
                    self.class_analysis_attributes[i][
                        j
                    ] = None  # make the blank attributes None for better use in spec
                if (
                    self.class_analysis_attributes_matrix[i][j] == "mf0"
                    or self.class_analysis_attributes_matrix[i][j] == ""
                ):
                    self.class_analysis_attributes_matrix[i][
                        j
                    ] = None  # make mf0 matrices None for better use in spec
                try:
                    self.class_analysis_lower_bounds[i][j] = float(
                        self.class_analysis_lower_bounds[i][j]
                    )
                    self.class_analysis_upper_bounds[i][j] = float(
                        self.class_analysis_upper_bounds[i][j]
                    )
                except:
                    if (
                        self.class_analysis_lower_bounds[i][j].lower() == "none"
                        or self.class_analysis_lower_bounds[i][j].lower() == ""
                    ):
                        self.class_analysis_lower_bounds[i][j] = None
                    else:
                        raise Exception(
                            "Lower bound not specified correct for attribute  %s"
                            % self.class_analysis_attributes[i][j]
                        )
                    if (
                        self.class_analysis_upper_bounds[i][j].lower() == "none"
                        or self.class_analysis_upper_bounds[i][j].lower() == ""
                    ):
                        self.class_analysis_upper_bounds[i][j] = None
                    else:
                        raise Exception(
                            "Upper bound not specified correct for attribute  %s"
                            % self.class_analysis_attributes[i][j]
                        )
                if self.class_analysis_selectors[i][j].lower() == "all":
                    self.class_analysis_selectors[i][j] = "ALL"
                elif self.class_analysis_selectors[i][j].lower() == "selected":
                    self.class_analysis_selectors[i][j] = "SELECTED"
                else:
                    self.class_analysis_selectors[i][j] = None
                if self.class_analysis_operators[i][j] not in operator_list:
                    if self.class_analysis_operators[i][j].lower() == "max":
                        self.class_analysis_operators[i][j] = ".max."
                    elif self.class_analysis_operators[i][j].lower() == "min":
                        self.class_analysis_operators[i][j] = ".min."
                    elif (
                        self.class_analysis_operators[i][j].lower() == "none"
                        or self.class_analysis_operators[i][j].strip(" ") == ""
                    ):
                        self.class_analysis_operators[i][j] = None
                    else:
                        raise Exception(
                            "The Path operator for the %s attribute is not specified correctly. It needs to be a binary operator"
                            % self.class_analysis_attributes[i][j]
                        )
                if (
                    str(self.class_analysis_multiply_path_demand[i][j]).lower()
                    == "true"
                ):
                    self.class_analysis_multiply_path_demand[i][j] = True
                elif (
                    str(self.class_analysis_multiply_path_demand[i][j]).lower()
                    == "false"
                ):
                    self.class_analysis_multiply_path_demand[i][j] = False
                else:
                    self.class_analysis_multiply_path_demand[i][j] = None

                if str(self.class_analysis_multiply_path_value[i][j]).lower() == "true":
                    self.class_analysis_multiply_path_value[i][j] = True
                elif (
                    str(self.class_analysis_multiply_path_value[i][j]).lower()
                    == "false"
                ):
                    self.class_analysis_multiply_path_value[i][j] = False
                else:
                    self.class_analysis_multiply_path_value[i][j] = None
        self.DemandMatrixList = []
        for i in range(0, len(self.demand_list)):
            demandMatrix = self.demand_list[i]
            if _MODELLER.emmebank.matrix(demandMatrix) is None:
                if str(demandMatrix).lower() == "mf0":
                    dm = _util.initializeMatrix(matrix_type="FULL")
                    demandMatrix = dm.id
                    print(
                        "Assigning a Zero Demand matrix for class '%s' on scenario %d"
                        % (str(self.class_names[i]), int(self.scenario.number))
                    )
                    self.demand_list[i] = dm.id
                    self.DemandMatrixList.append(
                        _MODELLER.emmebank.matrix(demandMatrix)
                    )
                else:
                    raise Exception("Matrix %s was not found!" % demandMatrix)
            else:
                self.DemandMatrixList.append(_MODELLER.emmebank.matrix(demandMatrix))

        # ---2. Pass in remaining args
        self.peak_hour_factor = peak_hour_factor
        self.iterations = iterations
        self.r_gap = r_gap
        self.br_gap = br_gap
        self.norm_gap = norm_gap
        self.run_title = run_title[:25]
        if str(background_transit).lower() == "true":
            self.BackgroundTransit = True
        else:
            self.BackgroundTransit = False

    # ----CONTEXT MANAGERS---------------------------------------------------------------------------------
    """
    Context managers for temporary database modifications.
    """

    @contextmanager
    def _AoNScenarioMANAGER(self):
        # Code here is executed upon entry

        tempScenarioNumber = _util.getAvailableScenarioNumber()

        if tempScenarioNumber is None:
            raise Exception("No additional scenarios are available!")

        scenario = _MODELLER.emmebank.copy_scenario(
            self.scenario.id,
            tempScenarioNumber,
            copy_path_files=False,
            copy_strat_files=False,
            copy_db_files=False,
        )
        scenario.title = "All-or-nothing assignment"

        _m.logbook_write(
            "Created temporary Scenario %s for all-or-nothing assignment."
            % tempScenarioNumber
        )

        try:
            yield scenario
            # Code here is executed upon clean exit
        finally:
            # Code here is executed in all cases.
            _MODELLER.emmebank.delete_scenario(tempScenarioNumber)
            _m.logbook_write("Deleted temporary Scenario %s" % tempScenarioNumber)

    @contextmanager
    def _timeAttributeMANAGER(self):
        # Code here is executed upon entry
        timeAttributes = []
        attributes = {}
        for i in range(len(self.demand_list)):
            attributeCreated = False
            at = "@ltime" + str(i + 1)
            timeAttribute = self.scenario.extra_attribute(at)
            if timeAttribute is None:
                # @ltime hasn't been defined
                _m.logbook_write(
                    "Creating temporary link cost attribute '@ltime" + str(i + 1) + "'."
                )
                timeAttribute = self.scenario.create_extra_attribute(
                    "LINK", at, default_value=0
                )
                timeAttributes.append(timeAttribute)
                attributeCreated = True
                attributes[timeAttribute.id] = attributeCreated
            elif self.scenario.extra_attribute(at).type != "LINK":
                # for some reason '@ltime' exists, but is not a link attribute
                _m.logbook_write(
                    "Creating temporary link cost attribute '@ltim" + str(i + 2) + "'."
                )
                at = "@ltim" + str(i + 2)
                timeAttribute = self.scenario.create_extra_attribute(
                    "LINK", at, default_value=0
                )
                timeAttributes.append(timeAttribute)
                attributeCreated = True
                attributes[timeAttribute.id] = attributeCreated

            if not attributeCreated:
                timeAttribute.initialize()
                timeAttributes.append(timeAttribute)
                attributes[timeAttribute.id] = attributeCreated
                _m.logbook_write("Initialized link cost attribute to 0.")

        try:
            yield timeAttributes
            # Code here is executed upon clean exit
        finally:
            # Code here is executed in all cases.
            for key in attributes:
                if attributes[key] is True:
                    _m.logbook_write("Deleting temporary link cost attribute.")
                    self.scenario.delete_extra_attribute(key)
                    # Delete the extra cost attribute only if it didn't exist before.

    @contextmanager
    def _costAttributeMANAGER(self):
        # Code here is executed upon entry
        costAttributes = []
        attributes = {}
        for i in range(len(self.demand_list)):
            attributeCreated = False
            at = "@lkcst" + str(i + 1)
            costAttribute = self.scenario.extra_attribute(at)
            if costAttribute is None:
                # @lkcst hasn't been defined
                _m.logbook_write(
                    "Creating temporary link cost attribute '@lkcst" + str(i + 1) + "'."
                )
                costAttribute = self.scenario.create_extra_attribute(
                    "LINK", at, default_value=0
                )
                costAttributes.append(costAttribute)
                attributeCreated = True
                attributes[costAttribute.id] = attributeCreated

            elif self.scenario.extra_attribute(at).type != "LINK":
                # for some reason '@lkcst' exists, but is not a link attribute
                _m.logbook_write(
                    "Creating temporary link cost attribute '@lcost" + str(i + 2) + "'."
                )
                at = "@lcost" + str(i + 2)
                costAttribute = self.scenario.create_extra_attribute(
                    "LINK", at, default_value=0
                )
                costAttributes.append(costAttribute)
                attributeCreated = True
                attributes[costAttribute.id] = attributeCreated

            if not attributeCreated:
                costAttribute.initialize()
                costAttributes.append(costAttribute)
                attributes[costAttribute.id] = attributeCreated
                _m.logbook_write("Initialized link cost attribute to 0.")

        try:
            yield costAttributes
            # Code here is executed upon clean exit
        finally:
            # Code here is executed in all cases.
            for key in attributes:
                if attributes[key] is True:
                    _m.logbook_write("Deleting temporary link cost attribute.")
                    self.scenario.delete_extra_attribute(key)
                    # Delete the extra cost attribute only if it didn't exist before.

    @contextmanager
    def _transitTrafficAttributeMANAGER(self):

        attributeCreated = False
        bgTrafficAttribute = self.scenario.extra_attribute("@tvph")

        if bgTrafficAttribute is None:
            bgTrafficAttribute = self.scenario.create_extra_attribute(
                "LINK", "@tvph", 0
            )
            attributeCreated = True
            _m.logbook_write("Created extra attribute '@tvph'")
        else:
            bgTrafficAttribute.initialize(0)
            _m.logbook_write("Initialized existing extra attribute '@tvph' to 0.")

        if EMME_VERSION >= 4:
            extraParameterTool = _MODELLER.tool(
                "inro.emme.traffic_assignment.set_extra_function_parameters"
            )
        else:
            extraParameterTool = _MODELLER.tool(
                "inro.emme.standard.traffic_assignment.set_extra_function_parameters"
            )
        if self.BackgroundTransit is True:
            extraParameterTool(el1="@tvph")

        try:
            yield
        finally:
            if attributeCreated:
                self.scenario.delete_extra_attribute("@tvph")
                _m.logbook_write("Deleted extra attribute '@tvph'")
            extraParameterTool(el1="0")

    # ----SUB FUNCTIONS---------------------------------------------------------------------------------

    def _getAtts(self):
        atts = {
            "Run Title": self.run_title,
            "Scenario": str(self.scenario.id),
            "Times Matrix": str(self.times_matrix_id),
            "Peak Hour Factor": str(self.peak_hour_factor),
            "Link Cost": str(self.link_cost),
            "iterations": str(self.iterations),
            "self": self.__MODELLER_NAMESPACE__,
        }

        return atts

    def _getTransitBGSpec(self):
        return {
            "result": "@tvph",
            "expression": "(60 / hdw) * (vauteq) * (ttf >= 3)",
            "aggregation": "+",
            "selections": {"link": "all", "transit_line": "all"},
            "type": "NETWORK_CALCULATION",
        }

    @contextmanager
    def _initOutputMatrices(self):
        with _m.logbook_trace("Initializing output matrices:"):
            created = [False] * len(self.demand_list)
            for i in range(len(self.demand_list)):
                if self.cost_matrix_id[i] == "mf0":
                    self.cost_matrix_id[i] = None
                else:
                    _util.initializeMatrix(
                        self.cost_matrix_id[i],
                        name="acost",
                        description="AUTO COST FOR CLASS: %s" % self.class_names[i],
                    )
                if self.times_matrix_id[i] == "mf0":
                    self.times_matrix_id[i] = None
                else:
                    if self.cost_matrix_id[i] == None:
                        mtx = _util.initializeMatrix(
                            description="temp cost matrix for class %s"
                            % self.class_names[i],
                            matrix_type="FULL",
                            default=0.0,
                        )
                        self.cost_matrix_id[i] = mtx.id
                        created[i] = True
                    _util.initializeMatrix(
                        self.times_matrix_id[i],
                        name="aivtt",
                        description="AUTO TIME FOR CLASS: %s" % self.class_names[i],
                    )
                if self.tolls_matrix_id[i] == "mf0":
                    self.tolls_matrix_id[i] = None
                else:
                    _util.initializeMatrix(
                        self.tolls_matrix_id[i],
                        name="atoll",
                        description="AUTO TOLL FOR CLASS: %s" % self.class_names[i],
                    )
            for i in range(len(self.class_analysis_attributes_matrix)):
                for j in range(len(self.class_analysis_attributes_matrix[i])):
                    if self.class_analysis_attributes_matrix[i][j] is not None:
                        _util.initializeMatrix(
                            self.class_analysis_attributes_matrix[i][j],
                            name=self.class_analysis_attributes[i][j],
                            description="Aggregate Attribute %s Matrix"
                            % self.class_analysis_attributes[i][j],
                        )
        try:
            yield self.cost_matrix_id
        finally:
            for i in range(0, len(created)):
                if created[i] == True:
                    _MODELLER.emmebank.delete_matrix(self.cost_matrix_id[i])

    def _getLinkCostCalcSpec(
        self, costAttributeId, link_cost, link_toll_attribute_id, perception
    ):
        return {
            "result": costAttributeId,
            "expression": "(length * %f + %s)*%f"
            % (link_cost, link_toll_attribute_id, perception),
            "aggregation": None,
            "selections": {"link": "all"},
            "type": "NETWORK_CALCULATION",
        }

    def _getPeakHourSpec(
        self, peak_hour_matrix_id, demand_matrix_id
    ):  # Was passed the matrix id VALUE, but here it uses it as a parameter
        return {
            "expression": demand_matrix_id + "*" + str(self.peak_hour_factor),
            "result": peak_hour_matrix_id,
            "constraint": {"by_value": None, "by_zone": None},
            "aggregation": {"origins": None, "destinations": None},
            "type": "MATRIX_CALCULATION",
        }

    def _calculateAppliedTollFactor(self):
        applied_toll_factor = []
        if self.toll_weight is not None:
            for i in range(0, len(self.toll_weight)):
                # Toll weight is in $/hr, needs to be converted to min/$
                applied_toll_factor.append(60.0 / self.toll_weight[i])
        return applied_toll_factor

    def _getSaveAutoTimesSpec(self, timeAttribute):
        return {
            "result": timeAttribute,
            "expression": "timau",
            "aggregation": None,
            "selections": {"link": "all"},
            "type": "NETWORK_CALCULATION",
        }

    def _getPrimarySOLASpec(
        self,
        peak_hour_matrix_id,
        applied_toll_factor,
        mode_list,
        class_volume_attributes,
        costAttribute,
        attributes,
        matrices,
        operators,
        lower_bounds,
        upper_bounds,
        selectors,
        multiply_path_demand,
        multiplyPathValue,
    ):

        if self.performance_flag:
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
                "max_iterations": self.iterations,
                "relative_gap": self.r_gap,
                "best_relative_gap": self.br_gap,
                "normalized_gap": self.norm_gap,
            },
        }
        # defines the aggregator
        SOLA_path_analysis = []
        for i in range(0, len(self.demand_list)):
            if attributes[i] is None:
                SOLA_path_analysis.append(None)
            else:
                SOLA_path_analysis.append([])
                allNone = True
                for j in range(len(attributes[i])):
                    if attributes[i][j] is None:
                        continue
                    allNone = False
                    path = {
                        "link_component": attributes[i][j],
                        "turn_component": None,
                        "operator": operators[i][j],
                        "selection_threshold": {
                            "lower": lower_bounds[i][j],
                            "upper": upper_bounds[i][j],
                        },
                        "path_to_od_composition": {
                            "considered_paths": selectors[i][j],
                            "multiply_path_proportions_by": {
                                "analyzed_demand": multiply_path_demand[i][j],
                                "path_value": multiplyPathValue[i][j],
                            },
                        },
                        "results": {"od_values": matrices[i][j]},
                        "analyzed_demand": None,
                    }
                    SOLA_path_analysis[i].append(path)
                if allNone is True:
                    SOLA_path_analysis[i] = []
        # Creates a list entry for each mode specified in the Mode List and its associated Demand Matrix
        # "mf"+str(int(int(self.times_matrix_id[0][2:])+3))
        SOLA_Class_Generator = [
            {
                "mode": mode_list[i],
                "demand": peak_hour_matrix_id[i].id,
                "generalized_cost": {
                    "link_costs": costAttribute[i].id,
                    "perception_factor": 1,
                },
                "results": {
                    "link_volumes": class_volume_attributes[i],
                    "turn_volumes": None,
                    "od_travel_times": {"shortest_paths": self.times_matrix_id[i]},
                },
                "path_analyses": SOLA_path_analysis[i],
            }
            for i in range(len(mode_list))
        ]
        SOLA_spec["classes"] = SOLA_Class_Generator

        return SOLA_spec

    def _CorrectTimesMatrixSpec(self, time_matrix, cost_matrix):
        spec = {
            "expression": "%s-%s" % (time_matrix, cost_matrix),
            "result": "%s" % time_matrix,
            "constraint": {"by_value": None, "by_zone": None},
            "aggregation": {"origins": None, "destinations": None},
            "type": "MATRIX_CALCULATION",
        }
        return spec

    def _CorrectCostMatrixSpec(self, cost_matrix, perception):
        spec = {
            "expression": "%s/%f" % (cost_matrix, perception),
            "result": "%s" % cost_matrix,
            "constraint": {"by_value": None, "by_zone": None},
            "aggregation": {"origins": None, "destinations": None},
            "type": "MATRIX_CALCULATION",
        }
        return spec

    def _modifyFunctionForAoNAssignment(self):
        allOrNothingFunc = _MODELLER.emmebank.function("fd98")
        if allOrNothingFunc is None:
            allOrNothingFunc = _MODELLER.emmebank.create_function("fd98", "ul2")
        else:
            allOrNothingFunc.expression = "ul2"

    def _getChangeLinkVDFto98Spec(self):
        return {
            "result": "vdf",
            "expression": "98",
            "aggregation": None,
            "selections": {"link": "all"},
            "type": "NETWORK_CALCULATION",
        }

    @_m.method(return_type=_m.TupleType)
    def percent_completed(self):
        return self._tracker.getProgress()

    @_m.method(return_type=str)
    def tool_run_msg_status(self):
        return self.tool_run_msg

    @_m.method(return_type=str)
    def _GetSelectAttributeOptionsHTML(self):
        list = []

        for att in self.scenario.extra_attributes():
            if not att.type == "LINK":
                continue
            label = "{id} ({domain}) - {name}".format(
                id=att.name, domain=att.type, name=att.description
            )
            html = str(
                '<option value="{id}">{text}</option>'.format(id=att.name, text=label)
            )
            list.append(html)
        return "\n".join(list)
