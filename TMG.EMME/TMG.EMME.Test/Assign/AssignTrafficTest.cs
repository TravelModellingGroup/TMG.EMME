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
    public class AssignTrafficTest : TestBase
    {
        [TestMethod]
        public void AssignTraffic()
        {
            var scenarioNumber = 2;
            Helper.ImportFrabitztownNetwork(scenarioNumber);
            Helper.ImportBinaryMatrix(scenarioNumber, 10, Path.GetFullPath("TestFiles/Test.mtx"));
            Assert.IsTrue(
                Helper.Modeller.Run(null, "tmg2.Assign.assign_traffic",
                JSONParameterBuilder.BuildParameters(writer =>
                {
                    writer.WriteBoolean("background_transit", true);
                    writer.WriteNumber("br_gap", 0);
                    writer.WriteNumber("iterations", 4);
                    writer.WriteNumber("norm_gap", 0);
                    writer.WriteBoolean("performance_flag", true);
                    writer.WriteNumber("r_gap", 0);
                    writer.WriteString("run_title", "road assignment");
                    writer.WriteNumber("scenario_number", scenarioNumber);
                    writer.WriteBoolean("sola_flag", true);
                    writer.WritePropertyName("mixed_use_ttf_ranges");
                    writer.WriteStartArray();
                    writer.WriteStartObject();
                    writer.WriteNumber("start", 3);
                    writer.WriteNumber("stop", 128);
                    writer.WriteEndObject();
                    writer.WriteEndArray();
                    writer.WriteStartArray("traffic_classes");
                    writer.WriteStartObject();
                    writer.WriteString("name", "traffic class 1");
                    writer.WriteString("mode", "c");
                    writer.WriteString("demand_matrix", "mf10");
                    writer.WriteString("time_matrix", "mf0");
                    writer.WriteString("cost_matrix", "mf4");
                    writer.WriteString("toll_matrix", "mf0");
                    writer.WriteNumber("peak_hour_factor", 1);
                    writer.WriteString("volume_attribute", "@auto_volume1");
                    writer.WriteString("link_toll_attribute", " @toll");
                    writer.WriteNumber("toll_weight", 1.0);
                    writer.WriteNumber("link_cost", 0.0);
                    writer.WriteStartArray("path_analyses");
                    writer.WriteStartObject();
                    writer.WriteString("attribute_id", "1");
                    writer.WriteString("aggregation_matrix", "");
                    writer.WriteString("aggregation_operator", "max");
                    writer.WriteString("lower_bound", "7");
                    writer.WriteString("upper_bound", "7");
                    writer.WriteString("path_selection", "all");
                    writer.WriteString("multiply_path_prop_by_demand", "7");
                    writer.WriteString("multiply_path_prop_by_value", "7");
                    writer.WriteString("analysis_attributes", "");
                    writer.WriteString("analysis_attributes_matrix", "mf0");
                    writer.WriteEndObject();
                    writer.WriteEndArray();
                    writer.WriteEndObject();
                    writer.WriteEndArray();

                }), LogbookLevel.Standard));
        }

        [TestMethod]
        public void AssignTrafficModule()
        {
            Helper.ImportFrabitztownNetwork(1);
            Helper.ImportBinaryMatrix(1, 10, Path.GetFullPath("TestFiles/Test.mtx"));

            var pathAnalyses = new[]
            {
                new Emme.Assign.AssignTraffic.PathAnalysis()
                {
                    Name = "PathAnalysis",
                    AttributeId = Helper.CreateParameter("1"),
                    AggregationMatrix = Helper.CreateParameter(""),
                    AggregationOperator = Helper.CreateParameter("max"),
                    LowerBound = Helper.CreateParameter("7"),
                    UpperBound = Helper.CreateParameter("7"),
                    PathSelection = Helper.CreateParameter("all"),
                    MultiplyPathPropByDemand = Helper.CreateParameter("7"),
                    MultiplyPathPropByValue = Helper.CreateParameter("7"),
                    AnalysisAttributes = Helper.CreateParameter(""),
                    AnalysisAttributesMatrixId = Helper.CreateParameter("mf0"),
                }
            };

            var trafficClasses = new[]
            {
                new Emme.Assign.AssignTraffic.TrafficClass()
                {
                    Name = "TrafficClass1",
                    Mode = Helper.CreateParameter('c'),
                    DemandMatrixNumber = Helper.CreateParameter("mf10"),
                    TimeMatrix = Helper.CreateParameter("mf0"),
                    CostMatrix = Helper.CreateParameter("mf4"),
                    TollMatrix = Helper.CreateParameter("mf0"),
                    PeakHourFactor = Helper.CreateParameter(1f),
                    VolumeAttribute = Helper.CreateParameter("@auto_volume1"),
                    LinkTollAttribute = Helper.CreateParameter("@toll"),
                    TollWeight = Helper.CreateParameter(1.0f),
                    LinkCost = Helper.CreateParameter(0.0f),
                    PathAnalyses = Helper.CreateParameters(pathAnalyses),
                }
            };
            var module = new Emme.Assign.AssignTraffic()
            {
                Name = "AssignTraffic",
                BackgroundTransit = Helper.CreateParameter(true),
                brGap = Helper.CreateParameter(0f),
                Iterations = Helper.CreateParameter(100),
                normGap = Helper.CreateParameter(0f),
                PerformanceFlag = Helper.CreateParameter(true),
                rGap = Helper.CreateParameter(0f),
                RunTitle = Helper.CreateParameter("road assignment"),
                ScenarioNumber = Helper.CreateParameter(1),
                SOLAFlag = Helper.CreateParameter(true),
                MixedUseTTFRanges = Helper.CreateParameter(new RangeSet(new List<Range> { new Range(3, 128) })),
                TrafficClasses = Helper.CreateParameters(trafficClasses),
            };
            module.Invoke(Helper.Modeller);
        }
    }
}
