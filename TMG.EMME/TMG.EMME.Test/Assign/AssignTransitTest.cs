﻿/*
    Copyright 2021 University of Toronto

    This file is part of TMG.EMME for XTMF2.

    TMG.EMME for XTMF2 is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    TMG.EMME for XTMF2 is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with TMG.EMME for XTMF2.  If not, see <http://www.gnu.org/licenses/>.
*/

using Microsoft.VisualStudio.TestTools.UnitTesting;
using System;
using System.Collections.Generic;
using System.Text;
using System.IO;
using XTMF2;

namespace TMG.Emme.Test.Assign
{
    [TestClass]
    public class AssignTransitTest : TestBase
    {
        [TestMethod]
        public void AssignTransit()
        {
            Helper.ImportFrabitztownNetwork(1);
            Helper.ImportBinaryMatrix(1, 10, Path.GetFullPath("TestFiles/Test.mtx"));
            Assert.IsTrue(
                Helper.Modeller.Run(null, "tmg2.Assign.assign_transit",
                JSONParameterBuilder.BuildParameters(writer =>
                {
                    writer.WriteBoolean("calculate_congested_ivtt_flag", true);
                    writer.WriteNumber("node_logit_scale", 0.0f);
                    writer.WriteString("effective_headway_attribute_id", "@ehdw");
                    writer.WriteNumber("effective_headway_slope", 0.0f);
                    writer.WriteString("headway_fraction_attribute_id", "@frac");
                    writer.WriteNumber("iterations", 100);
                    writer.WriteNumber("norm_gap", 0.0f);
                    writer.WriteNumber("rel_gap", 0.0f);
                    writer.WriteNumber("scenario_number", 0);
                    writer.WriteNumber("walk_speed", 0.0f);
                    writer.WriteStartArray("transit_classes");
                    writer.WriteStartObject();
                    writer.WriteString("board_penalty_matrix", "mf0");
                    writer.WriteNumber("board_penalty_perception", 0.0f);
                    writer.WriteString("congestion_matrix", "mf0");
                    writer.WriteString("demand_matrix", "mf0");
                    writer.WriteString("fare_matrix", "mf0");
                    writer.WriteNumber("fare_perception", 0.0f);
                    writer.WriteString("in_vehicle_time_matrix", "mf0");
                    writer.WriteString("link_fare_attribute_id", "@lfare");
                    writer.WriteString("mode", "*");
                    writer.WriteString("perceived_travel_time_matrix", "mf0");
                    writer.WriteString("segment_fare_attribute_id", "@sfare");
                    writer.WriteNumber("wait_time_perception", 0.0f);
                    writer.WriteString("wait_time_matrix", "mf0");
                    writer.WriteString("walk_time_perception_attribute_id", "@walkp");
                    writer.WriteString("walk_time_matrix", "mf0");
                    writer.WriteStartArray("walk_perceptions");
                    writer.WriteStartObject();
                    writer.WriteString("filter", "i=10000");
                    writer.WriteNumber("walk_perception_value", 1);
                    writer.WriteEndObject();
                    writer.WriteEndArray();
                    writer.WriteEndObject();
                    writer.WriteEndArray();
                    writer.WriteString("impedance_matrix", "");
                    writer.WriteString("congestion_exponent", "");
                    writer.WriteNumber("assignment_period", 0.0f);
                    writer.WriteString("name_string", "");
                    writer.WriteString("congested_assignment", "");
                    writer.WriteString("csvfile", "");
                    writer.WriteNumber("origin_distribution_logit_scale", 0.0f);
                    writer.WriteNumber("walk_distribution_logit_scale", 0.0f);
                    writer.WriteString("surface_transit_speed", "");
                    writer.WriteString("walk_all_way_flag", "");
                    writer.WriteString("xrow_ttf_range", "");                  

                }), LogbookLevel.Standard));

        }
        [TestMethod]
        public void AssignTransitModule()
        {
            var module = new Emme.Assign.AssignTransit()
            {
                


            };
            module.Invoke(Helper.Modeller);

        }
    }
}
