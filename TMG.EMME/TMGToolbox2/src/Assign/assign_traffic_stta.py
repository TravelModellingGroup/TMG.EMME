# ---LICENSE----------------------
"""
    Copyright 2023 Travel Modelling Group, Department of Civil Engineering, University of Toronto

    This file is part of TMG.EMME for XTMF2.

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
    Frist version by: WilliamsDiogu
"""
import inro.modeller as _m
import multiprocessing

_m.InstanceType = object
_m.ListType = list
_m.TupleType = object

_trace = _m.logbook_trace
_MODELLER = _m.Modeller()
_bank = _MODELLER.emmebank
_write = _m.logbook_write
_util = _MODELLER.module("tmg2.utilities.general_utilities")
EMME_VERSION = _util.get_emme_version(tuple)


class AssignTrafficSTTA(_m.Tool()):
    version = "1.0.0"
    tool_run_msg = ""
    number_of_tasks = 5
    parameters = _m.Attribute(str)
    number_of_processors = _m.Attribute(int)

    def __init__(self):
        self._tracker = _util.progress_tracker(self.number_of_tasks)
        self.scenario = _MODELLER.scenario
        self.number_of_processors = multiprocessing.cpu_count()
        self._traffic_util = _util.assign_traffic_util()

    def page(self):
        pb = _m.ToolPageBuilder(
            self,
            title="Multi-Class Road Assignment with STTA",
            description="Cannot be called from Modeller.",
            runnable=False,
            branding_text="XTMF",
        )
        return pb.render()

    def __call__(self, parameters):
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
        """
        matrix_indices_used_list keeps track of all the matrices already created/used
        """
        matrix_indices_used_list = []
        #   create all time dependent matrix dictionary
        for tc in parameters["traffic_classes"]:
            all_matrix_dict = self._create_time_dependent_matrix_dict(
                matrix_indices_used_list,
                parameters["interval_lengths"],
                tc["demand_matrix_number"],
                "demand_matrix",
                [("cost_matrix", tc["cost_matrix_number"]), ("time_matrix", tc["time_matrix_number"])],
            )
        #   load all time dependent output matrices
        load_input_matrix_list = self._load_input_matrices(all_matrix_dict, "demand_matrix")
        load_output_matrix_dict = self._load_output_matrices(all_matrix_dict, ["cost_matrix", "time_matrix"])
        # #   create list of time dependent input attribute
        with _trace(
            name="%s (%s v%s)" % (parameters["run_title"], self.__class__.__name__, self.version),
            attributes=self._load_atts(scenario, parameters["run_title"], parameters["iterations"], parameters["traffic_classes"], self.__MODELLER_NAMESPACE__),
        ):
            self._tracker.reset()
            with _util.temporary_matrix_manager() as temp_matrix_list:
                demand_matrix_list = self._init_input_matrices(load_input_matrix_list, temp_matrix_list)
                cost_matrix_list = self._init_output_matrices(load_output_matrix_dict, temp_matrix_list, matrix_name="cost_matrix", description="")
                time_matrix_list = self._init_output_matrices(load_output_matrix_dict, temp_matrix_list, matrix_name="time_matrix", description="")
                with _util.temporary_attribute_manager(scenario) as temp_attribute_list:
                    for tc in parameters["traffic_classes"]:
                        time_dependent_volume_attribute_list = self._create_time_dependent_attribute_list(tc["volume_attribute"], parameters["interval_lengths"], tc["attribute_start_index"])
                        self._create_volume_attribute(scenario, time_dependent_volume_attribute_list)
                    time_dependent_component_attribute_list = self._create_time_dependent_attribute_list(parameters["link_component_attribute"], parameters["interval_lengths"], parameters["start_index"])
                    transit_attribute_list = self._create_transit_traffic_attribute_list(scenario, time_dependent_component_attribute_list, temp_attribute_list)

    def _load_atts(self, scenario, run_title, iterations, traffic_classes, modeller_namespace):
        time_matrix_ids = ["mf" + str(mtx["time_matrix_number"]) for mtx in traffic_classes]
        link_costs = [str(lc["link_cost"]) for lc in traffic_classes]
        atts = {"Run Title": run_title, "Scenario": str(scenario.id), "Times Matrix": str(", ".join(time_matrix_ids)), "Link Cost": str(", ".join(link_costs)), "Iterations": str(iterations), "self": modeller_namespace}
        return atts

    def _create_time_dependent_attribute_list(self, attribute_name, interval_lengths_list, attribute_start_index):
        def check_att_name(at):
            if at.startswith("@"):
                return at
            else:
                return "@" + at

        time_dependent_attribute_list = [check_att_name(attribute_name) + str(attribute_start_index + i) for i, j in enumerate(interval_lengths_list)]
        return time_dependent_attribute_list

    def _create_time_dependent_matrix_dict(self, matrix_indices_used_list, interval_lengths_list, input_matrix_number, input_matrix_name, output_matrix_name_list):
        """
        creates all time dependent input and output matrix in a dictionary.
        Matrix index depends on the input matrix. For example, if time dependent
        input matrix ends starts from mf1 to mf4 all other matrices begin from mf5 and so on.
        """
        all_matrix_dict = {}
        # add all matrix names to be created to dict
        all_matrix_dict[input_matrix_name] = ""
        for i in range(0, len(output_matrix_name_list)):
            all_matrix_dict[output_matrix_name_list[i][0]] = ""
        #   add input matrix list
        input_matrix_list = []
        for i, j in enumerate(interval_lengths_list):
            if input_matrix_number == 0:
                input_matrix_list.append("mf0")
            else:
                input_matrix_list.append("mf" + str(input_matrix_number + i))
                matrix_indices_used_list.append(input_matrix_number + i)
        all_matrix_dict[input_matrix_name] = input_matrix_list
        for output_matrix in output_matrix_name_list:
            matrix_name = output_matrix[0]
            matrix_number = output_matrix[1]
            output_matrix_list = []
            for j in range(0, len(interval_lengths_list)):
                if matrix_number == 0:
                    output_matrix_list.append("mf0")
                else:
                    output_matrix_list.append("mf" + str(output_matrix[1] + j))
                    matrix_indices_used_list.append(matrix_number + j)
            all_matrix_dict[matrix_name] = output_matrix_list
        return all_matrix_dict

    def _load_input_matrices(self, all_matrix_dict, input_matrix_name):
        """
        Load input matrices creates and returns a list of (input) matrices based on matrix_name supplied.
        E.g of matrix_name: "demand_matrix", matrix_id: "mf2"
        """

        def exception(mtx_id):
            raise Exception("Matrix %s was not found!" % mtx_id)

        input_matrix_list = [_bank.matrix(mtx) if mtx == "mf0" or self._get_or_create(mtx).id == mtx else exception(mtx) for mtx in all_matrix_dict[input_matrix_name]]

        return input_matrix_list

    def _load_output_matrices(self, all_matrix_dict, matrix_name_list):
        output_matrix_dict = {}
        for matrix_name in matrix_name_list:
            matrix = [None if matrix_number == "mf0" else self._get_or_create(matrix_number) for matrix_number in all_matrix_dict[matrix_name]]
            output_matrix_dict[matrix_name] = matrix
        return output_matrix_dict

    def _get_or_create(self, matrix_id):
        mtx = _bank.matrix(matrix_id)
        if mtx is None:
            mtx = _bank.create_matrix(matrix_id, default_value=0)
        return mtx

    def _init_input_matrices(self, load_input_matrix_list, temp_matrix_list):
        """
        - Checks the list of all load matrices in load_input_matrix_list,
            for None, create a temporary matrix and initialize
        - Returns a list of all input matrices provided
        """
        input_matrix_list = []
        for mtx in load_input_matrix_list:
            if mtx == None:
                mtx = _util.initialize_matrix(matrix_type="FULL")
                temp_matrix_list.append(mtx)
            input_matrix_list.append(mtx)
        return input_matrix_list

    def _init_output_matrices(self, load_output_matrix_dict, temp_matrix_list, matrix_name="", description=""):
        """
        - Checks the dictionary of all load matrices in load_output_matrix_dict,
            for None, create a temporary matrix and initialize
        - Returns a list of all input matrices provided
        """
        output_matrix_list = []
        desc = "AUTO %s FOR CLASS" % (matrix_name.upper())
        if matrix_name in load_output_matrix_dict.keys():
            for mtx in load_output_matrix_dict[matrix_name]:
                if mtx == None:
                    matrix = _util.initialize_matrix(
                        name=matrix_name,
                        description=description if description != "" else desc,
                    )
                    temp_matrix_list.append(matrix)
                output_matrix_list.append(mtx)
        else:
            raise Exception('Output matrix name "%s" provided does not exist', matrix_name)
        return output_matrix_list

    def _create_volume_attribute(self, scenario, volume_attribute_list):
        for volume_attribute in volume_attribute_list:
            volume_attribute_at = scenario.extra_attribute(volume_attribute)
            if volume_attribute_at is not None:
                if volume_attribute_at.type != "LINK":
                    raise Exception("Volume Attribute '%s' is not a link type attribute" % volume_attribute)
                scenario.delete_extra_attribute(volume_attribute_at)
            scenario.create_extra_attribute("LINK", volume_attribute, default_value=0)

    def _create_transit_traffic_attribute_list(self, scenario, link_component_attribute_list, temp_attribute_list):
        transit_traffic_attribute_list = []
        for transit_traffic_att in link_component_attribute_list:
            t_traffic_attribute = self._create_temp_attribute(scenario, transit_traffic_att, "LINK", default_value=0.0, assignment_type="traffic")
            temp_attribute_list.append(t_traffic_attribute)
            transit_traffic_attribute_list.append(t_traffic_attribute)
        return transit_traffic_attribute_list

    def _create_temp_attribute(self, scenario, attribute_id, attribute_type, description=None, default_value=0.0, assignment_type=None):
        """
        Creates a temporary extra attribute in a given scenario
        """
        ATTRIBUTE_TYPES = ["NODE", "LINK", "TURN", "TRANSIT_LINE", "TRANSIT_SEGMENT"]
        attribute_type = str(attribute_type).upper()
        # check if the type provided is correct
        if attribute_type not in ATTRIBUTE_TYPES:
            raise TypeError("Attribute type '%s' provided is not recognized." % attribute_type)

        if len(attribute_id) > 18:
            raise ValueError("Attribute id '%s' can only be 19 characters long with no spaces plus no '@'." % attribute_id)
        prefix = str(attribute_id)
        attrib_id = ""
        if assignment_type == "transit":
            temp_extra_attribute = self._process_transit_attribute(scenario, prefix, attribute_type, default_value)
        elif assignment_type == "traffic":
            temp_extra_attribute = self._process_traffic_attribute(scenario, prefix, attribute_type, default_value)
        else:
            raise Exception("Attribute type is 'None' or 'invalid'." "Type can only be either 'transit' or 'traffic'.")
        attrib_id = temp_extra_attribute[1]
        msg = "Created temporary extra attribute %s in scenario %s" % (
            attrib_id,
            scenario.id,
        )
        if description:
            temp_extra_attribute[0].description = description
            msg += ": %s" % description
        _m.logbook_write(msg)
        return temp_extra_attribute[0]

    def _process_transit_attribute(self, scenario, transit_attrib_id, attribute_type, default_value):
        if not transit_attrib_id.startswith("@"):
            transit_attrib_id = "@" + transit_attrib_id
        checked_extra_attribute = scenario.extra_attribute(transit_attrib_id)
        if checked_extra_attribute is None:
            temp_transit_attrib = scenario.create_extra_attribute(attribute_type, transit_attrib_id, default_value)
        elif checked_extra_attribute != None and checked_extra_attribute.type != attribute_type:
            raise Exception("Attribute %s already exist or has some issues!" % transit_attrib_id)
        else:
            temp_transit_attrib = scenario.extra_attribute(transit_attrib_id)
            temp_transit_attrib.initialize(default_value)
        return temp_transit_attrib, transit_attrib_id

    def _process_traffic_attribute(self, scenario, traffic_attrib_id, attribute_type, default_value):
        if not traffic_attrib_id.startswith("@"):
            traffic_attrib_id = "@%s" % (traffic_attrib_id)
        if scenario.extra_attribute(traffic_attrib_id) is None:
            temp_traffic_attrib = scenario.create_extra_attribute(attribute_type, traffic_attrib_id, default_value)
            _m.logbook_write(
                "Created extra attribute '%s'",
            )
        else:
            temp_traffic_attrib = scenario.extra_attribute(temp_traffic_attrib)
            temp_traffic_attrib.initialize(0)
        return temp_traffic_attrib, traffic_attrib_id

    @_m.method(return_type=_m.TupleType)
    def percent_completed(self):
        return self._tracker.get_progress()

    @_m.method(return_type=str)
    def tool_run_msg_status(self):
        return self.tool_run_msg
