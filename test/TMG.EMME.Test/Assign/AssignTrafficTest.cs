/*
    Copyright 2022-2026 University of Toronto

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
using System.Diagnostics;
using System.IO;

namespace TMG.Emme.Test.Assign;

[TestClass]
public class AssignTrafficTest : TestBase
{
    const int ScenarioNumber = 1;

    [TestMethod]
    public void AssignTrafficDirectToolCall()
    {
        SetupDatabase();

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
                writer.WriteNumber("scenario_number", ScenarioNumber);
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
                writer.WriteNumber("demand_matrix", 10);
                writer.WriteNumber("time_matrix", 0);
                writer.WriteNumber("cost_matrix", 4);
                writer.WriteNumber("toll_matrix", 0);
                writer.WriteNumber("peak_hour_factor", 1);
                writer.WriteString("volume_attribute", "@auto_volume1");
                writer.WriteString("link_toll_attribute", " @toll");
                writer.WriteNumber("toll_weight", 1.0);
                writer.WriteNumber("link_cost", 0.0);
                writer.WriteStartArray("path_analyses");
                writer.WriteStartObject();
                writer.WriteString("attribute_id", "@auto_volume1");
                writer.WriteNumber("aggregation_matrix", 0);
                writer.WriteString("aggregation_operator", ".max.");
                writer.WriteNumber("lower_bound", 7);
                writer.WriteNumber("upper_bound", 7);
                writer.WriteString("path_selection", "SELECTED");
                writer.WriteBoolean("multiply_path_prop_by_demand", true);
                writer.WriteBoolean("multiply_path_prop_by_value", true);
                writer.WriteString("analysis_attributes", "");
                writer.WriteNumber("analyzed_demand", 0);
                writer.WriteEndObject();
                writer.WriteEndArray();
                writer.WriteEndObject();
                writer.WriteEndArray();

            }), LogbookLevel.Standard));
    }

    [TestMethod]
    public void AssignTrafficModule()
    {
        SetupDatabase();

        var pathAnalyses = new[]
        {
            new Emme.Assign.AssignTraffic.PathAnalysis()
            {
                Name = "PathAnalysis",
                AttributeId = Helper.CreateParameter("@auto_volume1"),
                AggregationMatrix = Helper.CreateParameter(0),
                AggregationOperator = Helper.CreateParameter(".max."),
                LowerBound = Helper.CreateParameter(7.0f),
                UpperBound = Helper.CreateParameter(7.0f),
                PathSelection = Helper.CreateParameter("SELECTED"),
                MultiplyPathPropByDemand = Helper.CreateParameter(true),
                MultiplyPathPropByValue = Helper.CreateParameter(true),
                AnalyzedDemand = Helper.CreateParameter(0),
            }
        };

        var trafficClasses = new[]
        {
            new Emme.Assign.AssignTraffic.TrafficClass()
            {
                Name = "TrafficClass1",
                Mode = Helper.CreateParameter('j'),
                DemandMatrixNumber = Helper.CreateParameter(10),
                TimeMatrix = Helper.CreateParameter(0),
                CostMatrix = Helper.CreateParameter(4),
                TollMatrix = Helper.CreateParameter(0),
                PeakHourFactor = Helper.CreateParameter(1f),
                VolumeAttribute = Helper.CreateParameter("@auto_volume1"),
                LinkTollAttribute = Helper.CreateParameter("@toll"),
                TollWeight = Helper.CreateParameter(1.0f),
                LinkCost = Helper.CreateParameter(0.0f),
                PathAnalyses = Helper.CreateParameters(pathAnalyses),
            },

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
            TrafficClasses = trafficClasses,
        };
        module.Invoke(Helper.Modeller);
    }

    [TestMethod]
    public void AssignTrafficModuleMultiClass()
    {
        SetupDatabase();

        var pathAnalyses = new[]
        {
            new Emme.Assign.AssignTraffic.PathAnalysis()
            {
                Name = "PathAnalysis",
                AttributeId = Helper.CreateParameter("@auto_volume1"),
                AggregationMatrix = Helper.CreateParameter(0),
                AggregationOperator = Helper.CreateParameter(".max."),
                LowerBound = Helper.CreateParameter(7.0f),
                UpperBound = Helper.CreateParameter(7.0f),
                PathSelection = Helper.CreateParameter("SELECTED"),
                MultiplyPathPropByDemand = Helper.CreateParameter(true),
                MultiplyPathPropByValue = Helper.CreateParameter(true),
                AnalyzedDemand = Helper.CreateParameter(0),
            }
        };

        var trafficClasses = new[]
        {
            new Emme.Assign.AssignTraffic.TrafficClass()
            {
                Name = "TrafficClass1",
                Mode = Helper.CreateParameter('j'),
                DemandMatrixNumber = Helper.CreateParameter(10),
                TimeMatrix = Helper.CreateParameter(0),
                CostMatrix = Helper.CreateParameter(4),
                TollMatrix = Helper.CreateParameter(0),
                PeakHourFactor = Helper.CreateParameter(1f),
                VolumeAttribute = Helper.CreateParameter("@auto_volume1"),
                LinkTollAttribute = Helper.CreateParameter("@toll"),
                TollWeight = Helper.CreateParameter(1.0f),
                LinkCost = Helper.CreateParameter(0.0f),
                PathAnalyses = Helper.CreateParameters(pathAnalyses),
            },

            new Emme.Assign.AssignTraffic.TrafficClass()
            {
                Name = "TrafficClass2",
                Mode = Helper.CreateParameter('j'),
                DemandMatrixNumber = Helper.CreateParameter(11),
                TimeMatrix = Helper.CreateParameter(0),
                CostMatrix = Helper.CreateParameter(4),
                TollMatrix = Helper.CreateParameter(0),
                PeakHourFactor = Helper.CreateParameter(1f),
                VolumeAttribute = Helper.CreateParameter("@auto_volume2"),
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
            TrafficClasses = trafficClasses,
        };
        module.Invoke(Helper.Modeller);
    }

    [TestMethod]
    public void AssignTrafficModuleNoPathAnalysis()
    {
        SetupDatabase();

        Emme.Assign.AssignTraffic.PathAnalysis[] pathAnalyses = [];

        var trafficClasses = new[]
        {
            new Emme.Assign.AssignTraffic.TrafficClass()
            {
                Name = "TrafficClass1",
                Mode = Helper.CreateParameter('c'),
                DemandMatrixNumber = Helper.CreateParameter(10),
                TimeMatrix = Helper.CreateParameter(0),
                CostMatrix = Helper.CreateParameter(4),
                TollMatrix = Helper.CreateParameter(0),
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
            TrafficClasses = trafficClasses,
        };
        module.Invoke(Helper.Modeller);
    }

    private static void SetupDatabase()
    {
        Helper.ImportFrabitztownNetwork(ScenarioNumber);
        Helper.ImportBinaryMatrix(ScenarioNumber, 10, Path.GetFullPath("TestFiles/Test.mtx"));
        Helper.ImportBinaryMatrix(ScenarioNumber, 11, Path.GetFullPath("TestFiles/Test.mtx"));
    }
}
