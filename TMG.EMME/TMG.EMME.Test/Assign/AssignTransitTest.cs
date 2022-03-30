/*
    Copyright 2022 University of Toronto

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
            Helper.ImportFrabitztownNetwork(2);
            Helper.ImportBinaryMatrix(2, 10, Path.GetFullPath("TestFiles/Test0.25.mtx"));
            Helper.RunAssignTraffic(2, "mf0");
            Helper.RunAssignBoardingPenalty(new[] { 2 });
            Assert.IsTrue(
                Helper.Modeller.Run(null, "tmg2.Assign.assign_transit",
                JSONParameterBuilder.BuildParameters(writer =>
                {
                    writer.WriteBoolean("calculate_congested_ivtt_flag", true);
                    writer.WriteBoolean("node_logit_scale", true);
                    writer.WriteString("effective_headway_attribute", "@ehdw");
                    writer.WriteNumber("effective_headway_slope", 0.165f);
                    writer.WriteString("headway_fraction_attribute", "@frac");
                    writer.WriteNumber("iterations", 5);
                    writer.WriteNumber("norm_gap", 0.0f);
                    writer.WriteNumber("rel_gap", 0.0f);
                    writer.WriteNumber("scenario_number", 2);
                    writer.WriteNumber("walk_speed", 4.0f);
                    writer.WriteStartArray("transit_classes");
                    writer.WriteStartObject();
                    writer.WriteString("name", "transit_class_1");
                    writer.WriteString("board_penalty_matrix", "mf0");
                    writer.WriteNumber("board_penalty_perception", 1.0f);
                    writer.WriteString("congestion_matrix", "mf0");
                    writer.WriteString("demand_matrix", "mf10");
                    writer.WriteString("fare_matrix", "mf0");
                    writer.WriteNumber("fare_perception", 20.0f);
                    writer.WriteString("in_vehicle_time_matrix", "mf0");
                    writer.WriteString("impedance_matrix", "mf0");
                    writer.WriteString("link_fare_attribute_id", "@lfare");
                    writer.WriteString("mode", "*");
                    writer.WriteString("perceived_travel_time_matrix", "mf0");
                    writer.WriteString("segment_fare_attribute", "@sfare");
                    writer.WriteNumber("wait_time_perception", 2.3f);
                    writer.WriteString("wait_time_matrix", "mf0");
                    writer.WriteString("walk_time_perception_attribute", "@walkp");
                    writer.WriteString("walk_time_matrix", "mf0");
                    writer.WriteStartArray("walk_perceptions");
                    writer.WriteStartObject();
                    writer.WriteString("filter", "i=1,999999");
                    writer.WriteNumber("walk_perception_value", 2.0f);
                    writer.WriteEndObject();
                    writer.WriteEndArray();
                    writer.WriteEndObject();
                    writer.WriteEndArray();
                    writer.WriteStartArray("surface_transit_speeds");
                    writer.WriteStartObject();
                    writer.WriteNumber("alighting_duration", 1.1219f);
                    writer.WriteNumber("boarding_duration", 1.9577f);
                    writer.WriteNumber("default_duration", 7.4331f);
                    writer.WriteNumber("global_erow_speed", 35f);
                    writer.WriteString("line_filter_expression", "");
                    writer.WriteString("mode_filter_expression", "b");
                    writer.WriteNumber("transit_auto_correlation", 1.612f);
                    writer.WriteEndObject();
                    writer.WriteEndArray();
                    writer.WriteStartArray("ttf_definitions");
                    writer.WriteStartObject();
                    writer.WriteNumber("congestion_exponent", 5.972385f);
                    writer.WriteNumber("congestion_perception", 1);
                    writer.WriteNumber("ttf", 4);
                    writer.WriteEndObject();
                    writer.WriteStartObject();
                    writer.WriteNumber("congestion_exponent", 5.972385f);
                    writer.WriteNumber("congestion_perception", 1);
                    writer.WriteNumber("ttf", 2);
                    writer.WriteEndObject();
                    writer.WriteStartObject();
                    writer.WriteNumber("congestion_exponent", 5.972385f);
                    writer.WriteNumber("congestion_perception", 1);
                    writer.WriteNumber("ttf", 1);
                    writer.WriteEndObject();
                    writer.WriteEndArray();
                    writer.WriteString("congestion_exponent", "");
                    writer.WriteNumber("assignment_period", 3.0f);
                    writer.WriteString("name_string", "");
                    writer.WriteBoolean("congested_assignment", true);
                    writer.WriteString("csvfile", "");
                    writer.WriteNumber("origin_distribution_logit_scale", 0.0f);
                    writer.WriteNumber("walk_distribution_logit_scale", 3.0f);
                    writer.WriteBoolean("surface_transit_speed", false);
                    writer.WriteBoolean("walk_all_way_flag", false);
                    writer.WriteString("xrow_ttf_range", "");

                }), LogbookLevel.Standard));

        }
        [TestMethod]
        public void AssignTransitModule()
        {
            Helper.ImportFrabitztownNetwork(2);
            Helper.ImportBinaryMatrix(2, 10, Path.GetFullPath("TestFiles/Test0.25.mtx"));
            Helper.RunAssignTraffic(2, "mf0");

            var walkPerceptions = new[]
            {

                new Emme.Assign.AssignTransit.WalkPerceptions()
                {
                    Name = "WalkPerceptions",
                    Filter = Helper.CreateParameter("i=10000,20000 or j=10000,20000 or i=97000,98000 or j=97000,98000"),
                    WalkPerceptionValue = Helper.CreateParameter(1.8f),
                }
            };

            var transitClasses = new[]
            {
                new Emme.Assign.AssignTransit.TransitClass()
                {
                    Name = "TransitClass1",
                    BoardPenaltyMatrix = Helper.CreateParameter("mf0"),
                    BoardingPenaltyPerception = Helper.CreateParameter(1.0f),
                    CongestionMatrix = Helper.CreateParameter("mf0"),
                    DemandMatrix = Helper.CreateParameter("mf10"),
                    FareMatrix = Helper.CreateParameter("mf0"),
                    FarePerception = Helper.CreateParameter(0.0f),
                    InVehicleTimeMatrix = Helper.CreateParameter("mf0"),
                    ImpedanceMatrix = Helper.CreateParameter("mf0"),
                    LinkFareAttributeId = Helper.CreateParameter("@lfare"),
                    Mode = Helper.CreateParameter("*"),
                    PerceivedTravelTimeMatrix = Helper.CreateParameter("mf0"),
                    SegmentFareAttributeId = Helper.CreateParameter("@sfare"),
                    WaitTimePerception = Helper.CreateParameter(0.0f),
                    WaitTimeMatrix = Helper.CreateParameter("mf0"),
                    WalkTimePerceptionAttributeId = Helper.CreateParameter("@walkp"),
                    WalkTimeMatrix = Helper.CreateParameter("mf0"),
                    WalkPerceptions =  Helper.CreateParameters(walkPerceptions),
                }
            };
            var surfaceTransitSpeeds = new[]
            {
                new Emme.Assign.AssignTransit.SurfaceTransitSpeedModel()
                {
                    Name = "STSM1",
                    AlightingDuration = Helper.CreateParameter(1.1219f),
                    BoardingDuration = Helper.CreateParameter(1.9577f),
                    DefaultDuration = Helper.CreateParameter(7.4331f),
                    GlobalEROWSpeed = Helper.CreateParameter(35f),
                    LineFilterExpression = Helper.CreateParameter(""),
                    ModeFilterExpression = Helper.CreateParameter("b"),
                    TransitAutoCorrelation = Helper.CreateParameter(1.612f),
                }
            };
            var ttfDefinitions = new[]
            {
                new Emme.Assign.AssignTransit.TTFDefinition()
                {
                    Name = "TTF4",
                    CongestionExponent = Helper.CreateParameter(5.972385f),
                    CongestionPerception = Helper.CreateParameter(1),
                    TTF = Helper.CreateParameter(4),
                },
                new Emme.Assign.AssignTransit.TTFDefinition()
                {
                    Name = "TTF2",
                    CongestionExponent = Helper.CreateParameter(5.972385f),
                    CongestionPerception = Helper.CreateParameter(1),
                    TTF = Helper.CreateParameter(2),
                },
                new Emme.Assign.AssignTransit.TTFDefinition()
                {
                    Name = "TTF1",
                    CongestionExponent = Helper.CreateParameter(5.972385f),
                    CongestionPerception = Helper.CreateParameter(1),
                    TTF = Helper.CreateParameter(1),
                }
            };
            var module = new Emme.Assign.AssignTransit()
            {
                CalculateCongestedIvttFlag = Helper.CreateParameter(true),
                NodeLogitScale = Helper.CreateParameter(true),
                EffectiveHeadwayAttributeId = Helper.CreateParameter("@ehdw"),
                EffectiveHeadwaySlope = Helper.CreateParameter(0.165f),
                HeadwayFractionAttributeId = Helper.CreateParameter("@frac"),
                Iterations = Helper.CreateParameter(5),
                NormalizedGap = Helper.CreateParameter(0.0f),
                RelativeGap = Helper.CreateParameter(0.0f),
                ScenarioNumber = Helper.CreateParameter(2),
                WalkSpeed = Helper.CreateParameter(4.0f),
                CongestionExponent = Helper.CreateParameter(""),
                AssignmentPeriod = Helper.CreateParameter(3.0f),
                NameString = Helper.CreateParameter(""),
                CongestedAssignment = Helper.CreateParameter(true),
                CSVFile = Helper.CreateParameter(""),
                OriginDistributionLogitScale = Helper.CreateParameter(0.0f),
                WalkDistributionLogitScale = Helper.CreateParameter(0.0f),
                SurfaceTransitSpeed = Helper.CreateParameter(false),
                WalkAllWayFlag = Helper.CreateParameter(false),
                XRowTTFRange = Helper.CreateParameter(""),
                TransitClasses = Helper.CreateParameters(transitClasses),
                SurfaceTransitSpeeds = Helper.CreateParameters(surfaceTransitSpeeds),
                TTFDefinitions = Helper.CreateParameters(ttfDefinitions)
            };
            module.Invoke(Helper.Modeller);
        }
    }
}
