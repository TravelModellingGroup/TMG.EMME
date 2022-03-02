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


import inro.modeller as _m
import traceback as _traceback
import math

_MODELLER = _m.Modeller()  # Instantiate Modeller once.
_util = _MODELLER.module("tmg2.utilities.general_utilities")
_tmgTPB = _MODELLER.module("tmg2.utilities.TMG_tool_page_builder")
_geom = _MODELLER.module("tmg2.utilities.geometry")

_m.InstanceType = object
_m.TupleType = object
_m.ListType = list


class RotateNetwork(_m.Tool()):
    version = "0.1.0"
    tool_run_msg = ""
    number_of_tasks = (
        6  # For progress reporting, enter the integer number of tasks here
    )
    # Tool Input Parameters
    #    Only those parameters neccessary for Modeller and/or XTMF to dock with
    #    need to be placed here. Internal parameters (such as lists and dicts)
    #    get intitialized during construction (__init__)
    scenario = _m.Attribute(_m.InstanceType)  # common varialbe or parameter
    ReferenceLinkINode = _m.Attribute(int)
    ReferenceLinkJNode = _m.Attribute(int)
    CorrespondingX0 = _m.Attribute(float)
    CorrespondingX1 = _m.Attribute(float)
    CorrespondingY0 = _m.Attribute(float)
    CorrespondingY1 = _m.Attribute(float)

    def __init__(self):
        # -- Init internal varaiables
        self.TRACKER = _util.progress_tracker(
            self.number_of_tasks
        )  # init the progress_tracker

        # --Set the defaults of parameters used by Modeller
        self.scenario = _MODELLER.scenario  # Default is primary scenario

    def page(self):
        pb = _tmgTPB.TmgToolPageBuilder(
            self,
            title="Rotate Network v%s" % self.version,
            description="Rotates & translates network based on two corresponding links.\
                         Select the node ids of a link in the network you want to rotate and \
                         translate, and then enter in the coordinates of the exact same link \
                         in your reference network.\
                         <br><br>Warning: this tool makes irreversible changes to your scenario! \
                         make sure you copy before running.",
            branding_text="- TMG Toolbox",
        )

        if self.tool_run_msg != "":  # to display messages in the page
            pb.tool_run_status(self.tool_run_msg_status)

        pb.add_select_scenario(
            tool_attribute_name="Scenario", title="Scenario:", allow_none=False
        )

        pb.add_text_box(
            tool_attribute_name="ReferenceLinkINode",
            size=7,
            title="Reference link i-node",
        )

        pb.add_text_box(
            tool_attribute_name="ReferenceLinkJNode",
            size=7,
            title="Reference link j-node",
        )

        with pb.add_table(visible_border=False, title="Corresponding vector") as t:
            with t.table_cell():
                pb.add_html("Coordinate 0: ")

            with t.table_cell():
                pb.add_html("X=")

            with t.table_cell():
                pb.add_text_box(tool_attribute_name="CorrespondingX0", size=10)

            with t.table_cell():
                pb.add_html("Y=")

            with t.table_cell():
                pb.add_text_box(tool_attribute_name="CorrespondingY0", size=10)

            t.new_row()

            with t.table_cell():
                pb.add_html("Coordinate 1: ")

            with t.table_cell():
                pb.add_html("X=")

            with t.table_cell():
                pb.add_text_box(tool_attribute_name="CorrespondingX1", size=10)

            with t.table_cell():
                pb.add_html("Y=")

            with t.table_cell():
                pb.add_text_box(tool_attribute_name="CorrespondingY1", size=10)

        return pb.render()

    def run(self):
        self.tool_run_msg = ""
        self.TRACKER.reset()

        try:
            self._execute()
        except Exception as e:
            self.tool_run_msg = _m.PageBuilder.format_exception(
                e, _traceback.format_exc()
            )
            raise
        self.tool_run_msg = _m.PageBuilder.format_info("Done.")

    def run_xtmf(self, parameters):
        self.scenario_number = parameters["scenario_number"]
        self.ReferenceLinkINode = parameters["reference_link_i_node"]
        self.ReferenceLinkJNode = parameters["reference_link_j_node"]
        self.CorrespondingX0 = parameters["corresponding_x_0"]
        self.CorrespondingY0 = parameters["corresponding_y_0"]
        self.CorrespondingX1 = parameters["corresponding_x_1"]
        self.CorrespondingY1 = parameters["corresponding_y_1"]

        self.scenario = _m.Modeller().emmebank.scenario(self.scenario_number)
        try:
            self._execute()
        except Exception as e:
            self.tool_run_msg = _m.PageBuilder.format_exception(
                e, _traceback.format_exc()
            )
            raise
        self.tool_run_msg = _m.PageBuilder.format_info("Done.")

    def _execute(self):
        with _m.logbook_trace(
            name="{classname} v{version}".format(
                classname=(self.__class__.__name__), version=self.version
            ),
            attributes=self._GetAtts(),
        ):
            network = self.scenario.get_network()
            self.TRACKER.complete_task()

            anchorVector = (
                (self.CorrespondingX0, self.CorrespondingY0),
                (self.CorrespondingX1, self.CorrespondingY1),
            )

            refLink = self._GetRefLink(network)
            referenceVector = self._GetLinkVector(refLink)
            _m.logbook_write(
                "Found reference link '%s-%s'"
                % (self.ReferenceLinkINode, self.ReferenceLinkJNode)
            )

            angle = self._GetRotationAngle(
                anchorVector, referenceVector
            )  # + math.pi / 2
            _m.logbook_write("Rotation: %s degrees" % math.degrees(angle))
            cosTheta = math.cos(angle)
            sinTheta = math.sin(angle)

            self.TRACKER.start_process(
                network.element_totals["centroids"]
                + network.element_totals["regular_nodes"]
            )
            for node in network.nodes():
                self._RotateNode(node, cosTheta, sinTheta)
                self.TRACKER.complete_subtask()
            self.TRACKER.complete_task()
            _m.logbook_write("Finished rotating nodes.")

            self.TRACKER.start_process(network.element_totals["links"])
            count = 0
            for link in network.links():
                if len(link.vertices) > 0:
                    self._RotateLinkVertices(link, cosTheta, sinTheta)
                    count += 1
                self.TRACKER.complete_task()
            self.TRACKER.complete_task()
            _m.logbook_write("Rotated %s links with vertices." % count)

            referenceVector = self._GetLinkVector(refLink)  # Reset the reference vector
            delta = self._GetTranslation(referenceVector, anchorVector)
            _m.logbook_write("Translation: %s" % str(delta))

            self.TRACKER.start_process(
                network.element_totals["centroids"]
                + network.element_totals["regular_nodes"]
            )
            for node in network.nodes():
                self._TranslateNode(node, delta)
                self.TRACKER.complete_subtask()
            self.TRACKER.complete_task()
            _m.logbook_write("Finished translating nodes.")

            self.TRACKER.start_process(network.element_totals["links"])
            count = 0
            for link in network.links():
                if len(link.vertices) > 0:
                    self._TranslateLink(link, delta)
                    count += 1
            self.TRACKER.complete_task()
            _m.logbook_write("Translated %s links with vertices." % count)

            self.scenario.publish_network(network, resolve_attributes=True)
            self.TRACKER.complete_task()

    # ---SUB FUNCTION------------------------------------------------

    def _GetAtts(self):
        atts = {
            "Scenario": str(self.scenario.id),
            "Version": self.version,
            "self": self.__MODELLER_NAMESPACE__,
        }

        return atts

    def _GetRefLink(self, network):
        link = network.link(self.ReferenceLinkINode, self.ReferenceLinkJNode)

        if link is None:
            raise Exception(
                "Reference link '%s-%s' does not exist in the network!"
                % (self.ReferenceLinkINode, self.ReferenceLinkJNode)
            )
        return link

    def _GetLinkVector(self, link):
        return ((link.i_node.x, link.i_node.y), (link.j_node.x, link.j_node.y))

    def _GetVectorBearing(self, vector):
        return math.atan2(vector[1][0] - vector[0][0], vector[1][1] - vector[0][1])

    def _GetRotationAngle(self, vector1, vector2):

        bearing1 = self._GetVectorBearing(vector1)
        bearing2 = self._GetVectorBearing(vector2)

        return bearing2 - bearing1

    def _GetTranslation(self, vector1, vector2):
        return (vector2[0][0] - vector2[0][0], vector2[0][1] - vector2[0][1])

    def _RotateNode(self, node, cosTheta, sinTheta):
        # Make copies of the coordinates
        x = node.x
        y = node.y

        node.x = (cosTheta * x) + (-sinTheta * y)
        node.y = (sinTheta * y) + (cosTheta * y)

    def _TranslateNode(self, node, delta):
        node.x += delta[0]
        node.y += delta[1]

    def _RotateLinkVertices(self, link, cosTheta, sinTheta):
        vertices = [link.vertices.pop() for i in range(0, len(link.vertices))]
        vertices.reverse()

        # Link's vertices have been removed and copied in-order to
        # this new list

        for vertex in vertices:
            tup = (
                cosTheta * vertex[0] - sinTheta * vertex[1],
                sinTheta * vertex[0] + cosTheta * vertex[1],
            )
            link.vertices.append(tup)

    def _TranslateLink(self, link, delta):
        vertices = [link.vertices.pop() for i in range(0, len(link.vertices))]
        vertices.reverse()

        # Link's vertices have been removed and copied in-order to
        # this new list

        for vertex in vertices:
            tup = (vertex[0] + delta[0], vertex[1] + delta[1])
            link.vertices.append(tup)

    @_m.method(return_type=_m.TupleType)
    def percent_completed(self):
        return self.TRACKER.get_progress()

    @_m.method(return_type=str)
    def tool_run_msg_status(self):
        return self.tool_run_msg
